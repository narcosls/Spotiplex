from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QScrollArea, QFormLayout, QDialog, QRadioButton, QButtonGroup
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import requests
from PIL import Image
import io
from utils.spotify_functions import get_playlist_cover, get_auth_token
from utils.dialogs import get_users

class UserSelectionApp(QWidget):
    def __init__(self, cover_url):
        super().__init__()
        self.setWindowTitle("Select Users with Playlist Cover")
        self.setGeometry(100, 100, 600, 800)

        self.users = get_users()  # Retrieve user list
        self.selected_users = []  # Store selected users
        self.cover_url = cover_url  # Store cover URL

        self.initUI()
        self.load_poster(self.cover_url)

    def initUI(self):
        layout = QVBoxLayout()

        # Poster Label
        self.poster_label = QLabel(self)
        self.poster_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.poster_label)

        # User Selection Area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        self.checkboxes = []

        for user in self.users:
            checkbox = QCheckBox(user)
            scroll_layout.addRow(checkbox)
            self.checkboxes.append(checkbox)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Select Button
        self.select_button = QPushButton("Select Users")
        self.select_button.clicked.connect(self.select_users)
        layout.addWidget(self.select_button)

        self.setLayout(layout)
        self.setStyleSheet(self.load_dark_theme())  # Apply custom dark theme

    def load_poster(self, cover_url):
        if cover_url:
            image_data = requests.get(cover_url).content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((400, 400), Image.LANCZOS)
            image_data = io.BytesIO()
            image.save(image_data, format='PNG')
            pixmap = QPixmap()
            pixmap.loadFromData(image_data.getvalue())
            self.poster_label.setPixmap(pixmap)
        else:
            self.poster_label.setText("No cover available")

    def load_dark_theme(self):
        return """
        QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QCheckBox {
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

    def select_users(self):
        self.selected_users = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        self.close()  # Close the window without showing a pop-up

class TrackSelectionDialog(QDialog):
    def __init__(self, spotify_track_info, similar_tracks):
        super().__init__()
        self.setWindowTitle("Select Matching Track")
        self.setGeometry(100, 100, 600, 400)
        self.spotify_track_info = spotify_track_info
        self.similar_tracks = similar_tracks
        self.selected_track = None

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Spotify Track Info
        spotify_info = (
            f"Spotify Track Info:\n"
            f"Artist: {', '.join(self.spotify_track_info['artists'])}\n"
            f"Album: {self.spotify_track_info['album']}\n"
            f"Track: {self.spotify_track_info['name']}\n"
            f"Duration: {self.spotify_track_info['duration']}"
        )
        spotify_label = QLabel(spotify_info)
        layout.addWidget(spotify_label)

        # Track Selection Area
        self.button_group = QButtonGroup(self)

        for idx, track in enumerate(self.similar_tracks):
            track_info = (
                f"Artist: {track.artist().title}, "
                f"Album: {track.album().title}, "
                f"Track: {track.title}, "
                f"Duration: {track.duration}"
            )
            radio_button = QRadioButton(track_info)
            self.button_group.addButton(radio_button, id=idx)
            layout.addWidget(radio_button)

        self.button_group.buttons()[0].setChecked(True)  # Default to first option

        # Select Button
        select_button = QPushButton("Select Track")
        select_button.clicked.connect(self.accept)
        layout.addWidget(select_button)

        self.setLayout(layout)
        self.setStyleSheet(self.load_dark_theme())  # Apply custom dark theme

    def load_dark_theme(self):
        return """
        QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
        QCheckBox {
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

    def accept(self):
        selected_id = self.button_group.checkedId()
        self.selected_track = self.similar_tracks[selected_id]
        super().accept()

    def get_selected_track(self):
        return self.selected_track

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ex = UserSelectionApp("https://example.com/cover.jpg")  # Example cover URL
    ex.show()
    sys.exit(app.exec_())
