import configparser
import logging
from logging.handlers import RotatingFileHandler

def create_logger(name, log_file, level=logging.INFO):
    """Create a logger with the specified name, log file, and logging level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def read_config(config_file, logger):
    """Read the configuration file and return the configuration data."""
    config = configparser.ConfigParser()
    config.read(config_file)
    
    config_data = {
        'SPOTIPY_CLIENT_ID': config.get('spotify', 'client_id'),
        'SPOTIPY_CLIENT_SECRET': config.get('spotify', 'client_secret'),
        'SPOTIPY_REDIRECT_URI': config.get('spotify', 'redirect_uri'),
        'PLEX_URL': config.get('plex', 'url'),
        'PLEX_TOKEN': config.get('plex', 'token'),
        'SPOTIFY_PLAYLIST_IDS': config.get('playlists', 'playlist_ids'),
        'PLEX_USER_TOKENS': config.get('users', 'tokens')
    }
    
    logger.info(f"Configuration file '{config_file}' loaded successfully.")
    return config_data
