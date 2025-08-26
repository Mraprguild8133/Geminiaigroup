#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Simplified for polling mode (development/local deployment)
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

# Initialize Flask app for health checks and optional API endpoints
app = Flask(__name__)

# Initialize bot
config = Config()
telegram_bot = TelegramGeminiBot(config)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        bot_status = 'healthy' if telegram_bot and telegram_bot.application else 'unhealthy'
        
        return jsonify({
            'status': 'healthy',
            'service': '@mraprguildbot - Gemini AI Training Assistant',
            'version': '1.0.0',
            'bot_status': bot_status,
            'mode': 'polling',
            'environment': config.ENVIRONMENT,
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
    return jsonify({'pong': True, 'mode': 'polling'}), 200

@app.route('/', methods=['GET'])
def home():
    """Root endpoint with bot information"""
    try:
        return render_template('index.html')
    except:
        # Fallback to JSON response if template fails
        return jsonify({
            'service': '@mraprguildbot - Gemini AI Training Assistant',
            'description': 'A specialized Telegram bot providing programming training and technical education assistance',
            'status': 'running',
            'mode': 'polling',
            'version': '1.0.0',
            'features': [
                'Private chat support',
                'Group chat assistance', 
                'Programming training',
                'Google Gemini AI integration',
                'Smart response triggers'
            ],
            'endpoints': {
                'health': '/health - Health check',
                'ping': '/ping - Simple ping response'
            }
        })

@app.route('/api', methods=['GET'])
def api_info():
    """API endpoint with JSON bot information"""
    return jsonify({
        'service': '@mraprguildbot - Gemini AI Training Assistant',
        'mode': 'polling',
        'status': 'running',
        'version': '1.0.0'
    })

def run_bot_polling():
    """Run the bot in polling mode"""
    logger.info("Starting bot in polling mode")
    try:
        telegram_bot.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"Bot polling failed: {e}")
        raise

def run_flask_server():
    """Run Flask server for health checks"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask health check server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    if config.ENVIRONMENT == 'production':
        logger.warning("Running in production mode with polling - consider using webhooks for production")
    
    # For simplicity, we'll run the bot polling in the main thread
    # and Flask server in a separate thread if needed, or just run bot polling
    # since health checks might not be necessary for local development
    
    if os.environ.get('RUN_FLASK', 'false').lower() == 'true':
        # Run both bot and Flask server (requires threading)
        import threading
        
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        
        logger.info("Flask server started in background thread")
        run_bot_polling()
    else:
        # Just run the bot polling (simpler for development)
        logger.info("Starting bot polling (Flask server not started)")
        run_bot_polling()
