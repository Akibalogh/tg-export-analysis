import logging
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Telegram API credentials
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

# Database setup
engine = create_engine('sqlite:///messages.db')
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_message_id = Column(Integer)
    chat_id = Column(Integer)
    chat_title = Column(String(255))
    sender_id = Column(Integer)
    sender_name = Column(String(255))
    date = Column(DateTime)
    text = Column(Text)

Base.metadata.create_all(bind=engine)

client = TelegramClient('session_name', api_id, api_hash)

async def dump_all_messages():
    await client.start(phone=phone)

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    logging.info("Starting full Telegram export...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        # Only DMs and private groups
        if isinstance(entity, (User, Chat, Channel)):
            chat_id = entity.id
            chat_title = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or 'Unknown'

            logging.info(f"Fetching messages from: {chat_title}")

            try:
                async for message in client.iter_messages(entity, reverse=False):
                    if not message.message:
                        continue

                    sender = await message.get_sender()
                    sender_name = None
                    if sender:
                        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()

                    msg = Message(
                        tg_message_id=message.id,
                        chat_id=chat_id,
                        chat_title=chat_title,
                        sender_id=message.from_id.user_id if message.from_id else None,
                        sender_name=sender_name,
                        date=message.date,
                        text=message.message.replace('\x00', '')  # clean null bytes
                    )
                    db.add(msg)

                db.commit()
                await asyncio.sleep(0.5)

            except Exception as e:
                logging.warning(f"Error on {chat_title}: {e}. Sleeping 15s.")
                await asyncio.sleep(15)

    db.close()
    logging.info("✅ Finished dumping all messages into 'messages.db'.")

with client:
    client.loop.run_until_complete(dump_all_messages())
