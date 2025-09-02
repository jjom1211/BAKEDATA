from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql
from datetime import datetime
import pytz

#Inicializacion de la aplicación de los endpoints
app = Flask(__name__, template_folder='HTML')

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata',
    'db': 'mydb'
}

# Ruta para mostrar el formulario de inicio de sesión
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    correo = data.get('correo')
    password = data.get('contraseña')

    # Conectar a la base de datos
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Consulta: trae nombre y rol principal
            sql = "SELECT emp_nombre, emp_rol_principal FROM empleados WHERE emp_correo = %s AND emp_contrasenia = %s"
            cursor.execute(sql, (correo, password))
            result = cursor.fetchone()

            if result:
                nombre = result['emp_nombre']
                rol_principal = result['emp_rol_principal']

                # Saludo según hora
                tz = pytz.timezone('America/Mexico_City')
                hora_actual = datetime.now(tz).hour
                if 5 <= hora_actual < 12:
                    saludo = f'¡Buenos días {nombre}!'
                elif 12 <= hora_actual < 19:
                    saludo = f'¡Buenas tardes {nombre}!'
                else:
                    saludo = f'¡Buenas noches {nombre}!'

                # Retorna nombre y rol principal al frontend
                return jsonify({'message': f'{saludo} , ¡Bienvenido!',
                                'rol_principal': rol_principal}), 200
            else:
                return jsonify({'error': 'Usuario o contraseña no válidos'}), 401
    finally:
        conn.close()

# Rutas para servir archivos estáticos
@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    return send_from_directory('JS', filename)

@app.route('/gerente.html')
def gerente():
    return render_template('gerente.html')

@app.route('/usuario.html')
def usuario():
    return render_template('usuario.html')

@app.route('/almacen.html')
def almacen():
    return render_template('almacen.html')

@app.route('/reparto.html')
def reparto():
    return render_template('reparto.html')

@app.route('/repCalendario.html')
def repCalendario():
    return render_template('repCalendario.html')


@app.route('/register.html')
def registro():
    return render_template('register.html')

@app.route('/produccion.html')
def produccion():
    return render_template('produccion.html')

@app.route('/ventas.html')
def ventas():
    return render_template('ventas.html')

@app.route('/limpieza.jinja2')
def limpieza():
    return render_template('limpieza.jinja2')


@app.route('/limDia.html')
def limDia():
    return render_template('limDia.html')

@app.route('/limCalendario.jinja2')
def limCalendario():
    return render_template('limCalendario.jinja2')

@app.route('/limRegistrarLimpieza.jinja2')
def limRegistrarLimpieza():
    return render_template('limRegistrarLimpieza.jinja2')

@app.route('/limActualizarFechaLimpieza.jinja2')
def limActualizarFechaLimpieza():
    return render_template('limActualizarFechaLimpieza.jinja2')

if __name__ == '__main__':
    app.run(debug=True)