from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='coleccionista')
    saldo = db.Column(db.Float, default=50.0)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    publicaciones = db.relationship('Publicacion', backref='vendedor', lazy=True)
    transacciones_enviadas = db.relationship('Transaccion', foreign_keys='Transaccion.id_comprador', backref='comprador', lazy=True)
    transacciones_recibidas = db.relationship('Transaccion', foreign_keys='Transaccion.id_vendedor', backref='vendedor_trans', lazy=True)


class Figurita(db.Model):
    __tablename__ = 'figuritas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), nullable=False)
    tipo = db.Column(db.String(20), default='normal')
    nombre_jugador = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    imagen_url = db.Column(db.String(255), default='')

    publicaciones = db.relationship('Publicacion', backref='figurita', lazy=True)


class Publicacion(db.Model):
    __tablename__ = 'publicaciones'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_figurita = db.Column(db.Integer, db.ForeignKey('figuritas.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    precio = db.Column(db.Float, default=0.0)
    descripcion = db.Column(db.Text, default='')
    imagen_url = db.Column(db.String(255), default='')
    activa = db.Column(db.Boolean, default=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class Transaccion(db.Model):
    __tablename__ = 'transacciones'
    id = db.Column(db.Integer, primary_key=True)
    id_comprador = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_vendedor = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    publicacion = db.relationship('Publicacion', backref='transacciones')


class Valoracion(db.Model):
    __tablename__ = 'valoraciones'
    id = db.Column(db.Integer, primary_key=True)
    id_evaluador = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_evaluado = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    puntuacion = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text, default='')
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


class Mensaje(db.Model):
    __tablename__ = 'mensajes'
    id = db.Column(db.Integer, primary_key=True)
    id_remitente = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_destinatario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_publicacion = db.Column(db.Integer, db.ForeignKey('publicaciones.id'), nullable=True)
    contenido = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    remitente = db.relationship('Usuario', foreign_keys=[id_remitente], backref='mensajes_enviados')
    destinatario = db.relationship('Usuario', foreign_keys=[id_destinatario], backref='mensajes_recibidos')
    publicacion_ref = db.relationship('Publicacion', foreign_keys=[id_publicacion])