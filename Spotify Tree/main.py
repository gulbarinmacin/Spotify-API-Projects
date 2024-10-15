from flask import Flask, request, redirect, url_for, session
import os
import requests
import base64
import json
from dotenv import load_dotenv
# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API bilgileri
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {
                    background-color: pink;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: 'Poppins', sans-serif;
                }
                div {
                    text-align: center;
                }
                h1 {
                    color: white;
                    font-weight: bold;
                    margin: 20px 0;
                    font-size: 50px;
                    opacity: 0;
                    transform: translateY(-50px);
                    animation: drop 0.5s forwards;
                }
                @keyframes drop {
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .spotify-link {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background-color: #1DB954;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 25px;
                    text-decoration: none;
                    transition: background-color 0.3s;
                    font-size: 18px;
                }
                .spotify-link:hover {
                    background-color: #1aa34a;
                }
                .logo {
                    width: 25px;
                    margin-right: 10px;
                }
            </style>
        </head>
        <body>
            <div>
                <h1>Spotify Ağacı</h1>
                <a class="spotify-link" href="/login">
                    <img class="logo" src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" alt="Spotify Logo"> 
                    Spotify'a Bağlan
                </a>
            </div>
        </body>
    </html>
    '''


@app.route('/login')
def login():
    scope = "user-top-read"
    auth_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token = get_access_token(code)
    session['access_token'] = token
    return redirect(url_for('top_tracks'))

def get_access_token(code):
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        return None

@app.route('/top_tracks')
def top_tracks():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "limit": 45,
        "time_range": "medium_term"
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        top_tracks = response.json()["items"]
        track_list = '''
        <html>
            <head>
                <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap" rel="stylesheet">
                <style>
                    body {
                        background-color: pink;
                        color: white;
                        font-weight: bold;
                        margin: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        flex-direction: column;
                        min-height: 100vh;
                        font-family: 'Poppins', sans-serif;
                        padding: 20px;
                    }
                    h1 {
                        margin-bottom: 20px;
                    }
                    .tree {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }
                    .row {
                        display: flex;
                        justify-content: center;
                    }
                    img {
                        width: 40px;
                        height: 40px;
                        display: block;
                    }
                    .trunk {
                        background-color: SaddleBrown;
                        width: 40px;
                        height: 100px;
                    }
                    button {
                        margin-top: 20px;
                        padding: 10px 20px;
                        font-size: 16px;
                        border: none;  /* Kenar çerçevesini kaldır */
                        border-radius: 20px;  /* Yuvarlak köşeler */
                        background-color: #1DB954;  /* Buton rengi (yeşil) */
                        color: white;  /* Yazı rengi */
                        font-family: 'Poppins', sans-serif;  /* Yazı fontu */
                        cursor: pointer;  /* Fare ile üzerine gelince imleç değişimi */
                        transition: background-color 0.3s;  /* Geçiş efekti */
                    }
                    button:hover {
                        background-color: #45a049;  /* Fareyle üzerine gelindiğinde rengi değişir */
                    }
                </style>
            </head>
            <body>
                <h1>Spotify Ağacın</h1>
                <div class="tree" id="trackImages">
        '''

        rows = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        track_index = 0
        for row_size in rows:
            track_list += '<div class="row">'
            for _ in range(row_size):
                if track_index < len(top_tracks):
                    image_url = top_tracks[track_index]['album']['images'][0]['url']
                    track_list += f'<img src="{image_url}" alt="Track Image">'
                    track_index += 1
            track_list += '</div>'

        track_list += '''
                </div>
                <div class="trunk"></div>
                <button id="downloadBtn">Ağacını İndir</button>
                <canvas id="canvas" style="display: none;"></canvas>
                <script>
                    document.getElementById("downloadBtn").onclick = function() {
                        const canvas = document.getElementById("canvas");
                        const ctx = canvas.getContext("2d");
                        const treeElement = document.getElementById("trackImages");
                        const images = treeElement.querySelectorAll("img");
                        const imageSize = 40;
                        const rows = [1, 2, 3, 4, 5, 6, 7, 8, 9];
                        
                        const paddingTop = 50;  // Üst boşluk
                        const paddingBottom = 100;  // Alt boşluk
                        const trunkHeight = 100;  // Gövde yüksekliği
                        const width = rows[rows.length - 1] * imageSize;  // Canvas genişliği
                        const height = rows.length * imageSize + trunkHeight + paddingTop + paddingBottom;  // Canvas yüksekliği

                        canvas.width = width + 40;  // Kenarlarda ekstra alan
                        canvas.height = height;
                        ctx.fillStyle = "pink";  // Arka plan rengi
                        ctx.fillRect(0, 0, width + 40, height);

                        let currentIndex = 0;

                        function drawNextImage() {
                            if (currentIndex >= images.length) {
                                // Gövdeyi çiz
                                ctx.fillStyle = "SaddleBrown";
                                const trunkX = (width - 40) / 2 + 20;  // Gövdeyi ortala ve boşlukları hesaba kat
                                const trunkY = rows.length * imageSize + paddingTop;  // Gövdeyi resimlerin altına yerleştir
                                ctx.fillRect(trunkX, trunkY, 40, trunkHeight);  // Gövdeyi çiz

                                const link = document.createElement("a");
                                link.download = "top_tracks_tree.png";
                                link.href = canvas.toDataURL();
                                link.click();
                                return;
                            }

                            const image = new Image();
                            image.src = images[currentIndex].src;
                            image.crossOrigin = "anonymous";
                            image.onload = function() {
                                let rowIndex = 0;
                                let positionInRow = 0;
                                let countInPreviousRows = 0;
                                while (countInPreviousRows + rows[rowIndex] <= currentIndex) {
                                    countInPreviousRows += rows[rowIndex];
                                    rowIndex++;
                                }
                                positionInRow = currentIndex - countInPreviousRows;

                                const x = (width - rows[rowIndex] * imageSize) / 2 + positionInRow * imageSize + 20;  // Boşluk için kenarlardan 20px ekledim
                                const y = rowIndex * imageSize + paddingTop;  // Resimleri paddingTop kadar aşağı kaydırın

                                ctx.drawImage(image, x, y, imageSize, imageSize);
                                currentIndex++;
                                drawNextImage();
                            };
                            image.onerror = function() {
                                currentIndex++;
                                drawNextImage();
                            };
                        }

                        drawNextImage();
                    };
                </script>
            </body>
        </html>
        '''
        return track_list
    else:
        return "Şarkılar alınırken bir hata oluştu."


if __name__ == '__main__':
    app.run(port=8000)
