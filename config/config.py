from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

import os
from pathlib import Path

# Request and content limits
MAX_REQUEST_SIZE = 1 * 1024 * 1024  # 1MB request limit
MAX_URL_LENGTH = 2048  # URL length limit
MAX_INPUT_SIZE = 100 * 1024  # 100KB for direct text input
MAX_CONTENT_INFLATION = 1.1  # Maximum 10% increase from GPT processing

# Server configuration
SERVER_HOST = '0.0.0.0'
SERVER_PORT = int(os.getenv('SERVER_PORT', '4973'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', '').lower() == 'true'

# API Security
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("API_TOKEN must be set in environment")

# Feed configuration
BASE_URL= os.getenv('BASE_URL', 'http://localhost:5000')
FEED_TITLE = os.getenv('FEED_TITLE', 'Hypercast')
FEED_DESCRIPTION = os.getenv('FEED_DESCRIPTION', 'A personal podcast generator for turning articles into audio for offline listening.')
FEED_IMAGE = os.getenv('FEED_IMAGE', 'podcast-cover.png')
FEED_SOUND = os.getenv('FEED_SOUND', 'intro-sound.mp3')
FEED_LANGUAGE = 'en-us'

# Base paths
APP_ROOT = Path(__file__).parent.parent
STATIC_PATH = APP_ROOT / 'app' / 'static'
AUDIO_PATH = STATIC_PATH / 'audio'
ASSETS_PATH = APP_ROOT / 'assets'
INTRO_SOUND_PATH = ASSETS_PATH / FEED_SOUND

# Audio configuration
AUDIO_OUTPUT_FORMAT = 'mp3'
AUDIO_OUTPUT_QUALITY = '192k'

# TTS configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TTS_MODEL = os.getenv('TTS_MODEL', 'tts-1')
TTS_VOICE = os.getenv('TTS_VOICE', 'onyx')
TTS_SPEED = float(os.getenv('TTS_SPEED', '1.0'))

# Content processing configuration
CONTENT_CLEANUP_MODEL = os.getenv('CONTENT_CLEANUP_MODEL', 'gpt-4o-mini')
TITLE_GENERATION_MODEL = os.getenv('TITLE_GENERATION_MODEL', 'gpt-4o-mini')
