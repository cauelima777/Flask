import os
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from flask_login import (
    UserMixin, LoginManager,
    login_user, login_required,
    logout_user
)
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
from flask_wtf import CSRFProtect

# -------------------------
# CONFIGURAÇÃO
# -------------------------

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY não definida no .env")

if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise ValueError("DATABASE_URL não definida no .env")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Sessão
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # True quando usar HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# -------------------------
# EXTENSÕES
# -------------------------

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

csrf = CSRFProtect(app)

# -------------------------
# USUÁRIO FIXO (ADMIN)
# -------------------------

class Usuario(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    admin_user = os.getenv('ADMIN_USER')
    return Usuario(id=1, username=admin_user)

# -------------------------
# MODELO DO DIÁRIO
# -------------------------

class Entrada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

# -------------------------
# ROTAS
# -------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin_user = os.getenv('ADMIN_USER')
        admin_password_hash = os.getenv('ADMIN_PASSWORD_HASH')

        if not admin_user or not admin_password_hash:
            return "Configuração de admin inválida", 500

        if username != admin_user or not check_password_hash(admin_password_hash, password):
            return "Credenciais inválidas", 401

        user = Usuario(id=1, username=admin_user)
        login_user(user, remember=False)

        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    anos = db.session.query(
        extract('year', Entrada.data_criacao).label('ano')
    ).distinct().order_by(db.desc('ano')).all()

    lista_anos = [int(a.ano) for a in anos]
    return render_template('index.html', anos=lista_anos)


@app.route('/ano/<int:ano>')
@login_required
def ver_ano(ano):
    entradas = Entrada.query.filter(
        extract('year', Entrada.data_criacao) == ano
    ).order_by(Entrada.data_criacao.desc()).all()

    return render_template('lista_ano.html', entradas=entradas, ano=ano)


@app.route('/escrever', methods=['GET', 'POST'])
@login_required
def escrever():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()

        if not titulo or not conteudo:
            return "Preencha todos os campos", 400

        nova_entrada = Entrada(
            titulo=titulo,
            conteudo=conteudo
        )

        db.session.add(nova_entrada)
        db.session.commit()

        return redirect(url_for('ver_ano', ano=nova_entrada.data_criacao.year))

    return render_template('escrever.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    entrada = Entrada.query.get_or_404(id)

    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        conteudo = request.form.get('conteudo', '').strip()

        if not titulo or not conteudo:
            return "Preencha todos os campos", 400

        entrada.titulo = titulo
        entrada.conteudo = conteudo

        db.session.commit()

        return redirect(url_for('ver_ano', ano=entrada.data_criacao.year))

    return render_template('editar.html', entrada=entrada)


@app.route('/deletar/<int:id>', methods=['POST'])
@login_required
def deletar(id):
    entrada = Entrada.query.get_or_404(id)
    ano = entrada.data_criacao.year

    db.session.delete(entrada)
    db.session.commit()

    return redirect(url_for('ver_ano', ano=ano))


@app.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    entrada = Entrada.query.get_or_404(id)
    return render_template('visualizar.html', entrada=entrada)

# -------------------------
# INICIALIZAÇÃO
# -------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(
        host='0.0.0.0',
        debug=os.getenv('DEBUG') == 'True'
    )