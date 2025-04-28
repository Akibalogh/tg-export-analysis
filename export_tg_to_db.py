import logging
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User, ChannelForbidden
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Telegram API credentials
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

# Database setup
engine = create_engine('sqlite:///messages.db')
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Define the Message table
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

# Create the messages table if it doesn't exist
Base.metadata.create_all(bind=engine)

# Setup Telegram client
client = TelegramClient('session_name', api_id, api_hash)

async def dump_all_messages():
    await client.start(phone=phone)

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    logging.info("Starting full Telegram export...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        # Only DMs, private groups, and accessible channels
        if isinstance(entity, (User, Chat, Channel)):
            chat_id = entity.id
            chat_title = getattr(entity, 'title', None) or getattr(entity, 'username', None) or getattr(entity, 'first_name', None) or 'Unknown'

            logging.info(f"Fetching messages from: {chat_title}")

            try:
                async for message in client.iter_messages(entity, reverse=False):
                    if not message.message:
                        continue

                    sender = None
                    sender_name = None
                    try:
                        sender = await message.get_sender()
                        if sender:
                            if hasattr(sender, 'first_name'):
                                sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                            elif hasattr(sender, 'title'):
                                sender_name = sender.title
                    except Exception:
                        sender_name = None  # In case sender cannot be fetched

                    msg = Message(
                        tg_message_id=message.id,
                        chat_id=chat_id,
                        chat_title=chat_title,
                        sender_id=message.from_id.user_id if message.from_id else None,
                        sender_name=sender_name,
                        date=message.date,
                        text=message.message.replace('\x00', '')  # Remove any null bytes
                    )
                    db.add(msg)

                db.commit()
                await asyncio.sleep(0.5)

            except ChannelForbidden:
                logging.warning(f"Skipping forbidden channel: {chat_title}")
                continue

            except Exception as e:
                logging.warning(f"Error on {chat_title}: {e}. Sleeping 15s.")
                await asyncio.sleep(15)

    db.close()
    logging.info("✅ Finished dumping all messages into 'messages.db'.")

# Run the export
with client:
    client.loop.run_until_complete(dump_all_messages())
