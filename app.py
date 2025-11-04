from flask import Flask, render_template

app = Flask(__name__)

@app.route('/inicio')
def homepage():
    return render_template('homepage.html')

@app.route('/avaliacao')
def avaliacao():
    return render_template('avaliacao.html')

if __name__ == '__main__':
    app.run(debug=True)
