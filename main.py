#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Production-focused with webhook support for Render.com deployment
"""

import os
import logging
import asyncio
import signal
from functools import wraps

from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application

from bot import TelegramGeminiBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize configuration
config = Config()

# Initialize Flask app
app = Flask(__name__)

# Global bot instance (will be initialized in main)
telegram_bot = None
application = None

def async_action(f):
    """Decorator to allow async functions to be called as Flask endpoints"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com monitoring"""
    try:
        bot_healthy = telegram_bot is not None and application is not None
        status = 'healthy' if bot_healthy else 'unhealthy'
        
        return jsonify({
            'status': status,
            'service': '@mraprguildbot - Gemini AI Training Assistant',
            'version': '1.0.0',
            'bot_initialized': telegram_bot is not None,
            'application_initialized': application is not None,
            'environment': config.ENVIRONMENT,
        }), 200 if bot_healthy else 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
@async_action
async def webhook():
    """Telegram webhook endpoint with async support"""
    try:
        if telegram_bot is None or application is None:
            logger.error("Bot not initialized")
            return jsonify({'status': 'error', 'message': 'Bot not initialized'}), 500
            
        json_data = request.get_json()
        if not json_data:
            logger.warning("Received empty webhook data")
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Process update
        update = Update.de_json(json_data, application.bot)
        if update:
            # Process the update asynchronously
            asyncio.create_task(application.process_update(update))
            return jsonify({'status': 'ok'}), 200
        else:
            logger.warning("Failed to parse update from webhook data")
            return jsonify({'status': 'error', 'message': 'Invalid update data'}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Root endpoint with bot information"""
    return jsonify({
        'service': '@mraprguildbot - Gemini AI Training Assistant',
        'description': 'A specialized Telegram bot providing programming training and technical education assistance',
        'status': 'running' if telegram_bot else 'initializing',
        'mode': 'webhook' if config.ENVIRONMENT == 'production' else 'polling',
        'version': '1.0.0'
    })

async def setup_webhook():
    """Setup webhook for production deployment"""
    try:
        webhook_url = f"{config.WEBHOOK_URL}/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        await application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        logger.info("Webhook setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        raise

async def run_polling():
    """Run bot in polling mode"""
    logger.info("Starting bot in polling mode")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )
    logger.info("Bot polling started")

async def run_webhook():
    """Run bot in webhook mode"""
    logger.info("Starting bot in webhook mode")
    await application.initialize()
    await application.start()
    await setup_webhook()
    logger.info("Bot webhook mode started")

async def shutdown():
    """Graceful shutdown"""
    logger.info("Shutting down bot...")
    if application:
        await application.stop()
        await application.shutdown()
    logger.info("Bot shutdown completed")

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(shutdown())

async def main():
    """Main async function to initialize and run the bot"""
    global telegram_bot, application
    
    try:
        # Initialize bot
        telegram_bot = TelegramGeminiBot(config)
        application = telegram_bot.application
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start the bot based on environment
        if config.ENVIRONMENT == 'production':
            await run_webhook()
        else:
            await run_polling()
            
        logger.info("Bot started successfully")
        
        # For production, we return here and let Flask run separately
        if config.ENVIRONMENT == 'production':
            return
            
        # For development (polling), keep the event loop running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        await shutdown()
        raise

def run_flask():
    """Run the Flask server"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    if config.ENVIRONMENT == 'production':
        # Production: Run both bot and Flask in the same event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the bot
        bot_task = loop.create_task(main())
        
        # Run Flask in the same event loop
        try:
            # Use a thread for Flask to avoid blocking
            import threading
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            # Run the event loop
            loop.run_until_complete(bot_task)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            loop.run_until_complete(shutdown())
            loop.close()
    else:
        # Development: Just run polling (Flask can be run separately if needed)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main())
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            loop.run_until_complete(shutdown())
            loop.close()
