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

NAVER_ID = PersistentConfig(
    "NAVER_ID",
    "naver.id",
    os.environ.get("NAVER_ID", "")
)

NAVER_CLIENT_SECRET = PersistentConfig(
    "NAVER.CLIENT_SECRET",
    "naver.client_secret",
    os.environ.get("NAVER_CLIENT_SECRET", "")
)

NAVER_MAP_CLIENT_ID = PersistentConfig(
    "NAVER_MAP_CLIENT_ID",
    "naver.map.client_id",
    os.environ.get("NAVER_MAP_CLIENT_ID", "")
)

NAVER_MAP_CLIENT_SECRET = PersistentConfig(
    "NAVER_MAP_CLIENT_SECRET",
    "naver.map.client_secret",
    os.environ.get("NAVER_MAP_CLIENT_SECRET", "")
)


def init_extended_config(app):
    """Initialize extended configurations"""
    app.state.config.NAVER_MAP_API_KEY = NAVER_MAP_API_KEY
    app.state.config.NAVER_MAP_CLIENT_ID = NAVER_MAP_CLIENT_ID
    app.state.config.NAVER_MAP_CLIENT_SECRET = NAVER_MAP_CLIENT_SECRET
    app.state.config.NAVER_MAP_CLIENT_SECRET = NAVER_ID
    app.state.config.NAVER_MAP_CLIENT_SECRET = NAVER_CLIENT_SECRET