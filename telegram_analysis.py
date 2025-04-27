from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

client = TelegramClient('session_name', api_id, api_hash)

async def recent_private_group_activity():
    await client.start(phone=phone)

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    active_groups = set()

    logging.info("Fetching your group dialogs...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', False):
            logging.info(f"Checking group: {entity.title}")
            latest_message = await client.get_messages(entity, limit=1)
            if latest_message:
                latest_date = latest_message[0].date
                logging.info(f"Latest message in '{entity.title}' at {latest_date.isoformat()}")
                if latest_date >= yesterday:
                    active_groups.add(entity.title)

    logging.info("\n✅ Analysis completed.\n")
    print("\nPrivate groups active in the last 24 hours:")
    if active_groups:
        for group in active_groups:
            print(f"- {group}")
    else:
        print("No active private groups found.")

with client:
    client.loop.run_until_complete(recent_private_group_activity())
