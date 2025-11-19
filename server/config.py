"""
Configuration for Rememory Server
"""

import os
import json


class Config:
    """Server configuration"""

    # Try to load from config.json file
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')

    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            GEMINI_API_KEY = config_data.get('GEMINI_API_KEY', '')
    else:
        # Fallback to environment variable
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000

    # State update interval (seconds)
    STATE_UPDATE_INTERVAL = 180  # 3 minutes

    # Data retention settings
    MAX_GPS_POINTS = 100  # Maximum GPS points to keep in memory
    MAX_CONTEXT_HISTORY = 10  # Maximum Gemini context history entries

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found! "
                "Please create server/config.json with your API key or set GEMINI_API_KEY environment variable."
            )
        return True
