"""
Gemini AI Service
Handles integration with Google Gemini AI API
"""

import logging
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not provided")
            
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            if not self.client:
                return False
            
            # Simple test request
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Test connection. Reply with 'OK'."
            )
            
            return bool(response.text and "OK" in response.text.upper())
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
    
    async def generate_response(self, user_message: str, user_name: str = "User", chat_name: str = "Group") -> str:
        """Generate AI response using Gemini"""
        try:
            if not self.client:
                logger.error("Gemini client not initialized")
                return "AI service is currently unavailable."
            
            # Create context-aware prompt
            system_prompt = (
                "You are @mraprguildbot, a Gemini AI Training Assistant in a Telegram group chat. "
                "You specialize in programming training, coding assistance, and technical education. "
                "Provide helpful, accurate, and engaging responses focused on learning and development. "
                "Keep responses conversational and appropriate for group training settings. "
                "Be educational, encouraging, and provide practical examples when possible. "
                f"The user's name is {user_name} and this is in the group '{chat_name}'."
            )
            
            # Prepare the message
            full_prompt = f"{system_prompt}\n\nUser message: {user_message}"
            
            logger.info(f"Generating response for message from {user_name}")
            
            # Generate response
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=full_prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                    top_p=0.9
                )
            )
            
            if response.text:
                logger.info("Successfully generated AI response")
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini")
                return "I'm having trouble generating a response. Please try rephrasing your message."
                
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return "I'm experiencing technical difficulties. Please try again in a moment."
    
    async def generate_contextual_response(self, user_message: str, conversation_history: list = None, user_name: str = "User", chat_name: str = "Group") -> str:
        """Generate response with conversation context"""
        try:
            if not self.client:
                logger.error("Gemini client not initialized")
                return "AI service is currently unavailable."
            
            # Build context from conversation history
            context_parts = []
            
            # Add system instruction
            system_instruction = (
                "You are @mraprguildbot, a Gemini AI Training Assistant in a Telegram group chat. "
                "You specialize in programming training, coding assistance, and technical education. "
                "Provide helpful, accurate, and engaging responses based on the conversation context. "
                "Keep responses conversational and appropriate for group training settings. "
                "Be educational, encouraging, and provide practical examples when possible. "
                f"The current user is {user_name} in the group '{chat_name}'."
            )
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    context_parts.append(types.Part(text=f"Previous: {msg}"))
            
            # Add current message
            context_parts.append(types.Part(text=f"Current message from {user_name}: {user_message}"))
            
            logger.info(f"Generating contextual response for {user_name}")
            
            # Generate response with context
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[types.Content(role="user", parts=context_parts)],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1000,
                    top_p=0.9
                )
            )
            
            if response.text:
                logger.info("Successfully generated contextual AI response")
                return response.text.strip()
            else:
                logger.warning("Empty contextual response from Gemini")
                return "I'm having trouble generating a response. Please try rephrasing your message."
                
        except Exception as e:
            logger.error(f"Error generating contextual Gemini response: {e}")
            return "I'm experiencing technical difficulties. Please try again in a moment."
