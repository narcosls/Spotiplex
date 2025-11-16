from fuzzywuzzy import fuzz
from .normalization import normalize_name

def calculate_similarity(plex_track, spotify_track, spotify_artist, spotify_album):
    """Calculate similarity score based on artist, album, and track names."""
    plex_artist = normalize_name(plex_track.artist().title)
    plex_album = normalize_name(plex_track.album().title)
    plex_title = normalize_name(plex_track.title)

    spotify_artist = normalize_name(spotify_artist)
    spotify_album = normalize_name(spotify_album)
    spotify_title = normalize_name(spotify_track)

    artist_similarity = fuzz.token_sort_ratio(plex_artist, spotify_artist)
    album_similarity = fuzz.token_sort_ratio(plex_album, spotify_album)
    track_similarity = fuzz.token_sort_ratio(plex_title, spotify_title)

    partial_artist_similarity = fuzz.partial_ratio(plex_artist, spotify_artist)
    partial_album_similarity = fuzz.partial_ratio(plex_album, spotify_album)
    partial_track_similarity = fuzz.partial_ratio(plex_title, spotify_title)

    overall_similarity = (artist_similarity * 0.3 + partial_artist_similarity * 0.2 +
                          album_similarity * 0.2 + partial_album_similarity * 0.1 +
                          track_similarity * 0.2 + partial_track_similarity * 0.1)

    return overall_similarity

def calculate_duration_similarity(plex_duration, spotify_duration):
    """Calculate similarity score based on track duration."""
    if not plex_duration or not spotify_duration:
        return 0
    duration_difference = abs(plex_duration - spotify_duration)
    max_duration = max(plex_duration, spotify_duration)
    duration_similarity = 100 - (duration_difference / max_duration * 100)
    return max(duration_similarity, 0)
