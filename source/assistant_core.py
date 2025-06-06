"""
AI Models and Context Management for Motivation Assistant

This module handles AI interactions, screenshot analysis, and Obsidian vault context generation.
"""

import logging
from pathlib import Path
from typing import Optional

from source.config import Config
from source.screenshot import ScreenshotAnalyzer
from source.ai_providers import OllamaProvider, GeminiProvider, AIProvider
from source.context_manager import ObsidianContextManager

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAssistant:
    """Main AI assistant coordinating all components."""

    def __init__(
        self,
        use_local_ai: bool = False,
        gemini_api_key: Optional[str] = None
    ):
        """
        Initialize AI assistant with specified provider.
        :param use_local_ai: Use Ollama (local) if True, else Gemini.
        :param gemini_api_key: Optional Gemini API key for cloud provider.
        """
        try:
            if use_local_ai:
                self.ai_provider = OllamaProvider()
                logger.info("Using Ollama (local AI)")
            else:
                self.ai_provider = GeminiProvider(api_key=gemini_api_key)
                logger.info("Using Gemini AI")
        except Exception as e:
            logger.error(f"Error initializing AI provider: {e}")
            # Fallback to the other provider
            try:
                if use_local_ai:
                    self.ai_provider = GeminiProvider(api_key=gemini_api_key)
                    logger.info("Fallback to Gemini AI")
                else:
                    self.ai_provider = OllamaProvider()
                    logger.info("Fallback to Ollama (local AI)")
            except Exception as fallback_error:
                logger.error(f"Fallback provider also failed: {fallback_error}")
                raise RuntimeError("No AI provider could be initialized")

        # Initialize components
        self.screenshot_analyzer = ScreenshotAnalyzer(self.ai_provider)
        self.context_manager = ObsidianContextManager()

        # Ensure context is available
        self.ensure_context()

    def send_notification(self) -> str:
        """Generate a motivational notification based on current context and screen."""
        try:
            context = self.context_manager.get_current_context()
            screenshot_description = self.screenshot_analyzer.capture_and_analyze()
            quote = self.ai_provider.generate_quote(context, screenshot_description)
            return quote
        except Exception as e:
            logger.error(f"Error generating notification: {e}")
            return "Stay focused on your goals! 💪"

    def ensure_context(self) -> None:
        """Ensure context is available, generate if needed."""
        if not Path(Config.CONTEXT_SNAPSHOT_FILENAME).exists():
            logger.info("Generating initial context snapshot...")
            self.context_manager.generate_context_snapshot()

    def refresh_context(self) -> bool:
        """Refresh the Obsidian context."""
        return self.context_manager.refresh_context()

    def switch_ai_provider(self, use_local_ai: bool, gemini_api_key: Optional[str] = None) -> bool:
        """Switch between local and cloud AI providers."""
        try:
            if use_local_ai:
                new_provider = OllamaProvider()
            else:
                new_provider = GeminiProvider(api_key=gemini_api_key)
            self.ai_provider = new_provider
            self.screenshot_analyzer.ai_provider = new_provider
            provider_name = "Ollama (local)" if use_local_ai else "Gemini"
            logger.info(f"Switched to {provider_name} AI provider")
            return True
        except Exception as e:
            logger.error(f"Error switching AI provider: {e}")
            return False


# Factory function for easy instantiation
def create_ai_assistant(
    use_local_ai: bool = False,
    gemini_api_key: Optional[str] = None
) -> AIAssistant:
    """Factory function to create AI assistant with error handling."""
    try:
        return AIAssistant(use_local_ai=use_local_ai, gemini_api_key=gemini_api_key)
    except Exception as e:
        logger.error(f"Failed to create AI assistant: {e}")
        raise


