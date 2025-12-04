from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from integracao_spotify import buscar_album, buscar_album_por_id
import user_data_management as db # Apelidei seu arquivo de banco para 'db'

app = Flask(__name__)

# Configuração da Sessão (Obrigatório para login funcionar)
app.secret_key = "chave_super_secreta_do_eko" 

# # ------------- rotas aqui -------------

# # --- MODO DESENVOLVEDOR: AUTO-LOGIN ---
# # Defina aqui o email que você quer usar para testes
# USUARIO_TESTE_EMAIL = "seu_email_real_do_banco@gmail.com" 
# USUARIO_TESTE_NOME = "Dev Mode"

# @app.before_request
# def auto_login_teste():
#     """
#     Se estiver rodando em modo debug (local) e não tiver ninguém logado,
#     força o login do usuário de teste.
#     """
#     if app.debug: # Só roda se o debug=True (que é o padrão quando vc roda local)
#         if 'usuario_email' not in session:
#             print(f"--- [DEV] Logando automaticamente como {USUARIO_TESTE_NOME} ---")
#             session['usuario_email'] = USUARIO_TESTE_EMAIL
#             session['usuario_nome'] = USUARIO_TESTE_NOME
# # ---------------------------------------

@app.route('/')
def homepage():
    # Se o usuário estiver logado, passamos o nome dele para o template
    usuario_logado = session.get('usuario_nome')
    return render_template('homepage.html', usuario=usuario_logado)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email_login') # O 'name' no HTML deve ser email_login
        senha = request.form.get('senha_login') # O 'name' no HTML deve ser senha_login
        
        # Chama a função do seu arquivo de banco
        status = db.login_match(email, senha)
        
        if status == 200:
            # Pega os dados do usuário para salvar na sessão
            dados_user = db.get_user(email)
            # dados_user[0] = email, dados_user[1] = nome
            session['usuario_email'] = dados_user[0]
            session['usuario_nome'] = dados_user[1]
            return redirect(url_for('homepage'))
        elif status == 404:
            flash("Usuário não encontrado.")
        elif status == 403:
            flash("Senha incorreta.")
            
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Chama a função de criar usuário
        resultado = db.new_user(email, usuario, senha)
        
        if resultado == "exists":
            flash("Esse email já está cadastrado.")
        else:
            flash("Conta criada com sucesso! Faça login.")
            return redirect(url_for('login'))
            
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear() # Limpa a sessão (desloga)
    return redirect(url_for('login'))

@app.route('/busca')
def busca():
    return render_template('busca.html')

@app.route("/minhas_avaliacoes")
def minhas_avaliacoes():
    # 1. Verifica se está logado
    if 'usuario_email' not in session:
        return redirect(url_for('login'))
    
    email = session['usuario_email']
    nome = session['usuario_nome']
    
    # 2. Busca as reviews no banco
    reviews = db.ler_avaliacoes_do_usuario(email)
    
    # 3. Calcula as estatísticas
    total_reviews = len(reviews)
    
    media_notas = 0
    if total_reviews > 0:
        soma_notas = sum([linha.nota for linha in reviews]) # Soma todas as notas
        media_notas = round(soma_notas / total_reviews, 1) # Divide e arredonda
        
    # 4. Renderiza o template mandando os dados
    return render_template("profile.html", 
                           nome=nome, 
                           reviews=reviews, 
                           total=total_reviews, 
                           media=media_notas)

@app.route("/avaliacao/<album_id>")
def avaliacao_album(album_id):
    # Verifica se está logado antes de deixar avaliar
    if 'usuario_email' not in session:
        flash("Você precisa estar logado para avaliar.")
        return redirect(url_for('login'))

    album, tracks = buscar_album_por_id(album_id)
    
    if album is None:
        return render_template("erro.html", mensagem="Álbum não encontrado"), 404
        
    return render_template("avaliacao.html", album=album, tracks=tracks)

# --- Rota para PROCESSAR o envio da avaliação ---
@app.route("/avaliacao/<album_id>/enviar", methods=["POST"])
def enviar_avaliacao(album_id):
    if 'usuario_email' not in session:
        return redirect(url_for('login'))
    
    # 1. Recupera dados do formulário
    nota = request.form.get('nota')
    comentario = request.form.get('comentario')
    
    # 2. Precisamos dos dados do álbum para salvar no banco (Nome, Artista, Capa)
    # Vamos buscar de novo no Spotify usando o ID para garantir que os dados estão certos
    album, _ = buscar_album_por_id(album_id)
    
    if not album:
        return "Erro ao recuperar dados do álbum", 404

    # 3. Chama sua função do banco de dados
    user_email = session['usuario_email']
    
    try:
        db.nova_avaliacao(
            user_email=user_email,
            spotify_id=album_id,
            nome_album=album['name'],     # Ajuste conforme a chave do seu dicionário do Spotify
            artista_album=album['artists'][0]['name'], # Pega o primeiro artista
            capa_album=album['images'][0]['url'],      # Pega a url da imagem
            nota=int(nota),
            comentario=comentario
        )
        flash("Avaliação salva com sucesso!")
        return redirect(url_for('minhas_avaliacoes'))
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return "Houve um erro ao salvar sua avaliação."

# --- rota da API (jsoN) ---
@app.route('/api/buscar_album', methods=['POST'])
def api_buscar_album():
    termo = request.form.get('query')
    if not termo:
        return jsonify({'erro': 'O termo de busca é obrigatório'}), 400
    try:
        resultados = buscar_album(termo)
        return jsonify(resultados)
    except Exception as e:
        print(f"Erro na rota API: {e}")
        return jsonify({'erro': 'Erro interno ao buscar álbum'}), 500

if __name__ == '__main__':
    app.run(debug=True)