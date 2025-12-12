"""
Configuration settings for the inpainting application
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY_1')
MODEL_NAME = "gemini-2.5-flash-image"

# Retry Configuration
MAX_RETRIES = 5
BASE_DELAY = 5  # seconds

# Rate Limiting
RATE_LIMIT = "5/minute"  # 5 requests per minute per IP
