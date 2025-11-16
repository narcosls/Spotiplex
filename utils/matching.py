from .similarity import calculate_similarity, calculate_duration_similarity
from .normalization import normalize_name

def filter_and_sort_tracks(plex_tracks, spotify_track_info):
    """Filter and sort Plex tracks based on similarity to Spotify track info."""
    spotify_track = spotify_track_info['name']
    spotify_artist = spotify_track_info['artists'][0]
    spotify_album = spotify_track_info['album']
    spotify_duration = spotify_track_info.get('duration_ms')

    scored_tracks = []

    for plex_track in plex_tracks:
        similarity = calculate_similarity(plex_track, spotify_track, spotify_artist, spotify_album)
        if spotify_duration:
            duration_similarity = calculate_duration_similarity(plex_track.duration, spotify_duration)
            similarity = (similarity * 0.8) + (duration_similarity * 0.2)
        
        scored_tracks.append((plex_track, similarity))
    
    # Filter out tracks where artist does not match
    scored_tracks = [track for track in scored_tracks if normalize_name(track[0].artist().title) == normalize_name(spotify_artist)]
    
    # Sort tracks by similarity score in descending order and limit to top 10
    scored_tracks.sort(key=lambda x: x[1], reverse=True)
    return [track[0] for track in scored_tracks[:10]]

def match_track(plex_tracks, spotify_track_info):
    """Match a Spotify track with Plex tracks using a hierarchical matching strategy."""
    filtered_tracks = filter_and_sort_tracks(plex_tracks, spotify_track_info)
    return filtered_tracks[0] if filtered_tracks else None
