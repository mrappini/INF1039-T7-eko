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

def buscar_album_por_id(album_id):
    if not sp:
        return {"erro": "Conexão com Spotify não disponível"}

    try:
        
        album_raw = sp.album(album_id)
        
        album_info = {
            "id": album_raw["id"],
            "nome": album_raw["name"],
            "artista": album_raw["artists"][0]["name"],
            "ano": album_raw["release_date"][:4],
            "data_lancamento": album_raw["release_date"],
            "generos": album_raw.get("genres", []),
            "imagem": album_raw["images"][0]["url"] if album_raw["images"] else None,
            "total_musicas": album_raw["total_tracks"],
            "link_spotify": album_raw["external_urls"]["spotify"],
            "label": album_raw.get('label', '')
        }
        
        faixas = []
        
        for item in album_raw['tracks']['items']:
            faixa = {
                'numero': item['track_number'],
                'nome': item['name'],
                'id': item['id'],
                'duracao_ms': item['duration_ms'],
                'preview_url': item['preview_url'],
                'link_spotify': item['external_urls']['spotify']
            }
            faixas.append(faixa)  
            
        return album_info,faixas    

    except Exception as e:
        print(f"Erro ao buscar álbum por ID: {e}")
        return {"erro": str(e)}
