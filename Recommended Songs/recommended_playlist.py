import requests
from flask import Flask, request, redirect

app = Flask(__name__)

# Spotify API credentials - Replace with your actual credentials
client_id = '6f874a900546415eac4d8610c53a52b9'  # Add your Client ID here
client_secret = 'd32519313bb34fd1859a32c2c355f8da'  # Add your Client Secret here
redirect_uri = 'http://localhost:8000/callback'  # Replace with your redirect URI

# Route to redirect user to Spotify for authorization
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login')
def login():
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=user-top-read,playlist-modify-private"
    return redirect(auth_url)

# Callback route to handle the redirect with authorization code
@app.route('/callback')
def callback():
    code = request.args.get('code')
    token = get_access_token(code)

    if not token:
        return "Error retrieving access token", 400

    # Get top tracks
    top_tracks = get_top_tracks(token)
    top_track_ids = [track['id'] for track in top_tracks]

    # Get recommendations based on top tracks
    recommended_tracks = get_recommendations(token, top_track_ids)
    recommended_track_uris = [track['uri'] for track in recommended_tracks]

    # Create a playlist with recommended songs
    created_playlist = create_playlist(token, recommended_track_uris)
    if created_playlist:
        playlist_link = f"https://open.spotify.com/playlist/{created_playlist['id']}"
        cover_image_url = created_playlist['images'][0]['url'] if created_playlist['images'] else None  # Get the cover image URL
        playlist_id = created_playlist['id']  # Get the playlist ID for embedding

        return f"""
        <html>
            <head>
                <style>
                    body {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        flex-direction: column; /* Center content vertically */
                        height: 100vh;
                        margin: 0;
                        font-family: 'Poppins', sans-serif;
                    }}
                    .container {{
                        text-align: center;
                    }}
                    img {{
                        max-width: 300px; /* Limit the width of the image */
                        border-radius: 15px; /* Rounded corners for image */
                        margin-bottom: 20px; /* Space between image and iframe */
                    }}
                    iframe {{
                        width: 100%; /* Full width */
                        height: 380px; /* Height for the embedded player */
                        border: none; /* No border */
                        border-radius: 10px; /* Rounded corners for iframe */
                        margin-top: 20px; /* Space above the iframe */
                    }}
                    button {{
                        padding: 15px 30px; /* Increased padding */
                        font-size: 18px; /* Increased font size */
                        background-color: #1DB954; /* Spotify green */
                        color: white; /* Text color */
                        border: none; /* Remove border */
                        border-radius: 15px; /* Rounded corners */
                        cursor: pointer; /* Pointer cursor on hover */
                        transition: background-color 0.3s; /* Smooth transition */
                        margin-top: 20px; /* Space between button and iframe */
                    }}
                    button:hover {{
                        background-color: #1ed760; /* Darker green on hover */
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    {f'<img src="{cover_image_url}" alt="Playlist Cover" />' if cover_image_url else ''}
                    <h1>Playlist created!</h1>
                    <iframe
                        title="Spotify Embed: Recommendation Playlist"
                        src="https://open.spotify.com/embed/playlist/{playlist_id}?utm_source=generator&theme=0"
                        allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                        loading="lazy"
                    ></iframe>
                    <a href="{playlist_link}" target="_blank">
                        <button>Open Playlist</button>
                    </a>
                </div>
            </body>
        </html>
    """

    else:
        return "Error creating playlist", 400

def get_access_token(code):
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get('access_token')

def fetch_web_api(endpoint, token, method='GET', body=None):
    url = f'https://api.spotify.com/{endpoint}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=body)
    return response.json()

def get_top_tracks(token):
    endpoint = 'v1/me/top/tracks?time_range=long_term&limit=5'
    return fetch_web_api(endpoint, token).get('items', [])

def get_recommendations(token, top_track_ids):
    endpoint = f'v1/recommendations?limit=20&seed_tracks={",".join(top_track_ids)}'
    return fetch_web_api(endpoint, token).get('tracks', [])

def create_playlist(token, tracks_uris):
    user_id = fetch_web_api('v1/me', token).get('id')
    playlist_data = {
        'name': 'Songs for you',
        'description': 'Playlist created by the tutorial on developer.spotify.com',
        'public': False
    }
    playlist = fetch_web_api(f'v1/users/{user_id}/playlists', token, 'POST', playlist_data)

    if 'id' not in playlist:
        print("Error creating playlist:", playlist)  # Print error details
        return None

    playlist_id = playlist['id']

    # Add only recommended tracks to the playlist
    fetch_web_api(f'v1/playlists/{playlist_id}/tracks?uris={",".join(tracks_uris)}', token, 'POST')

    return playlist

# Run the Flask app
if __name__ == '__main__':
    app.run(port=8000)
