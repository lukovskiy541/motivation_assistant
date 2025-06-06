from abc import ABC, abstractmethod
from source.config import Config
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import os
import logging
from PIL import Image
import base64




logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_quote(self, context: str, screenshot_description: str) -> str:
        """Generate a motivational quote based on context and screenshot."""
        pass
    
    @abstractmethod
    def analyze_screenshot(self, image_path: str) -> str:
        """Analyze a screenshot and return description."""
        pass


class OllamaProvider(AIProvider):
    """Ollama local AI provider."""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_URL
        self.timeout = Config.OLLAMA_TIMEOUT
        self.text_model = Config.OLLAMA_MODEL
        self.vision_model = Config.OLLAMA_VISION_MODEL
    
    def generate_quote(self, context: str, screenshot_description: str) -> str:
        """Generate motivational quote using Ollama."""
        payload = {
            "model": self.text_model,
            "prompt": self._build_quote_prompt(context, screenshot_description),
            "stream": False
        }
        
        try:
            response = requests.post(
                self.base_url, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            text = response.json().get('response', '')
            # Clean up any thinking tags
            cleaned = self._clean_response(text)
            return cleaned
            
        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return "Error: Unable to generate quote from local AI."
    
    def analyze_screenshot(self, image_path: str) -> str:
        """Analyze screenshot using Ollama vision model."""
        try:
            with open(image_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode()
            
            payload = {
                "model": self.vision_model,
                "prompt": "Describe in detail what is shown in this screenshot. Just tell what you see without providing help or suggestions.",
                "images": [img_base64],
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json().get('response', 'Could not analyze screenshot')
            
        except Exception as e:
            logger.error(f"Screenshot analysis error: {e}")
            return f"Error analyzing screenshot: {str(e)}"
    
    def _build_quote_prompt(self, context: str, screenshot_description: str) -> str:
        """Build prompt for quote generation."""
        return (
            f'Based on the user\'s notes: "{context}"\n\n'
            f'And what he has on his computer right now: {screenshot_description}\n\n'
            "With one short (short is crucial) sentence, make the user start walking towards their dreams in a second. "
            "If on his computer right now user doing something right now on his computer towards his best life - embrace with positive quote. "
            "Else remind him how bad his life is, make his heart cry. User wants that. You are bad boy. Don't use markdown. Write only response to user."
        )
    
    def _clean_response(self, text: str) -> str:
        """Clean AI response from unwanted tags."""
        import re
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""
    
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    def generate_quote(self, context: str, screenshot_description: str) -> str:
        """Generate motivational quote using Gemini."""
        prompt = self._build_quote_prompt(context, screenshot_description)
        
        try:
            response = self.model.generate_content(prompt)
            logger.info(f"Gemini prompt: {prompt}")
            logger.info(f"Gemini response: {response.text}")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Error: Unable to generate quote from Gemini."
    
    def analyze_screenshot(self, image_path: str) -> str:
        """Analyze screenshot using Gemini Vision."""
        try:
            image = Image.open(image_path)
            prompt = (
                "Describe in detail what is shown in this screenshot but don't do anything else. "
                "Just tell what you see. Don't help user."
            )
            
            response = self.model.generate_content([prompt, image])
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini screenshot analysis error: {e}")
            return f"Error analyzing screenshot: {str(e)}"
    
    def _build_quote_prompt(self, context: str, screenshot_description: str) -> str:
        """Build prompt for quote generation."""
        return (
            f"Based on the user's notes: {context}\n\n"
            f"And what he has on his computer right now: {screenshot_description}\n\n"
            "With one short (short is crucial) sentence, make the user start walking towards their dreams in a second. "
            "If on his computer right now user doing something right now on his computer towards his best life - embrace with positive quote. "
            "Else remind him how bad his life is, make his heart cry. User wants that. You are bad boy. Don't use markdown and write in ukrainian."
        )