# Telegram AI Chat Tool for Termux

This tool allows your Telegram account to act as an AI chatbot in group chats, powered by OpenRouter.ai. You can control which groups the bot is active in using `/allow` and `/unallow` commands. It's designed to run 24/7 on Termux.

## Features

*   **AI Chat Integration**: Responds to messages in allowed groups using an OpenRouter.ai language model.
*   **Group-Specific Control**: Use `/allow` and `/unallow` commands in a group to enable or disable the bot's responses in that specific group.
*   **Persistence**: Allowed chat settings are saved and loaded, so the bot remembers permissions across restarts.
*   **Termux Deployment**: Instructions for deploying and running the bot continuously on Termux.
*   **Self-Healing**: Basic error handling for API calls.

## Prerequisites

1.  **Android Device**: With Termux installed.
2.  **Termux**:
    *   Install Python: `pkg install python`
    *   Install `tmux` (for 24/7 background operation): `pkg install tmux`
3.  **Telegram API Credentials**:
    *   Go to [my.telegram.org](https://my.telegram.org/).
    *   Log in with your Telegram account.
    *   Click "API development tools" and create a new application.
    *   Note down your `API_ID` and `API_HASH`.
4.  **OpenRouter.ai API Key**:
    *   Sign up/log in to [OpenRouter.ai](https://openrouter.ai/).
    *   Go to your dashboard or API key section to generate an API key.

## Setup Instructions

### 1. Save the Script

1.  Create a directory for your bot in Termux:
    ```bash
    mkdir ~/telegram_ai_bot
    cd ~/telegram_ai_bot
    ```
2.  Create a file named `telegram_ai_chat_tool.py` in this directory.
3.  Copy and paste the entire Python code provided above into this file.

### 2. Install Python Dependencies

In your Termux terminal, navigate to the bot's directory and install the required libraries:

```bash
cd ~/telegram_ai_bot
pip install telethon requests
