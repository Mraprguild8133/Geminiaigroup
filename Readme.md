# Overview

This is @mraprguildbot - a specialized Gemini AI Training Assistant Telegram bot that integrates with Google's Gemini AI to provide programming and technical training assistance in both private chats and group chats. The bot is designed for deployment on Render.com and uses webhooks to receive Telegram updates. It handles user messages by processing them through the Gemini AI service and responds with educational, training-focused AI-generated content.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Structure
The bot follows a modular architecture with clear separation of concerns:

- **Main Application (`main.py`)**: Flask web server handling webhooks and health checks for cloud deployment
- **Bot Logic (`bot.py`)**: Core Telegram bot functionality with command and message handlers
- **AI Service (`gemini_service.py`)**: Dedicated service layer for Gemini AI integration
- **Configuration (`config.py`)**: Centralized environment variable management
- **Utilities (`utils.py`)**: Helper functions for message processing and chat type detection

## Deployment Architecture
The application is designed for cloud deployment on Render.com using:
- **Webhook-based updates**: Receives Telegram updates via HTTP webhooks instead of polling
- **Flask web server**: Provides webhook endpoint and comprehensive health monitoring
- **Environment-based configuration**: All sensitive data managed through environment variables
- **Docker containerization**: Full containerization support with optimized Dockerfile
- **Health monitoring**: Multiple monitoring endpoints (/health, /ping, /ready) for robust deployment
- **Port management**: Configurable port binding optimized for Render.com (default: 5000)

## Message Processing Flow
1. Telegram sends updates to the webhook endpoint
2. Flask routes the update to the Telegram bot application
3. Bot handlers process commands or forward messages to Gemini AI
4. AI responses are sent back through Telegram's API

## Error Handling
- Comprehensive error handling at each layer
- Logging for debugging and monitoring
- Graceful fallbacks for API failures

# External Dependencies

## AI Services
- **Google Gemini AI API**: Core AI functionality using the `google.genai` client library with the "gemini-2.5-flash" model

## Messaging Platform
- **Telegram Bot API**: Message handling and user interaction through the `python-telegram-bot` library

## Web Framework
- **Flask**: Lightweight web server for webhook handling and health checks

## Deployment Platform
- **Render.com**: Cloud hosting platform requiring webhook configuration and health monitoring endpoints

## Environment Variables Required
- `TELEGRAM_BOT_TOKEN`: Bot authentication token from Telegram
- `GEMINI_API_KEY`: API key for Google Gemini AI service
- `WEBHOOK_URL`: Public URL for receiving Telegram webhooks
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)
- `ENVIRONMENT`: Runtime environment (default: production)
- `BOT_NAME`: Display name for the bot
- `LOG_LEVEL`: Logging verbosity level
