import requests
from configparser import ConfigParser
from fuzzywuzzy import fuzz
import logging
from pathlib import Path
from plexapi.server import PlexServer
from helper_classes.playlist import Playlist
from helper_classes.user_inputs import UserInputs
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import json
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QRadioButton, QPushButton, QButtonGroup, QHBoxLayout, QDesktopWidget, QTextBrowser
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import sys
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

MATCH_STORAGE_FILE = "matched_tracks.json"

class TrackSelectionDialog(QDialog):
    def __init__(self, spotify_track_info, similar_tracks):
        super().__init__()
        self.setWindowTitle("Select Matching Track")

        # Get screen size
        screen = QDesktopWidget().screenGeometry()
        screen_width, screen_height = screen.width(), screen.height()

        # Calculate sizes based on screen size
        poster_size = int(min(screen_width, screen_height) * 0.4)  # 40% of the smaller dimension
        window_width, window_height = poster_size + 100, poster_size + 400
        
        self.setWindowTitle("Select Matching Track")
        self.setGeometry(100, 100, window_width, window_height)

        self.spotify_track_info = spotify_track_info
        self.similar_tracks = similar_tracks
        self.selected_track = None
        self.player = None

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        cover_layout = QHBoxLayout()
        spotify_info = (
            f"Spotify Track Info:\n"
            f"Artist: {', '.join(self.spotify_track_info['artists'])}\n"
            f"Album: {self.spotify_track_info['album']}\n"
            f"Track: {self.spotify_track_info['name']}\n"
            f"Duration: {self.spotify_track_info['duration']}"
        )
        spotify_label = QLabel(spotify_info)
        cover_layout.addWidget(spotify_label)

        cover_url = self.spotify_track_info.get('cover_url')
        if cover_url:
            cover_image = self.fetch_cover_image(cover_url)
            cover_label = QLabel()
            cover_label.setPixmap(cover_image)
            cover_layout.addWidget(cover_label)

        layout.addLayout(cover_layout)

        # Play Preview Button
        preview_url = self.spotify_track_info.get('preview_url')
        if preview_url:
            preview_layout = QHBoxLayout()
            play_button = QPushButton("Play Preview")
            play_button.setFont(QFont("Arial", 12))
            play_button.clicked.connect(lambda: self.play_preview(preview_url))
            stop_button = QPushButton("Stop")
            stop_button.setFont(QFont("Arial", 12))
            stop_button.clicked.connect(self.stop_preview)
            preview_layout.addWidget(play_button)
            preview_layout.addWidget(stop_button)
            layout.addLayout(preview_layout)

            self.media_player = QMediaPlayer()

        self.button_group = QButtonGroup(self)

        for idx, track in enumerate(self.similar_tracks):
            track_info = (
                f"Artist: {track.artist().title}, "
                f"Album: {track.album().title}, "
                f"Track: {track.title}, "
                f"Duration: {format_duration(track.duration if hasattr(track, 'duration') else 0)}"
            )
            radio_button = QRadioButton(track_info)
            self.button_group.addButton(radio_button, id=idx)
            layout.addWidget(radio_button)

        self.button_group.buttons()[0].setChecked(True)

        select_button = QPushButton("Select Track")
        select_button.setFont(QFont("Arial", 12))
        select_button.clicked.connect(self.accept)
        layout.addWidget(select_button)

        self.setLayout(layout)
        self.setStyleSheet(self.load_dark_theme())

    def fetch_cover_image(self, url):
        response = requests.get(url)
        image = QPixmap()
        image.loadFromData(response.content)
        return image.scaled(200, 200, Qt.KeepAspectRatio)

    def load_dark_theme(self):
        return """
        QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QRadioButton {
            color: #ffffff;
        }
        QPushButton {
            background-color: #444444;
            color: #ffffff;
            border: none;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QScrollArea {
            background-color: #2e2e2e;
        }
        """

    def play_preview(self, url):
        if self.media_player:
            self.media_player.setMedia(QMediaContent(QUrl(url)))
            self.media_player.play()

    def stop_preview(self):
        if self.media_player:
            self.media_player.stop()

    def accept(self):
        selected_id = self.button_group.checkedId()
        self.selected_track = self.similar_tracks[selected_id]
        if self.player:
            self.player.stop()
        super().accept()

    def get_selected_track(self):
        return self.selected_track

# Utility Functions

def format_duration(ms):
    """Convert milliseconds to hh:mm:ss or mm:ss format."""
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    hours = int((ms / (1000 * 60 * 60)) % 24)
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

def fetch_playlist_tracks(sp, playlist_id):
    """Fetch all tracks from a Spotify playlist, handling pagination."""
    tracks = []
    offset = 0
    limit = 100
    while True:
        results = sp.playlist_tracks(playlist_id, offset=offset, limit=limit)
        tracks.extend(results['items'])
        if results['next'] is None:
            break
        offset += limit
    return tracks

def fetch_playlist_info(spotify_client_id, spotify_client_secret, spotify_playlist_id):
    """Fetch playlist information from Spotify."""
    client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
    sp = Spotify(client_credentials_manager=client_credentials_manager)
    playlist = sp.playlist(spotify_playlist_id)
    name = playlist['name']
    description = playlist['description']
    poster = playlist['images'][0]['url'] if playlist['images'] else ""
    return {'name': name, 'description': description, 'poster': poster}

def load_matched_tracks(storage_file):
    """Load matched tracks from the storage file."""
    if Path(storage_file).exists():
        with open(storage_file, 'r') as f:
            return json.load(f)
    return {}

def save_matched_tracks(storage_file, matched_tracks):
    """Save matched tracks to the storage file."""
    with open(storage_file, 'w') as f:
        json.dump(matched_tracks, f, indent=4)

def fuzzy_match(spotify_track_info, plex_tracks, threshold=80):
    """Perform fuzzy matching of track names, artists, and albums."""
    best_match = None
    highest_score = 0

    for plex_track in plex_tracks:
        track_name_ratio = fuzz.ratio(spotify_track_info['name'], plex_track.title)
        artist_name_ratio = fuzz.ratio(spotify_track_info['artists'][0], plex_track.artist().title)
        album_name_ratio = fuzz.ratio(spotify_track_info['album'], plex_track.album().title)
        
        combined_score = (track_name_ratio + artist_name_ratio + album_name_ratio) / 3
        
        if combined_score > highest_score and combined_score > threshold:
            highest_score = combined_score
            best_match = plex_track
    
    if not best_match and plex_tracks:
        app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)
        dialog = TrackSelectionDialog(spotify_track_info, plex_tracks)
        if dialog.exec_() == QDialog.Accepted:
            best_match = dialog.get_selected_track()

    return best_match

def fetch_item_with_timeout(plex, rating_key, timeout=10):
    """Fetch Plex item with a timeout to avoid indefinite hangs."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(plex.fetchItem, rating_key)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logging.error(f"Fetching item with key {rating_key} timed out.")
            return None

def get_auth_token(user):
    """
    Get the Spotify auth token for a specific user from the config file.
    """
    config = ConfigParser()
    config.read('config.txt')
    users_tokens = config['users']['tokens'].split(',')
    for user_token in users_tokens:
        u, token = user_token.split(':')
        if u == user:
            return token
    return None

def sync_spotify_playlist_with_plex(plex: PlexServer, playlist: Playlist, userInputs: UserInputs, spotify_playlist_id: str, output_dir: Path):
    logging.info(f"Starting sync for playlist ID: {spotify_playlist_id}")
    client_credentials_manager = SpotifyClientCredentials(client_id=userInputs.spotify_client_id, client_secret=userInputs.spotify_client_secret)
    sp = Spotify(client_credentials_manager=client_credentials_manager)
    spotify_tracks = fetch_playlist_tracks(sp, spotify_playlist_id)
    matched_tracks = []
    matched_plex_tracks = []
    unmatched_tracks = []
    total_tracks = len(spotify_tracks)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    playlist_output_dir = output_dir / f"{playlist.name}_{timestamp}"
    playlist_output_dir.mkdir(parents=True, exist_ok=True)

    matched_track_ids = load_matched_tracks(MATCH_STORAGE_FILE)

    app = None
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    for idx, item in enumerate(spotify_tracks):
        track = item['track']
        spotify_track_info = {
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'preview_url': track.get('preview_url'),
            'explicit': track.get('explicit'),
            'type': track.get('type'),
            'episode': track.get('episode'),
            'track': track.get('track'),
            'disc_number': track.get('disc_number'),
            'track_number': track.get('track_number'),
            'duration': format_duration(track.get('duration_ms', 0)),
            'duration_ms': track.get('duration_ms', 0),
            'external_ids': track.get('external_ids'),
            'external_urls': track.get('external_urls'),
            'href': track.get('href'),
            'id': track.get('id'),
            'popularity': track.get('popularity'),
            'uri': track.get('uri'),
            'is_local': track.get('is_local'),
            'cover_url': track['album']['images'][0]['url'] if track['album']['images'] else None
        }
        logging.info(f"{idx + 1}/{total_tracks} Matching Spotify track '{spotify_track_info['name']}'...")

        if spotify_track_info['id'] in matched_track_ids:
            matched_key = matched_track_ids[spotify_track_info['id']]
            logging.info(f"Fetching previously matched track with key {matched_key}...")
            try:
                matched_track = plex.fetchItem(matched_key)
            except Exception as e:
                logging.error(f"Error fetching previously matched track with key {matched_key}: {e}")
                matched_track = None

            if matched_track:
                logging.info(f"Found previously matched track for '{spotify_track_info['name']}' by '{spotify_track_info['artists'][0]}'.")
                matched_plex_tracks.append(matched_track)
                continue
            else:
                logging.error(f"Failed to fetch previously matched track for '{spotify_track_info['name']}' by '{spotify_track_info['artists'][0]}'.")

        logging.info(f"Searching Plex tracks for '{spotify_track_info['name']}' by '{spotify_track_info['artists'][0]}'...")
        plex_tracks = plex.library.search(title=spotify_track_info['name'], libtype='track')
        filtered_plex_tracks = [track for track in plex_tracks if fuzz.ratio(track.artist().title, spotify_track_info['artists'][0]) > 80]

        logging.info(f"Found {len(filtered_plex_tracks)} potential matches for '{spotify_track_info['name']}'.")

        matched_track = fuzzy_match(spotify_track_info, filtered_plex_tracks)
        if not matched_track and filtered_plex_tracks:
            dialog = TrackSelectionDialog(spotify_track_info, filtered_plex_tracks)
            if dialog.exec_() == QDialog.Accepted:
                matched_track = dialog.get_selected_track()
        if matched_track:
            plex_track_info = {
                'title': matched_track.title,
                'artist': matched_track.artist().title,
                'album': matched_track.album().title,
                'duration': format_duration(matched_track.duration if hasattr(matched_track, 'duration') else 0),
                'audio_channels': matched_track.media[0].audioChannels if hasattr(matched_track, 'media') and matched_track.media else None,
                'location': matched_track.media[0].parts[0].file if matched_track.media and matched_track.media[0].parts else None,
                'disc_number': getattr(matched_track.media[0].parts[0], 'disc', None) if matched_track.media and matched_track.media[0].parts else None,
                'track_number': matched_track.index if hasattr(matched_track, 'index') else None
            }
            matched_tracks.append({
                'spotify_track': spotify_track_info,
                'plex_track': plex_track_info
            })
            matched_plex_tracks.append(matched_track)
            matched_track_ids[spotify_track_info['id']] = matched_track.ratingKey
            logging.info(f"Matched '{spotify_track_info['name']}' by {' & '.join(spotify_track_info['artists'])}.")
        else:
            unmatched_tracks.append({
                'spotify_track': spotify_track_info,
                'plex_track': None
            })
            logging.info(f"Could not match '{spotify_track_info['name']}' by {' & '.join(spotify_track_info['artists'])}.")

    save_matched_tracks(MATCH_STORAGE_FILE, matched_track_ids)

    combined_tracks_json = {
        'Match': matched_tracks,
        'Unmatched': unmatched_tracks
    }
    with open(playlist_output_dir / f'{playlist.name}_combined.json', 'w') as f:
        json.dump(combined_tracks_json, f, indent=4)
    logging.info(f"Creating or updating Plex playlist: {playlist.name}")
    try:
        existing_playlist = plex.playlist(playlist.name)
        logging.info(f"Found existing playlist: {playlist.name}")
    except Exception as e:
        existing_playlist = None
        logging.info(f"No existing playlist found, creating a new one: {playlist.name}. Exception: {e}")
    if existing_playlist:
        existing_playlist.removeItems(existing_playlist.items())
        existing_playlist.addItems(matched_plex_tracks)
        logging.info(f"Updated existing playlist: {playlist.name}")
    else:
        existing_playlist = plex.createPlaylist(playlist.name, items=matched_plex_tracks)
        logging.info(f"Created new playlist: {playlist.name}")

    logging.info(f"Updating playlist description and poster for: {playlist.name}")
    if playlist.description:
        existing_playlist.editSummary(summary=playlist.description)
    if playlist.poster:
        existing_playlist.uploadPoster(url=playlist.poster)
    logging.info(f"Finished syncing Spotify playlist '{playlist.name}' with Plex.")
    
    if app:
        app.quit()

def get_playlist_cover(user):
    """
    Get the cover image URL of the playlist for the given user.
    """
    config = ConfigParser()
    config.read('config.txt')
    spotify_client_id = config['spotify']['client_id']
    spotify_client_secret = config['spotify']['client_secret']
    playlist_id = config['playlists']['playlist_ids'].split(',')[0]
    token = get_auth_token(user)

    if not token:
        logging.error(f"No token found for user {user}")
        return None

    client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
    sp = Spotify(client_credentials_manager=client_credentials_manager)
    try:
        playlist = sp.playlist(playlist_id)
        return playlist['images'][0]['url'] if playlist['images'] else None
    except Exception as e:
        logging.error(f"Error fetching playlist cover for user {user}: {e}")
        return None

def get_auth_token(user):
    """
    Get the Spotify auth token for a specific user from the config file.
    """
    config = ConfigParser()
    config.read('config.txt')
    users_tokens = config['users']['tokens'].split(',')
    for user_token in users_tokens:
        u, token = user_token.split(':')
        if u == user:
            return token
    return None
