"""
Telegram Gemini AI Bot
Handles Telegram bot interactions and integrates with Gemini AI
"""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatType
from gemini_service import GeminiService
from config import Config
from utils import is_group_chat, sanitize_message

logger = logging.getLogger(__name__)

class TelegramGeminiBot:
    def __init__(self, config: Config):
        self.config = config
        self.gemini_service = GeminiService(config.GEMINI_API_KEY)
        
        # Build application
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self._add_handlers()
        
        logger.info("Telegram Gemini Bot initialized")
    
    def _add_handlers(self):
        """Add command and message handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Message handler for group messages
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            if not is_group_chat(update):
                # Private chat welcome
                await update.message.reply_text(
                    "🤖 Hi! I'm @mraprguildbot - your Gemini AI Training Assistant!\n\n"
                    "💬 You can ask me programming questions, get coding help, or discuss technical topics.\n"
                    "🧠 I'm powered by Google Gemini AI and specialize in training and education.\n\n"
                    "Type /help for more information or just start chatting with me!"
                )
                return
            
            # Group chat welcome
            await update.message.reply_text(
                "🤖 Hello everyone! I'm @mraprguildbot - your Gemini AI Training Assistant!\n\n"
                "💬 Just mention me (@mraprguildbot) or reply to my messages to get AI-powered responses.\n"
                "🧠 I can help with training questions, programming discussions, and provide intelligent insights.\n\n"
                "Type /help for more information!"
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await self._send_error_message(update, "Failed to process start command")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            if not is_group_chat(update):
                # Private chat help
                help_text = """
🤖 **@mraprguildbot - Private Chat Help**

**How to use me:**
• Just start chatting! Ask me anything
• I respond to all messages in private chats
• Ask programming questions, get coding help
• Use trigger words: hi, help, what, how, please, etc.
• Ask questions ending with ?

**Commands:**
• /start - Welcome message and introduction
• /help - Show this help message
• /status - Check bot status

**Features:**
• Programming and training assistance
• Intelligent conversation support
• Context-aware responses
• One-on-one learning support
• Error handling and logging

**Example questions:**
• "How do I create a Python function?"
• "What is machine learning?"
• "Help me debug this code"
                """
            else:
                # Group chat help
                help_text = """
🤖 **@mraprguildbot - Group Chat Help**

**How to use me:**
• Mention me (@mraprguildbot) in your message
• Reply to any of my previous messages
• Use trigger words: hi, help, what, how, please, etc.
• Ask questions ending with ?
• I'll provide AI-powered training responses using Google Gemini

**Commands:**
• /start - Welcome message and introduction
• /help - Show this help message
• /status - Check bot status

**Features:**
• Programming and training assistance
• Intelligent conversation support
• Context-aware responses
• Group chat optimization
• Error handling and logging

**Note:** Perfect for collaborative learning and training discussions!
                """
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await self._send_error_message(update, "Failed to process help command")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            # Test Gemini service
            gemini_status = await self.gemini_service.test_connection()
            
            chat_type = "Private Chat" if not is_group_chat(update) else "Group Chat"
            
            status_text = f"""
🤖 **@mraprguildbot Status**

✅ **Telegram Bot:** Online
{'✅' if gemini_status else '❌'} **Gemini AI:** {'Connected' if gemini_status else 'Disconnected'}
🏠 **Environment:** {self.config.ENVIRONMENT}
📊 **Chat Type:** {chat_type}
🎯 **Mode:** Training Assistant

All systems operational!
            """
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await self._send_error_message(update, "Failed to check status")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            message = update.message
            if not message or not message.text:
                return
            
            user_name = message.from_user.first_name or "User"
            chat_name = message.chat.title or "Private Chat"
            is_group = is_group_chat(update)
            
            logger.info(f"Received message from {user_name} in {chat_name}: {message.text[:50]}...")
            
            # In private chats, respond to all messages
            if not is_group:
                bot_mentioned = True
                logger.info("Private chat - responding to all messages")
            else:
                # In group chats, use selective response logic
                bot_mentioned = False
                bot_username = context.bot.username
                
                # Check for @mentions
                if message.entities:
                    for entity in message.entities:
                        if entity.type == "mention":
                            mention_text = message.text[entity.offset:entity.offset + entity.length]
                            if bot_username and mention_text.lower() == f"@{bot_username.lower()}":
                                bot_mentioned = True
                                logger.info(f"Bot mentioned directly: {mention_text}")
                                break
                
                # Check if replying to bot's message
                if message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id:
                    bot_mentioned = True
                    logger.info("Message is reply to bot")
                
                # Also respond to messages containing keywords (case insensitive) or questions
                message_lower = message.text.lower()
                trigger_words = [
                    'bot', 'ai', 'help', 'assistant', 'gemini', 'hello', 'hi', 'hey', 
                    'question', 'ask', 'tell me', 'what', 'how', 'why', 'when', 'where', 
                    'explain', 'can you', 'do you', 'please', 'thanks', 'chat'
                ]
                
                # Check for trigger words
                if any(word in message_lower for word in trigger_words):
                    bot_mentioned = True
                    logger.info(f"Trigger word found in message")
                
                # Also respond to questions (messages ending with ?)
                elif message.text.strip().endswith('?'):
                    bot_mentioned = True
                    logger.info("Message is a question")
            
            # Only respond if mentioned, replied to, contains trigger words, or is private chat
            if not bot_mentioned:
                logger.info("Bot not mentioned, skipping message")
                return
            
            # Show typing indicator
            await context.bot.send_chat_action(chat_id=message.chat_id, action="typing")
            
            # Get user message and generate response
            user_message = sanitize_message(message.text)
            user_name = message.from_user.first_name or "User"
            
            logger.info(f"Processing message from {user_name} in group {message.chat.title}")
            
            # Generate AI response
            ai_response = await self.gemini_service.generate_response(
                user_message, 
                user_name,
                message.chat.title or "Group Chat"
            )
            
            if ai_response:
                # Split long messages if needed
                if len(ai_response) > 4096:
                    # Split into chunks
                    chunks = [ai_response[i:i+4096] for i in range(0, len(ai_response), 4096)]
                    for chunk in chunks:
                        await message.reply_text(chunk)
                else:
                    await message.reply_text(ai_response)
            else:
                await message.reply_text(
                    "🤔 I'm having trouble generating a response right now. Please try again!"
                )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error_message(update, "Failed to process your message")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await self._send_error_message(
                update, 
                "An unexpected error occurred. Please try again later."
            )
    
    async def _send_error_message(self, update: Update, error_text: str):
        """Send error message to user"""
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    f"⚠️ {error_text}\n\nIf the problem persists, please contact the administrator."
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
