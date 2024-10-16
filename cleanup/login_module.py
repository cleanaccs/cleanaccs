import os
import json
import getpass
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

def get_phone_number(cache_dir):
    last_phone_file = os.path.join(cache_dir, 'last_phone.json')

    if os.path.exists(last_phone_file):
        with open(last_phone_file, 'r') as f:
            last_phone = json.load(f).get('phone_number', None)
    else:
        last_phone = None

    # Get user's phone number
    if last_phone:
        phone_number = input(f"Press Enter to use the last used phone number ({last_phone}) or enter a new one: ")
        phone_number = phone_number if phone_number != '' else last_phone
    else:
        phone_number = input("Enter your phone number: ")

    # Save the phone number to file
    with open(last_phone_file, 'w') as f:
        json.dump({'phone_number': phone_number}, f)
    return phone_number

async def login(client, phone_number):
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        try:
            await client.sign_in(phone_number, input('Enter the code you received: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=getpass.getpass("Enter your 2FA password: "))

def create_client(phone_number, cache_dir, api_id, api_hash):
    return TelegramClient(f'{cache_dir}/session_{phone_number}', api_id, api_hash)
