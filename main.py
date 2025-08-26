"""
Main entry point for the Telegram Gemini AI Bot
Runs bot with polling as primary method, webhook as secondary option
"""

import os
import logging
from flask import Flask, request, jsonify, render_template
from telegram import Update
from telegram.ext import Application
import asyncio
from bot import TelegramGeminiBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_flask_app(app, config):
    """Run Flask app in a separate thread"""
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)  # Reduce Flask logging noise
    
    logger.info(f"Starting Flask server on {config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )

async def setup_webhook_if_needed(bot, config):
    """Setup webhook only if WEBHOOK_URL is provided"""
    if config.WEBHOOK_URL:
        try:
            webhook_url = f"{config.WEBHOOK_URL}/webhook"
            await bot.application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook configured: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    return False

def main():
    """Main function to run the bot"""
    # Initialize configuration
    config = Config()
    
    # Initialize bot
    telegram_bot = TelegramGeminiBot(config)
    
    # Create Flask app for health monitoring and optional webhooks
    app = Flask(__name__)
    web_server = WebServer(app, telegram_bot, config)
    
    # Start Flask server in background thread for health monitoring
    flask_thread = threading.Thread(
        target=run_flask_app, 
        args=(app, config), 
        daemon=True
    )
    flask_thread.start()
    
    # Check if webhook should be configured
    if config.WEBHOOK_URL:
        logger.info("Webhook URL provided but using polling as primary method per user request")
    
    logger.info("Bot running with polling mode (primary method)")
    
    # Run with polling - no async event loop conflicts
    telegram_bot.application.run_polling(
        poll_interval=2.0,
        timeout=20,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
