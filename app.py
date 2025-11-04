from flask import Flask, render_template

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


@app.route('/login')
def login():

    return render_template('login.html')




if __name__ == '__main__':
    app.run(debug=True)

