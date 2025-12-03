from flask import Flask, render_template, request, jsonify
from integracao_spotify import buscar_album, buscar_album_por_id

app = Flask(__name__)

# ------------- rotas aqui -------------

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/busca')
def busca():
    return render_template('busca.html')

@app.route("/minhas_avaliacoes")
def minhas_avaliacoes():
    return render_template("profile.html")



@app.route("/avaliacao/<album_id>")
def avaliacao_album(album_id):

    album, tracks = buscar_album_por_id(album_id)
    
    if album is None:
        return render_template("erro.html", mensagem="Álbum não encontrado"), 404
        
    return render_template("avaliacao.html", album=album, tracks=tracks)

# --- rota da API (jsoN)

@app.route('/api/buscar_album', methods=['POST'])
def api_buscar_album():
    """
    essa é a rota que o JS chama.
    ela recebe o termo, chama o integracao_spotify, e devolve JSON.
    """
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