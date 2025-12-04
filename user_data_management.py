import sqlalchemy as db
from sqlalchemy import text
import hashlib
#import random
import secrets
engine = db.create_engine("sqlite:///login.sqlite")
#bad= ["SELECT", "DROP","DELETE","INSERT","CREATE","ALTER","GRANT","REVOKE","*","WHERE"]
conn = engine.connect() 

metadata = db.MetaData()

#conn.execute(text("DROP TABLE Usuario"))
Entrada = db.Table('Usuario', metadata,
              db.Column('Email', db.String(255),primary_key=True),
               db.Column('Usuario', db.String(255),nullable=False),
              db.Column('Senha', db.String(255), nullable=False),
               db.Column('Uid', db.String(255),nullable=False),
             
              )


# tabela de Álbuns (para não repetir nome/capa toda hora)
Albuns = db.Table('Albuns', metadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('spotify_id', db.String(50), unique=True, nullable=False), # ID do Spotify
    db.Column('titulo', db.String(150), nullable=False),
    db.Column('artista', db.String(150), nullable=False),
    db.Column('capa_url', db.String(300))
)

# tabela de Avaliações
Avaliacoes = db.Table('Avaliacoes', metadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('nota', db.Integer, nullable=False),
    db.Column('comentario', db.Text, nullable=True),
    # pega a data/hora atual automaticamente
    db.Column('data', db.DateTime, default=db.func.now()), 
    
    # CHAVE ESTRANGEIRA AQUI
    # faz a ligação da avaliação ao Email do usuário (que é a Primary Key na tabela Usuario)
    db.Column('user_email', db.String(255), db.ForeignKey('Usuario.Email'), nullable=False),
    # faz a ligação da avaliação ao ID interno do álbum
    db.Column('album_id', db.Integer, db.ForeignKey('Albuns.id'), nullable=False)
)

metadata.create_all(engine) 

def sha512(inp: str): return(hashlib.sha512(inp.encode()).hexdigest())
"""
def sanitize(inp: str,filter):
    for item in filter:
        inp = inp.removeprefix(item)
        inp = inp.removesuffix(item)
    return inp
"""

def get_user(email):
    getuser = db.select(Entrada).where(Entrada.c.Email == email)
    return(conn.execute(getuser).fetchone())

def login_match(email,senha):
    user_entry = get_user(email)
    if user_entry==None: return 404
    if sha512(senha)!=user_entry[2]: return 403
    return 200



def new_user(email,usuario,senha):
    user_entry = get_user(email)
    print(user_entry)
    if user_entry !=None: return "exists"
    register = db.insert(Entrada).values(Email=email, Usuario=usuario, Senha=sha512(senha),Uid=secrets.token_bytes(20).hex())
    Result = conn.execute(register)
    conn.commit()
    return Result.rowcount



def get_album_id_by_spotify(spotify_id):
    """busca o ID interno do álbum usando o ID do Spotify"""
    query = db.select(Albuns.c.id).where(Albuns.c.spotify_id == spotify_id)
    result = conn.execute(query).fetchone()
    if result:
        return result[0]
    return None

def criar_album_se_nao_existir(spotify_id, titulo, artista, capa_url):
    """
    serifica se o álbum já está no banco. 
    se não estiver, salva ele e retorna o novo ID.
    se já estiver, só retorna o ID existente.
    """
    existing_id = get_album_id_by_spotify(spotify_id)
    if existing_id:
        return existing_id
    
    # se não existe, insere
    ins = db.insert(Albuns).values(
        spotify_id=spotify_id,
        titulo=titulo,
        artista=artista,
        capa_url=capa_url
    )
    result = conn.execute(ins)
    conn.commit()
    return result.inserted_primary_key[0]

def nova_avaliacao(user_email, spotify_id, nome_album, artista_album, capa_album, nota, comentario):
    """
    essa eh a função principal para salvar a avaliação.
    1. garante que o álbum existe no banco.
    2. salva a avaliação linkada ao usuário e ao álbum.
    """
    # etapa 1: pega o ID do álbum (criando se necessário)
    album_db_id = criar_album_se_nao_existir(spotify_id, nome_album, artista_album, capa_album)
    
    # etapa 2: insere a avaliação
    ins = db.insert(Avaliacoes).values(
        user_email=user_email, # Quem avaliou
        album_id=album_db_id,  # Qual álbum (ID interno)
        nota=nota,
        comentario=comentario
    )
    result = conn.execute(ins)
    conn.commit()
    return "Avaliação salva com sucesso!"

def ler_avaliacoes_do_album(spotify_id):
    """isso vai retornar todas as avaliações de um álbum específico"""
    album_id = get_album_id_by_spotify(spotify_id)
    if not album_id:
        return []

    # faz um JOIN para pegar o nome do usuário junto com a avaliação
    query = db.select(Avaliacoes, Entrada.c.Usuario).join(
        Entrada, Avaliacoes.c.user_email == Entrada.c.Email
    ).where(Avaliacoes.c.album_id == album_id)
    
    return conn.execute(query).fetchall()



def ler_avaliacoes_do_usuario(email_usuario):
    """Retorna todas as avaliações de um usuário específico + dados do álbum"""
    
    # Fazemos um JOIN entre Avaliacoes e Albuns
    query = db.select(Avaliacoes, Albuns).join(
        Albuns, Avaliacoes.c.album_id == Albuns.c.id
    ).where(Avaliacoes.c.user_email == email_usuario)
    
    result = conn.execute(query).fetchall()
    return result

# simula um login (precisa de um usuário real no banco)
usuario_atual = "pedro@gmail.com" 

# usuário avalia um álbum (ex: "Chromakopia")
# esses dados virão da API do Spotify no  eko
print("Salvando avaliação...")
resultado = nova_avaliacao(
    user_email=usuario_atual,
    spotify_id="spotify_id_do_chromakopia_123", 
    nome_album="Chromakopia",
    artista_album="Tyler, The Creator",
    capa_album="http://url_da_capa.jpg",
    nota=5,
    comentario="Álbum absurdo, muito bom!"
)
print(resultado)

# 3. lê as avaliações desse álbum
print("Lendo avaliações...")
reviews = ler_avaliacoes_do_album("spotify_id_do_chromakopia_123")
for review in reviews:
    # review é uma tupla. O índice depende da ordem das colunas no select.
    # baseado na query: (id_review, nota, comentario, data, email, id_album, NomeUsuario)
    print(f"Usuário: {review[-1]} | Nota: {review[1]} | Comentário: {review[2]}")