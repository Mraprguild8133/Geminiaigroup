#!/usr/bin/env python3
"""
Bot runner for separate workflow execution
"""

import logging
from bot import TelegramGeminiBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting @mraprguildbot polling service")
    
    # Initialize bot
    config = Config()
    telegram_bot = TelegramGeminiBot(config)
    
    # Run polling
    telegram_bot.application.run_polling(drop_pending_updates=True)