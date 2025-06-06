import os

class Config:
    """Application configuration constants."""
    
    # File paths
    CONTEXT_SNAPSHOT_FILENAME = "context_snapshot.txt"
    OBSIDIAN_CONFIG_PATH = os.path.expandvars(r"%APPDATA%\Obsidian\obsidian.json")
    TEMP_SCREENSHOT_PATH = "temp_screenshot.png"
    
    # Obsidian settings
    DEFAULT_EXCLUDED_DIRS = {".obsidian", "унік", "Навчання поза уніком", "Матеріальна частина"}
    
    # Ollama settings
    OLLAMA_MODEL = "qwen3:latest"
    OLLAMA_VISION_MODEL = "llava:latest"
    OLLAMA_URL = "http://localhost:11434/api/generate"
    OLLAMA_TIMEOUT = 120
    
    # Gemini settings
    GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"