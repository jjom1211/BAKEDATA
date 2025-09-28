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
    return render_template('login.html')
    # Conectar a la base de datos
@app.route('/login', methods=['POST'])
def handle_login():
    data = request.json
    correo = data.get('correo')
    password = data.get('contraseña')

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtener usuario y rol principal
            sql = "SELECT emp_id, emp_nombre, emp_rol_principal FROM empleados WHERE emp_correo = %s AND emp_contrasenia = %s"
            cursor.execute(sql, (correo, password))
            empleado = cursor.fetchone()

            if not empleado:
                return jsonify({'error': 'Usuario o contraseña no válidos'}), 401

            emp_id = empleado['emp_id']
            nombre = empleado['emp_nombre']
            rol_principal = empleado['emp_rol_principal']

            # Buscar roles secundarios en tabla roles
            cursor.execute("SELECT rolemp FROM roles_empleados WHERE rolemp_emp_fk = %s", (emp_id,))
            rol_registro = cursor.fetchone()
            if rol_registro and rol_registro['rolemp']:
                try:
                    import json
                    roles_extra = json.loads(rol_registro['rolemp'])
                    if not isinstance(roles_extra, list):
                        roles_extra = [roles_extra]
                except:
                    roles_extra = []
            else:
                roles_extra = []

            # Si no hay roles extra, usar solo el principal
            roles_finales = roles_extra if roles_extra else [rol_principal]

            # Saludo según hora
            from datetime import datetime
            import pytz
            tz = pytz.timezone('America/Mexico_City')
            hora_actual = datetime.now(tz).hour
            if 5 <= hora_actual < 12:
                saludo = f'¡Buenos días {nombre}!'
            elif 12 <= hora_actual < 19:
                saludo = f'¡Buenas tardes {nombre}!'
            else:
                saludo = f'¡Buenas noches {nombre}!'

            return jsonify({
                'message': f'{saludo} , ¡Bienvenido!',
                'rol_principal': rol_principal,
                'roles': roles_finales
            }), 200
    finally:
        conn.close()

#____________________________________________#
# INICIO ENPOINT LIMPIEZA

@app.route('/limpieza')
def limpieza():
    return render_template('limpieza.jinja2')
@app.route("/limDia")
def ver_limpieza_dia():
    fecha = datetime.now(pytz.timezone("America/Mexico_City")).strftime('%Y-%m-%d 00:00:00')
    connection = pymysql.connect(**db_config)
    #Conexion para obtener las actividades existentes en la base de datos
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("""
            SELECT l.lim_actividad AS actividades_limpieza,
            ld.limdia_act_estado
            FROM limpieza_dia ld
            JOIN limpieza l ON ld.limdia_lim_fk = l.lim_id
            WHERE ld.limdia_limcal_fecha = %s
        """, (fecha,))
        actividades = cursor.fetchall() #Captura todos los elementos encontrados dentro de una lista
    connection.close()
    return render_template("limDia.jinja2", actividades=actividades) #Manda las actividades a un render de otro recurso
    """
    FUNCIONALIDAD DENTRO DE: LIMPIEZA DEL DIA
    
    Confirma actividades de limpieza marcadas como completadas (estado 'C').
    Actualiza el estado en la tabla `limpieza_dia` usando la fecha actual.
    
    """
@app.route('/confirmarLimpieza', methods=['POST'])
def confirmar_actividades():
    datos = request.get_json()
    actividades = datos.get("actividades", [])
    #Si no se selecciona nada
    if not actividades:
        return jsonify({"message": "No se seleccionó ninguna actividad"}), 400
    # Obtener la fecha actual con hora 00:00:00
    fecha = datetime.now(pytz.timezone("America/Mexico_City")).strftime('%Y-%m-%d 00:00:00')
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        # 1. Buscar los lim_id correspondientes a las actividades seleccionadas
        placeholders = ','.join(['%s'] * len(actividades))
        query_ids = f"""
            SELECT lim_id 
            FROM limpieza 
            WHERE lim_actividad IN ({placeholders})
        """
        cursor.execute(query_ids, actividades)
        ids_limpieza = [row[0] for row in cursor.fetchall()]#dentro del fetch (como tabla temporal) toma la primera fila (el ID)
        #Si no se encuentran actividades en la base de datos
        if not ids_limpieza:
            return jsonify({"message": "No se encontraron actividades válidas"}), 400
        # 2. Actualizar limpieza_dia con esos lim_id y la fecha actual
        placeholders_ids = ','.join(['%s'] * len(ids_limpieza)) #se aplica un REGEX para construir una lista con los IDs separados con comas
        query_update = f"""
            UPDATE limpieza_dia 
            SET limdia_act_estado = 'C' 
            WHERE limdia_limcal_fecha = %s 
            AND limdia_lim_fk IN ({placeholders_ids}) 
        """ #En base a las actividades seleccionadas se utilizan los campos para actualizar
        cursor.execute(query_update, [fecha] + ids_limpieza)
        connection.commit()
        return jsonify({"message": "Actividades actualizadas correctamente"}) #Si se pudo actualizar en BD
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Ocurrió un error al actualizar actividades"}), 500 #Si no se pudo actualizar en BD
    finally:
        connection.close()
    """
    FUNCIONALIDAD DENTRO DE: REGISTRAR LIMPIEZA DEL DIA
    Muestra una lista de todas las actividades de limpieza disponibles 
    para que el encargado seleccione cuáles se programarán.
    """
@app.route('/limRegistrarLimpieza')
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
        actividades_limpieza = [] #Excepcion para evitar desbordamiento, se manda una lista vacia si no hay coincidencias
    finally:
        connection.close()
    return render_template('limRegistrarLimpieza.jinja2', actividades_limpieza=actividades_limpieza) #Se envia la lista de actividades de la BD junto con el render del recurso
    """
    FUNCIONALIDAD DENTRO DE: REGISTRAR LIMPIEZA DEL DIA
    Registra las actividades seleccionadas para la fecha actual.
    Verifica si la fecha ya existe en el calendario, la inserta si no.
    Luego registra las actividades si aún no han sido registradas.
    """
@app.route('/registrar_limpieza', methods=['POST'])
def registrar_limpieza():
    data = request.get_json()
    actividades = data.get('actividades', [])
    fecha = datetime.now(pytz.timezone('America/Mexico_City')).strftime('%Y-%m-%d 00:00:00')
    ya_registradas = []
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # Verificar si ya existe el día en limpieza_calendario
            cursor.execute("SELECT 1 FROM limpieza_calendario WHERE limcal_fecha = %s", (fecha,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO limpieza_calendario (limcal_fecha) VALUES (%s)", (fecha,))
            # Insertar actividades si no existen ya para esa fecha
            for actividad in actividades:
                cursor.execute("SELECT lim_id FROM limpieza WHERE lim_actividad = %s", (actividad,))
                id_result = cursor.fetchone()
                if id_result:
                    lim_id = id_result[0]
                    # Verificar si ya existe en limpieza_dia
                    cursor.execute("""
                        SELECT 1 FROM limpieza_dia 
                        WHERE limdia_limcal_fecha = %s AND limdia_lim_fk = %s
                    """, (fecha, lim_id))
                    if cursor.fetchone():
                        ya_registradas.append(actividad)
                        continue  # No insertar duplicados
                    # Insertar si no existe
                    else:
                        cursor.execute("""
                        INSERT INTO limpieza_dia (limdia_limcal_fecha, limdia_lim_fk, limdia_act_estado)
                        VALUES (%s, %s, 'N')
                    """, (fecha, lim_id))
            connection.commit()
        if ya_registradas:
            return jsonify({
                'mensaje': 'Registro parcial exitoso',
                'advertencia': 'Algunas actividades ya estaban registradas para hoy.',
                'omitidas': ya_registradas
            }), 200
        else:
            return jsonify({'mensaje': 'Registro exitoso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
    """
    FUNCIONALIDAD DENTRO DE: CALENDARIO
    Muestra las fechas disponibles en el calendario de limpieza
    en las que se han registrado actividades.
    """
@app.route('/limCalendario')
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

    """
    FUNCIONALIDAD DENTRO DE: CALENDARIO
    Devuelve en formato JSON las actividades de limpieza 
    registradas para una fecha específica, incluyendo su estado.
    """
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
            resultado = [{'actividad': t[0], 'estado': t[1]} for t in tareas] #Toma de la pseudotabla los valores de la primera y segunda fila
            return jsonify(resultado)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500 #Si hay errores de conexion a la BD
    finally:
        connection.close()
        
    """
    FUNCIONALIDAD DENTRO DE: ACTUALIZAR FECHA DE LIMPIEZA
    Actualizacion para añadir, cambiar o modificar una fecha o registro de limpieza
    dentro de un calendario
    """
    
@app.route('/limActualizarFechaLimpieza')
def limActualizarFechaLimpieza():
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
    return render_template('limActualizarFechaLimpieza.jinja2', dias_limpieza=dias_limpieza,actividades_limpieza = actividades_limpieza)

    """
    FUNCIONALIDAD DENTRO DE: ACTUALIZAR FECHA DE LIMPIEZA
    Actualizacion de las tareas, como agregar, eliminar o cambiar estados de las mismas
    """
@app.route('/actualizar_tareas', methods=['POST'])
def actualizar_tareas():
    data = request.get_json()
    fecha_str = data.get("fecha")
    tareas = data.get("tareas", [])
    if not fecha_str:
        return jsonify({"status": "error", "message": "Falta la fecha (YYYY-MM-DD)."}), 400
    fecha = f"{fecha_str} 00:00:00"  # normalizamos a DATETIME
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 🔹 Garantiza que exista el registro de fecha en limpieza_calendario
            cursor.execute("SELECT 1 FROM limpieza_calendario WHERE limcal_fecha = %s", (fecha,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO limpieza_calendario (limcal_fecha, limcal_estado) VALUES (%s, %s)",
                    (fecha, 'N')
                )
            # 🔹 Actualiza/Inserta cada tarea
            for t in tareas:
                actividad = t.get("actividad")
                estado = t.get("estado", "N")
                if not actividad:
                    continue
                # Busca el ID en limpieza
                cursor.execute("SELECT lim_id FROM limpieza WHERE lim_actividad = %s", (actividad,))
                row = cursor.fetchone()
                if not row:
                    continue
                lim_id = row[0]
                # Verifica si ya existe para la fecha
                cursor.execute("""
                    SELECT 1
                    FROM limpieza_dia
                    WHERE limdia_limcal_fecha = %s AND limdia_lim_fk = %s
                """, (fecha, lim_id))
                if cursor.fetchone():
                    # Actualiza
                    cursor.execute("""
                        UPDATE limpieza_dia
                        SET limdia_act_estado = %s
                        WHERE limdia_limcal_fecha = %s AND limdia_lim_fk = %s
                    """, (estado, fecha, lim_id))
                else:
                    # Inserta
                    cursor.execute("""
                        INSERT INTO limpieza_dia (limdia_limcal_fecha, limdia_lim_fk, limdia_act_estado)
                        VALUES (%s, %s, %s)
                    """, (fecha, lim_id, estado))
            connection.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error en /actualizar_tareas: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        connection.close()
        
        
# __________________________________________________________
# INICIO ENDPOINT PRODUCCION

@app.route('/gerente')
def gerente():
    return render_template('gerente.jinja2')

@app.route('/usuario')
def usuario():
    return render_template('usuario.jinja2')

@app.route('/almacen')
def almacen():
    return render_template('almacen.jinja2')

@app.route('/reparto')
def reparto():
    return render_template('reparto.jinja2')

@app.route('/CalendarioReparto')
def repCalendario():
    return render_template('repCalendario.jinja2')

@app.route('/Pedidos')
def repPedidos():
    return render_template('repPedidos.jinja2')

@app.route('/produccion')
def produccion():
    return render_template('produccion.jinja2')

@app.route('/ventas')
def ventas():
    return render_template('ventas.jinja2')

@app.route('/reportes')
def reportes():
    return render_template('reportes.jinja2')

@app.route('/encargado')
def encargado():
    return render_template('encargado.jinja2')

if __name__ == '__main__':
    app.run(debug=True)