import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from dotenv import load_dotenv
import os
from collections import defaultdict

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

async def weekly_sales_rep_summary():
    await client.start(phone=phone)

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    rep_message_counts = defaultdict(int)

    logging.info("Generating weekly summary (7 days)...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', False):
            logging.info(f"Scanning group: {entity.title}")

            try:
                async for message in client.iter_messages(entity, offset_date=now, limit=100):
                    if message.date < week_ago:
                        break

                    sender = await message.get_sender()
                    if sender:
                        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

                        for handle, alias in rep_handles.items():
                            if handle in sender_name:
                                rep_message_counts[alias] += 1
                                break

                await asyncio.sleep(0.3)

            except Exception as e:
                logging.warning(f"Error: {e}. Sleeping 15s.")
                await asyncio.sleep(15)

    print("\n📌 Sales Rep Activity Summary (Last 7 Days):")
    if rep_message_counts:
        for rep, count in sorted(rep_message_counts.items(), key=lambda x: -x[1]):
            print(f"- {rep}: {count} messages")
    else:
        print("No sales rep activity found in the past 7 days.")

with client:
    client.loop.run_until_complete(weekly_sales_rep_summary())
