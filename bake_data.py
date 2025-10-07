from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for
import pymysql
from datetime import date, datetime
import pytz
import json

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
            sql = "SELECT emp_id, emp_nombre, emp_rol_principal, emp_sucursal FROM empleados WHERE emp_correo = %s AND emp_contrasenia = %s"
            cursor.execute(sql, (correo, password))
            empleado = cursor.fetchone()
            if not empleado:
                return jsonify({'error': 'Usuario o contraseña no válidos'}), 401
            # --- INICIO DE LA MODIFICACIÓN ---
            # Limpiamos cualquier sesión anterior por seguridad
            session.clear()
            # Guardamos los datos del empleado en la sesión
            session['emp_id'] = empleado['emp_id']
            session['nombre'] = empleado['emp_nombre']
            session['sucursal'] = empleado['emp_sucursal'] # Muy útil para tus filtros
            emp_id = empleado['emp_id']
            rol_principal = empleado['emp_rol_principal']
            # Buscar roles secundarios en tabla roles
            cursor.execute("SELECT rolemp FROM roles_empleados WHERE rolemp_emp_fk = %s", (emp_id,))
            rol_registro = cursor.fetchone()
            roles_extra = []
            if rol_registro and rol_registro['rolemp']:
                try:
                    roles_extra = json.loads(rol_registro['rolemp'])
                except:
                    roles_extra = []
            # Si no hay roles extra, usar solo el principal
            roles_finales = roles_extra if roles_extra else [rol_principal]
            # Guardamos también los roles en la sesión
            session['roles'] = roles_finales
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


# __________________________________________________________
# INICIO ENDPOINT REPARTO
@app.route('/reparto')
def reparto():
    return render_template('reparto.jinja2')

@app.route('/CalendarioReparto')
def repCalendario():
    calendario_status = {}
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Obtenemos TODOS los eventos (pedidos y repartos) con su estado
            query = """
                (SELECT DATE(ped_fecha_pedido) as event_date, ped_estado_pedido as event_status FROM pedidos)
                UNION ALL
                (SELECT DATE(rep_fecha_entrega) as event_date, UPPER(rep_estado_reparto) as event_status FROM repartos)
            """
            cursor.execute(query)
            todos_los_eventos = cursor.fetchall()
            
            # 2. Agrupamos los eventos por día
            eventos_por_dia = {}
            for evento in todos_los_eventos:
                fecha_str = evento['event_date'].strftime('%Y-%m-%d')
                if fecha_str not in eventos_por_dia:
                    eventos_por_dia[fecha_str] = []
                eventos_por_dia[fecha_str].append(evento['event_status'])
            
            # 3. Analizamos cada día para asignarle un color de semáforo
            hoy = date.today()
            for fecha_str, estados in eventos_por_dia.items():
                fecha_evento = date.fromisoformat(fecha_str)
                es_dia_pasado = fecha_evento < hoy

                # Verificamos si hay alguna tarea pendiente ('P' o 'R')
                hay_pendientes = any(estado in ['P', 'R'] for estado in estados)
                
                # Verificamos si TODAS las tareas están completas ('C' para pedidos, 'E' para repartos)
                todas_completas = all(estado in ['C', 'E', 'X'] for estado in estados)

                if es_dia_pasado and hay_pendientes:
                    calendario_status[fecha_str] = 'rojo' # 🔴
                elif todas_completas:
                    calendario_status[fecha_str] = 'verde' # 🟢
                else:
                    calendario_status[fecha_str] = 'amarillo' # 🟡

    except Exception as e:
        print(f"Error al generar calendario: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
    
    return render_template('repCalendario.jinja2', calendario_status=calendario_status)


@app.route('/repartos_por_fecha/<fecha>', methods=['GET'])
def repartos_por_fecha(fecha):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT 
                    r.rep_id,
                    r.rep_estado_reparto,
                    p.ped_asunto,
                    p.ped_monto_total,
                    s.suc_nombre AS sucursal_destino_nombre
                FROM 
                    repartos r
                JOIN pedidos p ON r.rep_ped_id = p.ped_id
                LEFT JOIN sucursales s ON r.rep_suc_destino = s.suc_id
                WHERE 
                    r.rep_fecha_entrega = %s
            """
            cursor.execute(query, (fecha,))
            repartos = cursor.fetchall()
            return jsonify(repartos) # Podemos devolverlo directamente
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


@app.route('/pedidos_por_fecha/<fecha>', methods=['GET'])
def pedidos_por_fecha(fecha):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT 
                    p.ped_id,
                    p.ped_asunto, -- AÑADIDO
                    p.ped_estado_pedido,
                    p.ped_monto_total, -- AÑADIDO
                    s.suc_nombre AS sucursal_destino_nombre
                FROM 
                    pedidos p
                LEFT JOIN sucursales s ON p.ped_sucursal_destino = s.suc_id
                WHERE 
                    p.ped_fecha_pedido = %s
            """
            cursor.execute(query, (fecha,))
            pedidos = cursor.fetchall()
            return jsonify(pedidos) # Devolvemos la lista directamente
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            

@app.route('/Pedidos')
def repPedidos():
    if 'emp_id' not in session:
        # Para renderizar una página, es mejor redirigir al login
        return redirect(url_for('login')) 
    
    emp_id = session['emp_id']
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor: # Usar DictCursor es más limpio
            
            cursor.execute("SELECT emp_sucursal FROM empleados WHERE emp_id = %s", (emp_id,))
            empleado = cursor.fetchone()
            if not empleado:
                return "Empleado no encontrado", 404
            sucursal_origen_empleado = empleado['emp_sucursal']
            # Unimos (JOIN) pedidos con sucursales para obtener el nombre del destino
            query = """
                SELECT 
                    p.ped_id, 
                    p.ped_fecha_pedido, 
                    p.ped_monto_total,
                    s.suc_nombre AS sucursal_destino_nombre, -- Obtenemos el nombre y le ponemos un alias
                    p.ped_asunto, 
                    p.ped_comentarios
                FROM 
                    pedidos p
                JOIN 
                    sucursales s ON p.ped_sucursal_destino = s.suc_id
                WHERE 
                    p.ped_sucursal_origen = %s
                ORDER BY 
                    p.ped_fecha_pedido DESC
            """
            cursor.execute(query, (sucursal_origen_empleado,))
            lista_pedidos = cursor.fetchall()
            
            # ¡CAMBIO IMPORTANTE! Pasamos la lista a la plantilla
            return render_template('repPedidos.jinja2', pedidos=lista_pedidos)

    except Exception as e:
        print(f"Error en la base de datos: {e}")
        return "Error interno del servidor", 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@app.route('/Pedidos/<int:pedido_id>')
def api_detalle_pedido(pedido_id):
    if 'emp_id' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    connection = None  # Definir fuera para acceso en 'finally'
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Consulta principal (esta ya estaba bien)
            query = """
                SELECT 
                    p.*,
                    s_origen.suc_nombre as sucursal_origen_nombre,
                    s_destino.suc_nombre as sucursal_destino_nombre,
                    s_destino.suc_direccion as sucursal_destino_direccion,
                    COALESCE(e.emp_nombre, u.usu_nombre, 'Sistema') AS creador_nombre
                FROM pedidos p
                LEFT JOIN sucursales s_origen ON p.ped_sucursal_origen = s_origen.suc_id
                LEFT JOIN sucursales s_destino ON p.ped_sucursal_destino = s_destino.suc_id
                LEFT JOIN empleados e ON p.ped_emp_id = e.emp_id
                LEFT JOIN usuarios u ON p.ped_usu_id = u.usu_id
                WHERE p.ped_id = %s
            """
            cursor.execute(query, (pedido_id,))
            pedido_detalle = cursor.fetchone()

            if not pedido_detalle:
                return jsonify({'error': 'Pedido no encontrado'}), 404

            # --- NUEVA LÓGICA PARA AÑADIR PRODUCTOS Y MATERIAS PRIMAS ---
            
            # 1. Buscar productos asociados al pedido
            query_productos = """
                SELECT dp.detpedpro_cantidad, p.pro_nombre 
                FROM detalle_pedido_productos dp 
                JOIN productos p ON dp.detpedpro_pro_id = p.pro_id 
                WHERE dp.detpedpro_ped_id = %s
            """
            cursor.execute(query_productos, (pedido_id,))
            productos = cursor.fetchall()
            pedido_detalle['productos'] = productos  # Añadimos la lista al resultado

            # 2. Buscar materias primas asociadas al pedido
            query_materias_primas = """
                SELECT dm.detpedmat_cantidad, mp.matprim_nombre 
                FROM detalle_pedido_materias_primas dm 
                JOIN materias_primas mp ON dm.detpedmat_matprim_id = mp.matprim_id 
                WHERE dm.detpedmat_ped_id = %s
            """
            cursor.execute(query_materias_primas, (pedido_id,))
            materias_primas = cursor.fetchall()
            pedido_detalle['materias_primas'] = materias_primas # Añadimos la lista al resultado
            
            # --- FIN DE LA NUEVA LÓGICA ---

            # Formatear la fecha y el monto
            pedido_detalle['ped_fecha_pedido'] = pedido_detalle['ped_fecha_pedido'].strftime('%Y-%m-%d')
            pedido_detalle['ped_monto_total'] = float(pedido_detalle['ped_monto_total'])
            
            return jsonify(pedido_detalle)

    except Exception as e:
        print(f"Error en la API de detalle de pedido: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@app.route("/repDia")
def ver_repartos_dia():
    connection = pymysql.connect(**db_config)
    #Conexion para obtener las actividades existentes en la base de datos
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("""
        SELECT
            r.rep_id,
            r.rep_estado_reparto,
            p.ped_id,
            p.ped_asunto,
            p.ped_comentarios,
            p.ped_monto_total,
            suc_origen.suc_nombre AS sucursal_origen,
            suc_destino.suc_nombre AS sucursal_destino
            -- Puedes agregar aquí el JOIN con la tabla de usuarios si necesitas el nombre del cliente
        FROM
            repartos r
        JOIN
            pedidos p ON r.rep_ped_id = p.ped_id
        LEFT JOIN
            sucursales suc_origen ON r.rep_suc_origen = suc_origen.suc_id
        LEFT JOIN
            sucursales suc_destino ON r.rep_suc_destino = suc_destino.suc_id
        WHERE
            r.rep_fecha_entrega = CURDATE()
        """)
        pedidos = cursor.fetchall() #Captura todos los elementos encontrados dentro de una lista
    connection.close()
    return render_template("repDia.jinja2", pedidos=pedidos) #Manda las actividades a un render de otro recurso

@app.route("/detalles_reparto/<int:rep_id>")
def detalles_reparto(rep_id):
    """
    Devuelve los detalles completos de un solo reparto en formato JSON.
    """
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Una consulta más detallada para un solo reparto
            query = """
                SELECT
                    r.rep_id,
                    r.rep_estado_reparto,
                    r.rep_fecha_entrega,
                    p.ped_id,
                    p.ped_asunto,
                    p.ped_comentarios,
                    p.ped_monto_total,
                    p.ped_fecha_pedido,
                    suc_origen.suc_nombre AS sucursal_origen,
                    suc_destino.suc_nombre AS sucursal_destino,
                    suc_destino.suc_direccion AS sucursal_destino_direccion -- --- LÍNEA AÑADIDA ---
                FROM repartos r
                JOIN pedidos p ON r.rep_ped_id = p.ped_id
                LEFT JOIN sucursales suc_origen ON r.rep_suc_origen = suc_origen.suc_id
                LEFT JOIN sucursales suc_destino ON r.rep_suc_destino = suc_destino.suc_id
                WHERE r.rep_id = %s;
            """
            cursor.execute(query, (rep_id,))
            reparto_details = cursor.fetchone()
            if reparto_details:
                pedido_id = reparto_details['ped_id']
                # Buscar productos del pedido
                cursor.execute("""
                    SELECT dp.detpedpro_cantidad, p.pro_nombre 
                    FROM detalle_pedido_productos dp JOIN productos p ON dp.detpedpro_pro_id = p.pro_id 
                    WHERE dp.detpedpro_ped_id = %s
                """, (pedido_id,))
                productos = cursor.fetchall()
                reparto_details['productos'] = productos

                # Buscar materias primas del pedido (si aplica)
                cursor.execute("""
                    SELECT dm.detpedmat_cantidad, mp.matprim_nombre 
                    FROM detalle_pedido_materias_primas dm JOIN materias_primas mp ON dm.detpedmat_matprim_id = mp.matprim_id 
                    WHERE dm.detpedmat_ped_id = %s
                """, (pedido_id,))
                materias_primas = cursor.fetchall()
                reparto_details['materias_primas'] = materias_primas
                if reparto_details.get('rep_fecha_entrega'):
                    reparto_details['rep_fecha_entrega'] = reparto_details['rep_fecha_entrega'].strftime('%d-%m-%Y')
                if reparto_details.get('ped_fecha_pedido'):
                    reparto_details['ped_fecha_pedido'] = reparto_details['ped_fecha_pedido'].strftime('%d-%m-%Y')
                return jsonify(reparto_details)
            else:
                return jsonify({"error": "Reparto no encontrado"}), 404
    except Exception as e:
        print(f"Error en detalles_reparto: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if connection:
            connection.close()


@app.route('/confirmar_entregas', methods=['POST'])
def confirmar_entregas():
    datos = request.get_json()
    # Los IDs que recibes son de los pedidos, no de los repartos directamente
    pedidos_ids = datos.get("pedidos", [])
    if not pedidos_ids:
        return jsonify({"message": "No se seleccionó ningún pedido para confirmar"}), 400
    connection = None  # Definir fuera del try para que esté disponible en finally
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        # Preparamos el formato para la cláusula IN (...), ej: '%s,%s,%s'
        placeholders = ','.join(['%s'] * len(pedidos_ids))
        # Usamos una transacción para asegurar la integridad de los datos.
        # O se actualizan ambas tablas, o no se actualiza ninguna.
        connection.begin()
        # 1. Actualizar la tabla 'repartos'
        # Se actualiza el estado de los repartos asociados a los pedidos seleccionados.
        query_update_repartos = f"""
            UPDATE repartos
            SET rep_estado_reparto = 'E'
            WHERE rep_ped_id IN ({placeholders})
        """
        cursor.execute(query_update_repartos, pedidos_ids)
        # 2. Actualizar la tabla 'pedidos'
        # También se actualiza el estado de los pedidos originales.
        query_update_pedidos = f"""
            UPDATE pedidos
            SET ped_estado_pedido = 'C'
            WHERE ped_id IN ({placeholders})
        """
        cursor.execute(query_update_pedidos, pedidos_ids)
        # Si todo salió bien, confirmamos los cambios en la base de datos
        connection.commit()
        return jsonify({"message": "Entregas confirmadas correctamente"})
    except Exception as e:
        # Si ocurre cualquier error, revertimos todos los cambios
        if connection:
            connection.rollback()
        print("Error en la base de datos:", e)
        return jsonify({"message": "Ocurrió un error al confirmar las entregas"}), 500
    finally:
        if connection:
            connection.close()


@app.route('/agregarRepartos')
def vistaAgregarRepartos():
    """
    Muestra la página con la lista de pedidos listos para ser enviados.
    """
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor) # Usamos DictCursor para manejarlo como diccionario
        query = """
            SELECT * FROM pedidos p
            WHERE p.ped_estado_pedido = 'P' -- O el estado que uses para 'Pendiente'/'Aprobado'
            AND NOT EXISTS (
                SELECT 1 FROM repartos r WHERE r.rep_ped_id = p.ped_id
            );
        """
        cursor.execute(query)
        pedidos_pendientes = cursor.fetchall()
        # Renderiza la plantilla HTML y le pasa la lista de pedidos
        return render_template('repAgregarRepartos.jinja2', pedidos=pedidos_pendientes)

    except Exception as e:
        print(f"Error al obtener pedidos pendientes: {e}")
        # Aquí podrías redirigir a una página de error
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()


@app.route('/crear_reparto', methods=['POST'])
def crear_reparto():
    """
    Recibe una lista de IDs de pedidos y crea un registro en la tabla 'repartos' para cada uno.
    """
    datos = request.get_json()
    pedidos_ids = datos.get("pedidos", [])
    if not pedidos_ids:
        return jsonify({"message": "No se seleccionó ningún pedido"}), 400
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        # Iniciamos una transacción
        connection.begin()
        for ped_id in pedidos_ids:
            # 1. Insertar el nuevo reparto en la tabla 'repartos'
            query_insert = """
                INSERT INTO repartos (rep_ped_id, rep_suc_origen, rep_suc_destino, rep_fecha_entrega, rep_estado_reparto)
                SELECT
                    ped_id,
                    ped_sucursal_origen,
                    ped_sucursal_destino,
                    CURDATE(),      -- Fecha de hoy como inicio del reparto
                    'R'    -- Estado inicial
                FROM pedidos
                WHERE ped_id = %s;
            """
            cursor.execute(query_insert, (ped_id,))
            # 2. Actualizar el estado del pedido original a 'En Reparto'
            query_update = "UPDATE pedidos SET ped_estado_pedido = 'R' WHERE ped_id = %s;"
            cursor.execute(query_update, (ped_id,))

        # Si todo fue exitoso, confirmamos los cambios
        connection.commit()
        return jsonify({"message": f"{len(pedidos_ids)} reparto(s) creado(s) exitosamente"})
    except Exception as e:
        if connection:
            connection.rollback() # Revertimos todo si algo falla
        print(f"Error al crear repartos: {e}")
        return jsonify({"message": "Error en el servidor al crear repartos"}), 500
    finally:
        if connection:
            connection.close()


@app.route('/actualizarRepartos')
def vistaActualizarRepartos():
    """Muestra la página con la lista de todos los repartos existentes."""
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos todos los repartos con detalles del pedido asociado
            query = """
                SELECT 
                    r.rep_id, r.rep_fecha_entrega, r.rep_estado_reparto,
                    p.ped_id, p.ped_asunto
                FROM repartos r
                JOIN pedidos p ON r.rep_ped_id = p.ped_id
                ORDER BY r.rep_fecha_entrega DESC;
            """
            cursor.execute(query)
            repartos = cursor.fetchall()
            return render_template('repActualizarRepartos.jinja2', repartos=repartos)
    finally:
        if connection:
            connection.close()
@app.route('/guardar_cambios_reparto', methods=['POST'])
def guardar_cambios_reparto():
    """
    Actualiza un reparto. Si el nuevo estado es 'P' (Pendiente),
    borra el reparto y resetea el pedido para que pueda ser reasignado.
    """
    datos = request.get_json()
    rep_id = datos.get('rep_id')
    nueva_fecha = datos.get('nueva_fecha')
    nuevo_estado_reparto = datos.get('nuevo_estado', '').upper() # ej: 'P', 'R', 'E', 'X'

    if not all([rep_id, nueva_fecha, nuevo_estado_reparto]):
        return jsonify({'error': 'Faltan datos'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            connection.begin()

            # --- LÓGICA CONDICIONAL AÑADIDA ---
            # Si el nuevo estado es 'P', se ejecuta la lógica de borrado y reseteo.
            if nuevo_estado_reparto == 'P':
                # Obtenemos el ID del pedido asociado ANTES de borrar el reparto
                cursor.execute("SELECT rep_ped_id FROM repartos WHERE rep_id = %s", (rep_id,))
                resultado = cursor.fetchone()
                if not resultado:
                    raise Exception("No se encontró el reparto para resetear.")
                pedido_id_asociado = resultado[0]
                
                # 1. Borramos el reparto de la tabla 'repartos'
                cursor.execute("DELETE FROM repartos WHERE rep_id = %s", (rep_id,))
                
                # 2. Reseteamos el estado del pedido original a 'P' (Pendiente) en la tabla 'pedidos'
                cursor.execute("UPDATE pedidos SET ped_estado_pedido = 'P' WHERE ped_id = %s", (pedido_id_asociado,))
                
                msg = f"Reparto {rep_id} marcado como pendiente. Fue eliminado para poder ser reasignado y el Pedido {pedido_id_asociado} ha sido reseteado."

            # Si el estado es cualquier otro (R, E, X), se ejecuta la lógica de actualización normal.
            else:
                status_map = {
                    'R': 'R',
                    'E': 'C',  # Entregado en Repartos es Completado en Pedidos
                    'X': 'X'
                }
                nuevo_estado_pedido = status_map.get(nuevo_estado_reparto)

                if not nuevo_estado_pedido:
                    return jsonify({'error': 'Estado no válido proporcionado'}), 400

                # Se actualiza la tabla 'repartos'
                query_reparto = "UPDATE repartos SET rep_fecha_entrega = %s, rep_estado_reparto = %s WHERE rep_id = %s;"
                cursor.execute(query_reparto, (nueva_fecha, nuevo_estado_reparto, rep_id))

                # Se actualiza la tabla 'pedidos'
                query_pedido = "UPDATE pedidos SET ped_estado_pedido = %s WHERE ped_id = (SELECT rep_ped_id FROM repartos WHERE rep_id = %s);"
                cursor.execute(query_pedido, (nuevo_estado_pedido, rep_id))
                
                msg = f'Reparto {rep_id} y pedido asociado actualizados.'

            # --- FIN DE LA LÓGICA CONDICIONAL ---

            connection.commit()
            return jsonify({'message': msg})

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Error al actualizar reparto: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if connection:
            connection.close()

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