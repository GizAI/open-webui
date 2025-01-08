from open_webui.config import PersistentConfig
import os

####################################
# Extended configurations
####################################

NAVER_MAP_API_KEY = PersistentConfig(
    "NAVER_MAP_API_KEY",
    "naver.map.api_key",
    os.environ.get("NAVER_MAP_API_KEY", "")
)

def init_extended_config(app):
    """Initialize extended configurations"""
    app.state.config.NAVER_MAP_API_KEY = NAVER_MAP_API_KEY