from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/avaliacao')
def avaliacao(album_id):
    from integracao_spotify import sp
    album = sp.album(album_id)  
    tracks = album["tracks"]["items"]

    return render_template(
        "avaliacao.html",
        album=album,
        tracks=tracks
    )

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')


@app.route('/login')
def login():

    return render_template('login.html')

@app.route('/explorar')
def explorar():
    return render_template('busca.html')


if __name__ == '__main__':
    app.run(debug=True)

