#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Handles webhook setup and Flask server for Render.com deployment
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

# Initialize Flask app for webhook and health checks
app = Flask(__name__)

# Initialize bot
config = Config()
telegram_bot = TelegramGeminiBot(config)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render.com monitoring"""
    try:
        # Check if bot application is initialized
        bot_status = 'healthy' if telegram_bot and telegram_bot.application else 'unhealthy'
        
        return jsonify({
            'status': 'healthy',
            'service': '@mraprguildbot - Gemini AI Training Assistant',
            'version': '1.0.0',
            'bot_status': bot_status,
            'environment': config.ENVIRONMENT,
            'timestamp': str(asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 'N/A')
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for monitoring services"""
    return jsonify({'pong': True}), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for container orchestration"""
    try:
        # Check if all components are ready
        ready = telegram_bot and telegram_bot.application and telegram_bot.gemini_service
        
        return jsonify({
            'ready': bool(ready),
            'service': '@mraprguildbot',
            'components': {
                'telegram_bot': bool(telegram_bot),
                'application': bool(telegram_bot.application if telegram_bot else False),
                'gemini_service': bool(telegram_bot.gemini_service if telegram_bot else False)
            }
        }), 200 if ready else 503
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'ready': False,
            'error': str(e)
        }), 503

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    try:
        json_data = request.get_json()
        if not json_data:
            logger.warning("Received empty webhook data")
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        # Process update asynchronously
        update = Update.de_json(json_data, telegram_bot.application.bot)
        if update:
            asyncio.create_task(telegram_bot.application.process_update(update))
            return jsonify({'status': 'ok'}), 200
        else:
            logger.warning("Failed to parse update from webhook data")
            return jsonify({'status': 'error', 'message': 'Invalid update data'}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    """Root endpoint with bot dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        # Fallback to JSON response if template fails
        return jsonify({
            'service': '@mraprguildbot - Gemini AI Training Assistant',
            'description': 'A specialized Telegram bot providing programming training and technical education assistance',
            'status': 'running',
            'version': '1.0.0',
            'features': [
                'Private chat support',
                'Group chat assistance', 
                'Programming training',
                'Google Gemini AI integration',
                'Smart response triggers'
            ],
            'endpoints': {
                'health': '/health - Comprehensive health check',
                'ping': '/ping - Simple ping response',
                'ready': '/ready - Readiness probe for containers',
                'webhook': '/webhook - Telegram webhook endpoint'
            },
            'deployment': {
                'platform': 'Render.com',
                'container': 'Docker ready',
                'monitoring': 'Full health checks enabled'
            }
        })

@app.route('/api', methods=['GET'])
def api_info():
    """API endpoint with JSON bot information"""
    return jsonify({
        'service': '@mraprguildbot - Gemini AI Training Assistant',
        'description': 'A specialized Telegram bot providing programming training and technical education assistance',
        'status': 'running',
        'version': '1.0.0',
        'features': [
            'Private chat support',
            'Group chat assistance', 
            'Programming training',
            'Google Gemini AI integration',
            'Smart response triggers'
        ],
        'endpoints': {
            'health': '/health - Comprehensive health check',
            'ping': '/ping - Simple ping response',
            'ready': '/ready - Readiness probe for containers',
            'webhook': '/webhook - Telegram webhook endpoint'
        },
        'deployment': {
            'platform': 'Render.com',
            'container': 'Docker ready',
            'monitoring': 'Full health checks enabled'
        }
    })

async def setup_webhook():
    """Setup webhook for production deployment"""
    try:
        webhook_url = f"{config.WEBHOOK_URL}/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        await telegram_bot.application.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info("Webhook setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        raise

def run_development():
    """Run bot in production mode with Flask server (bot runs via separate workflow)"""
    # In development mode, just run Flask server
    # Bot can be run separately via the workflow system
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask web server on port {port}")
    logger.info("Bot polling should be started via workflow system for concurrent operation")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_bot_only():
    """Run just the bot polling (for workflow system)"""
    logger.info("Starting bot in production mode (polling)")
    telegram_bot.application.run_polling(drop_pending_updates=True)

async def run_production():
    """Initialize bot for production mode (webhook)"""
    logger.info("Initializing bot for production mode (bot)")
    
    # Initialize the application
    await telegram_bot.application.initialize()
    await telegram_bot.application.start()
    
    # Setup webhook
    await setup_webhook()
    
    logger.info("Bot initialized and webhook configured")

if __name__ == '__main__':
    if config.ENVIRONMENT == 'development':
        # Development mode - use polling
        run_development()
    else:
        # Production mode - setup webhook and run Flask server
        try:
            # Run async setup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_production())
            
            # Start Flask server
            port = int(os.environ.get('PORT', 5000))
            logger.info(f"Starting Flask server on port {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
            
        except Exception as e:
            logger.error(f"Failed to start production server: {e}")
            raise
