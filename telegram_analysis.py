from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging, os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

rep_handles = {
    "Aki Balogh": "Aki Balogh",
    "PMM": "Peter Moricz",
    "Amy Wu": "Amy Wu",
    "Walter Wong | Nolem Labs | RockX": "Walter Wong",
    "Kadeem Clarke": "Kadeem Clarke",
    "Mayank | iBTC": "Mayank Sachdev",
    "Dae L": "Dae Lee",
    "Jesse | iBTC": "Jesse Eisenberg",
    "Jesse Eisenberg": "Jesse Eisenberg"
}

client = TelegramClient('session_name', api_id, api_hash)

async def sales_rep_recent_activity():
    await client.start(phone=phone)

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    active_groups = {}

    logging.info("Checking groups for sales rep activity...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', False):
            logging.info(f"Scanning group: {entity.title}")
            async for message in client.iter_messages(entity, offset_date=now, limit=20):
                if message.date < yesterday:
                    break  # older than 24 hours, stop checking messages
                sender = await message.get_sender()
                if sender:
                    sender_name = sender.first_name or ""
                    sender_last_name = sender.last_name or ""
                    full_sender_name = f"{sender_name} {sender_last_name}".strip()

                    for handle in rep_handles:
                        alias = rep_handles[handle]
                        if handle in full_sender_name:
                            active_groups[entity.title] = alias
                            logging.info(f"Found message from '{alias}' in '{entity.title}' at {message.date.isoformat()}")
                            break

                if entity.title in active_groups:
                    break  # Stop after finding one rep message per group

    logging.info("\n✅ Analysis completed.\n")

    print("\n📌 Private groups with sales rep activity (last 24 hours):")
    if active_groups:
        for group, rep in active_groups.items():
            print(f"- {group} (Rep: {rep})")
    else:
        print("No recent sales rep activity found.")

with client:
    client.loop.run_until_complete(sales_rep_recent_activity())
