from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pymysql
from datetime import date, datetime
import pytz

#Inicializacion de la aplicación de los endpoints
app = Flask(__name__, template_folder='HTML')
# IMPORTANTE: Establece una llave secreta.
# ¡Cámbiala por una cadena de texto larga, aleatoria y secreta!
app.secret_key = 'esta-es-una-llave-muy-secreta-y-debes-cambiarla'

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata',
    'db': 'mydb'
}
# Rutas para servir archivos estáticos
@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    return send_from_directory('JS', filename)

# Ruta para mostrar el formulario de inicio de sesión
@app.route('/')
def login():
    return render_template('login.jinja2')
    # Conectar a la base de datos
@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    correo = data.get('correo')
    password = data.get('contraseña')
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Buscamos al empleado SOLO por su correo
            sql = "SELECT emp_id, emp_nombre, emp_rol_principal, emp_sucursal, emp_contrasenia FROM empleados WHERE emp_correo = %s"
            cursor.execute(sql, (correo,))
            empleado = cursor.fetchone()
            if not empleado:
                return jsonify({'error': 'Usuario no encontrado'}), 401
            # 2. Verificamos si el empleado existe Y si la contraseña hasheada coincide
            if not check_password_hash(empleado['emp_contrasenia'], password):
                # Si no existe o la contraseña no coincide, es un error
                return jsonify({'error': 'Contraseña Incorrecta'}), 401
            # --- INICIO DE LA MODIFICACIÓN ---
            # Limpiamos cualquier sesión anterior por seguridad
            session.clear()
            # Guardamos los datos del empleado en la sesión
            session['emp_id'] = empleado['emp_id']
            session['nombre'] = empleado['emp_nombre']
            session['sucursal'] = empleado['emp_sucursal'] # Muy útil para tus filtros
            emp_id = empleado['emp_id']
            rol_principal = empleado['emp_rol_principal']
            # Buscamos roles adicionales en la tabla empleados_roles
            # 1. Usamos un 'set' para guardar el rol principal (evita duplicados)
            roles_finales = {rol_principal}
            # 2. Buscamos todos los roles adicionales en la tabla 'empleados_roles'
            cursor.execute("SELECT emprol_rol_fk FROM empleados_roles WHERE emprol_emp_fk = %s", (emp_id,))
            roles_adicionales = cursor.fetchall() # Esto devuelve una lista de diccionarios
            # 3. Añadimos los roles adicionales al set
            if roles_adicionales:
                for rol in roles_adicionales:
                    roles_finales.add(rol['emprol_rol_fk'])
            # 4. Convertimos el set a una lista para guardarla en la sesión
            lista_roles_finales = list(roles_finales)
            # 5. Guardamos la lista COMPLETA de roles en la sesión
            session['roles'] = lista_roles_finales
            # Saludo según hora
            tz = pytz.timezone('America/Mexico_City')
            hora_actual = datetime.now(tz).hour
            if 5 <= hora_actual < 12:
                saludo = f'¡Buenos días {empleado['emp_nombre']}!'
            elif 12 <= hora_actual < 19:
                saludo = f'¡Buenas tardes {empleado['emp_nombre']}!'
            else:
                saludo = f'¡Buenas noches {empleado['emp_nombre']}!'
            return jsonify({
                'message': f'{saludo} , ¡Bienvenido!',
                'rol_principal': rol_principal,
                'roles': lista_roles_finales
            }), 200
    finally:
        conn.close()
