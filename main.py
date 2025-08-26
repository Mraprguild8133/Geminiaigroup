#!/usr/bin/env python3
"""
Main entry point for the Telegram Gemini AI Bot
Flask server for health checks & Telegram webhook (production mode)
"""

import os
import logging
import time
import asyncio
from flask import Flask, request, jsonify, render_template
from telegram import Update
from bot import TelegramGeminiBot
from config import Config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot
config = Config()
telegram_bot = TelegramGeminiBot(config)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "@mraprguildbot - Gemini AI Training Assistant",
        "version": "1.0.0",
        "bot_status": "healthy" if telegram_bot.application else "unhealthy",
        "environment": config.ENVIRONMENT,
        "timestamp": time.time()
    }), 200

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"pong": True}), 200

@app.route("/ready", methods=["GET"])
def readiness_check():
    ready = telegram_bot and telegram_bot.application and telegram_bot.gemini_service
    return jsonify({
        "ready": bool(ready),
        "service": "@mraprguildbot",
        "components": {
            "telegram_bot": bool(telegram_bot),
            "application": bool(telegram_bot.application if telegram_bot else False),
            "gemini_service": bool(telegram_bot.gemini_service if telegram_bot else False),
        }
    }), 200 if ready else 503

@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram webhook endpoint"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        update = Update.de_json(json_data, telegram_bot.application.bot)
        if update:
            loop = asyncio.get_event_loop()
            loop.create_task(telegram_bot.application.process_update(update))
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid update data"}), 400
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """Root endpoint"""
    try:
        return render_template("index.html")
    except Exception:
        return jsonify({
            "service": "@mraprguildbot - Gemini AI Training Assistant",
            "description": "A Telegram bot providing programming training with Gemini AI",
            "status": "running",
            "version": "1.0.0"
        })

@app.route("/api", methods=["GET"])
def api_info():
    return jsonify({
        "service": "@mraprguildbot - Gemini AI Training Assistant",
        "description": "Programming training + Gemini AI assistance",
        "status": "running",
        "version": "1.0.0"
    })

async def setup_webhook():
    """Setup webhook in production"""
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

async def run_production():
    """Initialize bot + webhook"""
    logger.info("Initializing bot in webhook mode...")
    await telegram_bot.application.initialize()
    await telegram_bot.application.start()
    await setup_webhook()
    logger.info("Bot initialized and webhook configured")

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_production())

        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start production server: {e}")
        raise
    
