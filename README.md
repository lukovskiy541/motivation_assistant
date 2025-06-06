# Motivation Assistant

**Motivation Assistant** is a Windows desktop application that helps you stay inspired by sending personalized motivational notifications based on your Obsidian notes and current screen activity, powered by modern AI models.

---

## Features

- **AI Motivation:** Generates motivational messages using your notes and current screen context.
- **Supports Local & Cloud AI:** Works with local Ollama or Google Gemini.
- **Obsidian Integration:** Analyzes your Obsidian vault for deeper context.
- **System Tray App:** Easy access via Windows system tray icon.
- **Autostart Option:** Can launch automatically with Windows.
- **Flexible Scheduling:** Sends notifications at random times several times per hour.

---

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/lukovskiy541/motivation_assistant
    cd motivation_assistant
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **(Optional) Set up local AI with Ollama:**
    - Install Ollama: https://ollama.com/
    - Download the LLaVA model:
      ```bash
      ollama pull llava:latest
      ollama serve
      ```

5. **(Optional) Add your Gemini API key to `.env`:**
    ```
    GEMINI_API_KEY=your_gemini_api_key
    ```

---

## Usage

```bash
python main.py
```

The app will appear in your Windows system tray. Right-click the icon for options.

---

## Project Structure

```
motivation_assistant/
│
├── main.py                # Entry point, GUI, system tray logic
├── assistant_core.py      # Main AI/context coordinator
├── ai_providers.py        # AI providers (Ollama, Gemini)
├── screenshot.py          # Screenshot analyzer
├── context_manager.py     # Obsidian integration
├── config.py              # Configuration and constants
├── requirements.txt       # Python dependencies
├── icon.png               # App icon
└── README.md
```

---

## Autostart

- Enable or disable autostart from the tray menu ("Launch on startup").
- The app manages a shortcut in your Windows Startup folder.

---

## Requirements

- Windows 10/11
- Python 3.8+
- Obsidian (for context integration)
- (Optional) Ollama for local AI

---

## License

MIT License

---

## Feedback & Support

Open an issue or pull request on this repository for questions, suggestions, or contributions!
