#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Simplified for polling mode (development/local deployment)
"""

import os
import logging
import socket
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

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

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
            'flask_server': os.environ.get('RUN_FLASK', 'false').lower() == 'true',
            'port': int(os.environ.get('PORT', 5000))
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
    return jsonify({
        'pong': True, 
        'mode': 'polling',
        'flask_server': os.environ.get('RUN_FLASK', 'false').lower() == 'true',
        'port': int(os.environ.get('PORT', 5000))
    }), 200

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
            'flask_server': os.environ.get('RUN_FLASK', 'false').lower() == 'true',
            'port': int(os.environ.get('PORT', 5000)),
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
        'version': '1.0.0',
        'flask_server': os.environ.get('RUN_FLASK', 'false').lower() == 'true',
        'port': int(os.environ.get('PORT', 5000))
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
    """Run Flask server for health checks with port handling"""
    port = int(os.environ.get('PORT', 5000))
    
    # Check if port is available
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use, trying to find alternative port...")
        # Try alternative ports
        for alternative_port in [port + 1, port + 2, port + 3, 8080, 3000]:
            if not is_port_in_use(alternative_port):
                port = alternative_port
                logger.info(f"Using alternative port: {port}")
                break
        else:
            logger.error("No available ports found for Flask server")
            return
    
    logger.info(f"Starting Flask health check server on port {port}")
    logger.info(f"Health check available at: http://0.0.0.0:{port}/health")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"Flask server failed to start: {e}")

if __name__ == '__main__':
    # Get environment variables
    run_flask = os.environ.get('RUN_FLASK', 'true').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    environment = config.ENVIRONMENT
    
    logger.info(f"Starting in {environment} mode")
    logger.info(f"RUN_FLASK: {run_flask}")
    logger.info(f"PORT: {port}")
    
    if environment == 'production':
        logger.warning("Running in production mode with polling - consider using webhooks for production")
    
    if run_flask:
        # Run both bot and Flask server using threading
        import threading
        
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        
        logger.info("Flask server started in background thread")
        logger.info("Starting bot polling...")
        run_bot_polling()
    else:
        # Just run the bot polling (simpler for development)
        logger.info("Starting bot polling only (Flask server disabled)")
        logger.info("Set RUN_FLASK=true to enable health check server")
        run_bot_polling()
