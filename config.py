import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # URL prefix configuration
        url_prefix = os.getenv("URL_PREFIX", "").rstrip("/")
        if url_prefix and not url_prefix.startswith("/"):
            url_prefix = "/" + url_prefix
        self.url_prefix = url_prefix


app_config = Config()
