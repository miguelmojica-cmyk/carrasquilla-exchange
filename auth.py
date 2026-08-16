import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, Usuario
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        contrasena = request.form.get('contrasena', '')

        # Validar nombre
        if len(nombre) < 3:
            flash('El nombre debe tener al menos 3 caracteres.', 'danger')
            return redirect(url_for('auth.registro'))

        # Validar formato de correo
        if not re.match(EMAIL_REGEX, email):
            flash('Ingresa un correo electrónico válido.', 'danger')
            return redirect(url_for('auth.registro'))

        # Validar longitud de contraseña
        if len(contrasena) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('auth.registro'))

        # Verificar si el email ya existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('auth.registro'))

        # Hashear contraseña y guardar usuario
        contrasena_hash = bcrypt.generate_password_hash(contrasena).decode('utf-8')
        nuevo_usuario = Usuario(nombre=nombre, email=email, contrasena=contrasena_hash)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Cuenta creada exitosamente. Inicia sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('registro.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        contrasena = request.form.get('contrasena', '')

        if not email or not contrasena:
            flash('Completa todos los campos.', 'danger')
            return redirect(url_for('auth.login'))

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not bcrypt.check_password_hash(usuario.contrasena, contrasena):
            flash('Correo o contraseña incorrectos.', 'danger')
            return redirect(url_for('auth.login'))

        if not usuario.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(usuario)
        return redirect(url_for('index'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))