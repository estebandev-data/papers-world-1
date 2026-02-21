from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime 
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURACIÓN DE SQLITE FORZADA ---
# Obtenemos la ruta absoluta del directorio donde está este archivo
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuramos la URI para que siempre apunte al archivo local, ignorando variables externas
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'papers_world.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

# --- FIN DE CONFIGURACIÓN ---

db = SQLAlchemy(app)

# --- MODELOS DE BASE DE DATOS ---

class Diseno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    dificultad = db.Column(db.String(20), default='Intermedio')
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(200), default='default_diseno.png')
    
    def __repr__(self):
        return f"Diseño('{self.nombre}', '{self.categoria}', '{self.precio}')"

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
    
# --- FUNCIÓN PARA INICIALIZAR LA DB ---
def inicializar_db():
    with app.app_context():
        # Crea el archivo .db y las tablas si no existen
        db.create_all()

        # Inserción de datos iniciales si la tabla está vacía
        if Diseno.query.count() == 0:
            disenos_ejemplo = [
                Diseno(nombre='Templo Japonés', categoria='Otros', dificultad='Avanzado', precio=18.50, imagen_url='templo.jpg'),
                Diseno(nombre='Zorro Low Poly', categoria='Animales', dificultad='Intermedio', precio=9.99, imagen_url='zorro.jpg'),
                Diseno(nombre='Auto Deportivo', categoria='Vehiculos', dificultad='Avanzado', precio=15.00, imagen_url='auto.jpg'),
                Diseno(nombre='Dragón de Fuego', categoria='Fantasia y Personajes', dificultad='Avanzado', precio=20.00, imagen_url='dragon.jpg'),
                Diseno(nombre='Cubo de Práctica', categoria='Otros', dificultad='Fácil', precio=0.00, imagen_url='cubo.jpg'),
            ]
            db.session.bulk_save_objects(disenos_ejemplo)
            db.session.commit()
            print("Base de datos SQLite creada y diseños de prueba insertados.")

# --- RUTAS ---

@app.route('/')
def index():
    try:
        disenos_carrusel = Diseno.query.order_by(func.random()).limit(5).all() 
    except Exception as e:
        print(f"Error en carrusel: {e}")
        disenos_carrusel = []
    
    return render_template('index.html', active_page='index', disenos_carrusel=disenos_carrusel)

@app.route('/disenos')
def disenos():
    todos_disenos = Diseno.query.all()
    conteo_categorias = db.session.query(
        Diseno.categoria, func.count(Diseno.id)
    ).group_by(Diseno.categoria).all()

    conteo_diccionario = dict(conteo_categorias)
    TAMANO_LOTE = 8 
    
    return render_template(
        'disenos.html', 
        disenos=todos_disenos, 
        tamano_lote=TAMANO_LOTE,
        conteo_categorias=conteo_diccionario
    )

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
            descripcion=f"Cotización rápida - Enlace: {request.form.get('link_modelo')}",
            archivo_referencia="Enlace en descripción"
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
        nuevo_comentario = Comentario(
            nombre_usuario=request.form.get('nombre_coment'),
            email_coment=request.form.get('email_coment'),
            calificacion=request.form.get('calificacion', 5, type=int),
            texto=request.form.get('texto_coment'),
            tipo_resena=request.form.get('tipo_resena')
        )
        db.session.add(nuevo_comentario)
        db.session.commit()
        return redirect(url_for('feedback'))
    
    comentarios = Comentario.query.order_by(Comentario.fecha.desc()).limit(6).all() 
    return render_template('feedback.html', comentarios=comentarios, active_page='feedback')

@app.route('/tienda')
def tienda():
    todos_disenos = Diseno.query.all()
    return render_template('tienda.html', disenos=todos_disenos, active_page='tienda')

# --- INICIALIZACIÓN FUERA DEL IF MAIN PARA RENDER ---
inicializar_db()

if __name__ == '__main__':
    app.run(debug=True)