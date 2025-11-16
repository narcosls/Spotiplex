import sys
from pathlib import Path
from configparser import ConfigParser
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtMultimedia import QMediaPlayer  # Add this import
from plexapi.server import PlexServer
from utils.spotify_functions import sync_spotify_playlist_with_plex, fetch_playlist_info, get_auth_token
from helper_classes.playlist import Playlist
from helper_classes.user_inputs import UserInputs
from utils.gui import UserSelectionApp
from datetime import datetime

def setup_logging(log_directory):
    log_directory.mkdir(parents=True, exist_ok=True)

    console_handler = logging.StreamHandler()
    console_handler.setStream(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def create_file_handler(log_filename):
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        return file_handler

    # Create log files
    main_log_file = log_directory / 'main.log'
    spotify_log_file = log_directory / 'spotify.log'
    plex_log_file = log_directory / 'plex.log'
    error_log_file = log_directory / 'error.log'
    app_log_file = log_directory / 'app.log'

    logging.basicConfig(level=logging.INFO, handlers=[
        console_handler,
        create_file_handler(main_log_file),
        create_file_handler(app_log_file)
    ])

    # Create individual loggers
    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(create_file_handler(error_log_file))

    spotify_logger = logging.getLogger('spotify')
    spotify_logger.setLevel(logging.INFO)
    spotify_logger.addHandler(create_file_handler(spotify_log_file))

    plex_logger = logging.getLogger('plex')
    plex_logger.setLevel(logging.INFO)
    plex_logger.addHandler(create_file_handler(plex_log_file))

    return logging.getLogger('main'), spotify_logger, plex_logger, error_logger

def main():
    # Create log directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_directory = Path('logs') / timestamp
    main_logger, spotify_logger, plex_logger, error_logger = setup_logging(log_directory)

    main_logger.info("Starting application...")

    # Read configuration
    config = ConfigParser()
    config.read('config.txt')

    # Start the GUI to select users
    app = QApplication(sys.argv)

    playlist_ids = config['playlists']['playlist_ids'].split(',')
    for playlist_id in playlist_ids:
        main_logger.info(f"Processing playlist ID: {playlist_id}")

        try:
            # Fetch playlist information
            playlist_info = fetch_playlist_info(config['spotify']['client_id'], config['spotify']['client_secret'], playlist_id)
            spotify_logger.info(f"Fetched playlist info: {playlist_info}")

            # Create Playlist instance
            playlist = Playlist(
                name=playlist_info['name'],
                description=playlist_info['description'],
                poster=playlist_info['poster']
            )

            # Show user selection GUI
            selection_app = UserSelectionApp(playlist_info['poster'])  # Pass the cover URL to the GUI
            selection_app.show()
            app.exec_()
            selected_users = selection_app.selected_users

            if not selected_users:
                main_logger.error("No users selected.")
                continue

            for selected_user in selected_users:
                # Fetch the auth token for the selected user
                token = get_auth_token(selected_user)
                main_logger.info(f"Token for user {selected_user}: {token}")
                if not token:
                    main_logger.error(f"No token found for user {selected_user}.")
                    continue

                # User Inputs (assuming this handles user-specific configurations)
                user_inputs = UserInputs(
                    spotify_client_id=config['spotify']['client_id'],
                    spotify_client_secret=config['spotify']['client_secret'],
                    plex_url=config['plex']['url'],
                    plex_token=token,
                    spotify_redirect_uri=config['spotify']['redirect_uri'],
                    spotify_playlist_ids=config['playlists']['playlist_ids']
                )

                main_logger.info(f"Plex URL: {user_inputs.plex_url}")
                main_logger.info(f"Plex Token: {user_inputs.plex_token}")

                # Output directory
                output_dir = Path('output') / timestamp / selected_user
                output_dir.mkdir(parents=True, exist_ok=True)

                # Sync Spotify playlist with Plex
                try:
                    plex = PlexServer(user_inputs.plex_url, user_inputs.plex_token)
                    plex_logger.info(f"Connected to Plex server at {user_inputs.plex_url}")
                    sync_spotify_playlist_with_plex(plex, playlist, user_inputs, playlist_id, output_dir)
                except Exception as e:
                    error_logger.error(f"Error connecting to Plex server: {e}")

        except Exception as e:
            error_logger.error(f"Error processing playlist ID {playlist_id}: {e}")

if __name__ == "__main__":
    main()
