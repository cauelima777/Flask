from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy import extract

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:U3QMcFCPz9G6EhvsLr7npp9pVQ5tgMeY@dpg-d7b6ftgule4c738sbue0-a.oregon-postgres.render.com/banco_yo'
db = SQLAlchemy(app)


class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)


#criar o banco de dados
with app.app_context():
    db.create_all()
    
    
# 1. Nova Página Principal (Agrupada por Ano)
@app.route('/')
def index():
    # Busca apenas os anos únicos que possuem memórias
    anos = db.session.query(extract('year', Entrada.data_criacao).label('ano'))\
             .distinct().order_by(db.desc('ano')).all()
    # Converte de tuplas para uma lista simples: [2026, 2025...]
    lista_anos = [int(a.ano) for a in anos]
    return render_template('index.html', anos=lista_anos)

# 2. Página do Ano Específico
@app.route('/ano/<int:ano>')
def ver_ano(ano):
    # Filtra as memórias que pertencem ao ano clicado
    entradas = Entrada.query.filter(extract('year', Entrada.data_criacao) == ano)\
                            .order_by(Entrada.data_criacao.desc()).all()
    return render_template('lista_ano.html', entradas=entradas, ano=ano)

@app.route('/escrever', methods=['GET', 'POST'])

def escrever(): 
    if request.method == 'POST':
        novo_titulo = request.form['titulo']
        novo_conteudo = request.form['conteudo']
        nova_entrada = Entrada(titulo=novo_titulo, conteudo=novo_conteudo)
        db.session.add(nova_entrada)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('escrever.html')

@app.route('/deletar/<int:id>')  # Adicione o <int:id> aqui
def deletar(id):
    entrada = Entrada.query.get_or_404(id)
    db.session.delete(entrada)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    entrada = Entrada.query.get_or_404(id)
    if request.method == 'POST':
        # Use os nomes exatos das colunas do seu modelo Entrada
        entrada.titulo = request.form['titulo']
        entrada.conteudo = request.form['conteudo']
        
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('editar.html', entrada=entrada)


@app.route('/visualizar/<int:id>')
def visualizar(id):
    entrada = Entrada.query.get_or_404(id)
    return render_template('visualizar.html', entrada=entrada)





app.run(debug = True)
