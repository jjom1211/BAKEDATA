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
    return render_template('limpieza.jinja2')

@app.route('/limDia.html')
def limDia():
    return render_template('limDia.html')


@app.route('/limRegistrarLimpieza.jinja2')
def limRegistrarLimpieza():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            query = "SELECT lim_actividad FROM limpieza"
            cursor.execute(query)
            resultados = cursor.fetchall()
            actividades_limpieza = [fila[0] for fila in resultados]
    except Exception as e:
        print(f"Error: {e}")
        actividades_limpieza = []
    finally:
        connection.close()
    return render_template('limRegistrarLimpieza.jinja2', actividades_limpieza=actividades_limpieza)


@app.route('/limCalendario.jinja2')
def limCalendario():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            query = "SELECT DATE(limcal_fecha) FROM limpieza_calendario"
            cursor.execute(query)
            resultados = cursor.fetchall()
            dias_limpieza = [fila[0].strftime('%Y-%m-%d') for fila in resultados]
    except Exception as e:
        print(f"Error: {e}")
        dias_limpieza = []
    finally:
        connection.close()
    return render_template('limCalendario.jinja2', dias_limpieza=dias_limpieza)


@app.route('/tareas_por_fecha/<fecha>', methods=['GET'])
def tareas_por_fecha(fecha):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    l.lim_actividad,
                    ld.limdia_act_estado
                FROM 
                    limpieza_dia ld
                JOIN 
                    limpieza l ON ld.limdia_lim_fk = l.lim_id
                WHERE 
                    ld.limdia_limcal_fecha = %s
            """
            cursor.execute(query, (fecha,))
            tareas = cursor.fetchall()
            resultado = [{'actividad': t[0], 'estado': t[1]} for t in tareas]
            return jsonify(resultado)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Rutas para servir archivos estáticos
@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    return send_from_directory('JS', filename)

if __name__ == '__main__':
    app.run(debug=True)