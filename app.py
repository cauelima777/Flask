from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import extract
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
app = Flask(__name__)
# Dica: Adicione uma SECRET_KEY para as sessões de login funcionarem
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' 
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:U3QMcFCPz9G6EhvsLr7npp9pVQ5tgMeY@dpg-d7b6ftgule4c738sbue0-a.oregon-postgres.render.com/banco_yo'
db = SQLAlchemy(app)




login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)

class Entrada(db.Model): # REMOVIDO @login_required daqui
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- ROTAS ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.senha_hash, request.form['password']):
            # Ao deixar remember=False, o cookie expira ao fechar o navegador
            login_user(user, remember=False) 
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/') # O route vem PRIMEIRO
@login_required # O required vem DEPOIS
def index():
    anos = db.session.query(extract('year', Entrada.data_criacao).label('ano'))\
             .distinct().order_by(db.desc('ano')).all()
    lista_anos = [int(a.ano) for a in anos]
    return render_template('index.html', anos=lista_anos)

@app.route('/ano/<int:ano>')
@login_required
def ver_ano(ano):
    entradas = Entrada.query.filter(extract('year', Entrada.data_criacao) == ano)\
                            .order_by(Entrada.data_criacao.desc()).all()
    return render_template('lista_ano.html', entradas=entradas, ano=ano)

@app.route('/escrever', methods=['GET', 'POST'])
@login_required
def escrever(): 
    if request.method == 'POST':
        novo_titulo = request.form['titulo']
        novo_conteudo = request.form['conteudo']
        nova_entrada = Entrada(titulo=novo_titulo, conteudo=novo_conteudo)
        db.session.add(nova_entrada)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('escrever.html')

@app.route('/deletar/<int:id>')
@login_required
def deletar(id):
    entrada = Entrada.query.get_or_404(id)
    db.session.delete(entrada)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    entrada = Entrada.query.get_or_404(id)
    if request.method == 'POST':
        entrada.titulo = request.form['titulo']
        entrada.conteudo = request.form['conteudo']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('editar.html', entrada=entrada)

@app.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    entrada = Entrada.query.get_or_404(id)
    return render_template('visualizar.html', entrada=entrada)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)