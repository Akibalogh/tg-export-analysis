from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import logging, os, asyncio

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

            try:
                async for message in client.iter_messages(entity, offset_date=now, limit=5):
                    if message.date < yesterday:
                        break
                    sender = await message.get_sender()
                    if sender:
                        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

                        for handle in rep_handles:
                            alias = rep_handles[handle]
                            if handle in sender_name:
                                active_groups[entity.title] = alias
                                logging.info(f"Message from '{alias}' in '{entity.title}' at {message.date.isoformat()}")
                                break

                    if entity.title in active_groups:
                        break
            except Exception as e:
                logging.warning(f"Encountered error: {e}. Sleeping for 15 seconds.")
                await asyncio.sleep(15)

            await asyncio.sleep(0.5)  # critical sleep between API calls to avoid throttling

    logging.info("\n✅ Analysis completed.\n")

    print("\n📌 Private groups with sales rep activity (last 24 hours):")
    if active_groups:
        for group, rep in active_groups.items():
            print(f"- {group} (Rep: {rep})")
    else:
        print("No recent sales rep activity found.")

with client:
    client.loop.run_until_complete(sales_rep_recent_activity())
