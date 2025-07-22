import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WELCOME_MESSAGE = os.environ.get(
    "WELCOME_MESSAGE",
    "👋 Welcome to our Telegram group!\n\nWe're excited to have you join our community. Here you can connect, share, and learn with others.\n\nPlease be respectful and follow the group guidelines. If you have any questions, feel free to ask.\n\nEnjoy your stay!"
)
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "-1001234567890"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002286109418"))
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/your_channel_url")

# Pyrogram configuration
API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
CHAT_ID = int(os.environ.get("CHAT_ID", "-1002286109418"))
WELCOME_TEXT = os.environ.get(
    "WELCOME_TEXT",
    "👋 Welcome to our Telegram group!\n\nWe're excited to have you join our community. Here you can connect, share, and learn with others.\n\nPlease be respectful and follow the group guidelines. If you have any questions, feel free to ask.\n\nEnjoy your stay!"
)

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "your_strong_password")
GROUP_INVITE_LINK = os.environ.get("GROUP_INVITE_LINK", "https://t.me/your_group_invite_link")
