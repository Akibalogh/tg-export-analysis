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

async def export_sales_rep_messages():
    await client.start(phone=phone)

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    messages_data = []

    logging.info("Fetching sales rep messages for the last 7 days...")

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
                                msg_time = message.date.strftime("%Y-%m-%d %H:%M:%S")
                                msg_text = message.message.replace("\n", " ").strip() if message.message else "[No text]"
                                messages_data.append({
                                    'Date': msg_time,
                                    'Sales Rep': alias,
                                    'Telegram Group': entity.title,
                                    'Message Sent': msg_text
                                })
                                break

                await asyncio.sleep(0.3)

            except Exception as e:
                logging.warning(f"Error: {e}. Sleeping 15s.")
                await asyncio.sleep(15)

    if messages_data:
        df = pd.DataFrame(messages_data)
        df.to_excel('sales_rep_activity_7_days.xlsx', index=False)
        logging.info("✅ Exported to 'sales_rep_activity_7_days.xlsx'")
    else:
        logging.info("✅ No sales rep messages found in the last 7 days.")

    print("\n📌 Export completed. Messages found:")
    if messages_data:
        for msg in messages_data:
            print(f"- [{msg['Date']}] {msg['Sales Rep']} in {msg['Telegram Group']}: {msg['Message Sent']}")
    else:
        print("No messages from sales reps in the past 7 days.")

with client:
    client.loop.run_until_complete(export_sales_rep_messages())
