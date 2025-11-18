from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.errors import SessionPasswordNeededError, FloodWaitError
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Telegram Channel API", version="1.0.0")

# Telegram API credentials from environment variables
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "telegram_session")

if not API_ID or not API_HASH:
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in environment variables")

# Initialize Telegram client
client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)

# Response models
class MessageModel(BaseModel):
    id: int
    date: datetime
    text: str
    sender_id: Optional[int] = None
    sender_username: Optional[str] = None
    views: Optional[int] = None
    forwards: Optional[int] = None

class ChannelModel(BaseModel):
    id: int
    title: str
    username: Optional[str] = None
    participants_count: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    """Initialize Telegram client on startup"""
    await client.start()
    if not await client.is_user_authorized():
        raise RuntimeError("Telegram client is not authorized. Please run setup script first.")

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect Telegram client on shutdown"""
    await client.disconnect()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Telegram Channel API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "connected": client.is_connected()}

@app.get("/channels", response_model=List[ChannelModel])
async def list_channels():
    """
    List all channels/dialogs the user has access to
    """
    try:
        channels = []
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, Channel):
                channel_info = ChannelModel(
                    id=entity.id,
                    title=entity.title,
                    username=entity.username,
                    participants_count=entity.participants_count if hasattr(entity, 'participants_count') else None
                )
                channels.append(channel_info)
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing channels: {str(e)}")

@app.get("/channels/{channel_id}/messages", response_model=List[MessageModel])
async def get_messages(
    channel_id: int,
    limit: int = Query(default=50, ge=1, le=1000, description="Number of messages to retrieve"),
    offset_id: Optional[int] = Query(default=None, description="Offset message ID for pagination"),
    min_id: Optional[int] = Query(default=None, description="Minimum message ID to retrieve"),
    max_id: Optional[int] = Query(default=None, description="Maximum message ID to retrieve")
):
    """
    Get messages from a specific channel
    
    - **channel_id**: The ID of the channel (use /channels endpoint to find IDs)
    - **limit**: Number of messages to retrieve (1-1000)
    - **offset_id**: Message ID to start from (for pagination)
    - **min_id**: Minimum message ID to retrieve
    - **max_id**: Maximum message ID to retrieve
    """
    try:
        # Get the channel entity
        entity = await client.get_entity(channel_id)
        
        # Build kwargs for iter_messages, only including non-None values
        iter_kwargs = {"limit": limit}
        if offset_id is not None:
            iter_kwargs["offset_id"] = offset_id
        if min_id is not None:
            iter_kwargs["min_id"] = min_id
        if max_id is not None:
            iter_kwargs["max_id"] = max_id
        
        messages = []
        async for message in client.iter_messages(entity, **iter_kwargs):
            # Extract sender information
            sender_id = None
            sender_username = None
            if message.sender:
                if isinstance(message.sender, User):
                    sender_id = message.sender.id
                    sender_username = message.sender.username
                elif isinstance(message.sender, Channel):
                    sender_id = message.sender.id
                    sender_username = message.sender.username
            
            # Get message text
            text = message.message or ""
            if message.media and not text:
                text = f"[Media: {type(message.media).__name__}]"
            
            message_model = MessageModel(
                id=message.id,
                date=message.date,
                text=text,
                sender_id=sender_id,
                sender_username=sender_username,
                views=message.views,
                forwards=message.forwards
            )
            messages.append(message_model)
        
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Channel not found: {str(e)}")
    except FloodWaitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limited. Wait {e.seconds} seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.get("/channels/by-username/{username}/messages", response_model=List[MessageModel])
async def get_messages_by_username(
    username: str,
    limit: int = Query(default=50, ge=1, le=1000, description="Number of messages to retrieve"),
    offset_id: Optional[int] = Query(default=None, description="Offset message ID for pagination"),
    min_id: Optional[int] = Query(default=None, description="Minimum message ID to retrieve"),
    max_id: Optional[int] = Query(default=None, description="Maximum message ID to retrieve")
):
    """
    Get messages from a channel by username (e.g., 'channelname' without @)
    
    - **username**: The username of the channel (without @)
    - **limit**: Number of messages to retrieve (1-1000)
    - **offset_id**: Message ID to start from (for pagination)
    - **min_id**: Minimum message ID to retrieve
    - **max_id**: Maximum message ID to retrieve
    """
    try:
        # Get the channel entity by username
        entity = await client.get_entity(username)
        
        # Build kwargs for iter_messages, only including non-None values
        iter_kwargs = {"limit": limit}
        if offset_id is not None:
            iter_kwargs["offset_id"] = offset_id
        if min_id is not None:
            iter_kwargs["min_id"] = min_id
        if max_id is not None:
            iter_kwargs["max_id"] = max_id
        
        messages = []
        async for message in client.iter_messages(entity, **iter_kwargs):
            # Extract sender information
            sender_id = None
            sender_username = None
            if message.sender:
                if isinstance(message.sender, User):
                    sender_id = message.sender.id
                    sender_username = message.sender.username
                elif isinstance(message.sender, Channel):
                    sender_id = message.sender.id
                    sender_username = message.sender.username
            
            # Get message text
            text = message.message or ""
            if message.media and not text:
                text = f"[Media: {type(message.media).__name__}]"
            
            message_model = MessageModel(
                id=message.id,
                date=message.date,
                text=text,
                sender_id=sender_id,
                sender_username=sender_username,
                views=message.views,
                forwards=message.forwards
            )
            messages.append(message_model)
        
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Channel not found: {str(e)}")
    except FloodWaitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limited. Wait {e.seconds} seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

