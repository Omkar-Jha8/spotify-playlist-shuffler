import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

# ---- Spotify API Credentials ----
CLIENT_ID = "CLIENT ID"
CLIENT_SECRET = "CLIENT SECRET"
REDIRECT_URI = "REDIRECT URL"
SCOPE = "user-read-private playlist-read-private playlist-modify-private playlist-modify-public"

# ---- Spotify Authentication ----
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )
)

# ---- Streamlit Page Config ----
st.set_page_config(page_title="Spotify Playlist Shuffler", page_icon="🎵", layout="wide")

# ---- Custom CSS ----
st.markdown("""
    <style>
        .profile-card {
            display: flex;
            align-items: center;
            gap: 20px;
            background-color: #111;
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            color: white;
        }
        .profile-card img {
            border-radius: 50%;
            width: 80px;
            height: 80px;
        }
        .profile-info h2 {
            margin: 0;
            color: #1DB954;
        }
        .profile-info a {
            text-decoration: none;
            color: #1DB954;
            font-size: 0.9rem;
        }
        .playlist-card {
            margin-top:15px;
            border-radius: 10px;
            background-color: #222;
            padding: 15px;
            text-align: center;
            color: white;
            transition: all 0.3s ease-in-out;
        }
        .playlist-card:hover {
            background-color: #333;
            transform: scale(1.03);
        }
        .playlist-img {
            border-radius: 10px;
            width: 100%;
        }
        .playlist-title {
            font-size: 1.1rem;
            margin-top: 8px;
            font-weight: bold;
        }
        .playlist-link a {
            text-decoration: none;
            color: #1DB954;
            font-size: 0.9rem;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Fetch User Info ----
user_info = sp.current_user()
user_name = user_info.get("display_name", "Spotify User")
user_url = user_info["external_urls"]["spotify"]
user_followers = user_info.get("followers", {}).get("total", 0)
# Default icon if user has no profile image
default_profile_icon = "https://cdn-icons-png.flaticon.com/512/847/847969.png"
user_image = user_info["images"][0]["url"] if user_info.get("images") else default_profile_icon


# ---- User Profile Card ----
st.markdown(f"""
    <div class="profile-card">
        <img src="{user_image}" alt="Profile Picture"/>
        <div class="profile-info">
            <h2>{user_name}</h2>
            <p>{user_followers} Followers</p>
            <p><a href="{user_url}" target="_blank">View Spotify Profile</a></p>
        </div>
    </div>
""", unsafe_allow_html=True)


# ---- Fetch User Playlists ----
playlists = sp.current_user_playlists(limit=20)["items"]

cols = st.columns(4)  # Display playlists in 4 columns
playlist_map = {}

for idx, playlist in enumerate(playlists):
    name = playlist["name"]
    pid = playlist["id"]
    url = playlist["external_urls"]["spotify"]
    image_url = playlist["images"][0]["url"] if playlist["images"] else "https://via.placeholder.com/150"

    with cols[idx % 4]:
        st.markdown(f"""
            <div class="playlist-card">
                <img src="{image_url}" class="playlist-img"/>
                <div class="playlist-title">{name}</div>
                <div class="playlist-link"><a href="{url}" target="_blank">Open in Spotify</a></div>
            </div>
        """, unsafe_allow_html=True)

        playlist_map[name] = pid

# ---- Select Playlist ----
selected_playlist = st.selectbox("Select a playlist to shuffle:", list(playlist_map.keys()))

# ---- Shuffle Button ----
if st.button("Shuffle Selected Playlist"):
    playlist_id = playlist_map[selected_playlist]

    # Fetch all tracks from selected playlist (with pagination)
    all_tracks = []
    results = sp.playlist_items(playlist_id)
    while results:
        for item in results["items"]:
            track = item.get("track")
            if track and track.get("uri") and track["uri"].startswith("spotify:track:"):
                all_tracks.append(track["uri"])
        if results["next"]:
            results = sp.next(results)
        else:
            break

    all_tracks = list(set(all_tracks))
    st.write(f"Fetched {len(all_tracks)} unique tracks.")

    if not all_tracks:
        st.error("No tracks found in this playlist!")
    else:
        random.shuffle(all_tracks)

        user_id = sp.current_user()["id"]
        new_playlist = sp.user_playlist_create(
            user_id, f"Shuffled - {selected_playlist}", public=False
        )
        new_playlist_id = new_playlist["id"]

        for i in range(0, len(all_tracks), 100):
            sp.playlist_add_items(new_playlist_id, all_tracks[i:i + 100])

        st.success(
            f"🎉 Shuffled playlist created: [Open Playlist]({new_playlist['external_urls']['spotify']})"
        )
