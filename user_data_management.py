import sqlalchemy as db
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError  # Importado para evitar o erro 500 em emails repetidos
import hashlib
import secrets
import os 

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---

def get_engine():
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Correção obrigatória para SQLAlchemy no Render/Neon
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # FIX: pool_pre_ping testa a conexão antes de usar (resolve o erro de SSL)
        # pool_recycle renova a conexão a cada 5 min
        return db.create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300
        )
    else:
        # Uso local
        return db.create_engine("sqlite:///login.sqlite")

engine = get_engine()
metadata = db.MetaData()

# --- DEFINIÇÃO DAS TABELAS ---

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

# --- FUNÇÕES DE LÓGICA ---

def sha512(inp: str): 
    return hashlib.sha512(inp.encode()).hexdigest()

def get_user(email):
    # Normalizamos o email para evitar erros de case-sensitive no Postgres
    email_limpo = email.lower()
    with engine.connect() as conn:
        query = db.select(Entrada).where(Entrada.c.Email == email_limpo)
        return conn.execute(query).fetchone()

def login_match(email, senha):
    user_entry = get_user(email)
    if user_entry is None: return 404
    if sha512(senha) != user_entry.Senha: return 403
    return 200

def new_user(email, usuario, senha):
    email_limpo = email.lower()
    if get_user(email_limpo) is not None: return "exists"
    
    try:
        with engine.connect() as conn:
            register = db.insert(Entrada).values(
                Email=email_limpo, 
                Usuario=usuario, 
                Senha=sha512(senha),
                Uid=secrets.token_bytes(20).hex()
            )
            result = conn.execute(register)
            conn.commit()
            return result.rowcount
    except IntegrityError:
        # Se o banco barrar por email duplicado, retornamos exists sem quebrar o site
        return "exists"

def get_album_id_by_spotify(spotify_id):
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
    user_email_limpo = user_email.lower()
    
    with engine.connect() as conn:
        # Apaga a avaliação antiga do mesmo usuário para o mesmo álbum
        apagar_velha = db.delete(Avaliacoes).where(
            (Avaliacoes.c.user_email == user_email_limpo) & 
            (Avaliacoes.c.album_id == album_db_id)
        )
        conn.execute(apagar_velha)
        
        ins = db.insert(Avaliacoes).values(
            user_email=user_email_limpo,
            album_id=album_db_id,
            nota=nota,
            comentario=comentario
        )
        conn.execute(ins)
        conn.commit()
        
    return "Avaliação atualizada com sucesso!"

def ler_avaliacoes_do_album(spotify_id):
    album_id = get_album_id_by_spotify(spotify_id)
    if not album_id:
        return []

    with engine.connect() as conn:
        query = db.select(
            Avaliacoes.c.id, 
            Avaliacoes.c.nota, 
            Avaliacoes.c.comentario, 
            Avaliacoes.c.user_email,
            Entrada.c.Usuario
        ).outerjoin(
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
        return lista_final

def ler_avaliacoes_do_usuario(email_usuario):
    email_limpo = email_usuario.lower()
    with engine.connect() as conn:
        query = db.select(Avaliacoes, Albuns).join(
            Albuns, Avaliacoes.c.album_id == Albuns.c.id
        ).where(Avaliacoes.c.user_email == email_limpo)
        result = conn.execute(query).fetchall()
        return result

def deletar_review(review_id, user_email):
    email_limpo = user_email.lower()
    with engine.connect() as conn:
        delete_query = db.delete(Avaliacoes).where(
            (Avaliacoes.c.id == review_id) & 
            (Avaliacoes.c.user_email == email_limpo)
        )
        result = conn.execute(delete_query)
        conn.commit()
        return result.rowcount