from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql
from datetime import datetime
import pytz

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

# Ruta para manejar el inicio de sesión
@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    username = data.get('username')
    password = data.get('contraseña')

    # Conectar a la base de datos
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # Consulta para verificar el usuario y la contraseña
            sql = "SELECT * FROM empleados WHERE emp_nombre = %s AND emp_contrasenia = %s"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()

            if result:
                # Obtener la hora local de México Centro
                tz = pytz.timezone('America/Mexico_City')
                hora_actual = datetime.now(tz).hour

                if 5 <= hora_actual < 12:
                    saludo = '¡Buenos días ' + username + ' !'
                elif 12 <= hora_actual < 19:
                    saludo = '¡Buenas tardes ' + username + ' !'
                else:
                    saludo = '¡Buenas noches ' + username + ' !'

                return jsonify({'message': f'{saludo} , ¡Bienvenido!'}), 200
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


@app.route('/produccion.html')
def produccion():
    return render_template('produccion.html')

@app.route('/ventas.html')
def ventas():
    return render_template('ventas.html')

@app.route('/limpieza.html')
def limpieza():
    return render_template('limpieza.html')


@app.route('/limDia.html')
def limDia():
    return render_template('limDia.html')

@app.route('/limCalendario.html')
def limCalendario():
    return render_template('limCalendario.html')




if __name__ == '__main__':
    app.run(debug=True)