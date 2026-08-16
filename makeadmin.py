from app import app, db
from models import Usuario

correos_admin = [
    'polg9599@gmail.com',
    'johangelrodriguez162@gmail.com',
]

with app.app_context():
    for correo in correos_admin:
        usuario = Usuario.query.filter_by(email=correo).first()
        if usuario:
            usuario.rol = 'administrador'
            db.session.commit()
            print('Listo:', usuario.nombre, '-', usuario.rol)
        else:
            print(f'No se encontró ningún usuario con el correo {correo}. Verifica que ya se haya registrado en /registro.')