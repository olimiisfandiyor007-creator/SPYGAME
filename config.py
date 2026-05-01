import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8639869450:AAGKAUD3iJfFaEnyBNvhARPbf_IoVkq8ams')

# Game settings
MAX_PLAYERS = 10
MIN_PLAYERS = 3
MAX_SPIES = 3

# Emojis
EMOJI = {
    'spy': '🕵️',
    'civilian': '👤',
    'room': '🚪',
    'play': '▶️',
    'stop': '⏹️',
    'settings': '⚙️',
    'category': '📂',
    'players': '👥',
    'ready': '✅',
    'wait': '⏳',
    'info': 'ℹ️',
    'warning': '⚠️',
    'success': '🎉',
    'fire': '🔥'
}