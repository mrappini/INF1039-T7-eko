from flask import Flask, render_template, request, jsonify
from integracao_spotify import buscar_album


app = Flask(__name__)


@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/avaliacao')
def avaliacao():
    album = {
    "titulo": "Currents",
    "artista": "Tame Impala",
    "ano": 2015,
    "genero": "Pop/Indie",
    "nota": 9.2
}
    return render_template('avaliacao.html', album=album)

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



