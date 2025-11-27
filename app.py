from flask import Flask, render_template, request, jsonify
from integracao_spotify import buscar_album, buscar_album_por_id

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/login')  # ← ADICIONE ESTA ROTA
def login():
    return render_template('login.html')  # Crie este template se necessário

@app.route("/album/<album_id>")
def avaliacao(album_id):
    album = buscar_album_por_id(album_id)
    return render_template("avaliacao.html", album=album)

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