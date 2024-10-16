import logging

import pytz
from telethon.tl.custom import Forward
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import User, Chat, Channel

from cleanup.config.scan_config import Config
from cleanup.docextract.scan_data import ScanDataType, ScanData
from cleanup.login_module import get_phone_number, login, create_client
from cleanup.storage.pg import PostgresStorage
from cleanup.utils import first_not_null, getattrd

logger = logging.getLogger(__name__)


class TelegramScanner:
    def __init__(self, config: Config, scan_data: list[ScanData]):
        if not scan_data:
            raise ValueError("No scan data provided.")
        if not config.telegram.api_id or not config.telegram.api_hash:
            raise ValueError("Telegram API ID and API hash are required in the configuration.")
        self.utc = pytz.UTC
        self.config = config
        self.telegram_config = config.telegram
        self.scan_data = scan_data
        self.cache_storage = PostgresStorage() if self.telegram_config.cache_messages or self.telegram_config.cache_peers else None
        self.ignored_ids = [int(d.data) for d in scan_data if d.data_type.to_str() == ScanDataType.TG_IGNORED_ID.to_str()]

    @staticmethod
    def get_peer_type(chat):
        if isinstance(chat, User):
            return 'user'
        elif isinstance(chat, Chat):
            return 'chat'
        elif isinstance(chat, Channel):
            return 'channel'
        return 'unknown'

    def __should_skip_dialog(self, dialog, from_date=None, to_date=None):
        dialog_date = dialog.date.replace(tzinfo=self.utc)
        return dialog.id in self.ignored_ids or dialog_date < from_date or dialog_date > to_date

    async def __clean_up_telegram(self, client):
        current_user = await client.get_me()
        current_user_id = getattr(current_user, 'id')

        async for dialog in client.iter_dialogs(limit=None, offset_date=self.telegram_config.to_date):
            dialog_id = dialog.id

            if self.__should_skip_dialog(dialog, self.telegram_config.from_date, self.telegram_config.to_date):
                continue

            if self.telegram_config.cache_peers:
                self.cache_storage.store_user_dialog(dialog_id, current_user_id)

            chat = await client.get_entity(dialog.id)
            dialog_name = first_not_null(getattrd(dialog, 'title'), getattrd(dialog, 'name'), self.get_chat_title(chat),
                                         dialog.id)

            print(dialog_name, dialog_id, chat.__class__.__name__)
            chat_id = dialog_id
            chat_username = getattr(chat, 'username', 'unknown')

            if isinstance(chat, User) and not self.telegram_config.dialogs.chats.enabled:
                print(f"Skipping user {dialog_name} (ID {dialog_id})")
                continue
            if isinstance(chat, Chat) and not self.telegram_config.dialogs.chats.enabled:
                print(f"Skipping chat {dialog_name} (ID {dialog_id})")
                continue
            if isinstance(chat, Channel) and not self.telegram_config.dialogs.channels.enabled:
                print(f"Skipping channel {dialog_name} (ID {dialog_id})")
                continue

            if self.telegram_config.dialogs.checks.enabled:
                for material in self.scan_data:
                    if material.data_type.to_str() == ScanDataType.TG_ID.to_str():
                        idd = int(material.data)
                        if chat_id == idd or chat_id == -idd or -idd == 1000000000000 - chat_id:
                            print(
                                f"------------------------------  Found dialog check violation: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                            continue
                    elif material.data_type.to_str() == ScanDataType.TG_USERNAME.to_str():
                        username = material.data
                        if chat_username == username:
                            print(
                                f"------------------------------  Found dialog check violation: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                            continue
                    elif material.data_type.to_str() == ScanDataType.TG_USER_NAME.to_str():
                        name = material.data
                        if dialog_name == name:
                            print(
                                f"------------------------------  Found dialog check violation: {dialog_name} (ID {dialog_id}) ------------------------------ ")
                            continue

            if self.telegram_config.cache_peers:
                self.cache_storage.store_peer([{
                    'id': dialog.id,
                    'title': dialog_name,
                    'username': chat_username,
                    'peer_type': self.get_peer_type(chat),
                    'users_count': 0,
                    'data': chat.to_json(ensure_ascii=False)
                }])

            if isinstance(chat, (User, Chat)):
                print(f"Starting processing chat {dialog_name} (ID {dialog_id})")
                await self.clean_chat(chat, client, current_user_id, dialog_id, dialog_name)
                if self.telegram_config.cache_peers:
                    self.cache_storage.mark_dialog_processed(dialog_id, current_user_id)
            elif isinstance(chat, Channel):
                if getattrd(chat, 'broadcast'):
                    print(f"Skipping broadcast channel {dialog_name} (ID {dialog_id})")
                    continue

                channel_full_info = await client(GetFullChannelRequest(chat))
                participants_count = getattrd(channel_full_info, 'full_chat.participants_count')
                if self.telegram_config.cache_peers:
                    self.cache_storage.store_full_chat_data(dialog_id, channel_full_info.to_json(ensure_ascii=False))
                    self.cache_storage.store_users_count(dialog_id, participants_count)
                filter_user = None
                if participants_count is not None and participants_count > self.telegram_config.dialogs.channels.self_only_after_users_count:
                    filter_user = current_user
                print(
                    f"Starting processing channel {dialog_name} (ID {dialog_id}), participants count: {participants_count}")
                await self.clean_chat(chat, client, current_user_id, dialog_id, dialog_name,
                                      from_user=filter_user)
                if self.telegram_config.cache_peers:
                    self.cache_storage.mark_dialog_processed(dialog_id, current_user_id)

    async def clean_chat(self, chat, client, current_user_id, dialog_id, dialog_name,
                         from_user=None):
        total_messages = 0
        total_deleted = 0
        async for message in client.iter_messages(chat, from_user=from_user, reverse=True,
                                                  offset_date=self.telegram_config.from_date):
            if message.date.replace(tzinfo=self.utc) > self.telegram_config.to_date:
                break

            if self.telegram_config.cache_messages:
                self.cache_storage.store_messages([{
                    'id': message.id,
                    'user_id': current_user_id,
                    'dialog_id': dialog_id,
                    'dialog_name': dialog_name,
                    'message_text': getattrd(message, 'message'),
                    'message': message.to_json(ensure_ascii=False),
                }])
            total_messages += 1
            deleted = await self.check_forward_from_unwanted(chat, client, message)
            if not deleted:
                deleted = await self.check_message_text(chat, client, message)
            if deleted:
                total_deleted += 1
                if self.telegram_config.cache_messages:
                    self.cache_storage.mark_message_deleted(message.id, dialog_id)

            if total_messages % 1000 == 0:
                print(f"Processed {total_messages} messages in chat: {dialog_name}")
        print(
            f"Cleanup complete for chat: {dialog_name}. Total messages processed: {total_messages}, deleted: {total_deleted}")

    async def check_message_text(self, chat, client, message):
        text = message.text
        if not text or len(text) < 5:
            return 0

        for material in self.scan_data:
            source = material.data_type
            material = material.data

            if source.to_str() == ScanDataType.TG_USERNAME.to_str() or source.to_str() == ScanDataType.TG_USER_NAME.to_str():
                if "@" + material in text or "t.me/" + material in text:
                    if await self.prompt_delete_message(chat, client, message, force=True, dryRun=True,
                                                        reason=f"========================================== Contains unwanted username: {material} ========================================== "):
                        return 1

            if (
                    source.to_str() == ScanDataType.TG_KEYWORD.to_str() or source.to_str() == ScanDataType.TG_URL.to_str() or source.to_str() == ScanDataType.INSTAGRAM_NAME.to_str() or source.to_str() == ScanDataType.INSTAGRAM_USERNAME.to_str()):
                if material in text:
                    if await self.prompt_delete_message(chat, client, message, force=True, dryRun=True,
                                                        reason=f"========================================== Contains unwanted text or URL: {material} ========================================== "):
                        return 1
        return 0

    @staticmethod
    def lower(s):
        if s:
            return s.lower()

    @staticmethod
    def nullable_int(s):
        if s:
            try:
                return int(s)
            except:
                return 0
        return 0

    async def check_forward_from_unwanted(self, chat, client, message):
        forward_from = getattr(message, 'forward', None)
        if forward_from and isinstance(forward_from, Forward):
            chat_username = self.lower(getattrd(forward_from, "chat.username"))
            chat_title = self.lower(getattrd(forward_from, "chat.title"))
            chat_id = self.nullable_int(getattrd(forward_from, 'chat_id'))
            channel_id = self.nullable_int(getattrd(forward_from, 'from_id.channel_id'))

            for material in self.scan_data:
                if material.data_type.to_str() == ScanDataType.TG_USERNAME.to_str():
                    username = material.data
                    if chat_username == username or chat_title == username:
                        if await self.prompt_delete_message(chat, client, message, dryRun=False, force=True,
                                                            reason=f"========================================== Forwarded from unwanted channel: {material} =========================================="):
                            return 1

                elif material.data_type.to_str() == ScanDataType.TG_USER_NAME.to_str():
                    name = material.data
                    if chat_username == name or chat_title == name:
                        if await self.prompt_delete_message(chat, client, message, dryRun=False, force=True,
                                                            reason=f"========================================== Forwarded from unwanted channel: {material} =========================================="):
                            return 1

                elif material.data_type.to_str() == ScanDataType.TG_ID.to_str():
                    idd = int(material.data)
                    if chat_id == idd or chat_id == -idd or channel_id == idd or channel_id == -idd or -idd == 1000000000000 - chat_id or -idd == 1000000000000 - channel_id:
                        if await self.prompt_delete_message(chat, client, message, dryRun=False, force=True,
                                                            reason=f"===================== Forwarded from unwanted channel: {material} =========================================="):
                            return 1

        return 0

    @staticmethod
    def get_chat_title(chat):
        return first_not_null(getattrd(chat, 'title'), getattrd(chat, 'name'), getattr(chat, 'username', None))

    async def prompt_delete_message(self, chat, client, message, force=False, reason=None, dryRun=True):
        chat_username = getattrd(chat, 'username')
        chat_title = self.get_chat_title(chat)
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

    async def __clean_up_from_db(self, client):
        current_user = await client.get_me()
        current_user_id = getattr(current_user, 'id')
        tg_usernames = [item.data.lower() for item in self.scan_data if
                        (item.data_type.to_str() == ScanDataType.TG_USERNAME.to_str())]
        storage = PostgresStorage()
        mentions = [item.data.lower() for item in self.scan_data if
                    (item.data_type.to_str() == ScanDataType.TG_KEYWORD.to_str())]

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

    async def __process(self, client, phone_number):
        await login(client, phone_number)
        await self.__clean_up_telegram(client)

    async def __process_from_db(self, client, phone_number):
        await login(client, phone_number)
        await self.__clean_up_from_db(client)

    def scan(self):
        cache_dir = self.config.paths.cache_dir
        phone_number = get_phone_number(cache_dir)
        client = create_client(phone_number, cache_dir, self.config.telegram.api_id, self.config.telegram.api_hash)
        with client:
            client.loop.run_until_complete(self.__process(client, phone_number))

#
# if __name__ == "__main__":
#     config, config_exists = load_config("config.yaml")
#     scan_data = load_scan_data(config)
#     scanner = TelegramScanner(config, scan_data)
#     scanner.scan()
