"""
Configuration management for Telegram Gemini Bot
"""

import os
from typing import Optional

class Config:
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # Gemini API Configuration
        self.GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
        if not self.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Webhook Configuration for Render.com
        self.WEBHOOK_URL: str = os.getenv('WEBHOOK_URL', '')
        
        # Environment Configuration
        self.ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
        
        # Only require webhook URL in production
        if self.ENVIRONMENT == 'production' and not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL environment variable is required for production")
        
        # Server Configuration
        self.PORT: int = int(os.getenv('PORT', 5000))
        self.HOST: str = os.getenv('HOST', '0.0.0.0')
        
        # Bot Configuration
        self.BOT_NAME: str = os.getenv('BOT_NAME', 'Mr AP R Guild Bot - Gemini AI Training Assistant')
        
        # Logging Configuration
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings"""
        
        # Validate Telegram token format
        if not self.TELEGRAM_BOT_TOKEN.count(':') == 1:
            raise ValueError("Invalid TELEGRAM_BOT_TOKEN format")
        
        # Validate webhook URL format for production
        if self.ENVIRONMENT == 'production' and self.WEBHOOK_URL:
            if not self.WEBHOOK_URL.startswith(('http://', 'https://')):
                raise ValueError("WEBHOOK_URL must be a valid HTTP(S) URL")
        
        # Validate port range
        if not 1 <= self.PORT <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
    
    def get_webhook_url(self) -> str:
        """Get full webhook URL"""
        return f"{self.WEBHOOK_URL}/webhook"
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == 'production'
    
    def __str__(self) -> str:
        """String representation of config (without sensitive data)"""
        return f"""
Config:
  Environment: {self.ENVIRONMENT}
  Port: {self.PORT}
  Host: {self.HOST}
  Bot Name: {self.BOT_NAME}
  Log Level: {self.LOG_LEVEL}
  Webhook URL: {self.WEBHOOK_URL if self.WEBHOOK_URL else 'Not set'}
  Telegram Token: {'Set' if self.TELEGRAM_BOT_TOKEN else 'Not set'}
  Gemini API Key: {'Set' if self.GEMINI_API_KEY else 'Not set'}
        """.strip()
