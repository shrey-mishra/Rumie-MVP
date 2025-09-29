from typing import Dict, Any
import httpx
import google.generativeai as genai
from app.config import settings
from app.logging_config import get_logger

logger = get_logger("gemini_service")

class GeminiService:
    """Service for interacting with Gemini AI API"""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Configure Gemini API
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.api_available = True
                logger.info("Gemini API configured successfully")
            except Exception as e:
                logger.warning("Failed to configure Gemini API, using mock responses", error=str(e))
                self.api_available = False
        else:
            logger.info("Gemini API key not configured, using mock responses")
            self.api_available = False
    
    async def generate_empathetic_response(
        self, 
        user_input: str, 
        user_personality: str, 
        mode_pref: str
    ) -> Dict[str, Any]:
        """
        Generate empathetic response based on user input and personality
        """
        try:
            if self.api_available:
                return await self._call_gemini_api(user_input, user_personality, mode_pref)
            else:
                return self._mock_empathetic_response(user_input, user_personality, mode_pref)
            
        except Exception as e:
            logger.error("Error generating empathetic response", error=str(e))
            return {
                "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                "confidence": 0.0,
                "emotion": "neutral"
            }
    
    def _mock_empathetic_response(
        self, 
        user_input: str, 
        user_personality: str, 
        mode_pref: str
    ) -> Dict[str, Any]:
        """Mock response for development"""
        responses = {
            "efficient_organizer": "I understand you're looking for a structured approach. Let me help you organize this efficiently.",
            "creative_thinker": "That's an interesting perspective! Let's explore some creative solutions together.",
            "analytical_processor": "Let me break this down systematically to help you understand the situation better.",
            "empathetic_listener": "I can sense this is important to you. Let's work through this together with care and understanding."
        }
        
        base_response = responses.get(user_personality, "I'm here to help you with that.")
        
        return {
            "response": f"{base_response} {user_input}",
            "confidence": 0.85,
            "emotion": "empathetic",
            "personality_match": user_personality,
            "mode_adapted": mode_pref
        }
    
    async def _call_gemini_api(
        self, 
        user_input: str, 
        user_personality: str, 
        mode_pref: str
    ) -> Dict[str, Any]:
        """Call actual Gemini API"""
        try:
            # Create a tailored prompt for the Gemini API
            prompt = f"""
            You are an empathetic AI assistant. The user has a {user_personality} personality and prefers {mode_pref} mode.
            
            User input: {user_input}
            
            Respond in a way that matches their personality and mode preferences. Be empathetic, helpful, and tailored to their communication style.
            """
            
            # Generate response using Gemini with proper async handling
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse the response
            response_text = response.text if response.text else "I understand your request."
            
            logger.info("Gemini API response generated", response_length=len(response_text))
            
            return {
                "response": response_text,
                "confidence": 0.9,  # High confidence for actual API responses
                "emotion": "empathetic",
                "personality_match": user_personality,
                "mode_adapted": mode_pref
            }
            
        except Exception as e:
            logger.error("Error calling Gemini API", error=str(e))
            # Fallback to mock response
            return self._mock_empathetic_response(user_input, user_personality, mode_pref)

# Global service instance
gemini_service = GeminiService()
