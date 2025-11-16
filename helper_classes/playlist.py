class Playlist:
    def __init__(self, name, description="", poster="", id=None):
        self.name = name
        self.description = description
        self.poster = poster
        self.id = id  # Initialize id if provided
