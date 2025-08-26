"""
Utility functions for Telegram Gemini Bot
"""

import re
import logging
from telegram import Update
from telegram.constants import ChatType
from typing import Optional, List

logger = logging.getLogger(__name__)

def is_group_chat(update: Update) -> bool:
    """Check if the update is from a group chat"""
    try:
        if not update or not update.effective_chat:
            return False
        
        return update.effective_chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    
    except Exception as e:
        logger.error(f"Error checking chat type: {e}")
        return False

def is_private_chat(update: Update) -> bool:
    """Check if the update is from a private chat"""
    try:
        if not update or not update.effective_chat:
            return False
        
        return update.effective_chat.type == ChatType.PRIVATE
    
    except Exception as e:
        logger.error(f"Error checking chat type: {e}")
        return False

def sanitize_message(message: str) -> str:
    """Sanitize and clean message text"""
    try:
        if not message:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', message.strip())
        
        # Remove bot mentions from the message content
        cleaned = re.sub(r'@\w+\s*', '', cleaned).strip()
        
        # Limit message length
        max_length = 4000
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        
        return cleaned
    
    except Exception as e:
        logger.error(f"Error sanitizing message: {e}")
        return message if message else ""

def extract_user_info(update: Update) -> dict:
    """Extract user information from update"""
    try:
        user_info = {
            'id': None,
            'username': None,
            'first_name': None,
            'last_name': None,
            'full_name': None
        }
        
        if update and update.effective_user:
            user = update.effective_user
            user_info.update({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name
            })
        
        return user_info
    
    except Exception as e:
        logger.error(f"Error extracting user info: {e}")
        return {'id': None, 'username': None, 'first_name': 'User', 'last_name': None, 'full_name': 'User'}

def extract_chat_info(update: Update) -> dict:
    """Extract chat information from update"""
    try:
        chat_info = {
            'id': None,
            'type': None,
            'title': None,
            'username': None
        }
        
        if update and update.effective_chat:
            chat = update.effective_chat
            chat_info.update({
                'id': chat.id,
                'type': chat.type,
                'title': chat.title,
                'username': chat.username
            })
        
        return chat_info
    
    except Exception as e:
        logger.error(f"Error extracting chat info: {e}")
        return {'id': None, 'type': None, 'title': 'Group Chat', 'username': None}

def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message for user display"""
    try:
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Generic user-friendly messages based on error types
        if "timeout" in error_msg.lower():
            return "⏱️ Request timed out. Please try again."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            return "🌐 Network connection issue. Please check your connection and try again."
        elif "unauthorized" in error_msg.lower() or "forbidden" in error_msg.lower():
            return "🔒 Authorization error. Please contact the administrator."
        elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
            return "🚦 Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"⚠️ An error occurred{': ' + context if context else ''}. Please try again later."
    
    except Exception as e:
        logger.error(f"Error formatting error message: {e}")
        return "⚠️ An unexpected error occurred. Please try again later."

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    try:
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return text if text else ""

def split_long_message(message: str, max_length: int = 4096) -> List[str]:
    """Split long message into chunks"""
    try:
        if not message or len(message) <= max_length:
            return [message] if message else []
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(message):
            # Find a good breaking point (prefer line breaks or spaces)
            end_pos = current_pos + max_length
            
            if end_pos >= len(message):
                chunks.append(message[current_pos:])
                break
            
            # Look for line break
            break_pos = message.rfind('\n', current_pos, end_pos)
            if break_pos == -1:
                # Look for space
                break_pos = message.rfind(' ', current_pos, end_pos)
            
            if break_pos == -1 or break_pos <= current_pos:
                # No good break point found, force split
                break_pos = end_pos
            
            chunks.append(message[current_pos:break_pos])
            current_pos = break_pos + (1 if break_pos < end_pos else 0)
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error splitting message: {e}")
        return [message] if message else []

def validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    try:
        if not token:
            return False
        
        # Basic format validation: should be like "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        pattern = r'^\d+:[A-Za-z0-9_-]+$'
        return bool(re.match(pattern, token))
    
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return False

def log_message_info(update: Update, message_type: str = "message"):
    """Log message information for debugging"""
    try:
        if not update:
            return
        
        user_info = extract_user_info(update)
        chat_info = extract_chat_info(update)
        
        logger.info(
            f"{message_type.capitalize()} received - "
            f"User: {user_info.get('first_name', 'Unknown')} "
            f"({user_info.get('id', 'Unknown')}), "
            f"Chat: {chat_info.get('title', 'Unknown')} "
            f"({chat_info.get('type', 'Unknown')})"
        )
    
    except Exception as e:
        logger.error(f"Error logging message info: {e}")
