"""
Setup script to authenticate with Telegram API
Run this script once to authenticate your Telegram account
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "telegram_session")
PHONE = os.getenv("TELEGRAM_PHONE")

if not API_ID or not API_HASH:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
    exit(1)

async def main():
    client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
    
    await client.start()
    print("Telegram client started")
    
    if not await client.is_user_authorized():
        print("Not authorized. Starting authentication...")
        
        if not PHONE:
            phone = input("Please enter your phone number (with country code, e.g., +1234567890): ")
        else:
            phone = PHONE
            print(f"Using phone number from .env: {phone}")
        
        await client.send_code_request(phone)
        
        try:
            code = input("Please enter the code you received: ")
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Two-step verification is enabled. Please enter your password: ")
            await client.sign_in(password=password)
        
        print("Successfully authenticated!")
    else:
        print("Already authorized!")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
    
    await client.disconnect()
    print("Setup complete! You can now run the API server.")

if __name__ == "__main__":
    asyncio.run(main())

