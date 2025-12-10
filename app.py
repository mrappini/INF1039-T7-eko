from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from integracao_spotify import buscar_album, buscar_album_por_id
import user_data_management as db 

app = Flask(__name__)
app.secret_key = "chave_super_secreta_do_eko" 

# --- ROTAS PRINCIPAIS ---

@app.route('/')
def homepage():
    usuario_logado = session.get('usuario_nome')
    return render_template('homepage.html', usuario=usuario_logado)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email_login')
        senha = request.form.get('senha_login')
        
        status = db.login_match(email, senha)
        
        if status == 200:
            dados_user = db.get_user(email)
            session['usuario_email'] = dados_user.Email
            session['usuario_nome'] = dados_user.Usuario
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
        
        try:
            resultado = db.new_user(email, usuario, senha)
        except TypeError:
            resultado = db.new_user(email, usuario, senha, "1.png")
        
        if resultado == "exists":
            flash("Esse email já está cadastrado.")
        else:
            flash("Conta criada com sucesso! Faça login.")
            return redirect(url_for('login'))     
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/busca')
def busca():
    return render_template('busca.html')

@app.route("/minhas_avaliacoes")
def minhas_avaliacoes():
    if 'usuario_email' not in session:
        return redirect(url_for('login'))
    
    email = session['usuario_email']
    nome = session['usuario_nome']
    
    reviews = db.ler_avaliacoes_do_usuario(email)
    
    total_reviews = len(reviews)
    media_notas = 0
    if total_reviews > 0:
        soma_notas = sum([linha.nota for linha in reviews])
        media_notas = round(soma_notas / total_reviews, 1)
        
    return render_template("profile.html", 
                           nome=nome, 
                           reviews=reviews, 
                           total=total_reviews, 
                           media=media_notas)

# --- ROTAS DE AVALIAÇÃO ---

@app.route("/avaliacao/<album_id>")
def avaliacao_album(album_id):
    if 'usuario_email' not in session:
        flash("Faça login para ver avaliações.")
        return redirect(url_for('login'))

    album, tracks = buscar_album_por_id(album_id)
    
    if album is None:
        return render_template("erro.html", mensagem="Álbum não encontrado"), 404
    
    reviews_do_album = db.ler_avaliacoes_do_album(album_id)

    return render_template("avaliacao.html", album=album, tracks=tracks, reviews=reviews_do_album)

@app.route("/avaliacao/<album_id>/enviar", methods=["POST"])
def enviar_avaliacao(album_id):
    if 'usuario_email' not in session:
        return redirect(url_for('login'))
    
    nota = request.form.get('rating') 
    comentario = request.form.get('comentario')
    
    if not nota: nota = 0.0
    
    album, _ = buscar_album_por_id(album_id)
    
    if not album:
        return "Erro: Álbum não encontrado", 404

    user_email = session['usuario_email']
    
    try:
        nome_album = album.get('nome') or album.get('name')
        
        artista_album = "Desconhecido"
        if 'artists' in album: 
             artista_album = album['artists'][0]['name']
        elif 'artista' in album:
             artista_album = album['artista']
             
        capa_album = ""
        if 'images' in album:
            capa_album = album['images'][0]['url']
        elif 'imagem' in album:
            capa_album = album['imagem']

        db.nova_avaliacao(
            user_email=user_email,
            spotify_id=album_id,
            nome_album=nome_album,
            artista_album=artista_album,
            capa_album=capa_album,
            nota=float(nota),
            comentario=comentario
        )
        flash("Avaliação enviada!")
        return redirect(url_for('avaliacao_album', album_id=album_id))
        
    except Exception as e:
        print(f"ERRO GRAVE AO SALVAR: {e}") 
        return f"Erro interno: {e}"


@app.route("/deletar/<int:review_id>")
def deletar_avaliacao(review_id):
    if 'usuario_email' not in session:
        return redirect(url_for('login'))
    
    email = session['usuario_email']
    

    linhas_afetadas = db.deletar_review(review_id, email)
    
    if linhas_afetadas > 0:
        flash("Avaliação apagada com sucesso!")
    else:
        flash("Erro: Você não tem permissão para apagar essa avaliação.")
        

    return redirect(request.referrer)

@app.route('/api/buscar_album', methods=['POST'])
def api_buscar_album():
    termo = request.form.get('query')
    if not termo:
        return jsonify({'erro': 'Termo vazio'}), 400
    try:
        resultados = buscar_album(termo)
        return jsonify(resultados)
    except Exception as e:
        print(e)
        return jsonify({'erro': 'Erro interno'}), 500
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('erro.html', mensagem="Página não encontrada. Você se perdeu no ritmo?"), 404

if __name__ == '__main__':
    app.run(debug=True)