from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime 
from sqlalchemy import func # func para usar COUNT

app = Flask (__name__)

# --- INICIO DE CONFIGURACIÓN DE POSTGRESQL (ÚNICA) ---

# Usa tu contraseña real: 12345678
LOCAL_POSTGRES_URL = "postgresql://postgres:12345678@127.0.0.1:5432/papers_world_db"

# 1. Configurar la URI de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or LOCAL_POSTGRES_URL

# 2. Configuración general
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

# --- FIN DE CONFIGURACIÓN DE POSTGRESQL ---

db = SQLAlchemy(app)
# --- modelo Base de Datos ---

# Modelo para los diseños 
class Diseno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    dificultad = db.Column(db.String(20), default='Intermedio')
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(200), default='default_diseno.png')
    
    def __repr__(self):
        return f"Diseño('{self.nombre}', '{self.categoria}', '{self.precio}')"

# Modelo para las reseñas y comentarios de los usuarios
class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), nullable=False)
    email_coment = db.Column(db.String(120), nullable=False)
    calificacion = db.Column(db.Integer, default=5) # 1 a 5 estrellas
    texto = db.Column(db.Text, nullable=False)
    tipo_resena = db.Column(db.String(50), default='General')
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Agregamos la fecha/hora 

# Modelo para las solicitudes de personalización
class SolicitudPersonalizacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False) # Para la ruta personalizacion
    email = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    archivo_referencia = db.Column(db.String(200)) # Ruta al archivo subido
    estado = db.Column(db.String(20), default='Pendiente')
    
# --- Función para crear la DB ---
def inicializar_db():
    # Solo crea las tablas si no existen (es necesario mantener esta línea)
    with app.app_context():
        db.create_all()

        # [BLOQUE COMENTADO]: Se elimina la inserción automática de datos de prueba.
        # Los datos reales ya fueron insertados manualmente en PostgreSQL.
        """
        if Comentario.query.count() == 0:
            comentarios_ejemplo = [
                Comentario(nombre_usuario='Ana G.', email_coment='a@test.com', calificacion=5, texto='¡El mejor diseño que he comprado!', tipo_resena='Diseño/Producto'),
                Comentario(nombre_usuario='Luis M.', email_coment='l@test.com', calificacion=4, texto='Excelentes clases, muy buen soporte en Discord.', tipo_resena='Clase/Tutorial'),
            ]
            for comentario in comentarios_ejemplo:
                db.session.add(comentario)

            # Insertar diseños prueba
            if Diseno.query.count() == 0:
                disenos_ejemplo = [
                    Diseno(nombre='Templo Japonés', categoria='Arquitectura', dificultad='Avanzado', precio=18.50),
                    Diseno(nombre='Zorro Low Poly', categoria='Animales', dificultad='Intermedio', precio=9.99),
                    Diseno(nombre='Cubo de Práctica', categoria='Básico', dificultad='Fácil', precio=0.00),
                ]
                for diseno in disenos_ejemplo:
                    db.session.add(diseno)
                
            db.session.commit()
            print("Base de datos y datos de ejemplo iniciales.")
        """

# @ app.route rutas 
# Ruta de Inicio
@app.route('/')
def index():
    """Ruta de la página de inicio carrusel de diseños."""
    #Ordenamos por func.random() 
    try:
        # Obtener 5 diseños de forma aleatoria
        disenos_carrusel = Diseno.query.order_by(func.random()).limit(5).all() 
    except Exception as e:
        # Manejo de error si la consulta falla
        print(f"Error al cargar diseños para el carrusel: {e}")
        disenos_carrusel = []
    
    # Renderizar la plantilla disenos_carrusel
    return render_template('index.html', 
                            active_page='index', 
                            disenos_carrusel=disenos_carrusel)

# Ruta de diseños desde la DB
@app.route('/disenos')
def disenos():
    todos_disenos = Diseno.query.all()
    
    # La consulta agrupa por la columna 'categoria' y cuenta el número de filas en ese grupo.
    conteo_categorias = db.session.query(
        Diseno.categoria, func.count(Diseno.id)
    ).group_by(Diseno.categoria).all()

    # Convertir la lista de tuplas en un diccionario para facilitar el acceso en la plantilla
    conteo_diccionario = dict(conteo_categorias)
    # También contamos el total de diseños
    total_disenos = len(todos_disenos)
    TAMANO_LOTE = 9
    
    return render_template(
        'disenos.html', 
        disenos=todos_disenos, 
        tamano_lote=TAMANO_LOTE,
        conteo_categorias=conteo_diccionario
    )

# Ruta de Personalización GET para mostrar, POST para guardar solicitud
@app.route('/personalizacion', methods=['GET', 'POST'])
def personalizacion():
    if request.method == 'POST':
        # 1. Capturar datos del formulario
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        descripcion = request.form.get('descripcion')
        
        # 2. Manejo de archivo subido
        archivo_referencia = request.files.get('archivo')
        archivo_nombre = archivo_referencia.filename if archivo_referencia and archivo_referencia.filename else 'N/A'
        
        nueva_solicitud = SolicitudPersonalizacion(
            nombre=nombre,
            email=email,
            descripcion=descripcion,
            archivo_referencia=archivo_nombre
        )
        # Guardar en la DB
        db.session.add(nueva_solicitud)
        db.session.commit()
        
        return redirect(url_for('personalizacion')) # Redirige después de enviar
    
    return render_template('personalizacion.html', active_page='personalizacion')

# Ruta de Aprende POST para cotización rápida
@app.route('/aprende', methods=['GET', 'POST'])
def aprende():
    if request.method == 'POST':
        # Los campos del formulario de Aprende son: link_modelo y email
        #  nombre_cotizacion
        nombre = request.form.get('nombre_cotizacion')
        link_modelo = request.form.get('link_modelo')
        email_cotizacion = request.form.get('email_cotizacion')
        
        nueva_solicitud = SolicitudPersonalizacion(
            nombre=nombre or "Usuario Rápido", # por defecto
            email=email_cotizacion,
            descripcion=f"Cotización diseño rápido - Enlace: {link_modelo}",
            archivo_referencia="Enlace proporcionado en descripción"
        )
        
        db.session.add(nueva_solicitud)
        db.session.commit()
        
        return redirect(url_for('aprende'))

    return render_template('aprende.html', active_page='aprende')

# Ruta de Clases
@app.route('/clases')
def clases():
    return render_template('clases.html', active_page='clases')

# Ruta de Feedback (GET para mostrar, POST para guardar comentario)
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        # Capturar datos del formulario
        nombre = request.form.get('nombre_coment')
        email = request.form.get('email_coment')
        calificacion = request.form.get('calificacion', 5, type=int)
        texto = request.form.get('texto_coment')
        tipo_resena = request.form.get('tipo_resena')

        nuevo_comentario = Comentario(
            nombre_usuario=nombre,
            email_coment=email,
            calificacion=calificacion,
            texto=texto,
            tipo_resena=tipo_resena
        )
        db.session.add(nuevo_comentario)
        db.session.commit()
        return redirect(url_for('feedback')) # Redirige para evitar doble envío
    
    # Si es GET cargamos todos los comentarios para mostrar
    # CLAVE: Limitar a 6 y ordenar por fecha descendente (más nuevo primero)
    comentarios = Comentario.query.order_by(Comentario.fecha.desc()).limit(6).all() 
    return render_template('feedback.html', comentarios=comentarios, active_page='feedback')

# Ruta de Tienda
@app.route('/tienda')
def tienda():
    todos_disenos = Diseno.query.all()
    return render_template('tienda.html', disenos=todos_disenos, active_page='tienda')

if __name__ == '__main__':
    inicializar_db() 
    app.run(debug=True)
