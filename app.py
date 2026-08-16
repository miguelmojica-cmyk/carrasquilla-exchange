import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from models import db, Usuario, Figurita, Publicacion, Mensaje

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carrasquilla.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SSL_STRICT'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'figuritas')
PUBLICACIONES_FOLDER = os.path.join(app.root_path, 'static', 'publicaciones')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def extension_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder.'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

from auth import auth_bp
app.register_blueprint(auth_bp)
csrf.exempt(auth_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/figuritas')
def figuritas():
    busqueda = request.args.get('q', '').strip()
    if busqueda:
        lista_figuritas = Figurita.query.filter(Figurita.nombre_jugador.ilike(f'%{busqueda}%')).order_by(Figurita.numero).all()
    else:
        lista_figuritas = Figurita.query.order_by(Figurita.numero).all()
    return render_template('figuritas.html', figuritas=lista_figuritas, busqueda=busqueda)

@app.route('/figuritas/<int:id>')
def detalle_figurita(id):
    figurita = Figurita.query.get_or_404(id)
    publicaciones = Publicacion.query.filter_by(id_figurita=id, activa=True).all()
    return render_template('detalle_figurita.html', figurita=figurita, publicaciones=publicaciones)

@app.route('/figuritas/<int:id>/publicar', methods=['POST'])
@login_required
def publicar_figurita(id):
    figurita = Figurita.query.get_or_404(id)
    tipo = request.form.get('tipo')
    precio = request.form.get('precio', 0)
    descripcion = request.form.get('descripcion', '')
    archivo = request.files.get('imagen')

    nombre_archivo = ''
    if archivo and archivo.filename != '':
        if extension_permitida(archivo.filename):
            nombre_archivo = secure_filename(f"pub_{current_user.id}_{id}_{archivo.filename}")
            archivo.save(os.path.join(PUBLICACIONES_FOLDER, nombre_archivo))
        else:
            flash('Formato de imagen no permitido. Usa PNG, JPG o JPEG.', 'danger')
            return redirect(url_for('detalle_figurita', id=id))

    nueva_publicacion = Publicacion(
        id_usuario=current_user.id,
        id_figurita=id,
        tipo=tipo,
        precio=float(precio) if precio else 0.0,
        descripcion=descripcion,
        imagen_url=nombre_archivo
    )
    db.session.add(nueva_publicacion)
    db.session.commit()
    flash('Tu figurita fue publicada exitosamente.', 'success')
    return redirect(url_for('detalle_figurita', id=id))

@app.route('/publicacion/<int:id>')
def detalle_publicacion(id):
    publicacion = Publicacion.query.get_or_404(id)
    return render_template('detalle_publicacion.html', publicacion=publicacion)

@app.route('/publicacion/<int:id_publicacion>/mensaje', methods=['POST'])
@login_required
def enviar_mensaje(id_publicacion):
    publicacion = Publicacion.query.get_or_404(id_publicacion)

    if publicacion.id_usuario == current_user.id:
        flash('No puedes enviarte un mensaje a ti mismo.', 'danger')
        return redirect(url_for('detalle_publicacion', id=id_publicacion))

    contenido = request.form.get('contenido', '').strip()
    if not contenido:
        flash('El mensaje no puede estar vacío.', 'danger')
        return redirect(url_for('detalle_publicacion', id=id_publicacion))

    nuevo_mensaje = Mensaje(
        id_remitente=current_user.id,
        id_destinatario=publicacion.id_usuario,
        id_publicacion=id_publicacion,
        contenido=contenido
    )
    db.session.add(nuevo_mensaje)
    db.session.commit()
    flash('Mensaje enviado.', 'success')
    return redirect(url_for('conversacion', otro_id=publicacion.id_usuario))

@app.route('/mensajes')
@login_required
def mensajes():
    vista = request.args.get('vista', 'recibidos')
    if vista == 'enviados':
        base = Mensaje.query.filter_by(id_remitente=current_user.id).order_by(Mensaje.fecha.desc()).all()
    else:
        base = Mensaje.query.filter_by(id_destinatario=current_user.id).order_by(Mensaje.fecha.desc()).all()

    conversaciones = {}
    for m in base:
        otro_id = m.id_remitente if vista == 'recibidos' else m.id_destinatario
        if otro_id not in conversaciones:
            conversaciones[otro_id] = m

    lista = list(conversaciones.values())
    return render_template('mensajes.html', conversaciones=lista, vista=vista)

@app.route('/mensajes/conversacion/<int:otro_id>')
@login_required
def conversacion(otro_id):
    otro = Usuario.query.get_or_404(otro_id)
    mensajes_conv = Mensaje.query.filter(
        or_(
            and_(Mensaje.id_remitente == current_user.id, Mensaje.id_destinatario == otro_id),
            and_(Mensaje.id_remitente == otro_id, Mensaje.id_destinatario == current_user.id)
        )
    ).order_by(Mensaje.fecha.asc()).all()

    Mensaje.query.filter_by(id_remitente=otro_id, id_destinatario=current_user.id, leido=False).update({'leido': True})
    db.session.commit()

    publicacion_relacionada = None
    for m in mensajes_conv:
        if m.publicacion_ref:
            publicacion_relacionada = m.publicacion_ref

    return render_template('conversacion.html', otro=otro, mensajes=mensajes_conv, publicacion=publicacion_relacionada)

@app.route('/mensajes/conversacion/<int:otro_id>/enviar', methods=['POST'])
@login_required
def enviar_mensaje_conversacion(otro_id):
    contenido = request.form.get('contenido', '').strip()
    if not contenido:
        flash('El mensaje no puede estar vacío.', 'danger')
        return redirect(url_for('conversacion', otro_id=otro_id))

    nuevo = Mensaje(id_remitente=current_user.id, id_destinatario=otro_id, contenido=contenido)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for('conversacion', otro_id=otro_id))

@app.route('/admin')
@login_required
def admin():
    if current_user.rol != 'administrador':
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('index'))
    usuarios = Usuario.query.all()
    figuritas = Figurita.query.order_by(Figurita.numero).all()
    return render_template('admin.html', usuarios=usuarios, figuritas=figuritas)

@app.route('/admin/agregar_figurita', methods=['POST'])
@login_required
def agregar_figurita():
    if current_user.rol != 'administrador':
        return redirect(url_for('index'))

    numero = request.form.get('numero')
    tipo = request.form.get('tipo', 'normal')
    nombre_jugador = request.form.get('nombre_jugador')
    pais = request.form.get('pais')
    archivo = request.files.get('imagen')

    nombre_archivo = ''
    if archivo and archivo.filename != '':
        if extension_permitida(archivo.filename):
            nombre_archivo = secure_filename(f"{numero}_{tipo}_{archivo.filename}")
            ruta_completa = os.path.join(UPLOAD_FOLDER, nombre_archivo)
            archivo.save(ruta_completa)
        else:
            flash('Formato de imagen no permitido. Usa PNG, JPG o JPEG.', 'danger')
            return redirect(url_for('admin'))

    nueva = Figurita(numero=numero, tipo=tipo, nombre_jugador=nombre_jugador, pais=pais, imagen_url=nombre_archivo)
    db.session.add(nueva)
    db.session.commit()
    flash('Figurita agregada exitosamente.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/eliminar_figurita/<int:id>')
@login_required
def eliminar_figurita(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('index'))
    figurita = Figurita.query.get_or_404(id)
    db.session.delete(figurita)
    db.session.commit()
    flash('Figurita eliminada correctamente.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/toggle_usuario/<int:id>')
@login_required
def toggle_usuario(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('index'))
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = not usuario.activo
    db.session.commit()
    flash(f'Usuario {"activado" if usuario.activo else "desactivado"} correctamente.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/eliminar_usuario/<int:id>')
@login_required
def eliminar_usuario(id):
    if current_user.rol != 'administrador':
        return redirect(url_for('index'))
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('admin'))
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('admin'))

@app.errorhandler(413)
def archivo_muy_grande(e):
    flash('El archivo es demasiado grande. Máximo 5 MB.', 'danger')
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    with app.app_context():
        db.create_all()
    app.run(debug=debug_mode, host='0.0.0.0')