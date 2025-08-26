#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Production-focused with webhook support for Render.com deployment
"""

import os
import logging
import asyncio
import signal
import threading
from functools import wraps

from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
            'environment': os.environ.get('ENVIRONMENT', 'production'),
            'port': os.environ.get('PORT', '5000')
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
        'mode': 'webhook',
        'version': '1.0.0',
        'port': os.environ.get('PORT', '5000')
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong', 'port': os.environ.get('PORT', '5000')})

async def setup_webhook():
    """Setup webhook for production deployment"""
    try:
        webhook_url = os.environ.get('WEBHOOK_URL', '')
        if not webhook_url:
            logger.error("WEBHOOK_URL environment variable is not set")
            return False
            
        webhook_url = f"{webhook_url}/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        await application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        logger.info("Webhook setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        return False

async def run_webhook():
    """Run bot in webhook mode"""
    logger.info("Starting bot in webhook mode")
    await application.initialize()
    await application.start()
    success = await setup_webhook()
    if success:
        logger.info("Bot webhook mode started successfully")
    else:
        logger.error("Failed to start bot in webhook mode")
    return success

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

def run_flask():
    """Run the Flask server on port 5000"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    """Main async function to initialize and run the bot"""
    global telegram_bot, application
    
    try:
        # Import here to avoid circular imports
        from bot import TelegramGeminiBot
        from config import Config
        
        # Initialize bot
        config = Config()
        telegram_bot = TelegramGeminiBot(config)
        application = telegram_bot.application
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)
        
        # Start the bot in webhook mode
        success = await run_webhook()
        return success
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        await shutdown()
        return False

if __name__ == '__main__':
    # Always use port 5000 for Render.com
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting application on port {port}")
    
    # Create and start event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start the bot in a separate thread
    bot_thread = threading.Thread(
        target=lambda: loop.run_until_complete(main()),
        daemon=True
    )
    bot_thread.start()
    
    # Run Flask app in the main thread
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        loop.run_until_complete(shutdown())
        loop.close()
