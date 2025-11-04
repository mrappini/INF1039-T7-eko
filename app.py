from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/avaliacao')
def avaliacao():

    return render_template('avaliacao.html')

@app.route('/cadastro')
def cadastro():

    return render_template('cadastro.html')


@app.route('/login')
def login():

    return render_template('login.html')




if __name__ == '__main__':
    app.run(debug=True)

