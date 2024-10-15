import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from telethon.tl.custom import Forward
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import User, Chat, Channel

from cleanup.docextract.channel import load_unwanted_materials, MaterialType, UnwantedMaterial
from cleanup.login_module import get_phone_number, login, create_client
from cleanup.storage.pg import PostgresStorage
from cleanup.utils import first_not_null, getattrd

# Load environment variables from .env file
load_dotenv()

# Replace these with your own values
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
version = "2"

# Set cache directory
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

# dry_run = True

utc = pytz.UTC


# Function to clean up undesired messages

def get_peer_type(chat):
    if isinstance(chat, User):
        return 'user'
    elif isinstance(chat, Chat):
        return 'chat'
    elif isinstance(chat, Channel):
        return 'channel'
    return 'unknown'


def should_skip_dialog(dialog):
    dialog_date = dialog.date.replace(tzinfo=utc)
    return dialog_date < from_date or dialog_date > to_date


from_date = datetime(2018, 1, 1, 0, 0, 0).replace(tzinfo=utc)
to_date = datetime(2025, 2, 1, 0, 0, 0).replace(tzinfo=utc)


async def clean_up_telegram(client, dry_run=False):
    # Initialize chat cache
    # chat_cache = ChatCache(os.path.join(cache_dir, 'chat_cache.json'), client)
    # processed_cache = ProcessedUsersCache(os.path.join(cache_dir, 'processed_cache.json'))
    current_user = await client.get_me()
    current_user_id = getattr(current_user, 'id')
    unwanted_materials = load_unwanted_materials(os.path.join(cache_dir, 'unwanted_2.json'))
    storage = PostgresStorage()

    # Iterate over all dialogs (chats, groups, channels)
    async for dialog in client.iter_dialogs(limit=None, offset_date=to_date):
        dialog_id = dialog.id

        if should_skip_dialog(dialog):
            continue

        # if storage.get_is_dialog_processed(dialog_id, current_user_id):
        #     continue

        storage.store_user_dialog(dialog_id, current_user_id)

        # Get chat entity
        chat = await client.get_entity(dialog.id)

        dialog_name = first_not_null(getattrd(dialog, 'title'), getattrd(dialog, 'name'), get_chat_title(chat),
                                     dialog.id)
        # if processed_cache.is_processed(chat.id, version):
        #     continue

        print(dialog_name, dialog_id, chat.__class__.__name__)

        chat_id = dialog_id
        chat_username = getattr(chat, 'username', 'unknown')

        for material in unwanted_materials:
            if material.source.to_str() == MaterialType.TG_ID.to_str():
                idd = int(material.material)
                if chat_id == idd or chat_id == -idd or -idd == 1000000000000 - chat_id:
                    print(f"------------------------------  Found: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                    continue
            elif material.source.to_str() == MaterialType.TG_USERNAME.to_str():
                username = material.material
                if chat_username == username:
                    print(f"------------------------------  Found: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                    continue
            elif material.source.to_str() == MaterialType.TG_NAME.to_str():
                name = material.material
                if dialog_name == name:
                    print(f"------------------------------  Found: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                    continue

        continue

        storage.store_peer([{
            'id': dialog.id,
            'title': dialog_name,
            'username': chat_username,
            'peer_type': get_peer_type(chat),
            'users_count': 0,
            'data': chat.to_json(ensure_ascii=False)
        }])

        if isinstance(chat, (User, Chat)):  # Skip if it's not a chat or user
            print(f"Starting processing chat {dialog_name} (ID {dialog_id})")
            await clean_chat(chat, client, current_user_id, dialog_id, dialog_name, storage, unwanted_materials,
                             dry_run=dry_run)
            storage.mark_dialog_processed(dialog_id, current_user_id)
        elif isinstance(chat, Channel):
            if getattrd(chat, 'broadcast'):
                print(f"Skipping broadcast channel {dialog_name} (ID {dialog_id})")
                continue

            channel_full_info = await client(GetFullChannelRequest(chat))
            storage.store_full_chat_data(dialog_id, channel_full_info.to_json(ensure_ascii=False))
            participants_count = getattrd(channel_full_info, 'full_chat.participants_count')
            storage.store_users_count(dialog_id, participants_count)
            filter_user = None
            if participants_count is not None and participants_count > 50:
                filter_user = current_user
            print(
                f"Starting processing channel {dialog_name} (ID {dialog_id}), participants count: {participants_count}")
            await clean_chat(chat, client, current_user_id, dialog_id, dialog_name, storage, unwanted_materials,
                             from_user=filter_user, dry_run=dry_run)
            storage.mark_dialog_processed(dialog_id, current_user_id)

        # user_input = input("Type any button to start processing or 's' to proceed to the next one")
        # if user_input.lower() == 's':
        #     # processed_cache.update_processed(chat.id, version, getattrd(chat, 'username'), dialog_name, 0, 0)
        #     continue


async def clean_chat(chat, client, current_user_id, dialog_id, dialog_name, storage, unwanted_channels, from_user=None,
                     dry_run=False):
    total_messages = 0
    total_deleted = 0
    async for message in client.iter_messages(chat, from_user=from_user, reverse=True, offset_date=from_date):
        if message.date.replace(tzinfo=utc) > to_date:
            break
        storage.store_messages([{
            'id': message.id,
            'user_id': current_user_id,
            'dialog_id': dialog_id,
            'dialog_name': dialog_name,
            'message_text': getattrd(message, 'message'),
            'message': message.to_json(ensure_ascii=False),
        }])
        total_messages += 1
        # chat = await chat_cache.get_chat_entity(message.peer_id)
        deleted = await check_forward_from_unwanted(chat, client, message,
                                                    unwanted_channels)
        if not deleted:
            deleted = await check_message_text(chat, client, message,
                                               unwanted_channels)
        if deleted:
            total_deleted += 1
            storage.mark_message_deleted(message.id, dialog_id)

        if total_messages % 1000 == 0:
            print(f"Processed {total_messages} messages in chat: {dialog_name}")
    print(
        f"Cleanup complete for chat: {dialog_name}. Total messages processed: {total_messages}, deleted: {total_deleted}")


async def check_message_text(chat, client, message, unwanted_materials: list[UnwantedMaterial]):
    text = message.text
    if not text or len(text) < 5:
        return 0

    for material in unwanted_materials:
        source = material.source
        material = material.material

        if source.to_str() == MaterialType.TG_USERNAME.to_str() or source.to_str() == MaterialType.TG_NAME.to_str():
            if "@" + material in text or "t.me/" + material in text:
                # if material in text:
                if await prompt_delete_message(chat, client, message, force=True, dryRun=True,
                                               reason=f"========================================== Contains unwanted username: {material} ========================================== "):
                    return 1

        if (source.to_str() == MaterialType.TG_KEYWORD.to_str() or
                source.to_str() == MaterialType.URL.to_str() or
                source.to_str() == MaterialType.INSTAGRAM_NAME.to_str() or
                source.to_str() == MaterialType.INSTAGRAM_LINK.to_str()):
            # if "@" + material.username in text or "t.me/" + material.username in text:
            if material in text:
                if await prompt_delete_message(chat, client, message, force=True, dryRun=True,
                                               reason=f"========================================== Contains unwanted text or URL: {material} ========================================== "):
                    return 1
    return 0


def lower(s):
    if s:
        return s.lower()


def nullable_int(s):
    if s:
        try:
            return int(s)
        except:
            return 0
    return 0


async def check_forward_from_unwanted(chat, client, message, unwanted_materials: list[UnwantedMaterial]):
    forward_from = getattr(message, 'forward', None)
    if forward_from and isinstance(forward_from, Forward):
        chat_username = lower(getattrd(forward_from, "chat.username"))
        chat_title = lower(getattrd(forward_from, "chat.title"))
        chat_id = nullable_int(getattrd(forward_from, 'chat_id'))
        channel_id = nullable_int(getattrd(forward_from, 'from_id.channel_id'))

        for material in unwanted_materials:
            if material.source.to_str() == MaterialType.TG_USERNAME.to_str():
                username = material.material
                if chat_username == username or chat_title == username:
                    if await prompt_delete_message(chat, client, message, dryRun=False,
                                                   force=True,
                                                   reason=f"========================================== Forwarded from unwanted channel: {material} =========================================="):
                        return 1

            elif material.source.to_str() == MaterialType.TG_NAME.to_str():
                name = material.material
                if chat_username == name or chat_title == name:
                    if await prompt_delete_message(chat, client, message, dryRun=False,
                                                   force=True,
                                                   reason=f"========================================== Forwarded from unwanted channel: {material} =========================================="):
                        return 1

            elif material.source.to_str() == MaterialType.TG_ID.to_str():
                idd = int(material.material)
                if chat_id == idd or chat_id == -idd or channel_id == idd or channel_id == -idd or -idd == 1000000000000 - chat_id or -idd == 1000000000000 - channel_id:
                    if await prompt_delete_message(chat, client, message, dryRun=False,
                                                   force=True,
                                                   reason=f"===================== Forwarded from unwanted channel: {material} =========================================="):
                        return 1

    return 0


def get_chat_title(chat):
    return first_not_null(getattrd(chat, 'title'), getattrd(chat, 'name'), getattr(chat, 'username', None))


async def prompt_delete_message(chat, client, message, force=False, reason=None, dryRun=True):
    chat_username = getattrd(chat, 'username')
    chat_title = get_chat_title(chat)
    message_content = message.message.replace("\n", " ")
    print(f"[chat: id={chat.id} @{chat_username} {chat_title}] [message: {message_content}]")
    if reason:
        print(f"Reason: {reason}")
    if dryRun:
        return False
    if force or input("Type any button or type 'no' to skip: ") != "no":
        await client.delete_messages(chat.id, [message.id])
        print("Message deleted.")
        print("------------------------------------------------------")
        return True
    return False


async def clean_up_from_db(client):
    current_user = await client.get_me()
    current_user_id = getattr(current_user, 'id')
    unwanted_materials = load_unwanted_materials(os.path.join(cache_dir, 'unwanted_2.json'))
    tg_usernames = [item.material.lower() for item in unwanted_materials if
                    (item.source.to_str() == MaterialType.TG_USERNAME.to_str())]
    storage = PostgresStorage()
    mentions = [item.material.lower() for item in unwanted_materials if
                (item.source.to_str() == MaterialType.TG_KEYWORD.to_str())]

    total_count = storage.count_messages(current_user_id)
    count = 0
    for message in storage.load_messages_in_batches(current_user_id):
        count += 1
        if count % 10000 == 0:
            print(f"Processed {count}/{total_count}")
        if not message.message_text:
            continue
        for tg_username in tg_usernames:
            username = tg_username.replace("@", "").lower()
            if f"@{username}" in message.message_text.lower() or f"t.me/{username}" in message.message_text.lower():
                print(message.to_str(), f"Reason: contains {username}")
        # if message.message_text and message.message_text.lower() in mentions:
        #     print(message.to_str())


async def process(client, phone_number, dry_run=False):
    await login(client, phone_number)
    await clean_up_telegram(client, dry_run)


async def process_from_db(client, phone_number):
    await login(client, phone_number)
    await clean_up_from_db(client)


if __name__ == "__main__":
    phone_number = get_phone_number()
    client = create_client(phone_number)
    with client:
        client.loop.run_until_complete(
            process(client, phone_number, dry_run=True)
            # process_from_db(client, phone_number)
        )
