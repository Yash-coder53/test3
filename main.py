import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
import requests
import json
import logging

# --- Configuration ---
# Get these from my.telegram.org after logging in with your Telegram account.
API_ID = os.environ.get('TG_API_ID', 'YOUR_TELEGRAM_API_ID') # Replace or set as environment variable
API_HASH = os.environ.get('TG_API_HASH', 'YOUR_TELEGRAM_API_HASH') # Replace or set as environment variable
SESSION_NAME = 'my_telegram_session' # Name for your session file

# Get your API key from OpenRouter.ai
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_KEY', 'YOUR_OPENROUTER_API_KEY') # Replace or set as environment variable
OPENROUTER_MODEL = "mistralai/mixtral-8x7b-instruct-v0.1" # Example model, choose one from OpenRouter

ALLOWED_CHATS_FILE = 'allowed_chats.json'
ALLOWED_CHATS = set() # Stores chat IDs where the bot is allowed to respond

# --- Logging Setup ---
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set to INFO for detailed bot logs

# --- Initialize Telegram Client ---
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# --- Persistence Functions ---
def load_allowed_chats():
    global ALLOWED_CHATS
    if os.path.exists(ALLOWED_CHATS_FILE):
        try:
            with open(ALLOWED_CHATS_FILE, 'r') as f:
                data = json.load(f)
                ALLOWED_CHATS = set(data)
            logger.info(f"Loaded allowed chats: {ALLOWED_CHATS}")
        except json.JSONDecodeError:
            logger.error("Error decoding allowed_chats.json. Starting with empty set.")
            ALLOWED_CHATS = set()
    else:
        logger.info("allowed_chats.json not found. Starting with empty set.")
        ALLOWED_CHATS = set()

def save_allowed_chats():
    with open(ALLOWED_CHATS_FILE, 'w') as f:
        json.dump(list(ALLOWED_CHATS), f)
    logger.info(f"Saved allowed chats: {ALLOWED_CHATS}")

# --- OpenRouter AI Interaction Function ---
async def get_ai_response(prompt):
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'YOUR_OPENROUTER_API_KEY':
        logger.error("OPENROUTER_API_KEY is not set. Cannot get AI response.")
        return "Sorry, my AI capabilities are not configured. Please set the OPENROUTER_API_KEY."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=30 # Add a timeout for the API request
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return "Sorry, I couldn't get a response from the AI at the moment due to an API error."
    except KeyError:
        logger.error(f"Unexpected response format from OpenRouter: {result}")
        return "Sorry, I received an unexpected response from the AI."

# --- Telegram Event Handler ---
@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_group or e.is_private))
async def handler(event):
    chat = await event.get_chat()
    chat_id = chat.id
    
    # Ignore messages from ourselves to prevent loops
    me = await client.get_me()
    if event.sender_id == me.id:
        return

    message_text = event.raw_text.strip()
    logger.info(f"[{chat.title if hasattr(chat, 'title') else 'Private Chat'}:{chat_id}] Received message: {message_text[:50]}...")

    # --- Command Handling ---
    if message_text.lower() == "/allow":
        if chat_id in ALLOWED_CHATS:
            await event.reply("I am already allowed to chat in this group.")
            logger.info(f"Chat {chat_id} already allowed.")
        else:
            ALLOWED_CHATS.add(chat_id)
            save_allowed_chats()
            await event.reply("Hello everyone! I'm now allowed to chat in this group. Ask me anything!")
            logger.info(f"Allowed chat {chat_id}.")
        return # Don't process as AI prompt

    if message_text.lower() == "/unallow":
        if chat_id not in ALLOWED_CHATS:
            await event.reply("I am not currently allowed to chat in this group.")
            logger.info(f"Chat {chat_id} already not allowed.")
        else:
            ALLOWED_CHATS.remove(chat_id)
            save_allowed_chats()
            await event.reply("Okay, I will no longer chat in this group unless re-allowed with /allow.")
            logger.info(f"Unallowed chat {chat_id}.")
        return # Don't process as AI prompt

    # --- AI Chat Logic ---
    if chat_id not in ALLOWED_CHATS:
        # Check if the message explicitly mentions our bot account.
        # This requires getting our own entity.
        me = await client.get_me()
        # You might need to adjust this to check for your actual username or display name
        # A simple check for now: if someone replies to us, or mentions our full name/username
        if event.is_reply and event.reply_to.reply_to_msg_id:
            try:
                original_message = await event.get_reply_message()
                if original_message and original_message.sender_id == me.id:
                    logger.info(f"[{chat_id}] Not allowed but got a reply to my message. Responding anyway.")
                    pass # Allow response if it's a reply to our own message
                else:
                    logger.info(f"[{chat_id}] Not allowed and not a reply to me. Ignoring message.")
                    return # Ignore if not allowed and not a reply to us
            except Exception as e:
                logger.warning(f"Error checking reply message: {e}. Defaulting to ignore.")
                return # Ignore on error
        else:
            # Further checks for mentions might be needed, but for simplicity,
            # if not explicitly allowed, only replies to own messages are processed.
            logger.info(f"[{chat_id}] Not allowed. Ignoring message.")
            return # Ignore if not allowed and not a reply to us

    # If we reach here, it means we are either allowed, or it's a reply to our own message
    # in an unallowed group (which we'll handle to provide context in case of error).
    
    # Get AI response
    ai_response = await get_ai_response(message_text)
    
    # Send AI response back to the group
    await event.reply(ai_response)
    logger.info(f"[{chat_id}] Sent AI response: {ai_response[:50]}...")

# --- Main function to run the client ---
async def main():
    print("Loading allowed chats...")
    load_allowed_chats() # Load allowed chats at startup

    print("Connecting to Telegram...")
    # client.start() will prompt for phone/code if session doesn't exist
    await client.start()
    
    # Get info about the connected account
    me = await client.get_me()
    logger.info(f"Telegram client connected as: {me.first_name} (@{me.username})")
    
    print("Client Connected. Listening for messages...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"An unhandled error occurred: {e}", exc_info=True)
