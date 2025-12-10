import sqlalchemy as db
from sqlalchemy import text
import hashlib
import secrets

engine = db.create_engine("sqlite:///login.sqlite")
metadata = db.MetaData()


Entrada = db.Table('Usuario', metadata,
      db.Column('Email', db.String(255), primary_key=True),
      db.Column('Usuario', db.String(255), nullable=False),
      db.Column('Senha', db.String(255), nullable=False),
      db.Column('Uid', db.String(255), nullable=False),
)

Albuns = db.Table('Albuns', metadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('spotify_id', db.String(50), unique=True, nullable=False),
    db.Column('titulo', db.String(150), nullable=False),
    db.Column('artista', db.String(150), nullable=False),
    db.Column('capa_url', db.String(300))
)

Avaliacoes = db.Table('Avaliacoes', metadata,
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('nota', db.Float, nullable=False), 
    db.Column('comentario', db.Text, nullable=True),
    db.Column('data', db.DateTime, server_default=db.func.now()), 
    db.Column('user_email', db.String(255), db.ForeignKey('Usuario.Email'), nullable=False),
    db.Column('album_id', db.Integer, db.ForeignKey('Albuns.id'), nullable=False)
)

metadata.create_all(engine) 



def sha512(inp: str): 
    return hashlib.sha512(inp.encode()).hexdigest()


def get_user(email):
    with engine.connect() as conn:
        query = db.select(Entrada).where(Entrada.c.Email == email)
        return conn.execute(query).fetchone()

def login_match(email, senha):
    user_entry = get_user(email)
    if user_entry is None: return 404
    if sha512(senha) != user_entry.Senha: return 403
    return 200

def new_user(email, usuario, senha):
    if get_user(email) is not None: return "exists"
    
    with engine.connect() as conn:
        register = db.insert(Entrada).values(
            Email=email, 
            Usuario=usuario, 
            Senha=sha512(senha),
            Uid=secrets.token_bytes(20).hex()
        )
        result = conn.execute(register)
        conn.commit()
        return result.rowcount


def get_album_id_by_spotify(spotify_id):
    """Busca o ID interno (número) usando o ID do Spotify (string)"""
    with engine.connect() as conn:
        query = db.select(Albuns.c.id).where(Albuns.c.spotify_id == spotify_id)
        result = conn.execute(query).fetchone()
        if result:
            return result.id
        return None

def criar_album_se_nao_existir(spotify_id, titulo, artista, capa_url):
    existing_id = get_album_id_by_spotify(spotify_id)
    if existing_id:
        return existing_id
    
    with engine.connect() as conn:
        print(f"--- [DB] Criando novo álbum no banco: {titulo} ---")
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
    album_db_id = criar_album_se_nao_existir(spotify_id, nome_album, artista_album, capa_album)
    
    with engine.connect() as conn:
        print(f"--- [DB] Atualizando review de {user_email} para o álbum {album_db_id} ---")
        apagar_velha = db.delete(Avaliacoes).where(
            (Avaliacoes.c.user_email == user_email) & 
            (Avaliacoes.c.album_id == album_db_id)
        )
        conn.execute(apagar_velha)
        
        ins = db.insert(Avaliacoes).values(
            user_email=user_email,
            album_id=album_db_id,
            nota=nota,
            comentario=comentario
        )
        conn.execute(ins)
        conn.commit()
        
    return "Avaliação atualizada com sucesso!"

def ler_avaliacoes_do_album(spotify_id):
    print(f"--- [DB] Buscando reviews para Spotify ID: {spotify_id} ---")
    
    album_id = get_album_id_by_spotify(spotify_id)
    if not album_id:
        print("--- [DB] Álbum ainda não existe no banco (0 reviews) ---")
        return []

    with engine.connect() as conn:
        query = db.select(Avaliacoes, Entrada.c.Usuario).outerjoin(
            Entrada, Avaliacoes.c.user_email == Entrada.c.Email
        ).where(Avaliacoes.c.album_id == album_id)
        
        resultados = conn.execute(query).fetchall()
        
        lista_final = []
        for linha in resultados:
            r_dict = {
                'id': linha.id,
                'nota': linha.nota,
                'comentario': linha.comentario,
                'Usuario': linha.Usuario if linha.Usuario else "Usuário Desconhecido",
                'user_email': linha.user_email 
            }
            lista_final.append(r_dict)

        print(f"--- [DB] Retornando {len(lista_final)} reviews para o site ---")
        return lista_final

def ler_avaliacoes_do_usuario(email_usuario):
    with engine.connect() as conn:
        query = db.select(Avaliacoes, Albuns).join(
            Albuns, Avaliacoes.c.album_id == Albuns.c.id
        ).where(Avaliacoes.c.user_email == email_usuario)
        result = conn.execute(query).fetchall()
        return result

def deletar_review(review_id, user_email):
    with engine.connect() as conn:
        delete_query = db.delete(Avaliacoes).where(
            (Avaliacoes.c.id == review_id) & 
            (Avaliacoes.c.user_email == user_email)
        )
        result = conn.execute(delete_query)
        conn.commit()
        return result.rowcount 