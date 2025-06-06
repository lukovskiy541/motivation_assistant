import os
import json
from pathlib import Path
from source.config import Config
import logging

logger = logging.getLogger(__name__)


class ObsidianContextManager:
    """Manages Obsidian vault context extraction."""
    
    def __init__(self):
        self.config_path = Path(Config.OBSIDIAN_CONFIG_PATH)
        self.context_file = Path(Config.CONTEXT_SNAPSHOT_FILENAME)
        self.excluded_dirs = Config.DEFAULT_EXCLUDED_DIRS
    
    def get_current_context(self) -> str:
        """Get current context, generating if necessary."""
        if not self.context_file.exists():
            logger.info("Context file not found, generating new context...")
            self.generate_context_snapshot()
        
        try:
            return self.context_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading context file: {e}")
            return ""
    
    def generate_context_snapshot(self) -> bool:
        """Generate context snapshot from Obsidian vault."""
        if not self.config_path.exists():
            logger.error(f"Obsidian config not found at {self.config_path}")
            return False
        
        try:
            # Load Obsidian config
            with open(self.config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Get vault paths
            vaults = [vault["path"] for vault in config_data["vaults"].values()]
            if not vaults:
                logger.error("No vaults found in Obsidian config")
                return False
            
            # Use first vault (TODO: Allow user selection)
            vault_path = Path(vaults[0])
            
            # Extract content
            content = self._extract_vault_content(vault_path)
            
            # Save context
            self.context_file.write_text(content, encoding='utf-8')
            logger.info(f"Context snapshot generated with {len(content)} characters")
            return True
            
        except Exception as e:
            logger.error(f"Error generating context snapshot: {e}")
            return False
    
    def _extract_vault_content(self, vault_path: Path) -> str:
        """Extract all markdown content from vault."""
        all_content = []
        
        for root, dirs, files in os.walk(vault_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            folder_name = os.path.basename(root)
            all_content.append(f"Назва папки: {folder_name}\n")
            
            # Process markdown files
            for filename in files:
                if filename.endswith(".md"):
                    file_path = Path(root) / filename
                    title = filename.removesuffix(".md")
                    
                    all_content.append(f"Назва файлу: {title}\n")
                    
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        all_content.append(f"Текст файлу: <<{content}>>\n")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return '\n'.join(all_content)
    
    def refresh_context(self) -> bool:
        """Force refresh of context snapshot."""
        if self.context_file.exists():
            try:
                self.context_file.unlink()
            except Exception as e:
                logger.warning(f"Could not remove old context file: {e}")
        
        return self.generate_context_snapshot()