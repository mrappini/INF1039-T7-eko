from flask import Flask, render_template, request, jsonify
from integracao_spotify import buscar_album, buscar_album_por_id

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/login')
def login():
    return render_template('login.html')

# RA1: PÁGINA ESPECÍFICA DO ÁLBUM (Mantém o album_id)
# usada quando o usuário clica em um álbum para avaliar, tipo vindo da busca
@app.route("/avaliacao/<album_id>")
def avaliacao_album(album_id):
    album,tracks = buscar_album_por_id(album_id)
    
    if album is None:
        return "parece que o álbum não foi encontrado...quer tentar novamente?", 404
    return render_template("avaliacao.html", album=album, tracks=tracks)

# RA2: PÁGINA GENÉRICA (NOVA ROTA PARA O NAVBAR)
# usada para listar todas as avaliações do usuário.

@app.route("/minhas_avaliacoes")
def minhas_avaliacoes():
    return render_template("minhas_avaliacoes.html")

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/busca')
def busca():
    return render_template('busca.html')

@app.route('/api/buscar_album', methods=['POST'])
def api_buscar_album():
    nome_album = request.form.get('album')
    if not nome_album:
        return jsonify({'erro': 'Nome do álbum é obrigatório'}), 400
    resultados = buscar_album(nome_album)
    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)