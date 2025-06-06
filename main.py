import sys
import os
import json
import random
import signal
import ctypes
import subprocess
from typing import Dict, Any, Optional

import win32com.client
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QMessageBox, QComboBox

from source.assistant_core import AIAssistant


class SettingsManager:
    """Handles application settings persistence."""
    
    def __init__(self):
        self.settings_path = os.path.join(
            os.path.expanduser("~"), 
            ".motivation_assistant_settings.json"
        )
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
        return {"autostart": False}
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to JSON file."""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")


class AutostartManager:
    """Manages Windows autostart functionality."""
    
    APP_NAME = "Motivation Assistant"
    
    def __init__(self):
        self.startup_dir = os.path.join(
            os.environ["APPDATA"], 
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        self.shortcut_path = os.path.join(self.startup_dir, f"{self.APP_NAME}.lnk")
    
    def set_autostart(self, enabled: bool) -> None:
        """Enable or disable autostart."""
        try:
            if enabled:
                self._create_shortcut()
            else:
                self._remove_shortcut()
        except Exception as e:
            print(f"Error managing autostart: {e}")
    
    def _create_shortcut(self) -> None:
        """Create startup shortcut."""
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(self.shortcut_path)
        shortcut.TargetPath = sys.executable
        shortcut.WorkingDirectory = os.path.dirname(sys.executable)
        shortcut.IconLocation = sys.executable
        shortcut.save()
    
    def _remove_shortcut(self) -> None:
        """Remove startup shortcut."""
        if os.path.exists(self.shortcut_path):
            os.remove(self.shortcut_path)


class NotificationScheduler:
    """Handles notification scheduling logic."""
    
    HOUR_MS = 60 * 60 * 1000
    NOTIFICATIONS_PER_HOUR = 2
    
    def __init__(self, show_message_callback):
        self.show_message_callback = show_message_callback
    
    def schedule_notifications(self) -> None:
        """Schedule random notifications within the next hour."""
        notification_times = sorted([
            random.randint(0, self.HOUR_MS) 
            for _ in range(self.NOTIFICATIONS_PER_HOUR)
        ])
        
        for time_ms in notification_times:
            QTimer.singleShot(time_ms, self.show_message_callback)
        
        QTimer.singleShot(self.HOUR_MS, self.schedule_notifications)


class MotivationAssistant:
    """Main application class for the Motivation Assistant."""
    
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.tray: Optional[QSystemTrayIcon] = None
        self.ai: Optional[AIAssistant] = None
        self.menu: Optional[QMenu] = None
        self.timer: Optional[QTimer] = None
        
        self.settings_manager = SettingsManager()
        self.autostart_manager = AutostartManager()
        self.notification_scheduler = NotificationScheduler(self.show_ai_message)
        
        self.action_autostart: Optional[QAction] = None
        self.action_show: Optional[QAction] = None
        self.action_change_provider: Optional[QAction] = None
        self.action_quit: Optional[QAction] = None
        
        self.settings = self.settings_manager.load_settings()
    
    def setup_application(self) -> None:
        """Initialize the PyQt application."""
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Motivation Assistant"
        )
        
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def prompt_for_ai_provider(self):
        """Prompt user for Gemini API key or to use local model and models if local."""
        from source import config  

        def is_ollama_installed():
            try:
                subprocess.run(["ollama", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            except Exception:
                return False

        def get_ollama_models():
            try:
                result = subprocess.run(["ollama", "list"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
                models = []
                for line in result.stdout.splitlines():
                    if line and not line.startswith("NAME"):
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            except Exception:
                return []

        class ApiKeyDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("AI Provider Setup")
                self.setModal(True)
                self.api_key = None
                self.use_local = False
                self.vision_model = ""
                self.text_model = ""

                layout = QVBoxLayout(self)

                self.label = QLabel("Choose AI provider:")
                layout.addWidget(self.label)

                self.radio_gemini = QRadioButton("Google Gemini (cloud)")
                self.radio_local = QRadioButton("Local model (Ollama)")
                self.radio_gemini.setChecked(True)
                layout.addWidget(self.radio_gemini)
                layout.addWidget(self.radio_local)

                self.api_key_input = QLineEdit()
                self.api_key_input.setPlaceholderText("Enter Gemini API key")
                layout.addWidget(self.api_key_input)

                # Vision/Text model selection for Ollama
                self.vision_label = QLabel("Ollama Vision Model:")
                self.vision_combo = QComboBox()
                self.text_label = QLabel("Ollama Text Model:")
                self.text_combo = QComboBox()

                # Only show model selection if Ollama is installed
                self.ollama_installed = is_ollama_installed()
                if self.ollama_installed:
                    models = get_ollama_models()
                    self.vision_combo.addItems(models)
                    self.text_combo.addItems(models)
                else:
                    self.vision_combo.addItem("Ollama not found")
                    self.text_combo.addItem("Ollama not found")

                layout.addWidget(self.vision_label)
                layout.addWidget(self.vision_combo)
                layout.addWidget(self.text_label)
                layout.addWidget(self.text_combo)

                # Show/hide fields based on selection
                def update_fields():
                    is_gemini = self.radio_gemini.isChecked()
                    self.api_key_input.setEnabled(is_gemini)
                    self.vision_label.setVisible(not is_gemini)
                    self.vision_combo.setVisible(not is_gemini)
                    self.text_label.setVisible(not is_gemini)
                    self.text_combo.setVisible(not is_gemini)

                self.radio_gemini.toggled.connect(update_fields)
                self.radio_local.toggled.connect(update_fields)
                update_fields()

                self.button_ok = QPushButton("OK")
                self.button_ok.clicked.connect(self.accept)
                layout.addWidget(self.button_ok)

            def accept(self):
                if self.radio_gemini.isChecked():
                    key = self.api_key_input.text().strip()
                    if not key:
                        QMessageBox.warning(self, "Input required", "Please enter your Gemini API key.")
                        return
                    self.api_key = key
                    self.use_local = False
                    self.vision_model = ""
                    self.text_model = ""
                else:
                    if not self.ollama_installed:
                        QMessageBox.warning(self, "Ollama not found", "Ollama is not installed or not in PATH.")
                        return
                    vision = self.vision_combo.currentText().strip()
                    text = self.text_combo.currentText().strip()
                    if not vision or not text or vision == "Ollama not found" or text == "Ollama not found":
                        QMessageBox.warning(self, "Input required", "Please select both Ollama models.")
                        return
                    self.api_key = None
                    self.use_local = True
                    self.vision_model = vision
                    self.text_model = text
                super().accept()

        dialog = ApiKeyDialog()
        if dialog.exec_() == QDialog.Accepted:
            self.settings["gemini_api_key"] = dialog.api_key
            self.settings["use_local_model"] = dialog.use_local
            self.settings["ollama_vision_model"] = dialog.vision_model
            self.settings["ollama_text_model"] = dialog.text_model
            self.settings_manager.save_settings(self.settings)

            # Update config.py variables at runtime
            if dialog.use_local:
                config.OLLAMA_VISION_MODEL = dialog.vision_model
                config.OLLAMA_TEXT_MODEL = dialog.text_model
            else:
                config.OLLAMA_VISION_MODEL = "llava:latest"
                config.OLLAMA_TEXT_MODEL = "qwen:latest"
        else:
            sys.exit(0)  # User cancelled

    def setup_ai_assistant(self) -> None:
        """Initialize the AI assistant."""
        # Prompt for API key or local model if not set
        if not self.settings.get("gemini_api_key") and not self.settings.get("use_local_model"):
            self.prompt_for_ai_provider()
        try:
            self.ai = AIAssistant(
                gemini_api_key=self.settings.get("gemini_api_key"),
                use_local_ai=self.settings.get("use_local_model", False)  
            )
        except Exception as e:
            print(f"Error initializing AI assistant: {e}")
            sys.exit(1)
    
    def setup_system_tray(self) -> None:
        """Setup the system tray icon and menu."""
        basedir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(basedir, "icon.png")
        
        self.tray = QSystemTrayIcon(QIcon(icon_path))
        self.tray.setVisible(True)
        
        self._setup_context_menu()
        self.tray.setContextMenu(self.menu)
    
    def _setup_context_menu(self) -> None:
        """Create and configure the context menu."""
        self.menu = QMenu()
        
        self.action_show = QAction("Get quote")
        self.action_change_provider = QAction("Change AI provider")  
        self.action_autostart = QAction("Launch on startup")
        self.action_quit = QAction("Quit")
        
        self.action_autostart.setCheckable(True)
        self.action_autostart.setChecked(self.settings.get("autostart", False))
        
        self.action_show.triggered.connect(self.show_message)
        self.action_change_provider.triggered.connect(self.change_ai_provider)  # CONNECT ACTION
        self.action_autostart.triggered.connect(self._toggle_autostart)
        self.action_quit.triggered.connect(self.quit_application)
        
        self.menu.addAction(self.action_show)
        self.menu.addAction(self.action_change_provider)  # ADD TO MENU
        self.menu.addAction(self.action_autostart)
        self.menu.addAction(self.action_quit)
    
    def change_ai_provider(self):
        """Show dialog to change AI provider and re-initialize assistant."""
        self.prompt_for_ai_provider()
        try:
            self.ai = AIAssistant(
                gemini_api_key=self.settings.get("gemini_api_key"),
                use_local_ai=self.settings.get("use_local_model", False)
            )
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to change AI provider: {e}")

    def setup_timer(self) -> None:
        """Setup the main application timer."""
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(100)
    
    def show_message(self) -> None:
        """Show a motivation message via manual trigger."""
        if self.ai and self.tray:
            try:
                message = self.ai.send_notification()
                self.tray.showMessage(
                    "Motivation Assistant", 
                    message, 
                    QSystemTrayIcon.Critical, 
                    3000
                )
            except Exception as e:
                print(f"Error showing message: {e}")
    
    def show_ai_message(self) -> None:
        """Show a motivation message via scheduled notification."""
        if self.ai and self.tray:
            try:
                message = self.ai.send_notification()
                self.tray.showMessage(
                    "Motivation Assistant", 
                    message, 
                    QSystemTrayIcon.Information, 
                    3000
                )
            except Exception as e:
                print(f"Error showing AI message: {e}")

    
    
    def _toggle_autostart(self) -> None:
        """Toggle autostart setting."""
        enabled = self.action_autostart.isChecked()
        self.settings["autostart"] = enabled
        self.settings_manager.save_settings(self.settings)
        self.autostart_manager.set_autostart(enabled)
    
    def quit_application(self) -> None:
        """Quit the application gracefully."""
        if self.app:
            self.app.quit()
    
    def _signal_handler(self, sig, frame) -> None:
        """Handle system signals for graceful shutdown."""
        self.quit_application()
    
    def run(self) -> None:
        """Run the application."""
        try:
            self.setup_application()
            self.setup_ai_assistant()
            self.setup_system_tray()
            self.setup_timer()
            
            self.notification_scheduler.schedule_notifications()
            
            sys.exit(self.app.exec())
            
        except Exception as e:
            print(f"Error running application: {e}")
            sys.exit(1)


def main():
    """Application entry point."""
    assistant = MotivationAssistant()
    assistant.run()


if __name__ == "__main__":
    main()