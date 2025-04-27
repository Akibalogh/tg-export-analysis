import logging
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from dotenv import load_dotenv
import os
import pandas as pd

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

async def fetch_sales_rep_messages():
    await client.start(phone=phone)

    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    messages_data = []

    logging.info("Fetching recent sales rep messages...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', False):
            logging.info(f"Checking group: {entity.title}")

            try:
                async for message in client.iter_messages(entity, offset_date=now, limit=20):
                    if message.date < yesterday:
                        break

                    sender = await message.get_sender()
                    if sender:
                        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

                        for handle, alias in rep_handles.items():
                            if handle in sender_name:
                                msg_time = message.date.strftime("%Y-%m-%d %H:%M:%S")
                                msg_text = message.message.replace("\n", " ").strip() if message.message else "[No text]"
                                messages_data.append({
                                    'Group': entity.title,
                                    'Rep Name': alias,
                                    'Message': msg_text,
                                    'Time (UTC)': msg_time
                                })
                                logging.info(f"[{entity.title}] {alias} at {msg_time}: {msg_text}")
                                break

                await asyncio.sleep(0.3)

            except Exception as e:
                logging.warning(f"Error: {e}. Sleeping 15s.")
                await asyncio.sleep(15)

    if messages_data:
        df = pd.DataFrame(messages_data)
        df.to_excel('sales_rep_activity.xlsx', index=False)
        logging.info("✅ Exported to 'sales_rep_activity.xlsx'")
    else:
        logging.info("✅ No recent sales rep messages found. No Excel file created.")

    print("\n📌 Detailed Sales Rep Activity (last 24 hours):")
    if messages_data:
        for msg in messages_data:
            print(f"- [{msg['Group']}] {msg['Rep Name']} at {msg['Time (UTC)']}: {msg['Message']}")
    else:
        print("No recent activity found.")

with client:
    client.loop.run_until_complete(fetch_sales_rep_messages())
