import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QDesktopWidget, QTextBrowser
from PyQt5.QtGui import QPalette, QColor, QPixmap, QFont
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from utils.config import read_config

class RatingKeyDialog(QDialog):
    def __init__(self, track_name, artist_name, album_name, year, duration, track_url, poster_url=None, preview_url=None):
        super().__init__()
        self.result = None
        self.preview_url = preview_url
        self.media_player = None

        # Get screen size
        screen = QDesktopWidget().screenGeometry()
        screen_width, screen_height = screen.width(), screen.height()

        # Calculate sizes based on screen size
        poster_size = int(min(screen_width, screen_height) * 0.4)  # 40% of the smaller dimension
        window_width, window_height = poster_size + 100, poster_size + 400
        
        self.setWindowTitle("Enter Rating Key")
        self.setGeometry(100, 100, window_width, window_height)

        layout = QVBoxLayout()
        
        # Set a larger font
        font = QFont()
        font.setPointSize(12)
        
        if poster_url:
            poster_label = QLabel(self)
            pixmap = QPixmap()
            pixmap.loadFromData(self.download_image(poster_url))
            pixmap = pixmap.scaled(poster_size, poster_size, Qt.KeepAspectRatio)
            poster_label.setPixmap(pixmap)
            poster_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(poster_label)
        
        track_info = QTextBrowser()
        track_info.setFont(font)
        track_info.setOpenExternalLinks(True)
        track_info.setReadOnly(True)
        track_info.setStyleSheet("background-color: transparent; border: none;")
        track_info.setHtml(f"""
            <b>Artist:</b> {artist_name}<br>
            <b>Track:</b> {track_name}<br>
            <b>Album:</b> {album_name}<br>
            <b>Year:</b> {year}<br>
            <b>Duration:</b> {duration}<br>
            <b>Link:</b> <a href="{track_url}" style="color:#2A82DA;">{track_url}</a>
        """)
        layout.addWidget(track_info)

        # Add play and stop buttons for preview after the link
        if self.preview_url:
            preview_layout = QHBoxLayout()
            play_button = QPushButton("Play Preview")
            play_button.setFont(font)
            play_button.clicked.connect(self.play_preview)
            stop_button = QPushButton("Stop")
            stop_button.setFont(font)
            stop_button.clicked.connect(self.stop_preview)
            preview_layout.addWidget(play_button)
            preview_layout.addWidget(stop_button)
            layout.addLayout(preview_layout)

            self.media_player = QMediaPlayer()

        input_layout = QHBoxLayout()
        self.input = QLineEdit(self)
        self.input.setFont(font)
        self.input.setPlaceholderText("Enter rating key")
        input_layout.addWidget(self.input)

        submit_button = QPushButton("Submit")
        submit_button.setFont(font)
        submit_button.clicked.connect(self.submit)
        input_layout.addWidget(submit_button)

        layout.addLayout(input_layout)

        buttons_layout = QHBoxLayout()
        prev_button = QPushButton("Previous")
        prev_button.setFont(font)
        prev_button.clicked.connect(self.previous)
        skip_button = QPushButton("Skip")
        skip_button.setFont(font)
        skip_button.clicked.connect(self.skip)

        buttons_layout.addWidget(prev_button)
        buttons_layout.addWidget(skip_button)
        layout.addLayout(buttons_layout)

        save_buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setFont(font)
        save_button.clicked.connect(self.save)
        save_close_button = QPushButton("Save and Close")
        save_close_button.setFont(font)
        save_close_button.clicked.connect(self.save_and_close)

        save_buttons_layout.addWidget(save_button)
        save_buttons_layout.addWidget(save_close_button)
        layout.addLayout(save_buttons_layout)

        self.setLayout(layout)

    def closeEvent(self, event):
        self.result = "save_and_close"
        event.accept()
    
    def download_image(self, url):
        from urllib.request import urlopen
        return urlopen(url).read()
        
    def get_rating_key(self):
        return self.input.text().strip()
    
    def submit(self):
        self.result = "submit"
        self.accept()
    
    def skip(self):
        self.result = "skip"
        self.reject()
    
    def previous(self):
        self.result = "previous"
        self.reject()
    
    def save(self):
        self.result = "save"
        self.accept()
    
    def save_and_close(self):
        self.result = "save_and_close"
        self.accept()

    def play_preview(self):
        if self.media_player and self.preview_url:
            self.media_player.setMedia(QMediaContent(QUrl(self.preview_url)))
            self.media_player.play()

    def stop_preview(self):
        if self.media_player:
            self.media_player.stop()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    # Set up logging
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = Path("logs") / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_dir / 'pre_match.log'), logging.StreamHandler()])
    logger = logging.getLogger('pre_match')

    config = read_config('config.txt', logger)
    spotify_playlist_ids = [id.strip() for id in config['SPOTIFY_PLAYLIST_IDS'].split(',') if id.strip()]

    if not spotify_playlist_ids:
        logger.error("No Spotify playlists specified in the config file.")
        return

    client_credentials_manager = SpotifyClientCredentials(client_id=config['SPOTIPY_CLIENT_ID'], client_secret=config['SPOTIPY_CLIENT_SECRET'])
    sp = Spotify(client_credentials_manager=client_credentials_manager)

    matched_tracks_file = Path("matched_tracks.json")
    if matched_tracks_file.exists():
        with open(matched_tracks_file, 'r') as f:
            matched_tracks = json.load(f)
    else:
        matched_tracks = {}

    def process_playlist(spotify_playlist_id):
        try:
            logger.info(f"Fetching playlist info for ID: {spotify_playlist_id}")
            playlist_info = sp.playlist(spotify_playlist_id)
            logger.info(f"Playlist info: {playlist_info}")

            if not playlist_info:
                logger.error(f"Failed to fetch playlist info for ID: {spotify_playlist_id}")
                return

            playlist_name = playlist_info['name']
            logger.info(f"Processing playlist '{playlist_name}'...")

            offset = 0
            spotify_tracks = []

            while True:
                try:
                    tracks_response = sp.playlist_tracks(spotify_playlist_id, offset=offset)
                except Exception as e:
                    logger.error(f"Error fetching tracks for playlist ID '{spotify_playlist_id}': {e}")
                    break

                logger.info(f"Fetched {len(tracks_response['items'])} tracks, Offset: {offset}")

                if not tracks_response['items']:
                    break

                spotify_tracks.extend(tracks_response['items'])
                offset += len(tracks_response['items'])

            if not spotify_tracks:
                logger.error(f"Failed to fetch tracks for playlist ID: {spotify_playlist_id}")
                return

            i = 0
            history = []
            while i < len(spotify_tracks):
                if i in history:
                    logger.warning(f"Track {i + 1} is being processed again.")
                else:
                    history.append(i)

                spotify_track = spotify_tracks[i]['track']
                try:
                    track_id = spotify_track['id']
                    if track_id in matched_tracks:
                        logger.info(f"Track '{spotify_track['name']}' by '{spotify_track['artists'][0]['name']}' is already matched. Skipping.")
                        i += 1
                        continue

                    track_name = spotify_track['name']
                    artist_name = spotify_track['artists'][0]['name']
                    album_name = spotify_track['album']['name']
                    year = spotify_track['album']['release_date'][:4]
                    duration_ms = spotify_track['duration_ms']
                    duration = f"{duration_ms // 60000}:{(duration_ms // 1000) % 60:02}"
                    track_url = spotify_track['external_urls']['spotify']
                    preview_url = spotify_track.get('preview_url')
                except KeyError as e:
                    logger.error(f"Error processing track data: {e}")
                    i += 1
                    continue

                logger.info(f"Matching Spotify track '{track_name}' by '{artist_name}'...")

                poster_url = spotify_track['album']['images'][0]['url'] if spotify_track['album']['images'] else None

                logger.info(f"Creating dialog for track '{track_name}' by '{artist_name}'")
                dialog = RatingKeyDialog(track_name, artist_name, album_name, year, duration, track_url, poster_url, preview_url)
                dialog_result = dialog.exec_()
                logger.info(f"Dialog result for track '{track_name}': {dialog.result}")

                if dialog.result == "submit":
                    rating_key = dialog.get_rating_key()
                    if rating_key:
                        try:
                            matched_tracks[track_id] = int(rating_key)
                        except ValueError:
                            logger.error(f"Invalid rating key '{rating_key}' entered for track '{track_name}'")
                    i += 1
                elif dialog.result == "skip":
                    i += 1
                elif dialog.result == "previous":
                    if len(history) > 1:
                        history.pop()
                        i = history.pop()
                        logger.info(f"Moving to previous track: {i + 1}")
                    else:
                        logger.warning("Already at the first track, cannot go back.")
                elif dialog.result == "save":
                    with open(matched_tracks_file, 'w') as f:
                        json.dump(matched_tracks, f)
                elif dialog.result == "save_and_close":
                    with open(matched_tracks_file, 'w') as f:
                        json.dump(matched_tracks, f)
                    return

            with open(matched_tracks_file, 'w') as f:
                json.dump(matched_tracks, f)

        except Exception as e:
            logger.error(f"Error processing playlist '{spotify_playlist_id}': {e}")

    for spotify_playlist_id in spotify_playlist_ids:
        process_playlist(spotify_playlist_id)

    logger.info("Processing complete. Exiting.")
    app.exit()

if __name__ == "__main__":
    main()
