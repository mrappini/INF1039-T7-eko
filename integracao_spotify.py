import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# CONFIGURAÇÃO DO SPOTIFY
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID', 'SUA_CLIENT_ID_AQUI')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET', 'SUA_CLIENT_SECRET_AQUI')

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def buscar_album(termo_busca):
    """
    Busca Híbrida: Realiza duas buscas separadas (por artista e por nome) 
    e combina os resultados para garantir que nada fique de fora.
    """
    if not termo_busca:
        return []

    lista_final = []
    ids_processados = set() # usado para evitar álbuns duplicados

    try:
        
        # primeiro, buscamos como se fosse um ARTISTA (Ex: Stevie Wonder)
        resultados_artista = sp.search(q=f'artist:"{termo_busca}"', type='album', limit=50, market='BR')
        
        # depois, buscamos como se fosse um NOME DE ÁLBUM (Ex: Thriller)
        # usamos o termo puro aqui para pegar qualquer match de texto
        resultados_nome = sp.search(q=termo_busca, type='album', limit=20, market='BR')

        def processar_resultados(items):
            for item in items:
                if not item: continue
                
                if item['id'] in ids_processados:
                    continue
                
                try:
                    # tenta pegar imagem, se não tiver usa None
                    imagem_url = item['images'][0]['url'] if item['images'] else None
                    
                    # pega apenas o ano da data (YYYY)
                    data_lancamento = item.get('release_date', '')[:4] if item.get('release_date') else 'N/A'

                    album_data = {
                        'nome': item['name'],
                        'artista': item['artists'][0]['name'],
                        'imagem': imagem_url,
                        'id': item['id'],
                        'data_lancamento': data_lancamento,
                        'total_musicas': item['total_tracks'],
                        'link_spotify': item['external_urls']['spotify']
                    }
                    
                    lista_final.append(album_data)
                    ids_processados.add(item['id'])
                    
                except Exception as e:
                    continue

        # processa primeiro os resultados de ARTISTA (prioridade)
        if 'albums' in resultados_artista:
            processar_resultados(resultados_artista['albums']['items'])
            
        # processa depois os resultados de NOME
        if 'albums' in resultados_nome:
            processar_resultados(resultados_nome['albums']['items'])

    except Exception as e:
        print(f"Erro na busca: {e}")
        return []
            
    return lista_final

def buscar_album_por_id(album_id):
    """
    Busca detalhes de um álbum específico pelo ID.
    """
    try:
        album_data = sp.album(album_id)
        tracks_data = sp.album_tracks(album_id)
        
        album_info = {
            'nome': album_data['name'],
            'artista': album_data['artists'][0]['name'],
            'imagem': album_data['images'][0]['url'] if album_data['images'] else None,
            'data_lancamento': album_data['release_date'][:4],
            'total_musicas': album_data['total_tracks'],
            'link_spotify': album_data['external_urls']['spotify'],
            'id': album_data['id']
        }
        
        tracks_info = []
        for track in tracks_data['items']:
            tracks_info.append({
                'nome': track['name'],
                'duracao_ms': track['duration_ms'],
                'numero': track['track_number'],
                'preview_url': track['preview_url']
            })
            
        return album_info, tracks_info
    except Exception as e:
        print(f"Erro ao buscar álbum por ID: {e}")
        return None, None