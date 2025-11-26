import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Credenciais do Spotify
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f"CLIENT_ID: {CLIENT_ID}")
print(f"CLIENT_SECRET: {CLIENT_SECRET}")

# Inicializa o cliente do Spotify
sp = None
try:
    auth_manager = SpotifyClientCredentials(
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("✅ Conexão com Spotify bem-sucedida!")
except Exception as e:
    print(f"❌ Erro ao autenticar com o Spotify: {e}")

def buscar_album(nome_album):
    if not sp:
        return {"erro": "Conexão com Spotify não disponível"}
    
    try:
        resultados = sp.search(
            q=f'album:"{nome_album}"', 
            type='album', 
            limit=10
        )
        
        albuns = []
        for item in resultados['albums']['items']:
            album_info = {
                'id': item['id'],
                'nome': item['name'],
                'artista': item['artists'][0]['name'],
                'imagem': item['images'][0]['url'] if item['images'] else None,
                'data_lancamento': item['release_date'],
                'total_musicas': item['total_tracks'],
                'link_spotify': item['external_urls']['spotify']
            }
            albuns.append(album_info)
        
        return albuns
    except Exception as e:
        print(f"Erro ao buscar álbum: {e}")
        return {"erro": str(e)}