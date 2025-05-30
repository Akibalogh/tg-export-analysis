import logging
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat, User, PeerUser
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, UniqueConstraint
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
    tg_message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    chat_title = Column(String(255))
    sender_id = Column(Integer)
    sender_name = Column(String(255))
    date = Column(DateTime)
    text = Column(Text)

    __table_args__ = (
        UniqueConstraint('tg_message_id', 'chat_id', name='uix_tg_message_chat'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Setup Telegram client
client = TelegramClient('session_name', api_id, api_hash)

async def dump_all_messages():
    await client.start(phone=phone)
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    logging.info("Starting incremental Telegram export...")

    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        if isinstance(entity, (User, Chat, Channel)):
            chat_id = entity.id
            chat_title = (
                getattr(entity, 'title', None) or
                getattr(entity, 'username', None) or
                getattr(entity, 'first_name', None) or
                'Unknown'
            )

            # Fetch the latest message ID for this chat
            latest_message = db.query(Message).filter_by(chat_id=chat_id).order_by(Message.tg_message_id.desc()).first()
            latest_message_id = latest_message.tg_message_id if latest_message else 0

            logging.info(f"Fetching messages from {chat_title} after message ID {latest_message_id}")

            try:
                async for message in client.iter_messages(entity, min_id=latest_message_id):
                    if not message.message:
                        continue

                    sender_name = None
                    sender_id = None

                    try:
                        if message.from_id and isinstance(message.from_id, PeerUser):
                            sender_id = message.from_id.user_id

                        sender = await message.get_sender()
                        if sender:
                            sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
                            if hasattr(sender, 'title'):
                                sender_name = sender.title

                    except Exception:
                        sender_name = None

                    # Create and add message to the DB
                    msg = Message(
                        tg_message_id=message.id,
                        chat_id=chat_id,
                        chat_title=chat_title,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        date=message.date,
                        text=message.message.replace('\x00', '')  # Clean null bytes
                    )
                    db.add(msg)

                db.commit()
                await asyncio.sleep(0.5)

            except FloodWaitError as e:
                logging.warning(f"Rate limit hit. Sleeping for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)

            except Exception as e:
                logging.warning(f"Error fetching from {chat_title}: {e}. Skipping this chat.")
                continue

    db.close()
    logging.info("✅ Finished incremental export into 'messages.db'.")

# Run export
with client:
    client.loop.run_until_complete(dump_all_messages())
