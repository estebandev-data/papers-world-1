from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
database_url = os.environ.get('DATABASE_URL', '')

# SQLAlchemy requiere "postgresql://" en vez de "postgres://"
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-local-desarrollo')

db = SQLAlchemy(app)

# --- MODELOS ---

class Diseno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    dificultad = db.Column(db.String(20), default='Intermedio')
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(200), default='default_diseno.png')

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), nullable=False)
    email_coment = db.Column(db.String(120), nullable=False)
    calificacion = db.Column(db.Integer, default=5)
    texto = db.Column(db.Text, nullable=False)
    tipo_resena = db.Column(db.String(50), default='General')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class SolicitudPersonalizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    archivo_referencia = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='Pendiente')

# --- RUTAS ---

@app.route('/')
def index():
    try:
        disenos_carrusel = Diseno.query.order_by(func.random()).limit(5).all()
    except Exception as e:
        print(f"Error: {e}")
        disenos_carrusel = []
    return render_template('index.html', active_page='index', disenos_carrusel=disenos_carrusel)

@app.route('/disenos')
def disenos():
    try:
        todos_disenos = Diseno.query.all()
        conteo_categorias = db.session.query(
            Diseno.categoria, func.count(Diseno.id)
        ).group_by(Diseno.categoria).all()
        conteo_diccionario = dict(conteo_categorias)
    except Exception as e:
        print(f"Error al cargar datos en /disenos: {e}")
        todos_disenos = []
        conteo_diccionario = {}
        
    # El resto del código es igual:
    TAMANO_LOTE = 9
    return render_template('disenos.html', disenos=todos_disenos, tamano_lote=TAMANO_LOTE, conteo_categorias=conteo_diccionario)

@app.route('/personalizacion', methods=['GET', 'POST'])
def personalizacion():
    if request.method == 'POST':
        nueva_solicitud = SolicitudPersonalizacion(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            descripcion=request.form.get('descripcion'),
            archivo_referencia=request.files.get('archivo').filename if request.files.get('archivo') else 'N/A'
        )
        db.session.add(nueva_solicitud)
        db.session.commit()
        return redirect(url_for('personalizacion'))
    return render_template('personalizacion.html', active_page='personalizacion')

@app.route('/aprende', methods=['GET', 'POST'])
def aprende():
    if request.method == 'POST':
        nueva_solicitud = SolicitudPersonalizacion(
            nombre=request.form.get('nombre_cotizacion') or "Usuario Rápido",
            email=request.form.get('email_cotizacion'),
            descripcion=f"Cotización rápida: {request.form.get('link_modelo')}",
            archivo_referencia="Enlace"
        )
        db.session.add(nueva_solicitud)
        db.session.commit()
        return redirect(url_for('aprende'))
    return render_template('aprende.html', active_page='aprende')

@app.route('/clases')
def clases():
    return render_template('clases.html', active_page='clases')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        nuevo = Comentario(
            nombre_usuario=request.form.get('nombre_coment'),
            email_coment=request.form.get('email_coment'),
            calificacion=request.form.get('calificacion', 5, type=int),
            texto=request.form.get('texto_coment'),
            tipo_resena=request.form.get('tipo_resena')
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('feedback'))
    comentarios = Comentario.query.order_by(Comentario.fecha.desc()).limit(6).all()
    return render_template('feedback.html', comentarios=comentarios, active_page='feedback')

@app.route('/tienda')
def tienda():
    todos_disenos = Diseno.query.all()
    return render_template('tienda.html', disenos=todos_disenos, active_page='tienda')

if __name__ == '__main__':
    app.run(debug=True)

    with app.app_context():
        db.create_all()