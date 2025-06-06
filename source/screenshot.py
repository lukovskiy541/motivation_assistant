
from source.ai_providers import AIProvider
from source.config import Config
import pyautogui
import time
import os
import logging

logger = logging.getLogger(__name__)


class ScreenshotAnalyzer:
    """Handles screenshot capture and analysis."""
    
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
        self.screenshot_path = Config.TEMP_SCREENSHOT_PATH
    
    def capture_and_analyze(self) -> str:
        """Capture screenshot and return AI analysis."""
        start_time = time.time()
        
        try:
            # Capture screenshot
            capture_start = time.time()
            screenshot = pyautogui.screenshot()
            screenshot.save(self.screenshot_path)
            capture_time = time.time() - capture_start
            
            logger.info(f"Screenshot captured in {capture_time:.2f} seconds")
            
            # Analyze with AI
            analysis_start = time.time()
            description = self.ai_provider.analyze_screenshot(self.screenshot_path)
            analysis_time = time.time() - analysis_start
            
            total_time = time.time() - start_time
            logger.info(
                f"Screenshot analysis completed:\n"
                f"- Capture: {capture_time:.2f}s\n"
                f"- Analysis: {analysis_time:.2f}s\n"
                f"- Total: {total_time:.2f}s"
            )
            
            return description
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return f"Error: {str(e)}"
        finally:
            # Clean up temporary file
            self._cleanup_screenshot()
    
    def _cleanup_screenshot(self) -> None:
        """Remove temporary screenshot file."""
        try:
            if os.path.exists(self.screenshot_path):
                os.remove(self.screenshot_path)
        except OSError as e:
            logger.warning(f"Could not remove temporary screenshot: {e}")
