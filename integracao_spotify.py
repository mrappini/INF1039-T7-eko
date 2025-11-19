import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

# carrega o env
load_dotenv()


# credenciais do spotify
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Conexão com Spotify bem-sucedida!")
except Exception as e:
    print(f"Erro ao autenticar com o Spotify: {e}")
    sp = None
    
    
    
#as funcoes q serao usadas pelo eko

def buscar_album(nome_do_album):
    
    if not sp:
        return None # falha na autenticação
        
    try:
        resultados = sp.search(q=f'album:{nome_do_album}', type='album', limit=1)
        
        if resultados['albums']['items']:
            album = resultados['albums']['items'][0]
            
            
            dados_do_album = {
                'nome': album['name'],
                'artista': album['artists'][0]['name'], 
                'ano_lancamento': album['release_date'].split('-')[0],
                'capa_url': album['images'][0]['url'], 
                'spotify_id': album['id']
            }
            return dados_do_album
            
        return None
        
    except Exception as e:
        print(f"Erro ao buscar álbum: {e}")
        return None

############################################################

if __name__ == '__main__':
    print("Testando busca...")
    album_teste = buscar_album("ok computer")
    if album_teste:
        print("Álbum encontrado:")
        print(album_teste)
    else:
        print("Álbum não encontrado.")