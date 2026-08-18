import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, Usuario
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 15


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip().lower()
        contrasena = request.form.get('contrasena', '')

        if len(nombre) < 3:
            flash('El nombre debe tener al menos 3 caracteres.', 'danger')
            return redirect(url_for('auth.registro'))

        if not re.match(EMAIL_REGEX, email):
            flash('Ingresa un correo electrónico válido.', 'danger')
            return redirect(url_for('auth.registro'))

        if len(contrasena) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'danger')
            return redirect(url_for('auth.registro'))

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Ese correo ya está registrado.', 'danger')
            return redirect(url_for('auth.registro'))

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

        # Cuenta bloqueada temporalmente
        if usuario and usuario.bloqueado_hasta and usuario.bloqueado_hasta > datetime.utcnow():
            minutos_restantes = int((usuario.bloqueado_hasta - datetime.utcnow()).total_seconds() / 60) + 1
            flash(f'Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta de nuevo en {minutos_restantes} minuto(s).', 'danger')
            return redirect(url_for('auth.login'))

        if not usuario or not bcrypt.check_password_hash(usuario.contrasena, contrasena):
            if usuario:
                usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
                if usuario.intentos_fallidos >= MAX_INTENTOS:
                    usuario.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=MINUTOS_BLOQUEO)
                    db.session.commit()
                    flash(f'Demasiados intentos fallidos. Cuenta bloqueada por {MINUTOS_BLOQUEO} minutos.', 'danger')
                    return redirect(url_for('auth.login'))
                db.session.commit()
            flash('Correo o contraseña incorrectos.', 'danger')
            return redirect(url_for('auth.login'))

        if not usuario.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.login'))

        # Login exitoso: resetear contador
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        db.session.commit()

        login_user(usuario)
        return redirect(url_for('index'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))