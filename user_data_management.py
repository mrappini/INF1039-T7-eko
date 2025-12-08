import sqlalchemy as db
from sqlalchemy import text
import hashlib
import secrets

engine = db.create_engine("sqlite:///login.sqlite")
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
    # o server default garante que o banco preencha a data se o python não fizer auto
    db.Column('data', db.DateTime, server_default=db.func.now()), 
    db.Column('user_email', db.String(255), db.ForeignKey('Usuario.Email'), nullable=False),
    db.Column('album_id', db.Integer, db.ForeignKey('Albuns.id'), nullable=False)
)

metadata.create_all(engine) 

# --- FUNÇÕES AUXILIARES ---

def sha512(inp: str): 
    return hashlib.sha512(inp.encode()).hexdigest()

# --- FUNÇÕES DE USUÁRIO (meu eko e afins) ---

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

# --- FUNÇÕES DE ÁLBUNS E AVALIAÇÕES (aqui é importante tá) ---

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
    #parte 1: garante que o álbum existe e pega o ID dele
    album_db_id = criar_album_se_nao_existir(spotify_id, nome_album, artista_album, capa_album)
    
    with engine.connect() as conn:
        # antes de inserir, deleta qualquer avaliação que tenha O MESMO email E O MESMO álbum, sen uma mesma pessoa fica com varias
        print(f"--- [DB] Removendo review anterior de {user_email} para o álbum {album_db_id} ---")
        apagar_velha = db.delete(Avaliacoes).where(
            (Avaliacoes.c.user_email == user_email) & 
            (Avaliacoes.c.album_id == album_db_id)
        )
        conn.execute(apagar_velha)
        
        # --- PASSO PADRAO: INSERÇÃO ---
        print(f"--- [DB] Salvando Nova Review | Nota: {nota} ---")
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
        # passo 1 debug: imprime TUDO que tem na tabela de avaliações para este álbum (sem filtro de usuário ainda)
        check_query = db.select(Avaliacoes).where(Avaliacoes.c.album_id == album_id)
        check_result = conn.execute(check_query).fetchall()
        print(f"--- [DEBUG] Reviews brutas na tabela para este álbum: {len(check_result)} ---")
        for r in check_result:
            print(f"    -> Review ID: {r.id} | Nota: {r.nota} | Email: {r.user_email}")

        # passo2 a Query Real (sgora usando OUTERJOIN para não esconder reviews se o usuário der erro)
        # se o usuário não for encontrado, o nome virá como None, mas a review aparece.
        query = db.select(Avaliacoes, Entrada.c.Usuario).outerjoin(
            Entrada, Avaliacoes.c.user_email == Entrada.c.Email
        ).where(Avaliacoes.c.album_id == album_id)
        
        resultados = conn.execute(query).fetchall()
        
        # tratamento para caso o usuário venha nulo (evita erro no HTML)
        lista_final = []
        for linha in resultados:
            # linha é uma tupla.tem que garantir que tenha o campo Usuario acessível
            # transformamos em um objeto simples para o template não encher o saco
            r_dict = {
                'id': linha.id,
                'nota': linha.nota,
                'comentario': linha.comentario,
                'Usuario': linha.Usuario if linha.Usuario else "Usuário Desconhecido"
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