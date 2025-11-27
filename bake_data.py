from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pymysql
from pymysql import err
from datetime import date, datetime
import pytz
import json
import decimal

#Inicializacion de la aplicación de los endpoints
app = Flask(__name__, template_folder='HTML')
# IMPORTANTE: Establece una llave secreta.
# ¡Cámbiala por una cadena de texto larga, aleatoria y secreta!
app.secret_key = 'esta-es-una-llave-muy-secreta-y-debes-cambiarla'
app.config['SESSION_COOKIE_NAME'] = 'session_empleado_grace'
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


@app.route('/gerente')
def gerente():
    return render_template('gerente.jinja2')

@app.route('/usuario')
def usuario():
    return render_template('usuario.jinja2')


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

@app.route('/produccion')
def produccion():
    return render_template('produccion.jinja2')

# ==============================================================================
# 3. FUNCIONES DE LÓGICA DE NEGOCIO (BD Utilities)
#    Funciones que contienen lógica de BD pura, no son rutas de Flask.
# ==============================================================================

def get_materias_primas():
    """Obtiene una lista de todas las materias primas de la base de datos."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # Selecciona campos clave
            cursor.execute("SELECT matprim_id, matprim_nombre, matprim_unimed, matprim_descr FROM materias_primas")
            rows = cursor.fetchall()
            materias = []
            for row in rows:
                materias.append({
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2],
                    'descripcion': row[3]
                })
            return materias
    finally:
        conn.close()

def buscar_materias_logic(query):
    """Contiene la lógica de la BD para buscar materias primas por nombre."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT matprim_id, matprim_nombre, matprim_unimed, matprim_descr 
            FROM materias_primas 
            WHERE matprim_nombre LIKE %s
            """
            like_query = f"%{query}%"
            cursor.execute(sql, (like_query,))
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2],
                    'descripcion': row[3]
                } for row in rows
            ]
    finally:
        conn.close()

@app.route("/verMateriaPrima")
def materias_primas():
    """Página que lista todas las materias primas."""
    materias = get_materias_primas()
    return render_template('proVerMateriaPrima.jinja2', materias=materias)

@app.route('/solicitarMateriaPrima')
def solicitarMateriaPrima():
    """Página para solicitar materia prima."""
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # 1. Obtenemos la lista de proveedores
            cursor.execute("SELECT prov_id, prov_nombre_empresa FROM proveedores WHERE prov_estado = 'A'")
            proveedores = cursor.fetchall()
            
            # 2. Obtenemos la lista de sucursales (para traslados)
            # Excluimos la sucursal actual, no puedes pedirte a ti mismo
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales WHERE suc_id != %s", (session['sucursal'],))
            sucursales = cursor.fetchall()
            
        return render_template('proSolicitarMateriaPrima.jinja2', 
                            proveedores=proveedores,
                            sucursales=sucursales)
    except Exception as e:
        print(f"Error en solicitarMateriaPrima: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()

@app.route('/produccionDeHoy')
def produccionHoy():
    """Página que muestra la producción del día."""
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))

    # 1. Determinar si es gerente
    es_gerente = 'G' in session.get('roles', [])
    sucursales = []

    connection = None
    try:
        # 2. Si es Gerente, cargamos todas las sucursales
        if es_gerente:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
                sucursales = cursor.fetchall()
    except Exception as e:
        print(f"Error cargando sucursales: {e}")
    finally:
        if connection: connection.close()

    # 3. Pasamos todo a la plantilla
    return render_template('proProduccionDelDia.jinja2', 
                            es_gerente=es_gerente, 
                            sucursales=sucursales, 
                            sucursal_propia=session['sucursal'])
    
@app.route('/api/inventario/<int:sucursal_id>')
def obtener_inventario_materias_primas(sucursal_id):
    """Obtiene el inventario de materias primas para una sucursal específica (API Restful)."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT invmatprim_matprim_fk AS id, invmatprim_matprim_nombre AS nombre, invmatprim_unimed AS unidad, invmatprim_stock AS stock
                FROM inventario_materias_primas
                WHERE invmatprim_suc_fk = %s
            """, (sucursal_id,))
            rows = cursor.fetchall()
            datos = [
                {
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2],
                    'stock': float(row[3])
                }
                for row in rows
            ]
            return jsonify(datos)
    finally:

        conn.close()


# ==============================================================================
# 5. RUTAS DE API: MATERIAS PRIMAS, PRODUCTOS E INVENTARIO
#    Endpoints que retornan datos en formato JSON.
# ==============================================================================

@app.route('/buscar_materias')
def buscar_materias():
    """Endpoint para buscar materias por nombre."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT matprim_id, matprim_nombre, matprim_unimed, matprim_descr
                FROM materias_primas
                WHERE matprim_nombre LIKE %s
            """
            like_query = f"%{query}%"
            cursor.execute(sql, (like_query,))
            rows = cursor.fetchall()

            productos = [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "unidad": row[2],
                    "descripcion": row[3]
                }
                for row in rows
            ]
        return jsonify(productos)
    finally:
        conn.close()

@app.route('/get_materias_por_sucursal')
def get_materias_por_sucursal():
    """Obtiene el inventario de materias primas para una sucursal específica (Legacy/Query String)."""
    sucursal_id = request.args.get('sucursal')
    if not sucursal_id:
        return jsonify([])

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    invmatprim_matprim_fk AS id,
                    invmatprim_matprim_nombre AS nombre,
                    invmatprim_unimed AS unidad,
                    invmatprim_stock AS stock
                FROM inventario_materias_primas
                WHERE invmatprim_suc_fk = %s
            """, (sucursal_id,))
            rows = cursor.fetchall()

        materias = [
            {'id': row[0], 'nombre': row[1], 'unidad': row[2], 'stock': float(row[3])}
            for row in rows
        ]
        return jsonify(materias)
    finally:
        conn.close()

@app.route('/buscar_productos')
def buscar_productos():
    """Endpoint para buscar productos por nombre."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT pro_id, pro_nombre, pro_unimed, pro_descr
                FROM productos
                WHERE pro_nombre LIKE %s
            """
            like_query = f"%{query}%"
            cursor.execute(sql, (like_query,))
            rows = cursor.fetchall()

            productos = [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "unidad": row[2],
                    "descripcion": row[3]
                }
                for row in rows
            ]
        return jsonify(productos)
    finally:
        conn.close()


# ==============================================================================
# 6. RUTAS DE API: PRODUCCIÓN DEL DÍA
#    Endpoints específicos para la gestión de producción.
# ==============================================================================
    if 'sucursal' not in session: 
        return jsonify({"success": False, "message": "No autorizado"}), 401
        
    # 1. Definir sucursal por defecto (la de la sesión)
    sucursal_destino_id = session['sucursal']
    usuario_es_gerente = 'G' in session.get('roles', [])
    
    data = request.get_json()
    
    # --- DEBUG: Imprimir en consola qué llegó ---
    print(f"DEBUG: Usuario Gerente? {usuario_es_gerente}")
    print(f"DEBUG: JSON recibido: {data}")
    
    productos_lista = []
    
    # 2. Lógica de Selección de Sucursal
    if isinstance(data, dict):
        # Si el frontend envía un objeto { sucursal_id: X, productos: [...] }
        solicitada_id = data.get('sucursal_id')
        productos_lista = data.get('productos', [])
        
        # Si es Gerente Y mandó una ID, la usamos.
        # IMPORTANTE: Convertir a int() para asegurar que no sea un string "2"
        if usuario_es_gerente and solicitada_id:
            try:
                sucursal_destino_id = int(solicitada_id)
                print(f"DEBUG: Cambio de sucursal autorizado a ID: {sucursal_destino_id}")
            except ValueError:
                print("DEBUG: ID de sucursal inválido, usando la propia.")
    
    elif isinstance(data, list):
        # Formato antiguo
        productos_lista = data
    
    if not productos_lista:
        return jsonify({"success": False, "message": "No hay productos."}), 400

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # 3. Obtener el nombre de la sucursal donde se va a guardar (PARA CONFIRMAR)
            cursor.execute("SELECT suc_nombre FROM sucursales WHERE suc_id = %s", (sucursal_destino_id,))
            row_suc = cursor.fetchone()
            nombre_sucursal_destino = row_suc[0] if row_suc else f"ID {sucursal_destino_id}"

            # 4. Insertar
            sql = """
                INSERT INTO produccion_del_dia 
                (pro_dia_suc_fk, pro_dia_pro_fk, pro_dia_nombre, pro_dia_cantidad, pro_dia_estado) 
                VALUES (%s, %s, %s, %s, 'P')
            """
            
            for producto in productos_lista:
                prod_id = producto.get('id') 
                nombre = producto.get('pro_dia_nombre')
                cantidad = producto.get('pro_dia_cantidad')

                if prod_id and cantidad:
                    # Usamos la variable sucursal_destino_id que calculamos arriba
                    cursor.execute(sql, (sucursal_destino_id, prod_id, nombre, cantidad))
            
            conn.commit()
            
            # --- MENSAJE DE CONFIRMACIÓN EXPLÍCITO ---
            mensaje = f"Producción registrada EXITOSAMENTE en: {nombre_sucursal_destino}"
            return jsonify({"success": True, "message": mensaje})
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()
        
@app.route('/api/obtener_produccion_hoy', methods=['GET'])
def api_obtener_produccion_hoy():
    if 'sucursal' not in session: return jsonify({"success": False}), 401
    
    # Lógica de selección de sucursal
    sucursal_objetivo = session['sucursal'] # Por defecto, la propia
    # Si el JS envía 'sucursal_id' en la URL (query param)
    solicitada_id = request.args.get('sucursal_id')
    # Si es gerente y pide una específica, usamos esa
    if 'G' in session.get('roles', []) and solicitada_id:
        try:
            sucursal_objetivo = int(solicitada_id)
        except:
            pass

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # --- CONSULTA AGRUPADA (Misma lógica que definimos antes) ---
            sql = """
                SELECT 
                    pro_dia_nombre, 
                    pro_dia_estado,
                    SUM(pro_dia_cantidad) as cantidad_total,
                    GROUP_CONCAT(pro_dia_id) as lista_ids
                FROM produccion_del_dia 
                WHERE pro_dia_suc_fk = %s AND pro_dia_fecha = CURDATE()
                GROUP BY pro_dia_nombre, pro_dia_estado
                ORDER BY pro_dia_nombre ASC
            """
            cursor.execute(sql, (sucursal_objetivo,))
            rows = cursor.fetchall()
            
            produccion = []
            for row in rows:
                ids_str = row['lista_ids']
                if isinstance(ids_str, bytes): ids_str = ids_str.decode('utf-8')
                lista_ids = [int(x) for x in ids_str.split(',')] if ids_str else []

                produccion.append({
                    'pro_dia_nombre': row['pro_dia_nombre'],
                    'pro_dia_estado': row['pro_dia_estado'],
                    'pro_dia_cantidad': float(row['cantidad_total']),
                    'ids_reales': lista_ids
                })
            
            return jsonify(produccion)
    finally:
        conn.close()

@app.route('/api/confirmar_produccion', methods=['POST'])
def api_confirmar_produccion():
    if 'sucursal' not in session: return jsonify({"success": False}), 401
    emp_id = session.get('emp_id')
    empleado_id = emp_id if emp_id else None
    data = request.get_json()
    ids_produccion = data.get('ids_produccion', [])
    
    # Obtenemos la sucursal objetivo del JSON (para saber dónde sumar inventario)
    solicitada_id = data.get('sucursal_id')
    sucursal_objetivo = session['sucursal']
    
    if 'G' in session.get('roles', []) and solicitada_id:
        sucursal_objetivo = int(solicitada_id)

    if not ids_produccion: return jsonify({"success": False, "message": "Nada seleccionado"}), 400

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            conn.begin()
            
            format_strings = ','.join(['%s'] * len(ids_produccion))
            
            # 1. Obtener datos
            cursor.execute(f"""
                SELECT pro_dia_id, pro_dia_pro_fk, pro_dia_cantidad, pro_dia_nombre 
                FROM produccion_del_dia 
                WHERE pro_dia_id IN ({format_strings}) AND pro_dia_suc_fk = %s AND pro_dia_estado = 'P'
            """, (*ids_produccion, sucursal_objetivo))
            
            items = cursor.fetchall()

            for item in items:
                pk_produccion = item['pro_dia_id']
                producto_id = item['pro_dia_pro_fk']
                cantidad = item['pro_dia_cantidad']
                nombre = item['pro_dia_nombre']

                # 2. Actualizar Inventario (en la sucursal_objetivo)
                cursor.execute("SELECT pro_unimed FROM productos WHERE pro_id = %s", (producto_id,))
                row_prod = cursor.fetchone()
                unidad = row_prod['pro_unimed'] if row_prod else 'PZA'

                sql_inventario = """
                    INSERT INTO inventario_productos (invpro_pro_fk, invpro_suc_fk, pro_nombre, pro_stock, invpro_unimed_fk)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE pro_stock = pro_stock + VALUES(pro_stock)
                """
                cursor.execute(sql_inventario, (producto_id, sucursal_objetivo, nombre, cantidad, unidad))

                # --- 3. NUEVO: Guardar en Historial de Producción (LO QUE FALTABA) ---
                sql_historico = """
                    INSERT INTO historial_produccion 
                    (hist_suc_fk, hist_pro_fk, hist_emp_fk, hist_cantidad)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql_historico, (sucursal_objetivo, producto_id, empleado_id, cantidad))
                # ---------------------------------------------------------------------

                # 4. Marcar como Completado
                cursor.execute("UPDATE produccion_del_dia SET pro_dia_estado = 'C' WHERE pro_dia_id = %s", (pk_produccion,))

            conn.commit()
            return jsonify({"success": True, "message": "Producción confirmada."})
            
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()
# En tu archivo app.py


    if 'sucursal' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_id = session['sucursal']
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # LÓGICA DE INTELIGENCIA:
            # 1. Filtra por Sucursal.
            # 2. Filtra por el mismo día de la semana de hoy (DAYOFWEEK(NOW())).
            # 3. Filtra los últimos 90 días para que la tendencia sea reciente.
            # 4. Agrupa por producto y promedia la cantidad.
            
            query = """
                SELECT 
                    p.pro_id as id, 
                    p.pro_nombre as nombre, 
                    p.pro_unimed as unidad,
                    AVG(h.hist_cantidad) as cantidad_promedio
                FROM historial_produccion h
                JOIN productos p ON h.hist_pro_fk = p.pro_id
                WHERE h.hist_suc_fk = %s
                AND DAYOFWEEK(h.hist_fecha) = DAYOFWEEK(NOW())
                AND h.hist_fecha >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY p.pro_id, p.pro_nombre, p.pro_unimed
                HAVING cantidad_promedio > 0
            """
            cursor.execute(query, (sucursal_id,))
            sugerencias = cursor.fetchall()
            
            # Formateamos los datos para el frontend
            resultados = []
            for item in sugerencias:
                resultados.append({
                    'id': item['id'],
                    'nombre': item['nombre'],
                    'unidad': item['unidad'],
                    # Redondeamos. Si es 'PZA' (Pieza) usamos entero, si no (KG/LT) usamos 2 decimales.
                    'cantidad': int(item['cantidad_promedio']) if item['unidad'] == 'PZA' else round(float(item['cantidad_promedio']), 2)
                })
            
            return jsonify(resultados)

    except Exception as e:
        print(f"Error en sugerencias del día: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()



# ==============================================================================
# MÓDULO: REGISTRO DE PRODUCCIÓN
# ==============================================================================

@app.route("/registrarProduccion", methods=["GET"])
def registrar_produccion():
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))
    
    roles = session.get('roles', [])
    es_gerente = 'G' in roles
    sucursales = []
    connection = None
    try:
        if es_gerente:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
                sucursales = cursor.fetchall()
    except Exception as e:
        print(f"Error cargando sucursales: {e}")
    finally:
        if connection: connection.close()

    return render_template("proRegistrarProduccion.jinja2", 
                            es_gerente=es_gerente, 
                            sucursales=sucursales, 
                            sucursal_propia=session['sucursal'])

# --- API 1: REGISTRAR PRODUCCIÓN (Guardar en BD) ---
@app.route('/api/registrar_produccion', methods=['POST'])
def api_registrar_produccion():
    if 'sucursal' not in session: return jsonify({"success": False, "message": "No autorizado"}), 401
        
    sucursal_destino_id = session['sucursal']
    usuario_es_gerente = 'G' in session.get('roles', [])
    # 1. Obtienes el momento actual en la zona de CDMX
    zona_mx = pytz.timezone("America/Mexico_City")
    fecha_actual_mx = datetime.now(zona_mx)
    # 2. Lo conviertes a string formato 'YYYY-MM-DD' para MySQL
    fecha_produccion = fecha_actual_mx.strftime('%Y-%m-%d')
    data = request.get_json()
    productos_lista = []
    
    if isinstance(data, dict):
        solicitada_id = data.get('sucursal_id')
        productos_lista = data.get('productos', [])
        if usuario_es_gerente and solicitada_id:
            try:
                sucursal_destino_id = int(solicitada_id)
            except ValueError: pass
    elif isinstance(data, list):
        productos_lista = data
    
    if not productos_lista:
        return jsonify({"success": False, "message": "No hay productos."}), 400

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT suc_nombre FROM sucursales WHERE suc_id = %s", (sucursal_destino_id,))
            row_suc = cursor.fetchone()
            nombre_sucursal = row_suc[0] if row_suc else f"ID {sucursal_destino_id}"

            sql = """
                INSERT INTO produccion_del_dia 
                (pro_dia_suc_fk, pro_dia_pro_fk, pro_dia_nombre, pro_dia_cantidad, pro_dia_estado,pro_dia_fecha) 
                VALUES (%s, %s, %s, %s, 'P',%s)
            """
            for producto in productos_lista:
                prod_id = producto.get('id') 
                nombre = producto.get('pro_dia_nombre')
                cantidad = producto.get('pro_dia_cantidad')
                fecha_produccion

                if prod_id and cantidad:
                    cursor.execute(sql, (sucursal_destino_id, prod_id, nombre, cantidad,fecha_produccion))
            
            conn.commit()
            return jsonify({"success": True, "message": f"Producción registrada en: {nombre_sucursal}"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

# --- API 2: SUGERENCIAS DEL DÍA (Histórico) ---
@app.route('/api/sugerencias_produccion_dia', methods=['GET'])
def api_sugerencias_produccion_dia():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    sucursal_id = session['sucursal']
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT p.pro_id as id, p.pro_nombre as nombre, p.pro_unimed as unidad, AVG(h.hist_cantidad) as cantidad_promedio
                FROM historial_produccion h
                JOIN productos p ON h.hist_pro_fk = p.pro_id
                WHERE h.hist_suc_fk = %s
                AND DAYOFWEEK(h.hist_fecha) = DAYOFWEEK(NOW())
                AND h.hist_fecha >= DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY p.pro_id, p.pro_nombre, p.pro_unimed
                HAVING cantidad_promedio > 0
            """
            cursor.execute(query, (sucursal_id,))
            sugerencias = cursor.fetchall()
            
            resultados = []
            for item in sugerencias:
                resultados.append({
                    'id': item['id'],
                    'nombre': item['nombre'],
                    'unidad': item['unidad'],
                    'cantidad': int(item['cantidad_promedio']) if item['unidad'] == 'PZA' else round(float(item['cantidad_promedio']), 2)
                })
            return jsonify(resultados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()

# --- API 3: PEDIDOS QUE REQUIEREN PRODUCCIÓN (TODOS LOS PENDIENTES) ---
@app.route('/api/pedidos_para_produccion', methods=['GET'])
def api_pedidos_para_produccion():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # CAMBIO: Eliminado filtro de CURDATE(). Se muestran TODOS los pendientes.
            query = """
                SELECT 
                    p.ped_id, 
                    p.ped_asunto, 
                    p.ped_fecha_entrega, 
                    p.ped_hora_entrega,
                    
                    COALESCE(s_dest.suc_nombre, 'Cliente Externo') as destino,
                    COALESCE(s_orig.suc_nombre, 'Matriz/Desconocido') as origen

                FROM pedidos p
                LEFT JOIN sucursales s_dest ON p.ped_sucursal_destino = s_dest.suc_id
                LEFT JOIN sucursales s_orig ON p.ped_sucursal_origen = s_orig.suc_id
                
                WHERE 
                    p.ped_estado_pedido = 'P' -- Solo pendientes de cualquier fecha
                
                ORDER BY p.ped_fecha_entrega ASC, p.ped_hora_entrega ASC
            """
            cursor.execute(query)
            pedidos = cursor.fetchall()
            
            for p in pedidos:
                if p['ped_fecha_entrega']:
                    p['ped_fecha_entrega'] = p['ped_fecha_entrega'].strftime('%d/%m/%Y')
                if p['ped_hora_entrega']:
                    # Formato HH:MM
                    if hasattr(p['ped_hora_entrega'], 'total_seconds'):
                        seconds = p['ped_hora_entrega'].total_seconds()
                        h = int(seconds // 3600)
                        m = int((seconds % 3600) // 60)
                        p['ped_hora_entrega'] = f"{h:02}:{m:02}"
                    else:
                        p['ped_hora_entrega'] = str(p['ped_hora_entrega'])[:5]
                    
            return jsonify(pedidos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()

# --- API 4: DETALLES DE PEDIDO PARA CARGAR ---
@app.route('/api/items_pedido_produccion/<int:pedido_id>', methods=['GET'])
def api_items_pedido_produccion(pedido_id):
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT 
                    dp.detpedpro_pro_id as id, 
                    p.pro_nombre as nombre, 
                    p.pro_unimed as unidad, 
                    dp.detpedpro_cantidad as cantidad
                FROM detalle_pedido_productos dp
                JOIN productos p ON dp.detpedpro_pro_id = p.pro_id
                WHERE dp.detpedpro_ped_id = %s
            """
            cursor.execute(query, (pedido_id,))
            items = cursor.fetchall()
            for i in items: i['cantidad'] = float(i['cantidad'])
            return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()


# ==============================================================================
# 7. Rutas API: Solicitud de Materia Prima
#    Endpoints para gestionar solicitudes de materia prima.
# ==============================================================================
# --- RUTA PARA MOSTRAR LA PÁGINA (MODIFICADA) ---

# --- API PARA PROCESAR LA SOLICITUD (MODIFICADA) ---
# En tu archivo app.py
# (Asegúrate de tener import decimal, import json, from datetime import date)

# --- REEMPLAZA TU API ACTUAL CON ESTA ---
@app.route('/api/solicitar_materia_prima', methods=['POST'])
def api_solicitar_materia_prima():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    empleado_id = session['emp_id']
    sucursal_id_destino = session['sucursal'] # El DESTINO siempre es quien pide
    
    data = request.json
    carrito = data.get('carrito')
    comentarios = data.get('comentarios', '')
    tipo_origen = data.get('tipo_origen') # 'proveedor' o 'sucursal'
    origen_id = data.get('origen_id')
    fecha_entrega = data.get('fecha_entrega') # YYYY-MM-DD
    hora_entrega = data.get('hora_entrega')   # HH:MM (puede ser vacío)
    
    if not carrito or not tipo_origen or not origen_id or not fecha_entrega:
        return jsonify({'success': False, 'message': 'Faltan datos obligatorios.'}), 400
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            # --- Lógica de Costos (sin cambios) ---
            monto_total_solicitud = 0
            detalles_para_insertar = []
            ids_materias = [item['id'] for item in carrito]
            format_strings = ','.join(['%s'] * len(ids_materias))
            cursor.execute(f"SELECT matprim_id, matprim_costo_unit FROM materias_primas WHERE matprim_id IN ({format_strings})", tuple(ids_materias))
            costos = {row['matprim_id']: row['matprim_costo_unit'] for row in cursor.fetchall()}
            proveedor_fk = None
            sucursal_origen_fk = None # Inicia como None
            asunto = ""

            if tipo_origen == 'proveedor':
                proveedor_fk = int(origen_id)
                sucursal_origen_fk = 1 
                asunto = "Pedido a Proveedor (MP)"
                for item in carrito:
                     monto_total_solicitud += decimal.Decimal(costos.get(int(item['id']), 0)) * decimal.Decimal(item['cantidad'])
            elif tipo_origen == 'sucursal':
                sucursal_origen_fk = int(origen_id) # Asignamos el ID de la otra sucursal
                asunto = "Solicitud de Traslado (MP)"
                monto_total_solicitud = 0 

            # 3. Insertar el Pedido principal
            # INSERT PEDIDO CON FECHA Y HORA DE ENTREGA
            sql_pedido = """
                INSERT INTO pedidos 
                (ped_emp_id, ped_sucursal_origen, ped_sucursal_destino, ped_prov_fk, 
                ped_fecha_pedido, ped_fecha_entrega, ped_hora_entrega, 
                ped_monto_total, ped_estado_pedido, ped_asunto, ped_comentarios) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'P', %s, %s)
            """
            today = date.today()
            # Si hora_entrega viene vacío, pasamos None
            hora_val = hora_entrega if hora_entrega else None
            
            cursor.execute(sql_pedido, (
                empleado_id, sucursal_origen_fk, sucursal_id_destino, proveedor_fk, 
                today, fecha_entrega, hora_val, 
                monto_total_solicitud, asunto, comentarios
            ))
            pedido_id = cursor.lastrowid 

            # Insertar detalles (Materia Prima)
            sql_detalle = """
                INSERT INTO detalle_pedido_materias_primas 
                (detpedmat_ped_id, detpedmat_matprim_id, detpedmat_cantidad, detpedmat_precio_unitario) 
                VALUES (%s, %s, %s, %s) -- Asumimos precio 0 o calculas el real
            """
            for item in carrito:
                item_id = int(item['id'])
                cantidad = decimal.Decimal(item['cantidad'])
                costo_unitario = decimal.Decimal(costos.get(item_id, 0))
                detalles_para_insertar.append((pedido_id, item_id, cantidad, costo_unitario))
            
            cursor.executemany(sql_detalle, detalles_para_insertar)
            
            connection.commit()
            
        return jsonify({'success': True, 'message': f'Solicitud #{pedido_id} ({asunto}) registrada exitosamente.'}), 200
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al finalizar solicitud de materia prima: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection:
            connection.close()

# __________________________________________________________
# INICIO ENDPOINT ALMACEN

@app.route('/almacen')
def almacen():
    return render_template('almacen.jinja2')

# RUTA PARA VER MATERIAS PRIMAS
@app.route("/almacen/verMateriasPrimas")
def materias_primas_almacen():
    materias = get_materias_primas_almacen()
    return render_template('almVerMateriasPrimas.jinja2', materias=materias)

# RUTA PARA SOLICITAR MATERIA PRIMA
@app.route('/api/materia_prima/actualizar')
def solicitar_MateriaPrima():
    """
    Ruta para la página de solicitud.
    Reutiliza la función 'solicitarMateriaPrima' del módulo Producción 
    para servir el mismo HTML.
    """
    return api_solicitar_materia_prima()

@app.route('/almacen/solicitarMateriaPrima')
def solicitarMateriaPrima_almacen():
    """Página para solicitar materia prima."""
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # 1. Obtenemos la lista de proveedores
            cursor.execute("SELECT prov_id, prov_nombre_empresa FROM proveedores WHERE prov_estado = 'A'")
            proveedores = cursor.fetchall()
            
            # 2. Obtenemos la lista de sucursales (para traslados)
            # Excluimos la sucursal actual, no puedes pedirte a ti mismo
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales WHERE suc_id != %s", (session['sucursal'],))
            sucursales = cursor.fetchall()
            
        return render_template('almSolicitarMateriaPrima.jinja2', 
                            proveedores=proveedores,
                            sucursales=sucursales)
    except Exception as e:
        print(f"Error en solicitarMateriaPrima: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()



# RUTA  PARA VER PRODUCTOS
@app.route("/almacen/verProductos")
def productos():
    """
    Obtiene la lista completa de productos y la sirve en la plantilla HTML.
    Esta ruta responde al clic del botón 'Ver Productos'.
    """
    # Verificamos que el empleado esté logueado
    if 'emp_id' not in session:
        return redirect(url_for('login'))
        
    # --- SIMPLIFICACIÓN: Obtenemos la sucursal directamente de la sesión ---
    # Ya no es necesario buscar el empleado en la base de datos.
    sucursal_actual_id = session.get('sucursal')

    # Si por alguna razón la sucursal no está en la sesión, redirigimos.
    if not sucursal_actual_id:
        flash('No se pudo identificar la sucursal. Por favor, inicia sesión de nuevo.', 'error')
        return redirect(url_for('login'))

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Obtener la lista de todas las sucursales para el dropdown (esto sigue siendo necesario)
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales ORDER BY suc_nombre")
            sucursales = cursor.fetchall()
            # 2. Obtener el inventario inicial usando el ID de la sesión
            query_inventario = """
                SELECT ip.invpro_pro_fk AS id, p.pro_nombre AS nombre, p.pro_unimed AS unidad, ip.pro_stock AS stock
                FROM inventario_productos ip
                JOIN productos p ON ip.invpro_pro_fk = p.pro_id
                WHERE ip.invpro_suc_fk = %s
            """
            cursor.execute(query_inventario, (sucursal_actual_id,))
            inventario_inicial = cursor.fetchall()
        # Pasamos los datos a la plantilla
        return render_template('almVerProductos.jinja2', 
                                sucursales=sucursales,
                                inventario_inicial=inventario_inicial,
                                sucursal_actual_id=sucursal_actual_id)
    except Exception as e:
        print(f"Error al ver productos: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()


def get_all_productos():
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # Seleccionamos los campos necesarios de la tabla 'productos'
            cursor.execute("SELECT pro_id, pro_nombre, pro_precio, pro_costo_unit, pro_unimed, pro_descr FROM productos")
            rows = cursor.fetchall()
            productos = []
            for row in rows:
                productos.append({
                    'id': row[0],
                    'nombre': row[1],
                    'precio': row[2],
                    'costo': row[3],
                    'unidad': row[4],
                    'descripcion': row[5]
                })
            return productos
    except Exception as e:
        print(f"Error al obtener productos de la BD: {e}")
        return []
    finally:
        conn.close()


@app.route('/api/inventario/<int:sucursal_id>')
def obtener_inventario_productos(sucursal_id):
    """Obtiene el inventario de materias primas para una sucursal específica (API Restful)."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    invmatprim_matprim_fk AS id,
                    invmatprim_matprim_nombre AS nombre,
                    invmatprim_unimed AS unidad,
                    invmatprim_stock AS stock
                FROM inventario_materias_primas
                WHERE invmatprim_suc_fk = %s
            """, (sucursal_id,))
            
            rows = cursor.fetchall()
            datos = [
                {
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2],
                    'stock': float(row[3])
                }
                for row in rows
            ]
            return jsonify(datos)
    finally:
        conn.close()

def get_materias_primas_almacen():
    """Obtiene una lista de TODAS las materias primas, INCLUYENDO EL COSTO."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # Esta consulta SÍ incluye 'matprim_costo_unit'
            cursor.execute("SELECT matprim_id, matprim_nombre, matprim_unimed, matprim_descr, matprim_costo_unit FROM materias_primas")
            rows = cursor.fetchall()
            materias = []
            for row in rows:
                materias.append({
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2],
                    'descripcion': row[3],
                    'costo': row[4]
                })
            return materias
    finally:
        conn.close()

# -----------------------------------------------------------
UNIDADES_DE_MEDIDA = [
    ('KG', 'Kilogramo'),
    ('GR', 'Gramo'),
    ('PZA', 'Pieza'),
    ('L', 'Litro'),
    ('ml', 'Mililitro'),
    ('M', 'Metro')
]
# -----------------------------------------------------------
# RUTA PARA ACTUALIZAR MATERIA PRIMA
# -----------------------------------------------------------
@app.route('/actualizarMateriaPrima')
def actualizar_materias_page():
    """
    Muestra la página de edición de materias primas.
    NO debe leer request.json aquí.
    """
    try:
        # Su único trabajo es obtener datos y mostrar la plantilla
        materias = get_materias_primas_almacen() 
    except Exception as e:
        print(f"Error al obtener materias primas para edición: {e}")
        materias = []
        
    # Renderiza el HTML y le pasa las materias
    return render_template(
        'almActualizarMateriaPrima.jinja2', 
        materias=materias, 
        unidades=UNIDADES_DE_MEDIDA
    )

# -----------------------------------------------------------
# ACTUALIZAR MATERIA PRIMA (API)
# -----------------------------------------------------------
@app.route('/api/materia_prima/actualizar', methods=['POST'])
def api_actualizar_materia():
    """
    Endpoint API para actualizar una materia prima.
    Esta SÍ es POST y SÍ lee request.json
    """
    # Obtenemos los datos enviados por el JavaScript
    data = request.json
    
    mat_id = data.get('id')
    descripcion = data.get('descripcion')
    unidad = data.get('unidad')
    costo = data.get('costo')

    if not all([mat_id, unidad, costo is not None]):
        return jsonify({'error': 'Faltan datos (id, unidad, costo)'}), 400

    conn = conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE materias_primas 
                SET 
                    matprim_descr = %s,
                    matprim_unimed = %s,
                    matprim_costo_unit = %s
                WHERE 
                    matprim_id = %s
            """
            cursor.execute(sql, (descripcion, unidad, costo, mat_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Materia Prima {mat_id} actualizada.'})

    except Exception as e:
        conn.rollback() 
        print(f"Error en API al actualizar materia prima: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()
        
# ===========================================================
# RUTA PARA ACTUALIZAR PRODUCTOS
# ===========================================================

@app.route('/actualizarProductos')
def actualizar_productos_page():
    """
    Muestra la página de edición de productos.
    """
    try:
        # Reutilizamos la función que ya existe
        productos_lista = get_all_productos() 
    except Exception as e:
        print(f"Error al obtener productos para edición: {e}")
        productos_lista = []
        
    return render_template(
        'almActualizarProductos.jinja2', 
        productos=productos_lista, 
        unidades=UNIDADES_DE_MEDIDA # Reutilizamos la lista de unidades
    )

@app.route('/api/producto/actualizar', methods=['POST'])
def api_actualizar_producto():
    """
    Endpoint API para actualizar un producto.
    """
    data = request.json
    
    prod_id = data.get('id')
    descripcion = data.get('descripcion')
    unidad = data.get('unidad')
    precio = data.get('precio') 
    
    # --- CAMBIO 1: Recibir 'costo_unit' (como lo envía el JS) ---
    costo_unit = data.get('costo_unit') # No 'costo', sino 'costo_unit'

    # --- CAMBIO 2: Agregar el nuevo campo a la validación ---
    if not all([prod_id, unidad, precio is not None, costo_unit is not None]):
        return jsonify({'error': 'Faltan datos (id, unidad, precio o costo_unit)'}), 400
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # --- CAMBIO 3: Agregar 'pro_costo_unit' a la consulta SQL ---
            sql = """
                UPDATE productos 
                SET 
                    pro_descr = %s,
                    pro_unimed = %s,
                    pro_precio = %s,
                    pro_costo_unit = %s  -- <-- ¡AQUÍ ESTÁ LA MAGIA!
                WHERE 
                    pro_id = %s
            """
            
            # --- CAMBIO 4: Agregar 'costo_unit' a la tupla de datos ---
            # (El orden debe coincidir con el SQL)
            cursor.execute(sql, (
                descripcion, 
                unidad, 
                precio, 
                costo_unit,  # <-- El valor que faltaba
                prod_id
            ))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Producto {prod_id} actualizado.'})

    except Exception as e:
        conn.rollback()
        print(f"Error en API al actualizar producto: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# RUTA PARA SOLICITAR PRODUCTOS
@app.route('/almacen/solicitarProductos')
def solicitar_productos():
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))
            
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Productos disponibles (Catálogo)
            query_productos = """
                SELECT pro_id as id, pro_nombre as nombre, pro_costo_unit as costo, pro_unimed as unidad
                FROM productos ORDER BY pro_nombre
            """
            cursor.execute(query_productos)
            productos_disponibles = cursor.fetchall()
            for prod in productos_disponibles:
                prod['costo'] = float(prod['costo'])
            
            # 2. Sucursales (Para el selector de Origen)
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
            sucursales = cursor.fetchall()
            
        return render_template('almSolicitarProductos.jinja2', 
                                productos=productos_disponibles,
                                sucursales=sucursales)
    except Exception as e:
        print(f"Error en solicitar_productos_vista: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection: connection.close()


# ==============================================================================
# MÓDULO: REGISTRO DE ENTRADAS (ALMACÉN)
# # ==============================================================================

# --- 1. RUTA DE VISTA ---
@app.route('/registrarEntradas')
def registrar_entradas_vista():
    if 'sucursal' not in session: return redirect(url_for('login'))
    return render_template('almRegistrarEntradas.jinja2')

# --- 2. API: LISTAR PEDIDOS POR RECIBIR (Lógica de Origen Corregida) ---
@app.route('/api/pedidos_por_recibir')
def api_pedidos_por_recibir():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_destino = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # CORRECCIÓN DE LÓGICA DE ORIGEN:
            query = """
                SELECT 
                    p.ped_id, 
                    p.ped_asunto, 
                    p.ped_monto_total,
                    p.ped_fecha_entrega,
                    p.ped_hora_entrega,
                    CASE 
                        WHEN p.ped_prov_fk IS NOT NULL THEN CONCAT('Prov: ', prov.prov_nombre_empresa)
                        WHEN p.ped_usu_id IS NOT NULL THEN 'Cliente (Web/App)'
                        ELSE CONCAT('Suc: ', s.suc_nombre)
                    END as origen
                FROM pedidos p
                LEFT JOIN sucursales s ON p.ped_sucursal_origen = s.suc_id
                LEFT JOIN proveedores prov ON p.ped_prov_fk = prov.prov_id
                WHERE 
                    p.ped_sucursal_destino = %s 
                    AND p.ped_estado_pedido = 'R' 
                ORDER BY 
                    p.ped_fecha_entrega ASC, 
                    p.ped_hora_entrega ASC
            """
            cursor.execute(query, (sucursal_destino,))
            pedidos = cursor.fetchall()
            
            # Formateo amigable de fecha y hora
            for p in pedidos:
                p['ped_monto_total'] = float(p['ped_monto_total'])
                
                # Fecha
                fecha_display = ""
                if p['ped_fecha_entrega']:
                    fecha_display = p['ped_fecha_entrega'].strftime('%d/%m/%Y')
                    # IMPORTANTE: Reemplazar el objeto date original con string para JSON
                    p['ped_fecha_entrega'] = p['ped_fecha_entrega'].strftime('%Y-%m-%d')
                else:
                    p['ped_fecha_entrega'] = None
                
                # Hora (CORRECCIÓN DEL ERROR TIMEDELTA)
                hora_display = ""
                if p['ped_hora_entrega']:
                    if hasattr(p['ped_hora_entrega'], 'total_seconds'):
                        seconds = p['ped_hora_entrega'].total_seconds()
                        h = int(seconds // 3600)
                        m = int((seconds % 3600) // 60)
                        hora_display = f"{h:02}:{m:02}"
                    else:
                        hora_display = str(p['ped_hora_entrega'])[:5]
                    
                    p['ped_hora_entrega'] = hora_display
                else:
                    p['ped_hora_entrega'] = None
                
                p['fecha_formateada'] = f"{fecha_display} {hora_display}".strip()

            return jsonify(pedidos)
    except Exception as e:
        print(f"Error api_pedidos_por_recibir: {e}")
        # Devolver una lista vacía en lugar de error JSON para no romper el frontend
        return jsonify([]) 
    finally:
        if connection: connection.close()

# --- 3. API: OBTENER DETALLES DEL PEDIDO ---
@app.route('/api/obtener_detalles_pedido/<int:pedido_id>')
def api_obtener_detalles_pedido(pedido_id):
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            items = []
            
            # Productos
            cursor.execute("""
                SELECT d.detpedpro_pro_id as id, d.detpedpro_cantidad as cantidad_esperada, 
                    p.pro_nombre as nombre, p.pro_unimed as unidad, 'producto' as tipo
                FROM detalle_pedido_productos d
                JOIN productos p ON d.detpedpro_pro_id = p.pro_id
                WHERE d.detpedpro_ped_id = %s
            """, (pedido_id,))
            items.extend(cursor.fetchall())

            # Materias Primas
            cursor.execute("""
                SELECT d.detpedmat_matprim_id as id, d.detpedmat_cantidad as cantidad_esperada, 
                       m.matprim_nombre as nombre, m.matprim_unimed as unidad, 'materia' as tipo
                FROM detalle_pedido_materias_primas d
                JOIN materias_primas m ON d.detpedmat_matprim_id = m.matprim_id
                WHERE d.detpedmat_ped_id = %s
            """, (pedido_id,))
            items.extend(cursor.fetchall())

            for item in items:
                item['cantidad_esperada'] = float(item['cantidad_esperada'])

            return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()
# --- 4. API: CONFIRMAR RECEPCIÓN (Corrección Lógica Origen + Precios) ---
@app.route('/api/confirmar_recepcion', methods=['POST'])
def api_confirmar_recepcion():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401
    
    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    
    data = request.json
    pedido_id = data.get('pedido_id')
    items_recibidos = data.get('items', []) 
    accion_faltante = data.get('accion_faltante', 'CERRAR')

    if not pedido_id or not items_recibidos:
        return jsonify({'success': False, 'message': 'Datos incompletos.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            items_backorder_prod = []
            items_backorder_mat = []

            for item in items_recibidos:
                tipo = item.get('tipo')
                item_id = item.get('id')
                cantidad_recibida = float(item.get('cantidad_recibida'))
                cantidad_esperada = float(item.get('cantidad_esperada'))

                if cantidad_recibida < 0: 
                    raise Exception(f"Error en ítem {item_id}: Cantidad negativa.")
                
                # Detectar faltantes para backorder
                if cantidad_recibida < cantidad_esperada and accion_faltante == 'BACKORDER':
                    diferencia = cantidad_esperada - cantidad_recibida
                    if tipo == 'producto':
                        items_backorder_prod.append({'id': item_id, 'cant': diferencia})
                    elif tipo == 'materia':
                        items_backorder_mat.append({'id': item_id, 'cant': diferencia})

                # Actualizar Inventario con lo REAL recibido
                if cantidad_recibida > 0:
                    if tipo == 'producto':
                        cursor.execute("SELECT pro_nombre, pro_unimed FROM productos WHERE pro_id = %s", (item_id,))
                        info = cursor.fetchone()
                        if info:
                            cursor.execute("""
                                INSERT INTO inventario_productos (invpro_pro_fk, invpro_suc_fk, pro_nombre, pro_stock, invpro_unimed_fk)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE pro_stock = pro_stock + VALUES(pro_stock)
                            """, (item_id, sucursal_id, info['pro_nombre'], cantidad_recibida, info['pro_unimed']))
                            
                            cursor.execute("""
                                INSERT INTO movimientos_productos (mov_suc_fk, mov_pro_fk, mov_emp_fk, mov_cantidad, mov_tipo, mov_motivo, mov_referencia_id, stock_anterior, stock_nuevo)
                                SELECT %s, %s, %s, %s, 'ENTRADA', 'RECEPCION_PEDIDO', %s, pro_stock - %s, pro_stock 
                                FROM inventario_productos WHERE invpro_pro_fk = %s AND invpro_suc_fk = %s
                            """, (sucursal_id, item_id, empleado_id, cantidad_recibida, pedido_id, cantidad_recibida, item_id, sucursal_id))

                    elif tipo == 'materia':
                        cursor.execute("SELECT matprim_nombre, matprim_unimed FROM materias_primas WHERE matprim_id = %s", (item_id,))
                        info = cursor.fetchone()
                        if info:
                            cursor.execute("""
                                INSERT INTO inventario_materias_primas (invmatprim_matprim_fk, invmatprim_suc_fk, invmatprim_matprim_nombre, invmatprim_stock, invmatprim_unimed)
                                VALUES (%s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE invmatprim_stock = invmatprim_stock + VALUES(invmatprim_stock)
                            """, (item_id, sucursal_id, info['matprim_nombre'], cantidad_recibida, info['matprim_unimed']))

            # --- GENERACIÓN DE PEDIDO HIJO (CORREGIDO) ---
            msg_extra = ""
            if accion_faltante == 'BACKORDER' and (items_backorder_prod or items_backorder_mat):
                # CORRECCIÓN: Incluimos ped_usu_id y ped_emp_id tal cual vienen del original
                sql_header = """
                    INSERT INTO pedidos (ped_fecha_pedido, ped_sucursal_origen, ped_sucursal_destino, ped_emp_id, ped_usu_id, ped_asunto, ped_comentarios, ped_monto_total, ped_estado_pedido, ped_prov_fk)
                    SELECT CURDATE(), ped_sucursal_origen, ped_sucursal_destino, ped_emp_id, ped_usu_id, CONCAT(ped_asunto, ' (Faltante)'), 'Generado por faltante en recepción', 0, 'P', ped_prov_fk
                    FROM pedidos WHERE ped_id = %s
                """
                cursor.execute(sql_header, (pedido_id,))
                new_id = cursor.lastrowid
                
                # Copiamos detalles incluyendo precio original
                for i in items_backorder_prod:
                    cursor.execute("SELECT detpedpro_precio_unitario FROM detalle_pedido_productos WHERE detpedpro_ped_id=%s AND detpedpro_pro_id=%s", (pedido_id, i['id']))
                    res = cursor.fetchone()
                    precio = res['detpedpro_precio_unitario'] if res else 0
                    
                    cursor.execute("INSERT INTO detalle_pedido_productos (detpedpro_ped_id, detpedpro_pro_id, detpedpro_cantidad, detpedpro_precio_unitario) VALUES (%s, %s, %s, %s)", (new_id, i['id'], i['cant'], precio))
                
                for i in items_backorder_mat:
                    cursor.execute("SELECT detpedmat_precio_unitario FROM detalle_pedido_materias_primas WHERE detpedmat_ped_id=%s AND detpedmat_matprim_id=%s", (pedido_id, i['id']))
                    res = cursor.fetchone()
                    precio = res['detpedmat_precio_unitario'] if res else 0

                    cursor.execute("INSERT INTO detalle_pedido_materias_primas (detpedmat_ped_id, detpedmat_matprim_id, detpedmat_cantidad, detpedmat_precio_unitario) VALUES (%s, %s, %s, %s)", (new_id, i['id'], i['cant'], precio))
                
                msg_extra = f" Se creó el Pedido #{new_id} con los faltantes."

            # Cerrar el ciclo
            cursor.execute("UPDATE pedidos SET ped_estado_pedido = 'C' WHERE ped_id = %s", (pedido_id,))
            cursor.execute("UPDATE repartos SET rep_estado_reparto = 'E' WHERE rep_ped_id = %s", (pedido_id,))
            
            connection.commit()
            return jsonify({'success': True, 'message': f'Recepción #{pedido_id} registrada.{msg_extra}'})
            
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en confirmar_recepcion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()

# --- 5. NUEVA API: BUSCADOR UNIFICADO (Productos + Materias Primas) ---
@app.route('/api/buscar_productos')
def api_buscar_productos():
    if 'sucursal' not in session: return jsonify([])
    
    query_str = request.args.get('q', '').strip()
    if not query_str or len(query_str) < 1: return jsonify([]) 

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # CONSULTA UNIFICADA: Busca en ambas tablas y agrega la columna 'tipo'
            sql = """
                (SELECT pro_id as id, pro_nombre as nombre, pro_unimed as unidad, 'producto' as tipo 
                FROM productos 
                WHERE pro_nombre LIKE %s OR CAST(pro_id AS CHAR) LIKE %s
                LIMIT 5)
                UNION ALL
                (SELECT matprim_id as id, matprim_nombre as nombre, matprim_unimed as unidad, 'materia' as tipo 
                FROM materias_primas 
                WHERE matprim_nombre LIKE %s OR CAST(matprim_id AS CHAR) LIKE %s
                LIMIT 5)
            """
            param = f"%{query_str}%"
            # Pasamos el parámetro 4 veces (2 por cada tabla)
            cursor.execute(sql, (param, param, param, param))
            resultados = cursor.fetchall()
            return jsonify(resultados)
    except Exception as e:
        print(f"Error búsqueda: {e}")
        return jsonify([])
    finally:
        if connection: connection.close()

# --- 6. API: REGISTRAR ENTRADA MANUAL (CORREGIDA) ---
@app.route('/api/registrar_entrada_manual', methods=['POST'])
def api_registrar_entrada_manual():
    if 'emp_id' not in session or 'sucursal' not in session: return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.json
    items = data.get('items', [])
    motivo = data.get('motivo', 'Ajuste Manual')
    sucursal_id = session['sucursal']
    empleado_id = session['emp_id']
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        # CORRECCIÓN 1: Usamos DictCursor
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()
            for item in items:
                item_id = item.get('id')
                cantidad = float(item.get('cantidad'))
                tipo = item.get('tipo', 'producto') 
                
                if tipo == 'producto':
                    cursor.execute("SELECT pro_nombre, pro_unimed FROM productos WHERE pro_id = %s", (item_id,))
                    info = cursor.fetchone()
                    if not info: continue

                    # CORRECCIÓN 2: Usamos claves de diccionario
                    cursor.execute("""
                        INSERT INTO inventario_productos (invpro_pro_fk, invpro_suc_fk, pro_nombre, pro_stock, invpro_unimed_fk)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE pro_stock = pro_stock + VALUES(pro_stock)
                    """, (item_id, sucursal_id, info['pro_nombre'], cantidad, info['pro_unimed'])) # info['pro_unimed'] en lugar de info[1]

                    cursor.execute("""
                        INSERT INTO movimientos_productos (mov_suc_fk, mov_pro_fk, mov_emp_fk, mov_cantidad, mov_tipo, mov_motivo, mov_referencia_id, stock_anterior, stock_nuevo)
                        SELECT %s, %s, %s, %s, 'ENTRADA', %s, 0, pro_stock - %s, pro_stock 
                        FROM inventario_productos WHERE invpro_pro_fk = %s AND invpro_suc_fk = %s
                    """, (sucursal_id, item_id, empleado_id, cantidad, motivo, cantidad, item_id, sucursal_id))
                
                elif tipo == 'materia':
                    cursor.execute("SELECT matprim_nombre, matprim_unimed FROM materias_primas WHERE matprim_id = %s", (item_id,))
                    info = cursor.fetchone()
                    if not info: continue

                    # CORRECCIÓN 3: Usamos claves de diccionario (Esto corrige el error reported)
                    cursor.execute("""
                        INSERT INTO inventario_materias_primas (invmatprim_matprim_fk, invmatprim_suc_fk, invmatprim_matprim_nombre, invmatprim_stock, invmatprim_unimed)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE invmatprim_stock = invmatprim_stock + VALUES(invmatprim_stock)
                    """, (item_id, sucursal_id, info['matprim_nombre'], cantidad, info['matprim_unimed']))
            
            connection.commit()
            return jsonify({'success': True, 'message': 'Entrada manual registrada.'})
            
    except Exception as e:
        if connection: connection.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()


# ==============================================================================
# MÓDULO: REGISTRO DE SALIDAS (ALMACÉN)
# ==============================================================================

# ==============================================================================
# MÓDULO: REGISTRO DE SALIDAS (ALMACÉN)
# ==============================================================================

# --- 1. RUTA DE VISTA ---
@app.route('/registrarSalidas')
def registrar_salidas_vista():
    if 'sucursal' not in session: return redirect(url_for('login'))
    return render_template('almRegistrarSalidas.jinja2')

# --- 2. API: VER PEDIDOS POR SURTIR (Donde yo soy el ORIGEN) ---
@app.route('/api/pedidos_por_surtir')
def api_pedidos_por_surtir():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    mi_sucursal_id = session['sucursal']
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Buscamos pedidos donde YO (mi sucursal) soy el ORIGEN y el estado es 'P'
            query = """
                SELECT 
                    p.ped_id, 
                    p.ped_fecha_pedido, 
                    p.ped_asunto, 
                    p.ped_monto_total,
                    p.ped_fecha_entrega,
                    COALESCE(s_dest.suc_nombre, 'Cliente Externo') as destino
                FROM pedidos p
                LEFT JOIN sucursales s_dest ON p.ped_sucursal_destino = s_dest.suc_id
                WHERE p.ped_sucursal_origen = %s 
                AND p.ped_estado_pedido = 'P'
                AND p.ped_fecha_entrega = CURDATE()
                ORDER BY p.ped_fecha_entrega ASC, p.ped_fecha_pedido ASC
            """
            cursor.execute(query, (mi_sucursal_id,))
            pedidos = cursor.fetchall()
            
            # Formateo de datos
            for p in pedidos: 
                p['ped_monto_total'] = float(p['ped_monto_total'])
                if p['ped_fecha_pedido']:
                    p['ped_fecha_pedido'] = p['ped_fecha_pedido'].strftime('%d/%m/%Y')
                if p['ped_fecha_entrega']:
                    p['ped_fecha_entrega'] = p['ped_fecha_entrega'].strftime('%d/%m/%Y')
                else:
                    p['ped_fecha_entrega'] = "Sin fecha"
            
            return jsonify(pedidos)
    except Exception as e:
        print(f"Error pedidos por surtir: {e}")
        return jsonify([])
    finally:
        if connection: connection.close()

# --- 3. API: SURTIR PEDIDO (Salida Automática por Pedido) ---
@app.route('/api/surtir_pedido', methods=['POST'])
def api_surtir_pedido():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401
    
    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    pedido_id = request.json.get('pedido_id')

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            # 1. Obtener detalles (Productos y Materias Primas del pedido)
            # PRODUCTOS
            cursor.execute("SELECT detpedpro_pro_id as id, detpedpro_cantidad as cant, 'producto' as tipo FROM detalle_pedido_productos WHERE detpedpro_ped_id = %s", (pedido_id,))
            items_prod = cursor.fetchall()
            # MATERIAS PRIMAS
            cursor.execute("SELECT detpedmat_matprim_id as id, detpedmat_cantidad as cant, 'materia' as tipo FROM detalle_pedido_materias_primas WHERE detpedmat_ped_id = %s", (pedido_id,))
            items_mat = cursor.fetchall()
            
            # --- CORRECCIÓN DE ERROR: Convertimos ambos a lista antes de sumar ---
            todos_items = list(items_prod) + list(items_mat)

            if not todos_items:
                raise Exception("El pedido está vacío, no se puede surtir.")

            # 2. Procesar Descuentos de Inventario
            for item in todos_items:
                item_id = item['id']
                cantidad = float(item['cant'])
                tipo = item['tipo']

                if tipo == 'producto':
                    # Verificar Stock (Bloqueo FOR UPDATE para evitar errores de concurrencia)
                    cursor.execute("SELECT pro_stock FROM inventario_productos WHERE invpro_pro_fk=%s AND invpro_suc_fk=%s FOR UPDATE", (item_id, sucursal_id))
                    stock_row = cursor.fetchone()
                    if not stock_row or float(stock_row['pro_stock']) < cantidad:
                        raise Exception(f"Stock insuficiente del Producto ID {item_id}")

                    # Restar Stock
                    cursor.execute("UPDATE inventario_productos SET pro_stock = pro_stock - %s WHERE invpro_pro_fk=%s AND invpro_suc_fk=%s", (cantidad, item_id, sucursal_id))
                    
                    # Auditoría
                    cursor.execute("""
                        INSERT INTO movimientos_productos (mov_suc_fk, mov_pro_fk, mov_emp_fk, mov_cantidad, mov_tipo, mov_motivo, mov_referencia_id, stock_anterior, stock_nuevo) 
                        VALUES (%s,%s,%s,%s,'SALIDA','SURTIDO_PEDIDO',%s,%s,%s)
                    """, (sucursal_id, item_id, empleado_id, cantidad, pedido_id, stock_row['pro_stock'], float(stock_row['pro_stock']) - cantidad))

                elif tipo == 'materia':
                    # Verificar Stock Materia
                    cursor.execute("SELECT invmatprim_stock FROM inventario_materias_primas WHERE invmatprim_matprim_fk=%s AND invmatprim_suc_fk=%s FOR UPDATE", (item_id, sucursal_id))
                    stock_row = cursor.fetchone()
                    if not stock_row or float(stock_row['invmatprim_stock']) < cantidad:
                        raise Exception(f"Stock insuficiente de Materia Prima ID {item_id}")

                    # Restar Stock Materia
                    cursor.execute("UPDATE inventario_materias_primas SET invmatprim_stock = invmatprim_stock - %s WHERE invmatprim_matprim_fk=%s AND invmatprim_suc_fk=%s", (cantidad, item_id, sucursal_id))
                    
                    # Auditoría Materia
                    cursor.execute("""
                        INSERT INTO movimientos_materias_primas (movmp_suc_fk, movmp_matprim_fk, movmp_emp_fk, movmp_cantidad, movmp_tipo, movmp_motivo, movmp_referencia_id, stock_anterior, stock_nuevo) 
                        VALUES (%s,%s,%s,%s,'SALIDA','SURTIDO_PEDIDO',%s,%s,%s)
                    """, (sucursal_id, item_id, empleado_id, cantidad, pedido_id, stock_row['invmatprim_stock'], float(stock_row['invmatprim_stock']) - cantidad))

            # 3. Actualizar estado del pedido a 'R' (En Reparto / Ruta)
            cursor.execute("UPDATE pedidos SET ped_estado_pedido = 'R' WHERE ped_id = %s", (pedido_id,))
            
            # Opcional: Crear registro inicial en tabla REPARTOS si se maneja ese módulo
            cursor.execute("""
                INSERT INTO repartos (rep_ped_id, rep_suc_origen, rep_suc_destino, rep_fecha_entrega, rep_estado_reparto)
                SELECT ped_id, ped_sucursal_origen, ped_sucursal_destino, ped_fecha_entrega, 'R'
                FROM pedidos WHERE ped_id = %s
                ON DUPLICATE KEY UPDATE rep_estado_reparto = 'R'
            """, (pedido_id,))

            connection.commit()
            return jsonify({'success': True, 'message': f'Pedido #{pedido_id} surtido exitosamente.'})

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al surtir pedido: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()

# --- 4. API: REGISTRAR SALIDA MANUAL (Producción, Merma, etc.) ---
@app.route('/api/registrar_salida_manual', methods=['POST'])
def api_registrar_salida_manual():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_id = session['sucursal']
    empleado_id = session['emp_id']
    data = request.json
    
    items = data.get('items', [])
    motivo = data.get('motivo', 'Consumo Interno')

    if not items: return jsonify({'success': False, 'message': 'Lista vacía'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()
            
            for item in items:
                tipo = item.get('tipo')
                item_id = item.get('id')
                cantidad = float(item.get('cantidad'))

                if cantidad <= 0: raise Exception("Cantidad inválida")

                if tipo == 'producto':
                    cursor.execute("SELECT pro_stock FROM inventario_productos WHERE invpro_pro_fk=%s AND invpro_suc_fk=%s FOR UPDATE", (item_id, sucursal_id))
                    row = cursor.fetchone()
                    if not row or float(row['pro_stock']) < cantidad: raise Exception(f"Stock insuficiente Prod ID {item_id}")
                    
                    cursor.execute("UPDATE inventario_productos SET pro_stock = pro_stock - %s WHERE invpro_pro_fk=%s AND invpro_suc_fk=%s", (cantidad, item_id, sucursal_id))
                    
                    cursor.execute("INSERT INTO movimientos_productos (mov_suc_fk, mov_pro_fk, mov_emp_fk, mov_cantidad, mov_tipo, mov_motivo, stock_anterior, stock_nuevo) VALUES (%s,%s,%s,%s,'SALIDA',%s,%s,%s)", (sucursal_id, item_id, empleado_id, cantidad, motivo, row['pro_stock'], float(row['pro_stock'])-cantidad))

                elif tipo == 'materia':
                    cursor.execute("SELECT invmatprim_stock FROM inventario_materias_primas WHERE invmatprim_matprim_fk=%s AND invmatprim_suc_fk=%s FOR UPDATE", (item_id, sucursal_id))
                    row = cursor.fetchone()
                    if not row or float(row['invmatprim_stock']) < cantidad: raise Exception(f"Stock insuficiente Materia ID {item_id}")

                    cursor.execute("UPDATE inventario_materias_primas SET invmatprim_stock = invmatprim_stock - %s WHERE invmatprim_matprim_fk=%s AND invmatprim_suc_fk=%s", (cantidad, item_id, sucursal_id))
                    
                    cursor.execute("INSERT INTO movimientos_materias_primas (movmp_suc_fk, movmp_matprim_fk, movmp_emp_fk, movmp_cantidad, movmp_tipo, movmp_motivo, stock_anterior, stock_nuevo) VALUES (%s,%s,%s,%s,'SALIDA',%s,%s,%s)", (sucursal_id, item_id, empleado_id, cantidad, motivo, row['invmatprim_stock'], float(row['invmatprim_stock'])-cantidad))

            connection.commit()
        return jsonify({'success': True, 'message': 'Salida registrada correctamente.'})
    except Exception as e:
        if connection: connection.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()




# __________________________________________________________
# INICIO ENDPOINT REPARTO
@app.route('/reparto')
def reparto():
    return render_template('reparto.jinja2')

@app.route('/CalendarioReparto')
def repCalendario():
    calendario_status = {}
    
    # 1. Validación de Sesión y Sucursal
    if 'emp_id' not in session or 'sucursal' not in session:
        return redirect(url_for('login'))
    
    sucursal_id = session['sucursal']

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # --- CAMBIO LÓGICO: Fuente de verdad = Tabla REPARTOS ---
            # Solo traemos repartos de la sucursal actual
            query = """
                SELECT 
                    DATE(rep_fecha_entrega) as fecha_entrega, 
                    rep_estado_reparto 
                FROM repartos 
                WHERE rep_suc_origen = %s
            """
            cursor.execute(query, (sucursal_id,))
            eventos = cursor.fetchall()
            
            # 2. Agrupar eventos por fecha
            eventos_por_dia = {}
            for evento in eventos:
                fecha_str = evento['fecha_entrega'].strftime('%Y-%m-%d')
                if fecha_str not in eventos_por_dia:
                    eventos_por_dia[fecha_str] = []
                eventos_por_dia[fecha_str].append(evento['rep_estado_reparto'])
            
            # 3. Lógica del Semáforo (Basada en Estados de Reparto: R, E, X)
            hoy = date.today()
            
            for fecha_str, estados in eventos_por_dia.items():
                fecha_objeto = date.fromisoformat(fecha_str)
                
                # 'E' = Entregado. Consideramos 'X' (Cancelado) como finalizado también para no alertar.
                todos_finalizados = all(estado in ['E', 'X'] for estado in estados)
                
                # Si hay algo en 'R' (Reparto) o 'P' (Pendiente), está activo.
                hay_activos = any(estado in ['R', 'P'] for estado in estados)

                if fecha_objeto < hoy and hay_activos:
                    # Fecha ya pasó y hay cosas sin entregar = URGENTE
                    calendario_status[fecha_str] = 'rojo' 
                elif todos_finalizados:
                    # Todo entregado o cancelado = OK
                    calendario_status[fecha_str] = 'verde'
                else:
                    # Fecha futura o día actual con activos = EN PROCESO
                    calendario_status[fecha_str] = 'amarillo'

    except Exception as e:
        print(f"Error al generar calendario: {e}")
        return "Error en servidor", 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
    
    return render_template('repCalendario.jinja2', calendario_status=calendario_status)


@app.route('/api/entregas_por_fecha/<fecha>', methods=['GET'])
def api_entregas_por_fecha(fecha):
    if 'sucursal' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    sucursal_id = session['sucursal']
    
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # --- CAMBIO LÓGICO: Join principal desde REPARTOS ---
            # Filtramos por fecha y por sucursal de origen
            query = """
                SELECT 
                    p.ped_hora_entrega,
                    p.ped_id,
                    s.suc_nombre AS sucursal_destino_nombre,
                    p.ped_asunto,
                    r.rep_estado_reparto, -- ESTADO VIENE DEL REPARTO
                    p.ped_monto_total
                FROM 
                    repartos r
                JOIN 
                    pedidos p ON r.rep_ped_id = p.ped_id
                LEFT JOIN 
                    sucursales s ON r.rep_suc_destino = s.suc_id
                WHERE 
                    r.rep_fecha_entrega = %s
                    AND r.rep_suc_origen = %s
                ORDER BY 
                    p.ped_hora_entrega ASC
            """
            cursor.execute(query, (fecha, sucursal_id))
            entregas = cursor.fetchall()
            
            # Formateo de datos
            for ent in entregas:
                # Hora
                if ent['ped_hora_entrega']:
                    if hasattr(ent['ped_hora_entrega'], 'total_seconds'):
                        seconds = ent['ped_hora_entrega'].total_seconds()
                        horas = int(seconds // 3600)
                        minutos = int((seconds % 3600) // 60)
                        ent['ped_hora_entrega'] = f"{horas:02}:{minutos:02}"
                    else:
                        ent['ped_hora_entrega'] = str(ent['ped_hora_entrega'])[:5]
                else:
                    ent['ped_hora_entrega'] = '--:--'
                
                # Monto
                ent['ped_monto_total'] = float(ent['ped_monto_total'])

            return jsonify(entregas)
            
    except Exception as e:
        print(f"Error API entregas: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@app.route('/Pedidos')
def repPedidos():
    if 'emp_id' not in session:
        return redirect(url_for('login')) 
    
    emp_id = session['emp_id']
    filtro_actual = request.args.get('filtro', 'dia') 

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT emp_sucursal FROM empleados WHERE emp_id = %s", (emp_id,))
            empleado = cursor.fetchone()
            if not empleado:
                return "Empleado no encontrado", 404
            
            sucursal_origen_empleado = empleado['emp_sucursal']

            # --- Query Base ---
            base_query = """
                SELECT 
                    p.ped_id, 
                    p.ped_fecha_pedido, 
                    p.ped_monto_total,
                    s.suc_nombre AS sucursal_destino_nombre, 
                    p.ped_asunto, 
                    p.ped_comentarios,
                    p.ped_fecha_entrega,
                    p.ped_hora_entrega,
                    p.ped_estado_pedido
                FROM 
                    pedidos p
                JOIN 
                    sucursales s ON p.ped_sucursal_destino = s.suc_id
                WHERE 
                    p.ped_sucursal_origen = %s
            """
            
            # --- LÓGICA DE FILTRADO ---
            if filtro_actual == 'pendientes':
                # Pendientes: Sin fecha de entrega definida Y que no estén completados
                base_query += " AND p.ped_fecha_entrega IS NULL AND p.ped_estado_pedido != 'C' OR (p.ped_fecha_entrega != CURDATE() AND p.ped_estado_pedido ='P')"
            else:
                # Del día: (Creados HOY) O (Para entregar HOY)
                base_query += """ 
                    AND (
                        DATE(p.ped_fecha_pedido) = CURDATE() 
                        OR 
                        DATE(p.ped_fecha_entrega) = CURDATE()
                    )
                """

            # 4. Ordenamiento
            base_query += " ORDER BY COALESCE(p.ped_fecha_entrega, p.ped_fecha_pedido) ASC, p.ped_hora_entrega ASC"

            cursor.execute(base_query, (sucursal_origen_empleado,))
            lista_pedidos = cursor.fetchall()
            
            # --- CORRECCIÓN DE HORA (Igual que en Actualizar Repartos) ---
            # Convertimos el objeto timedelta a string limpio "HH:MM"
            for pedido in lista_pedidos:
                if pedido['ped_hora_entrega']:
                    # Verificamos si es un objeto timedelta (tiene total_seconds)
                    if hasattr(pedido['ped_hora_entrega'], 'total_seconds'):
                        seconds = pedido['ped_hora_entrega'].total_seconds()
                        horas = int(seconds // 3600)
                        minutos = int((seconds % 3600) // 60)
                        pedido['ped_hora_entrega'] = f"{horas:02}:{minutos:02}"
                    else:
                        # Si por alguna razón ya es string, lo dejamos o lo cortamos
                        pedido['ped_hora_entrega'] = str(pedido['ped_hora_entrega'])[:5]
                else:
                    pedido['ped_hora_entrega'] = None # Aseguramos que sea None si está vacío

            return render_template('repPedidos.jinja2', pedidos=lista_pedidos, filtro_actual=filtro_actual)

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
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # --- CONSULTA MEJORADA CON LÓGICA DE ORIGEN ---
            query = """
                SELECT 
                    p.*,
                    -- Lógica Inteligente para el ORIGEN
                    CASE 
                        WHEN p.ped_prov_fk IS NOT NULL THEN CONCAT('Proveedor: ', prov.prov_nombre_empresa)
                        WHEN p.ped_usu_id IS NOT NULL THEN CONCAT('Cliente Web: ', u.usu_nombre)
                        WHEN s_origen.suc_nombre IS NOT NULL THEN CONCAT('Sucursal: ', s_origen.suc_nombre)
                        ELSE 'Origen Desconocido'
                    END as origen_nombre,
                    
                    -- Lógica para el DESTINO
                    COALESCE(s_destino.suc_nombre, 'Destino Externo') as destino_nombre,
                    COALESCE(s_destino.suc_direccion, 'Dirección no disponible') as destino_direccion,
                    
                    -- Creador del pedido
                    COALESCE(e.emp_nombre, u.usu_nombre, 'Sistema') AS creador_nombre

                FROM pedidos p
                LEFT JOIN sucursales s_origen ON p.ped_sucursal_origen = s_origen.suc_id
                LEFT JOIN sucursales s_destino ON p.ped_sucursal_destino = s_destino.suc_id
                LEFT JOIN empleados e ON p.ped_emp_id = e.emp_id
                LEFT JOIN usuarios u ON p.ped_usu_id = u.usu_id
                LEFT JOIN proveedores prov ON p.ped_prov_fk = prov.prov_id -- JOIN CRÍTICO AGREGADO
                WHERE p.ped_id = %s
            """
            cursor.execute(query, (pedido_id,))
            pedido_detalle = cursor.fetchone()

            if not pedido_detalle:
                return jsonify({'error': 'Pedido no encontrado'}), 404

            # --- 1. Buscar productos asociados ---
            query_productos = """
                SELECT dp.detpedpro_cantidad, p.pro_nombre, p.pro_unimed 
                FROM detalle_pedido_productos dp 
                JOIN productos p ON dp.detpedpro_pro_id = p.pro_id 
                WHERE dp.detpedpro_ped_id = %s
            """
            cursor.execute(query_productos, (pedido_id,))
            pedido_detalle['productos'] = cursor.fetchall()

            # --- 2. Buscar materias primas asociadas ---
            query_materias = """
                SELECT dm.detpedmat_cantidad, mp.matprim_nombre, mp.matprim_unimed
                FROM detalle_pedido_materias_primas dm 
                JOIN materias_primas mp ON dm.detpedmat_matprim_id = mp.matprim_id 
                WHERE dm.detpedmat_ped_id = %s
            """
            cursor.execute(query_materias, (pedido_id,))
            pedido_detalle['materias_primas'] = cursor.fetchall()

            # --- Formateo de Datos ---
            if pedido_detalle.get('ped_fecha_pedido'):
                pedido_detalle['ped_fecha_pedido'] = pedido_detalle['ped_fecha_pedido'].strftime('%Y-%m-%d')
            
            if pedido_detalle.get('ped_fecha_entrega'):
                pedido_detalle['ped_fecha_entrega'] = pedido_detalle['ped_fecha_entrega'].strftime('%Y-%m-%d')
            else:
                pedido_detalle['ped_fecha_entrega'] = 'Pendiente'
            
            if pedido_detalle.get('ped_hora_entrega'):
                pedido_detalle['ped_hora_entrega'] = str(pedido_detalle['ped_hora_entrega'])
            else:
                pedido_detalle['ped_hora_entrega'] = '--:--'

            pedido_detalle['ped_monto_total'] = float(pedido_detalle['ped_monto_total'])
            
            return jsonify(pedido_detalle)

    except Exception as e:
        print(f"Error en API detalle pedido: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500
    finally:
        if connection: connection.close()

@app.route("/repDia")
def ver_repartos_dia():
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        
        # --- BLOQUE DE AUTOMATIZACIÓN (CORREGIDO) ---
        # Antes de consultar, generamos los repartos faltantes para hoy
        with connection.cursor() as cursor:
            connection.begin()
            
            # 1. Insertar repartos automáticamente para pedidos de HOY
            # CORRECCIÓN: Eliminamos 'rep_hora_entrega' ya que esa columna NO existe en la tabla repartos.
            query_auto_create = """
                INSERT INTO repartos (
                    rep_ped_id, 
                    rep_suc_origen, 
                    rep_suc_destino, 
                    rep_fecha_entrega, 
                    rep_estado_reparto
                )
                SELECT
                    ped_id,
                    ped_sucursal_origen,
                    ped_sucursal_destino,
                    ped_fecha_entrega,
                    'R'
                FROM pedidos
                WHERE 
                    ped_fecha_entrega = CURDATE()
                    AND ped_estado_pedido = 'R'
                    -- Evitamos duplicados: Solo si NO existe ya en repartos
                    AND ped_id NOT IN (SELECT rep_ped_id FROM repartos)
            """
            cursor.execute(query_auto_create)
            connection.commit()

        # --- BLOQUE DE CONSULTA ---
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
            SELECT
                r.rep_id,
                r.rep_estado_reparto,
                r.rep_fecha_entrega,
                p.ped_id,
                p.ped_asunto,
                p.ped_comentarios,
                p.ped_monto_total,
                p.ped_hora_entrega, -- La hora viene de la tabla pedidos
                suc_origen.suc_nombre AS sucursal_origen,
                suc_destino.suc_nombre AS sucursal_destino
            FROM
                repartos r
            JOIN
                pedidos p ON r.rep_ped_id = p.ped_id
            LEFT JOIN
                sucursales suc_origen ON r.rep_suc_origen = suc_origen.suc_id
            LEFT JOIN
                sucursales suc_destino ON r.rep_suc_destino = suc_destino.suc_id
            WHERE
                r.rep_fecha_entrega = CURDATE() AND r.rep_estado_reparto in ('R','E')
            ORDER BY 
                p.ped_hora_entrega ASC -- CORRECCIÓN: Ordenamos por la hora del PEDIDO
            """)
            pedidos = cursor.fetchall()

            # Formateo de hora en Python para la vista
            for p in pedidos:
                if p['ped_hora_entrega']:
                     if hasattr(p['ped_hora_entrega'], 'total_seconds'):
                        seconds = p['ped_hora_entrega'].total_seconds()
                        horas = int(seconds // 3600)
                        minutos = int((seconds % 3600) // 60)
                        p['ped_hora_entrega'] = f"{horas:02}:{minutos:02}"
                     else:
                        p['ped_hora_entrega'] = str(p['ped_hora_entrega'])[:5]
            
        return render_template("repDia.jinja2", pedidos=pedidos)

    except Exception as e:
        print(f"Error en Repartos del Día: {e}")
        if connection:
            connection.rollback()
        return "Error al procesar los repartos del día", 500
    finally:
        if connection:
            connection.close()
            
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
            SET ped_estado_pedido = 'R'
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



# ==============================================================================
# MÓDULO: GESTIÓN LOGÍSTICA (MONITOR DE LOGÍSTICA)
# Reemplaza: /agregarRepartos, /crear_reparto, /actualizarRepartos
# ==============================================================================

@app.route('/gestionLogistica')
def vista_gestion_logistica():
    """
    Muestra TODOS los pedidos ACTIVOS (Pendientes y En Reparto) de la SUCURSAL ACTUAL.
    FILTRO DE SEGURIDAD: Oculta pedidos Completados, Entregados o Cancelados.
    """
    # 1. Validación de Sesión
    if 'emp_id' not in session:
        return redirect(url_for('login'))
    
    # OPTIMIZACIÓN: Obtener sucursal directamente de la sesión
    sucursal_origen = session.get('sucursal')
    
    # Validación extra por si la sesión está corrupta o incompleta
    if not sucursal_origen:
        return redirect(url_for('login'))

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 2. Consulta Blindada
            # Ya no hacemos la query extra a 'empleados', usamos la variable de sesión directa.
            query = """
                SELECT 
                    p.ped_id, 
                    p.ped_asunto,
                    r.rep_id, -- Será NULL si el pedido está Pendiente puro
                    
                    -- Fecha y Estado (Coalesce para priorizar Reparto si existe)
                    COALESCE(r.rep_fecha_entrega, p.ped_fecha_entrega) as fecha_programada,
                    COALESCE(r.rep_estado_reparto, p.ped_estado_pedido) as estado_actual,
                    
                    -- Hora del pedido
                    p.ped_hora_entrega
                    
                FROM pedidos p
                LEFT JOIN repartos r ON p.ped_id = r.rep_ped_id
                
                WHERE 
                    -- A. Filtro de Sucursal (Seguridad)
                    p.ped_sucursal_origen = %s
                    
                    -- B. Filtro de Estado del Pedido Maestro
                    -- No mostrar si ya está Completado (C) o Cancelado (X)
                    AND p.ped_estado_pedido NOT IN ('X', 'C')
                    
                    -- C. Filtro de Estado del Reparto (Lógica Correctora)
                    -- Muestra si NO tiene reparto (NULL) -> Pendientes
                    -- O si tiene reparto pero NO es Entregado (E) ni Cancelado (X)
                    AND (
                        r.rep_estado_reparto IS NULL 
                        OR 
                        r.rep_estado_reparto NOT IN ('X', 'E')
                    )
                
                -- Ordenamiento
                ORDER BY 
                    FIELD(COALESCE(r.rep_estado_reparto, p.ped_estado_pedido), 'R', 'P'),
                    fecha_programada DESC,
                    p.ped_hora_entrega ASC
            """
            cursor.execute(query, (sucursal_origen,))
            registros = cursor.fetchall()

            # --- Formateo de Hora ---
            for reg in registros:
                if reg['ped_hora_entrega']:
                    if hasattr(reg['ped_hora_entrega'], 'total_seconds'):
                        seconds = reg['ped_hora_entrega'].total_seconds()
                        horas = int(seconds // 3600)
                        minutos = int((seconds % 3600) // 60)
                        reg['ped_hora_entrega'] = f"{horas:02}:{minutos:02}"
                    else:
                        reg['ped_hora_entrega'] = str(reg['ped_hora_entrega'])[:5]
                else:
                    reg['ped_hora_entrega'] = ""

            return render_template('repGestionLogistica.jinja2', registros=registros)

    except Exception as e:
        print(f"Error en Gestión Logística: {e}")
        return "Error al cargar el monitor logístico", 500
    finally:
        if connection:
            connection.close()


@app.route('/guardar_gestion_logistica', methods=['POST'])
def guardar_gestion_logistica():
    if 'emp_id' not in session:
        return jsonify({'error': 'Sesión expirada'}), 401

    datos = request.get_json()
    ped_id = datos.get('ped_id')
    
    # Limpieza de datos
    fecha = datos.get('fecha')
    if fecha == "": fecha = None
    
    hora = datos.get('hora')
    if hora == "": hora = None
    
    nuevo_estado = datos.get('estado', '').upper()

    if not ped_id:
        return jsonify({'error': 'Falta el ID del pedido'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            connection.begin()

            # ... (Aquí va tu lógica de mapeo de estados igual que antes) ...
            map_estado_pedido = {'P': 'P', 'R': 'R', 'E': 'R', 'X': 'X'}
            est_ped = map_estado_pedido.get(nuevo_estado, 'P')

            cursor.execute("SELECT rep_id FROM repartos WHERE rep_ped_id = %s", (ped_id,))
            existe = cursor.fetchone()

            # --- AQUI ES DONDE OCURRE LA MAGIA DEL MANEJO DE ERRORES ---
            # Intentamos ejecutar la lógica. Si la BD rechaza el NULL, saltará al 'except'
            
            if existe:
                # Si no mandas fecha y la BD es estricta, esto fallará y lo atraparemos abajo
                cursor.execute("""
                    UPDATE repartos 
                    SET rep_fecha_entrega = %s, rep_estado_reparto = %s 
                    WHERE rep_ped_id = %s
                """, (fecha, nuevo_estado, ped_id))
            else:
                # Intentamos insertar. Si fecha es None y la columna es NOT NULL, fallará aquí.
                cursor.execute("""
                    INSERT INTO repartos (rep_ped_id, rep_suc_origen, rep_suc_destino, rep_fecha_entrega, rep_estado_reparto)
                    SELECT ped_id, ped_sucursal_origen, ped_sucursal_destino, %s, %s
                    FROM pedidos WHERE ped_id = %s
                """, (fecha, nuevo_estado, ped_id))

            # Actualizar Pedido Maestro
            cursor.execute("""
                UPDATE pedidos 
                SET ped_estado_pedido = %s, ped_fecha_entrega = %s, ped_hora_entrega = %s
                WHERE ped_id = %s
            """, (est_ped, fecha, hora, ped_id))
            
            connection.commit()
            return jsonify({'message': 'Guardado correctamente.'})

    # --- ATRAPAR ERRORES DE MYSQL ---
    except err.IntegrityError as e:
        # Revertimos cambios para no dejar datos corruptos
        if connection: connection.rollback()
        
        # e.args suele ser una tupla (codigo_error, mensaje)
        codigo, mensaje = e.args
        
        # Error 1048: Column cannot be null
        if codigo == 1048:
            print(f"Intento de guardar NULL en campo obligatorio: {mensaje}")
            return jsonify({'error': 'Error de Base de Datos: Intentaste guardar un registro de logística sin FECHA, pero el sistema requiere una fecha obligatoria.'}), 400
        
        # Otros errores de integridad (claves duplicadas, foráneas, etc.)
        return jsonify({'error': f'Error de integridad de datos: {mensaje}'}), 400

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error general: {e}")
        return jsonify({'error': f'Error inesperado: {str(e)}'}), 500
        
    finally:
        if connection: connection.close()
# __________________________________________________________

# INICIO ENDPOINTS VENTAS

@app.route('/ventas')
def ventas():
    return render_template('ventas.jinja2')

# --- FUNCIÓN AUXILIAR CORREGIDA: Ahora valida el teléfono ---
def crear_nuevo_cliente(nombre, apellido, correo, telefono, contraseña):
    hashed_password = generate_password_hash(contraseña)
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Validación de correo duplicado
            cursor.execute("SELECT usu_correo FROM usuarios WHERE usu_correo = %s", (correo,))
            if cursor.fetchone():
                return False, "El correo electrónico ya está registrado."
            
            # --- VALIDACIÓN DE TELÉFONO AÑADIDA ---
            cursor.execute("SELECT usu_telefono FROM usuarios WHERE usu_telefono = %s", (telefono,))
            if cursor.fetchone():
                return False, "El número de teléfono ya está registrado."

            # Lógica de secuencia para obtener el ID (tu método)
            cursor.execute("INSERT INTO user_sequence (valor) VALUES (1)")
            cursor.execute("SELECT LAST_INSERT_ID() as new_id")
            nuevo_id = cursor.fetchone()['new_id']

            # Inserción del nuevo usuario
            sql = "INSERT INTO usuarios (usu_id, usu_nombre, usu_apellido, usu_correo, usu_contrasenia, usu_telefono) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (nuevo_id, nombre, apellido, correo, hashed_password, telefono))
            
        connection.commit()
        return True, f"¡Cliente '{nombre} {apellido}' registrado exitosamente!"
    except Exception as e:
        print(f"Error en BD al crear cliente: {e}")
        return False, "Ocurrió un error con la base de datos."
    finally:
        if connection:
            connection.close()


@app.route('/ventas/registrarCliente', methods=['GET', 'POST'])
def ventas_registrar_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        contraseña = request.form.get('contraseña')
        confirmacion = request.form.get('confirmacion_de_contraseña')

        if contraseña != confirmacion:
            # Devuelve un error en formato JSON
            return jsonify({'success': False, 'message': 'Las contraseñas no coinciden.'}), 400

        # Llama a la función auxiliar
        exito, mensaje = crear_nuevo_cliente(nombre, apellido, correo, telefono, contraseña)
        
        # Devuelve una respuesta JSON basada en el resultado
        if exito:
            return jsonify({'success': True, 'message': mensaje}), 200
        else:
            return jsonify({'success': False, 'message': mensaje}), 400
            
    # El método GET sigue mostrando el formulario como antes
    return render_template('venUsuRegister.jinja2')


@app.route("/verProductosVenta")
def ventas_Ver_Productos():
    # Verificamos que el empleado esté logueado
    if 'emp_id' not in session:
        return redirect(url_for('login'))
        
    # --- SIMPLIFICACIÓN: Obtenemos la sucursal directamente de la sesión ---
    # Ya no es necesario buscar el empleado en la base de datos.
    sucursal_actual_id = session.get('sucursal')

    # Si por alguna razón la sucursal no está en la sesión, redirigimos.
    if not sucursal_actual_id:
        flash('No se pudo identificar la sucursal. Por favor, inicia sesión de nuevo.', 'error')
        return redirect(url_for('login'))

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Obtener la lista de todas las sucursales para el dropdown (esto sigue siendo necesario)
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales ORDER BY suc_nombre")
            sucursales = cursor.fetchall()
            # 2. Obtener el inventario inicial usando el ID de la sesión
            query_inventario = """
                SELECT ip.invpro_pro_fk AS id, p.pro_nombre AS nombre, p.pro_unimed AS unidad, ip.pro_stock AS stock
                FROM inventario_productos ip
                JOIN productos p ON ip.invpro_pro_fk = p.pro_id
                WHERE ip.invpro_suc_fk = %s
            """
            cursor.execute(query_inventario, (sucursal_actual_id,))
            inventario_inicial = cursor.fetchall()
        # Pasamos los datos a la plantilla
        return render_template('venVerProductos.jinja2', 
                                sucursales=sucursales,
                                inventario_inicial=inventario_inicial,
                                sucursal_actual_id=sucursal_actual_id)
    except Exception as e:
        print(f"Error al ver productos: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()

@app.route('/ventas/inventario/productos/<int:sucursal_id>')
def obtener_inventario(sucursal_id):
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        # Usamos DictCursor para manejar los resultados como diccionarios
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # --- CONSULTA CORREGIDA CON JOIN ---
            # Unimos inventario_productos con la tabla productos para obtener el nombre
            query = """
                SELECT 
                    ip.invpro_pro_fk AS id,
                    p.pro_nombre AS nombre,
                    p.pro_unimed AS unidad,
                    ip.pro_stock AS stock
                FROM inventario_productos ip
                JOIN productos p ON ip.invpro_pro_fk = p.pro_id
                WHERE ip.invpro_suc_fk = %s
            """
            cursor.execute(query, (sucursal_id,))
            inventario = cursor.fetchall()
            
            # Convertir 'stock' a float para asegurar que sea compatible con JSON
            for item in inventario:
                item['stock'] = float(item['stock'])

            return jsonify(inventario)
    except Exception as e:
        print(f"Error en API de inventario: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if connection:
            connection.close()

@app.route('/verCaja')
def ver_caja():
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    sucursal_actual_id = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Buscamos todas las cajas que pertenecen a la sucursal del empleado
            # (Aunque solo sea una, esta consulta funcionará si en el futuro añades más)
            cursor.execute("SELECT * FROM CAJA WHERE caja_suc_fk = %s", (sucursal_actual_id,))
            cajas = cursor.fetchall()
        
        # Pasamos la lista de cajas (aunque sea de un solo elemento) a la plantilla
        return render_template('venVerCaja.jinja2', cajas=cajas)
    finally:
        if connection:
            connection.close()


@app.route('/movimientosEfectivo')
def movimientos_efectivo_vista():
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    sucursal_id = session['sucursal']
    
    # 1. Definimos las fuentes externas/conceptuales
    fuentes_externas = [
        {'id': 'INGRESO_EXTERNO', 'nombre': 'Ingreso Externo (ej. Fondo Inicial)'},
        {'id': 'EGRESO_EXTERNO', 'nombre': 'Egreso Externo (ej. Retiro a Banco)'}
    ]

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 2. Obtenemos las cajas reales de la sucursal
            cursor.execute("SELECT caja_id as id, CONCAT('Caja ', caja_id) as nombre FROM CAJA WHERE caja_suc_fk = %s", (sucursal_id,))
            cajas_reales = cursor.fetchall()
        
        # 3. Pasamos ambas listas a la plantilla
        return render_template('venMovimientosEfectivo.jinja2', 
                                cajas_reales=cajas_reales,
                                fuentes_externas=fuentes_externas)
    finally:
        if connection:
            connection.close()

# --- API PARA PROCESAR CUALQUIER MOVIMIENTO DE EFECTIVO ---
@app.route('/ventas/procesar_movimiento', methods=['POST'])
def ventas_procesar_movimiento():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    # Obtenemos datos
    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    origen = request.form.get('fuente_origen')
    destino = request.form.get('fuente_destino')
    monto_str = request.form.get('monto')
    motivo = request.form.get('motivo')

    # ... (Validaciones de monto, motivo, etc. como antes) ...
    if origen == destino:
        return jsonify({'success': False, 'message': 'El origen y destino no pueden ser el mismo.'}), 400

    try:
        monto = decimal.Decimal(monto_str)
        # ... más validaciones de monto ...
    except:
        return jsonify({'success': False, 'message': 'Monto no válido.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            connection.begin()

            # Lógica de movimiento
            # CASO 1: Ingreso Externo (Dinero entra al sistema)
            if origen == 'INGRESO_EXTERNO':
                cursor.execute("UPDATE CAJA SET caja_efectivo = caja_efectivo + %s WHERE caja_id = %s AND caja_suc_fk = %s", (monto, destino, sucursal_id))
                caja_origen_id, caja_destino_id = 0, destino # 0 representa una fuente externa

            # CASO 2: Egreso Externo (Dinero sale del sistema)
            elif destino == 'EGRESO_EXTERNO':
                cursor.execute("UPDATE CAJA SET caja_efectivo = caja_efectivo - %s WHERE caja_id = %s AND caja_suc_fk = %s", (monto, origen, sucursal_id))
                caja_origen_id, caja_destino_id = origen, 0

            # CASO 3: Transferencia Interna (Dinero se mueve entre cajas)
            else:
                cursor.execute("UPDATE CAJA SET caja_efectivo = caja_efectivo - %s WHERE caja_id = %s AND caja_suc_fk = %s", (monto, origen, sucursal_id))
                cursor.execute("UPDATE CAJA SET caja_efectivo = caja_efectivo + %s WHERE caja_id = %s AND caja_suc_fk = %s", (monto, destino, sucursal_id))
                caja_origen_id, caja_destino_id = origen, destino

            # Registrar en el historial (ahora 'historial_movimientos')
            sql_historial = "INSERT INTO historial_transferencias (ht_emp_fk, ht_suc_fk, ht_caja_origen_fk, ht_caja_destino_fk, ht_monto, ht_motivo) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql_historial, (empleado_id, sucursal_id, caja_origen_id, caja_destino_id, monto, motivo))

            connection.commit()
            return jsonify({'success': True, 'message': f'Movimiento de ${monto} registrado exitosamente.'}), 200
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en movimiento: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor.'}), 500
    finally:
        if connection: connection.close()


@app.route('/actualizarCaja')
def actualizar_caja_vista():
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    sucursal_id = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos TODAS las cajas de la sucursal para el menú
            cursor.execute("SELECT caja_id FROM CAJA WHERE caja_suc_fk = %s ORDER BY caja_id", (sucursal_id,))
            cajas_disponibles = cursor.fetchall()
        
        # Ya no pasamos el efectivo, el JS se encargará de eso
        return render_template('venActualizarCaja.jinja2', cajas=cajas_disponibles)
    finally:
        if connection:
            connection.close()


@app.route('/api/caja_detalle/<int:caja_id>')
def api_caja_detalle(caja_id):
    if 'sucursal' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_id = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Buscamos la caja específica EN LA SUCURSAL DEL USUARIO por seguridad
            cursor.execute("SELECT caja_efectivo FROM CAJA WHERE caja_id = %s AND caja_suc_fk = %s", (caja_id, sucursal_id))
            caja = cursor.fetchone()
            if caja:
                caja['caja_efectivo'] = float(caja['caja_efectivo'])
                return jsonify(caja)
            else:
                return jsonify({'error': 'Caja no encontrada en esta sucursal'}), 404
    finally:
        if connection:
            connection.close()

# --- AÑADE ESTE ENDPOINT COMPLETO A TU app.py ---

@app.route('/api/procesarAjusteCaja', methods=['POST'])
def api_procesar_ajuste_caja():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    
    caja_id = request.form.get('caja_id')
    monto_str = request.form.get('monto')
    tipo_operacion = request.form.get('tipo_operacion')
    motivo = request.form.get('motivo')

    # --- Validaciones ---
    if not all([caja_id, monto_str, tipo_operacion, motivo]):
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400
    try:
        monto = decimal.Decimal(monto_str)
        if monto <= 0: raise ValueError
    except (ValueError, decimal.InvalidOperation):
        return jsonify({'success': False, 'message': 'El monto debe ser un número positivo.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            # 1. Obtener y bloquear el saldo actual para evitar concurrencia
            cursor.execute("SELECT caja_efectivo FROM CAJA WHERE caja_id = %s AND caja_suc_fk = %s FOR UPDATE", (caja_id, sucursal_id))
            caja = cursor.fetchone()
            if not caja:
                raise Exception("Caja no encontrada en esta sucursal.")
            
            saldo_anterior = caja['caja_efectivo']
            
            # 2. Calcular nuevo saldo y validar retiro
            if tipo_operacion == 'retirar':
                if monto > saldo_anterior:
                    # Este error se enviará al frontend si no hay fondos suficientes
                    raise Exception(f'Fondos insuficientes. No se puede retirar ${monto}.')
                saldo_nuevo = saldo_anterior - monto
                tipo_historial = 'RETIRO'
            else: # 'agregar'
                saldo_nuevo = saldo_anterior + monto
                tipo_historial = 'AGREGO'

            # 3. Actualizar la tabla CAJA (con la consulta correcta)
            cursor.execute("UPDATE CAJA SET caja_efectivo = %s WHERE caja_id = %s AND caja_suc_fk = %s", (saldo_nuevo, caja_id, sucursal_id))

            # 4. Insertar en el historial de auditoría
            sql_historial = """
                INSERT INTO historial_ajustes_caja 
                (ajuste_emp_fk, ajuste_suc_fk, ajuste_caja_fk, ajuste_tipo, ajuste_monto, ajuste_motivo, saldo_anterior, saldo_nuevo) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_historial, (empleado_id, sucursal_id, caja_id, tipo_historial, monto, motivo, saldo_anterior, saldo_nuevo))

            connection.commit()
        
        return jsonify({'success': True, 'message': f'Operación de {tipo_historial.lower()} por ${monto} registrada exitosamente.'}), 200

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al actualizar caja: {e}")
        # Enviamos el mensaje de error específico al frontend para el alert()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection:
            connection.close()



@app.route('/corteDeCaja')
def corte_turno_vista():
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    sucursal_id = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos TODAS las cajas de la sucursal para el menú
            cursor.execute("SELECT caja_id FROM CAJA WHERE caja_suc_fk = %s ORDER BY caja_id", (sucursal_id,))
            cajas_disponibles = cursor.fetchall()
        
        # Pasamos la lista de cajas a la plantilla
        return render_template('venCorteCaja.jinja2', cajas=cajas_disponibles)
    finally:
        if connection:
            connection.close()
            

# --- AÑADE ESTA NUEVA API PARA OBTENER EL RESUMEN DEL DÍA ---
@app.route('/api/resumen_caja_dia/<int:caja_id>')
def api_resumen_caja_dia(caja_id):
    if 'sucursal' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_id = session['sucursal']
    resumen = {
            'caja_efectivo': 0, 
            'caja_tarjeta': 0,
            'caja_total_dia': 0,
            'total_retiros_ajuste': 0,
            'total_retiros_corte_turno': 0 # Ya no se incluye 'total_retiros_transferencia'
        }
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Obtener saldos actuales
            cursor.execute("SELECT caja_efectivo, caja_tarjeta, caja_total_dia FROM CAJA WHERE caja_id = %s AND caja_suc_fk = %s", (caja_id, sucursal_id))
            caja = cursor.fetchone()
            if caja:
                resumen['caja_efectivo'] = float(caja['caja_efectivo'])
                resumen['caja_tarjeta'] = float(caja['caja_tarjeta'])
                resumen['caja_total_dia'] = float(caja['caja_total_dia'])
            # 2. Sumar retiros por "Ajuste" del día
            cursor.execute("SELECT SUM(ajuste_monto) as total FROM historial_ajustes_caja WHERE ajuste_caja_fk = %s AND ajuste_tipo = 'RETIRO' AND DATE(ajuste_fecha) = CURDATE()", (caja_id,))
            resumen['total_retiros_ajuste'] = float(cursor.fetchone()['total'] or 0)
            
            # 3. Sumar retiros por "Corte de Turno" del día
            cursor.execute("SELECT SUM(efectivo_retirado) as total FROM historial_cortes WHERE corte_caja_fk = %s AND DATE(corte_fecha) = CURDATE()", (caja_id,))
            resumen['total_retiros_corte_turno'] = float(cursor.fetchone()['total'] or 0)
            
            resumen['total_acumulado_dia'] = (
                resumen['caja_total_dia'] + 
                resumen['total_retiros_ajuste'] + 
                resumen['total_retiros_corte_turno']
            )
            
            
            
            return jsonify(resumen)
    except Exception as e:
            print(f"Error en resumen de caja: {e}")
            return jsonify({'error': 'Error al cargar resumen'}), 500
    finally:
            if connection:
                connection.close()


# --- API MODIFICADA PARA PROCESAR AMBOS TIPOS DE CORTE ---
@app.route('/api/procesarCorteTurno', methods=['POST'])
def api_procesar_corte_turno():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    caja_id = request.form.get('caja_id')
    # Nuevo campo para saber qué acción tomar
    tipo_corte = request.form.get('tipo_corte') 

    if not caja_id or not tipo_corte:
        return jsonify({'success': False, 'message': 'Datos incompletos.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            # --- LÓGICA BIFURCADA ---
            
            # --- CASO 1: CORTE DE TURNO (Retiro Parcial) ---
            if tipo_corte == 'turno':
                denominaciones_contadas = {
                    '1000': int(request.form.get('b1000', 0)), '500': int(request.form.get('b500', 0)),
                    '200': int(request.form.get('b200', 0)), '100': int(request.form.get('b100', 0)),
                    '50': int(request.form.get('b50', 0)),  '20': int(request.form.get('b20', 0)),
                    '10': int(request.form.get('m10', 0)),   '5': int(request.form.get('m5', 0)),
                }
                total_retirado = sum(float(valor) * cantidad for valor, cantidad in denominaciones_contadas.items())
                if total_retirado <= 0:
                    raise Exception('No se especificó ninguna cantidad a retirar.')

                cursor.execute("SELECT caja_efectivo FROM CAJA WHERE caja_id = %s AND caja_suc_fk = %s FOR UPDATE", (caja_id, sucursal_id))
                caja = cursor.fetchone()
                if not caja: raise Exception("Caja no encontrada.")
                saldo_anterior = caja['caja_efectivo']

                if total_retirado > float(saldo_anterior):
                    raise Exception(f'Error: Se intentó retirar ${total_retirado:.2f} pero solo hay ${saldo_anterior:.2f} en caja.')

                saldo_restante = saldo_anterior - decimal.Decimal(total_retirado)
                cursor.execute("UPDATE CAJA SET caja_efectivo = %s WHERE caja_id = %s AND caja_suc_fk = %s", (saldo_restante, caja_id, sucursal_id))

                desglose_json = json.dumps(denominaciones_contadas)
                sql_historial = "INSERT INTO historial_cortes (corte_emp_fk, corte_suc_fk, corte_caja_fk, efectivo_retirado, efectivo_restante, desglose_denominaciones) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql_historial, (empleado_id, sucursal_id, caja_id, total_retirado, saldo_restante, desglose_json))
                
                mensaje_exito = f'Corte de turno realizado. Se retiraron ${total_retirado:.2f}. Efectivo restante: ${saldo_restante:.2f}.'

            # --- CASO 2: CORTE DE DÍA (Reseteo a Cero) ---
            elif tipo_corte == 'dia':
                cursor.execute("SELECT caja_efectivo, caja_tarjeta FROM CAJA WHERE caja_id = %s AND caja_suc_fk = %s FOR UPDATE", (caja_id, sucursal_id))
                caja = cursor.fetchone()
                if not caja: raise Exception("Caja no encontrada.")
                
                saldo_final_efectivo = caja['caja_efectivo']
                saldo_final_tarjeta = caja['caja_tarjeta']

                # Registra el retiro total de efectivo y el total de tarjeta
                sql_historial = "INSERT INTO historial_cortes (corte_emp_fk, corte_suc_fk, corte_caja_fk, efectivo_retirado, efectivo_restante, tarjeta_total_dia) VALUES (%s, %s, %s, %s, 0.00, %s)"
                cursor.execute(sql_historial, (empleado_id, sucursal_id, caja_id, saldo_final_efectivo, saldo_final_tarjeta))

                # Resetea AMBOS campos a CERO
                cursor.execute("UPDATE CAJA SET caja_efectivo = 0.00, caja_tarjeta = 0.00 WHERE caja_id = %s AND caja_suc_fk = %s", (caja_id, sucursal_id))
                
                mensaje_exito = f'Cierre de día exitoso. Se registraron ${saldo_final_efectivo:.2f} en efectivo y ${saldo_final_tarjeta:.2f} en tarjeta.'
            
            else:
                raise Exception("Tipo de corte no válido.")

            connection.commit()
            return jsonify({'success': True, 'message': mensaje_exito}), 200
            
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en corte de caja: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection:
            connection.close()



# --- RUTA PARA MOSTRAR LA INTERFAZ DE VENTA ---
@app.route('/registrarVenta')
def registrar_venta_vista():
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))
        
    sucursal_id = session['sucursal']
    cajas_disponibles = [] # inicializar las cajas
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Ver cajas existentes en la sucursal
            cursor.execute("SELECT caja_id FROM CAJA WHERE caja_suc_fk = %s ORDER BY caja_id", (sucursal_id,))
            cajas_disponibles = cursor.fetchall()
            
    except Exception as e:
        print(f"Error fetching cajas for venta: {e}")
        # Handle error appropriately, maybe flash a message
    finally:
        if connection:
            connection.close()
    # Pass sucursal_id AND the list of cajas
    return render_template('venRegistrarVenta.jinja2', 
                            sucursal_id=sucursal_id, 
                            cajas=cajas_disponibles) # Pass the list

# --- API PARA OBTENER PRODUCTOS DISPONIBLES EN LA SUCURSAL ---
@app.route('/api/productos_venta/<int:sucursal_id>')
def api_productos_venta(sucursal_id):
    # Validar que la sucursal pedida sea la misma del empleado por seguridad
    if 'sucursal' not in session or session['sucursal'] != sucursal_id:
        return jsonify({"error": "Acceso no autorizado a esta sucursal"}), 403
        
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos productos con stock > 0 en la sucursal
            query = """
                SELECT 
                    p.pro_id as id, 
                    p.pro_nombre as nombre, 
                    p.pro_precio as precio, 
                    ip.pro_stock as stock,
                    p.pro_unimed as unidad
                FROM productos p
                JOIN inventario_productos ip ON p.pro_id = ip.invpro_pro_fk
                WHERE ip.invpro_suc_fk = %s AND ip.pro_stock > 0
                ORDER BY p.pro_nombre
            """
            cursor.execute(query, (sucursal_id,))
            productos = cursor.fetchall()
            # Convertir Decimal a float para JSON
            for prod in productos:
                prod['precio'] = float(prod['precio'])
                prod['stock'] = float(prod['stock'])
            return jsonify(productos)
    except Exception as e:
        print(f"Error api_productos_venta: {e}")
        return jsonify({"error": "Error al obtener productos"}), 500
    finally:
        if connection: connection.close()

# --- API PARA FINALIZAR Y REGISTRAR LA VENTA ---
@app.route('/api/finalizar_venta', methods=['POST'])
def api_finalizar_venta():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    # Obtenemos datos de la sesión y del JSON enviado por el frontend
    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    data = request.json
    carrito = data.get('carrito') # Lista de {'id': ..., 'cantidad': ..., 'precio': ...}
    monto_recibido = decimal.Decimal(data.get('monto_recibido', 0))
    cambio_devuelto = decimal.Decimal(data.get('cambio_devuelto', 0))
    caja_id = data.get('caja_id')
    metodo_pago = data.get('metodo_pago')
    if not carrito or monto_recibido <= 0:
        return jsonify({'success': False, 'message': 'Datos de venta incompletos.'}), 400
    if not metodo_pago or metodo_pago not in ['efectivo', 'tarjeta']:
        return jsonify({'success': False, 'message': 'Método de pago inválido.'}), 400
    
    monto_total_venta = sum(decimal.Decimal(item['precio']) * int(item['cantidad']) for item in carrito)
    efectivo_neto_recibido = 0
    if metodo_pago == 'efectivo':
        efectivo_neto_recibido = monto_recibido - cambio_devuelto

    # Verificación de consistencia
    if metodo_pago == 'efectivo' and efectivo_neto_recibido != monto_total_venta:
        # Considerar un margen de error pequeño por redondeos si es necesario
        # if abs(efectivo_neto_recibido - monto_total_venta) > 0.01:
        print(f"WARN: Discrepancia en montos. Total:{monto_total_venta}, Neto:{efectivo_neto_recibido}")
        # Podrías devolver un error aquí si quieres ser estricto

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin() # INICIA TRANSACCIÓN
            #Obtener el nombre de la sucursal
            cursor.execute("SELECT suc_nombre FROM sucursales WHERE suc_id = %s", (sucursal_id,))
            sucursal_info = cursor.fetchone()
            if not sucursal_info:
                raise Exception("Sucursal no encontrada.")
            sucursal_nombre = sucursal_info['suc_nombre']
            # 1. Insertar en VENTA
            sql_venta = "INSERT INTO VENTA (venta_emp_fk, venta_caja_fk, venta_suc_fk, venta_fecha, venta_monto_total, venta_sucursal,venta_metodo_pago) VALUES (%s, %s, %s, %s, %s, %s,%s)"
            today = date.today()
            cursor.execute(sql_venta, (empleado_id, caja_id, sucursal_id, today, monto_total_venta,sucursal_nombre,metodo_pago))
            venta_id = cursor.lastrowid # Obtenemos el ID de la venta recién creada

            # 2. Insertar en DETALLES_VENTA (un registro por cada producto)
            sql_detalle = "INSERT INTO DETALLES_VENTA (detven_venta_fk, detven_pro_fk, detven_pro_precio, detven_pro_nombre, detven_pro_cant, detven_pro_precio_total) VALUES (%s, %s, %s, %s, %s, %s)"
            detalles_para_insertar = []
            for item in carrito:
                precio_unitario = decimal.Decimal(item['precio'])
                cantidad = int(item['cantidad'])
                precio_total_linea = precio_unitario * cantidad
                detalles_para_insertar.append((
                    venta_id, item['id'], precio_unitario, item['nombre'], # Asume que 'nombre' viene en el carrito
                    cantidad, precio_total_linea
                ))
            cursor.executemany(sql_detalle, detalles_para_insertar)

            # 3. Actualizar INVENTARIO_PRODUCTOS (restar stock)
            sql_update_stock = "UPDATE inventario_productos SET pro_stock = pro_stock - %s WHERE invpro_pro_fk = %s AND invpro_suc_fk = %s"
            stock_para_actualizar = []
            for item in carrito:
                # VALIDACIÓN CRÍTICA: Volver a verificar stock antes de restar
                cursor.execute("SELECT pro_stock FROM inventario_productos WHERE invpro_pro_fk = %s AND invpro_suc_fk = %s FOR UPDATE", (item['id'], sucursal_id))
                stock_actual = cursor.fetchone()
                if not stock_actual or stock_actual['pro_stock'] < item['cantidad']: 
                    raise Exception(f"Stock insuficiente para {item['nombre']}.")
                stock_para_actualizar.append((item['cantidad'], item['id'], sucursal_id))
            cursor.executemany(sql_update_stock, stock_para_actualizar)

            # 4. Actualizar CAJA (sumar el efectivo neto)
            if metodo_pago == 'efectivo':
                sql_update_caja = "UPDATE CAJA SET caja_efectivo = caja_efectivo + %s WHERE caja_id = %s AND caja_suc_fk = %s"
                cursor.execute(sql_update_caja, (efectivo_neto_recibido, caja_id, sucursal_id))
            else: # Tarjeta
                # Sumamos el total de la venta a la columna caja_tarjeta
                sql_update_caja = "UPDATE CAJA SET caja_tarjeta = caja_tarjeta + %s WHERE caja_id = %s AND caja_suc_fk = %s"
                cursor.execute(sql_update_caja, (monto_total_venta, caja_id, sucursal_id))
            connection.commit() # TERMINA TRANSACCIÓN CON ÉXITO
            
        return jsonify({'success': True, 'message': f'Venta #{venta_id} registrada exitosamente.'}), 200

    except Exception as e:
        if connection: connection.rollback() # DESHACE TODO SI ALGO FALLA
        print(f"Error al finalizar venta: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()



# ==============================================================================
# MÓDULO: COBRO Y CIERRE DE PEDIDOS (CAJA)
# ==============================================================================

@app.route('/cobrarPedidos')
def cobrar_pedidos_vista():
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))
    
    sucursal_id = session['sucursal']
    cajas = []
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtener cajas de la sucursal para el selector
            cursor.execute("SELECT caja_id FROM CAJA WHERE caja_suc_fk = %s", (sucursal_id,))
            cajas = cursor.fetchall()
    except Exception as e:
        print(f"Error cargando cajas: {e}")
    finally:
        if connection: connection.close()

    return render_template('venCobrarPedidos.jinja2', cajas=cajas)


# --- API 1: OBTENER PEDIDOS PENDIENTES DE COBRO ---
@app.route('/api/pedidos_por_cobrar')
def api_pedidos_por_cobrar():
    if 'sucursal' not in session: return jsonify({'error': 'No autorizado'}), 401
    
    sucursal_id = session['sucursal']
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # CORRECCIÓN DE LÓGICA:
            # Buscamos pedidos que YA LLEGARON a la tienda (Estado 'C'ompletado logísticamente)
            # y que están pendientes de entrega final al cliente (Cobro).
            # Filtramos hasta la fecha de hoy (incluye atrasados no recogidos).
            query = """
                SELECT 
                    p.ped_id,
                    p.ped_fecha_entrega,
                    p.ped_asunto,
                    p.ped_monto_total,
                    p.ped_estado_pedido,
                    COALESCE(u.usu_nombre, 'Cliente Mostrador') as cliente_nombre
                FROM pedidos p
                LEFT JOIN usuarios u ON p.ped_usu_id = u.usu_id
                WHERE 
                    p.ped_sucursal_origen = %s -- O destino, según quien cobra. Asumimos origen=tienda venta.
                    AND p.ped_fecha_entrega <= CURDATE()
                    AND p.ped_estado_pedido = 'C' -- SOLO LOS QUE YA ESTÁN EN TIENDA
                    AND p.ped_usu_id IS NOT NULL
                ORDER BY p.ped_fecha_entrega ASC
            """
            # Nota: Si la sucursal que cobra es la de DESTINO (donde el cliente recoge), 
            # cambia 'p.ped_sucursal_origen' por 'p.ped_sucursal_destino' en el WHERE.
            
            cursor.execute(query, (sucursal_id,))
            pedidos = cursor.fetchall()
            
            for p in pedidos:
                p['ped_monto_total'] = float(p['ped_monto_total'])
                if p['ped_fecha_entrega']:
                    p['ped_fecha_entrega'] = p['ped_fecha_entrega'].strftime('%d/%m/%Y')
            
            return jsonify(pedidos)
    except Exception as e:
        print(f"Error pedidos por cobrar: {e}")
        return jsonify([])
    finally:
        if connection: connection.close()


# --- API 2: PROCESAR COBRO (FINALIZAR PEDIDO) ---
@app.route('/api/procesar_cobro_pedido', methods=['POST'])
def api_procesar_cobro_pedido():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    empleado_id = session['emp_id']
    sucursal_id = session['sucursal']
    
    data = request.json
    pedido_id = data.get('pedido_id')
    caja_id = data.get('caja_id')
    metodo_pago = data.get('metodo_pago')
    
    if not pedido_id or not caja_id:
        return jsonify({'success': False, 'message': 'Faltan datos.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            connection.begin()

            # 1. Obtener datos del pedido
            cursor.execute("SELECT * FROM pedidos WHERE ped_id = %s", (pedido_id,))
            pedido = cursor.fetchone()
            if not pedido: raise Exception("Pedido no encontrado")
            
            # Validar estado
            if pedido['ped_estado_pedido'] != 'C':
                raise Exception("El pedido no está listo para cobro (No está en estado 'C').")

            monto_total = float(pedido['ped_monto_total'])
            
            # Obtener nombre sucursal
            cursor.execute("SELECT suc_nombre FROM sucursales WHERE suc_id = %s", (sucursal_id,))
            suc_row = cursor.fetchone()
            sucursal_nombre = suc_row['suc_nombre'] if suc_row else "Sucursal"

            # 2. Registrar VENTA (Dinero entra)
            sql_venta = """
                INSERT INTO VENTA 
                (venta_emp_fk, venta_caja_fk, venta_suc_fk, venta_fecha, venta_monto_total, venta_sucursal, venta_metodo_pago) 
                VALUES (%s, %s, %s, CURDATE(), %s, %s, %s)
            """
            cursor.execute(sql_venta, (empleado_id, caja_id, sucursal_id, monto_total, sucursal_nombre, metodo_pago))
            venta_id = cursor.lastrowid

            # 3. Copiar productos a DETALLES_VENTA
            cursor.execute("""
                SELECT dp.detpedpro_pro_id, dp.detpedpro_cantidad, dp.detpedpro_precio_unitario, p.pro_nombre
                FROM detalle_pedido_productos dp
                JOIN productos p ON dp.detpedpro_pro_id = p.pro_id
                WHERE dp.detpedpro_ped_id = %s
            """, (pedido_id,))
            items_prod = cursor.fetchall()

            sql_detalle = """
                INSERT INTO DETALLES_VENTA 
                (detven_venta_fk, detven_pro_fk, detven_pro_precio, detven_pro_nombre, detven_pro_cant, detven_pro_precio_total) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in items_prod:
                total_linea = float(item['detpedpro_cantidad']) * float(item['detpedpro_precio_unitario'])
                cursor.execute(sql_detalle, (
                    venta_id, item['detpedpro_pro_id'], item['detpedpro_precio_unitario'], 
                    item['pro_nombre'], item['detpedpro_cantidad'], total_linea
                ))

            # 4. Actualizar Saldos en CAJA
            if metodo_pago == 'efectivo':
                cursor.execute("UPDATE CAJA SET caja_efectivo = caja_efectivo + %s WHERE caja_id = %s", (monto_total, caja_id))
            else:
                cursor.execute("UPDATE CAJA SET caja_tarjeta = caja_tarjeta + %s WHERE caja_id = %s", (monto_total, caja_id))

            # 5. FINALIZAR PEDIDO -> Estado 'E' (Entregado al Cliente)
            cursor.execute("UPDATE pedidos SET ped_estado_pedido = 'E' WHERE ped_id = %s", (pedido_id,))
            
            # Aseguramos que el reparto (si existe) quede cerrado
            cursor.execute("UPDATE repartos SET rep_estado_reparto = 'E' WHERE rep_ped_id = %s", (pedido_id,))

            connection.commit()
            return jsonify({'success': True, 'message': f'Pedido #{pedido_id} cobrado y entregado exitosamente.'})

    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al cobrar: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()

# ==============================================================================
# MÓDULO: SOLICITUD DE PRODUCTOS (SUCURSAL -> ALMACÉN)
# ==============================================================================

@app.route('/solicitarProductos')
def solicitar_productos_vista():
    if 'sucursal' not in session or 'emp_id' not in session:
        return redirect(url_for('login'))
            
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Productos disponibles (Catálogo)
            query_productos = """
                SELECT pro_id as id, pro_nombre as nombre, pro_costo_unit as costo, pro_unimed as unidad
                FROM productos ORDER BY pro_nombre
            """
            cursor.execute(query_productos)
            productos_disponibles = cursor.fetchall()
            for prod in productos_disponibles:
                prod['costo'] = float(prod['costo'])
            
            # 2. Sucursales (Para el selector de Origen)
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
            sucursales = cursor.fetchall()
            
        return render_template('venSolicitarProductos.jinja2', 
                                productos=productos_disponibles,
                                sucursales=sucursales)
    except Exception as e:
        print(f"Error en solicitar_productos_vista: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection: connection.close()

@app.route('/api/finalizar_solicitud', methods=['POST'])
def api_finalizar_solicitud():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    empleado_id = session['emp_id']
    sucursal_id_destino = session['sucursal'] # Quien PIDE (Destino de la mercancía)
    
    data = request.json
    carrito = data.get('carrito')
    sucursal_id_origen = data.get('sucursal_origen_id') # A quien le PIDO (Origen)
    comentarios = data.get('comentarios', '')
    
    # --- NUEVOS CAMPOS DE FECHA Y HORA ---
    fecha_entrega = data.get('fecha_entrega')
    hora_entrega = data.get('hora_entrega')

    if not carrito:
        return jsonify({'success': False, 'message': 'El carrito está vacío.'}), 400
    if not sucursal_id_origen:
        return jsonify({'success': False, 'message': 'Debes seleccionar una sucursal de origen.'}), 400
    if not fecha_entrega:
        return jsonify({'success': False, 'message': 'La fecha de entrega es obligatoria.'}), 400
    
    # Calcular monto total (basado en costo)
    monto_total_solicitud = sum(decimal.Decimal(item['costo']) * int(item['cantidad']) for item in carrito)

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            connection.begin()

            # 1. Insertar el Pedido (Con Fecha y Hora de Entrega)
            sql_pedido = """
                INSERT INTO pedidos 
                (ped_emp_id, ped_sucursal_origen, ped_sucursal_destino, 
                ped_fecha_pedido, ped_fecha_entrega, ped_hora_entrega,
                ped_monto_total, ped_estado_pedido, ped_asunto, ped_comentarios) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'P', 'Solicitud de Productos', %s)
            """
            today = date.today()
            hora_val = hora_entrega if hora_entrega else None # Manejar hora vacía
            
            cursor.execute(sql_pedido, (
                empleado_id, sucursal_id_origen, sucursal_id_destino, 
                today, fecha_entrega, hora_val,
                monto_total_solicitud, comentarios
            ))
            pedido_id = cursor.lastrowid

            # 2. Insertar detalles
            sql_detalle = """
                INSERT INTO detalle_pedido_productos 
                (detpedpro_ped_id, detpedpro_pro_id, detpedpro_cantidad, detpedpro_precio_unitario) 
                VALUES (%s, %s, %s, %s)
            """
            detalles_para_insertar = []
            for item in carrito:
                costo_unitario = decimal.Decimal(item['costo'])
                cantidad = int(item['cantidad'])
                detalles_para_insertar.append((pedido_id, item['id'], cantidad, costo_unitario))
            
            cursor.executemany(sql_detalle, detalles_para_insertar)
            
            connection.commit()
            
        return jsonify({'success': True, 'message': f'Solicitud #{pedido_id} registrada exitosamente.'}), 200
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al finalizar solicitud: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()


#----------------------------
# INICIO MODULO DE REPORTES

@app.route('/reportes')
def reportes():
    return render_template('reportes.jinja2')

# En tu archivo app.py

# --- RUTA PARA MOSTRAR LA PÁGINA DE REPORTES ---
@app.route('/reporteDeVentas')
def reporte_de_ventas_vista():
    # Solo muestra la página, el JS hará el trabajo
    return render_template('repoVentas.jinja2')
# En tu archivo app.py

@app.route('/api/reporte_ventas_agregado', methods=['POST'])
def api_reporte_ventas_agregado():
    if 'sucursal' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    sucursal_id = session['sucursal']
    data = request.json
    fecha_base = data.get('fecha', date.today().isoformat())
    rango = data.get('rango', 'dia')
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # --- 1. Lógica de rango de fechas (sin cambios) ---
            if rango == 'dia':
                sql_where_fechas = " AND v.venta_fecha = %s "
                params = [fecha_base]
            elif rango == 'semana':
                sql_where_fechas = " AND YEARWEEK(v.venta_fecha, 1) = YEARWEEK(%s, 1) "
                params = [fecha_base]
            elif rango == 'mes':
                sql_where_fechas = " AND YEAR(v.venta_fecha) = YEAR(%s) AND MONTH(v.venta_fecha) = MONTH(%s) "
                params = [fecha_base, fecha_base]
            elif rango == 'ano':
                sql_where_fechas = " AND YEAR(v.venta_fecha) = YEAR(%s) "
                params = [fecha_base]
            
            params.append(sucursal_id)
            
            # --- 2. Resumen de Totales (sin cambios) ---
            sql_totales = f"""
                SELECT SUM(venta_monto_total) as total_vendido, COUNT(venta_id) as numero_tickets
                FROM VENTA v
                WHERE 1=1 {sql_where_fechas} AND v.venta_suc_fk = %s
            """
            cursor.execute(sql_totales, params)
            resumen_totales = cursor.fetchone()

            # --- 3. Productos Más Vendidos (sin cambios) ---
            sql_productos = f"""
                SELECT d.detven_pro_nombre, SUM(d.detven_pro_cant) as cantidad_total
                FROM DETALLES_VENTA d
                JOIN VENTA v ON d.detven_venta_fk = v.venta_id
                WHERE 1=1 {sql_where_fechas} AND v.venta_suc_fk = %s
                GROUP BY d.detven_pro_nombre ORDER BY cantidad_total DESC LIMIT 10
            """
            cursor.execute(sql_productos, params)
            productos_top = cursor.fetchall()
            
            # --- 4. Datos para la Gráfica (CONSULTA MODIFICADA) ---
            grafica_data = {'labels': [], 'data': []}
            if rango == 'dia':
                 pass # No hay gráfica para un solo día
            elif rango == 'ano':
                # --- CAMBIO: Pedimos el NÚMERO del mes, no el nombre ---
                sql_grafica = f"""
                    SELECT MONTH(v.venta_fecha) as label, SUM(v.venta_monto_total) as total
                    FROM VENTA v
                    WHERE 1=1 {sql_where_fechas} AND v.venta_suc_fk = %s
                    GROUP BY MONTH(v.venta_fecha)
                    ORDER BY MONTH(v.venta_fecha)
                """
                cursor.execute(sql_grafica, params)
            else: # Semana o Mes
                sql_grafica = f"""
                    SELECT DATE(v.venta_fecha) as label, SUM(v.venta_monto_total) as total
                    FROM VENTA v
                    WHERE 1=1 {sql_where_fechas} AND v.venta_suc_fk = %s
                    GROUP BY DATE(v.venta_fecha) ORDER BY DATE(v.venta_fecha)
                """
                cursor.execute(sql_grafica, params)

            # --- 5. Procesamiento de Datos de Gráfica (LÓGICA DE TRADUCCIÓN AÑADIDA) ---
            if rango != 'dia':
                resultados_grafica = cursor.fetchall()
                
                # --- LÓGICA DE TRADUCCIÓN A ESPAÑOL ---
                meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                labels = []
                
                if rango == 'ano':
                    # Convertimos el número de mes (1-12) a nombre en español
                    labels = [meses_es[int(row['label']) - 1] for row in resultados_grafica]
                else:
                    # Formateamos la fecha (ej. 20-Oct)
                    labels = [row['label'].strftime('%d-%b') for row in resultados_grafica] # ej. 20-Oct
                
                grafica_data = {
                    'labels': labels,
                    'data': [float(row['total']) for row in resultados_grafica]
                }
            
        return jsonify({
            'resumen_totales': resumen_totales,
            'productos_top': productos_top,
            'grafica_data': grafica_data
        })
        
    except Exception as e:
        print(f"Error en api_reporte_ventas_agregado: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()



# --- RUTA PARA MOSTRAR LA PÁGINA DE REPORTE DE INVENTARIO ---
@app.route('/reporteDeInventario')
def reporte_inventario_vista():
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    sucursal_actual_id = session['sucursal']
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos la lista de sucursales para el filtro
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales ORDER BY suc_nombre")
            sucursales = cursor.fetchall()
            
        return render_template('repoInventario.jinja2', 
                               sucursales=sucursales,
                               sucursal_actual_id=sucursal_actual_id)
    except Exception as e:
        print(f"Error en reporte_inventario_vista: {e}")
        return "Error al cargar la página", 500
    finally:
        if connection:
            connection.close()

# --- API PARA OBTENER LOS DATOS DEL REPORTE DE STOCK ---
@app.route('/api/reporte_stock', methods=['POST'])
def api_reporte_stock():
    if 'sucursal' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    data = request.json
    sucursal_id = data.get('sucursal_id')
    tipo_reporte = data.get('tipo_reporte') # 'productos' o 'materias_primas'

    if not sucursal_id or not tipo_reporte:
        return jsonify({'error': 'Faltan parámetros.'}), 400

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            if tipo_reporte == 'productos':
                query = """
                    SELECT 
                        p.pro_id AS id, 
                        p.pro_nombre AS nombre, 
                        p.pro_unimed AS unidad, 
                        p.pro_costo_unit AS costo,
                        ip.pro_stock AS stock,
                        (p.pro_costo_unit * ip.pro_stock) AS valor_total
                    FROM productos p
                    JOIN inventario_productos ip ON p.pro_id = ip.invpro_pro_fk
                    WHERE ip.invpro_suc_fk = %s
                    ORDER BY p.pro_nombre
                """
            elif tipo_reporte == 'materias_primas':
                query = """
                    SELECT 
                        mp.matprim_id AS id,
                        mp.matprim_nombre AS nombre,
                        mp.matprim_unimed AS unidad,
                        mp.matprim_costo_unit AS costo,
                        im.invmatprim_stock AS stock,
                        (mp.matprim_costo_unit * im.invmatprim_stock) AS valor_total
                    FROM materias_primas mp
                    JOIN inventario_materias_primas im ON mp.matprim_id = im.invmatprim_matprim_fk
                    WHERE im.invmatprim_suc_fk = %s
                    ORDER BY mp.matprim_nombre
                """
            else:
                return jsonify({'error': 'Tipo de reporte no válido.'}), 400

            cursor.execute(query, (sucursal_id,))
            items = cursor.fetchall()
            
            # Calcular el valor total del inventario
            valor_inventario_total = 0
            for item in items:
                item['costo'] = float(item['costo'])
                item['stock'] = float(item['stock'])
                item['valor_total'] = float(item['valor_total'])
                valor_inventario_total += item['valor_total']

        return jsonify({
            'items': items,
            'valor_inventario_total': valor_inventario_total
        })
        
    except Exception as e:
        print(f"Error en api_reporte_stock: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()



# --- RUTA PARA MOSTRAR LA PÁGINA DE REPORTE DE CAJA ---
@app.route('/reporteDeCaja')
def reporte_caja_vista():
    # Solo necesitamos mostrar la plantilla. El JS se encargará de
    # pedir los datos del día de hoy al cargar.
    if 'sucursal' not in session:
        return redirect(url_for('login'))
        
    return render_template('repoCaja.jinja2')

# --- API PARA OBTENER LOS DATOS DEL REPORTE DE CAJA POR DÍA ---
@app.route('/api/reporte_caja_dia', methods=['POST'])
def api_reporte_caja_dia():
    if 'sucursal' not in session:
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    sucursal_id = session['sucursal']
    data = request.json
    fecha_reporte = data.get('fecha')

    if not fecha_reporte:
        return jsonify({'error': 'No se proporcionó una fecha.'}), 400

    # Objeto que enviaremos al frontend
    resumen = {
        'ventas_efectivo': 0, 'ventas_tarjeta': 0,
        'ajustes_agregado': 0, 'ajustes_retiro': 0,
        'cortes_turno_retiro': 0, 'saldo_final_efectivo': 0,
        'saldo_final_tarjeta': 0
    }
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # 1. Total Ventas en Efectivo del día
            cursor.execute("""
                SELECT SUM(venta_monto_total) as total 
                FROM VENTA 
                WHERE venta_fecha = %s AND venta_suc_fk = %s AND venta_metodo_pago = 'efectivo'
            """, (fecha_reporte, sucursal_id))
            resumen['ventas_efectivo'] = float(cursor.fetchone()['total'] or 0)

            # 2. Total Ventas con Tarjeta del día
            cursor.execute("""
                SELECT SUM(venta_monto_total) as total 
                FROM VENTA 
                WHERE venta_fecha = %s AND venta_suc_fk = %s AND venta_metodo_pago = 'tarjeta'
            """, (fecha_reporte, sucursal_id))
            resumen['ventas_tarjeta'] = float(cursor.fetchone()['total'] or 0)

            # 3. Total Ajustes (AGREGO) del día
            cursor.execute("""
                SELECT SUM(ajuste_monto) as total 
                FROM historial_ajustes_caja 
                WHERE DATE(ajuste_fecha) = %s AND ajuste_suc_fk = %s AND ajuste_tipo = 'AGREGO'
            """, (fecha_reporte, sucursal_id))
            resumen['ajustes_agregado'] = float(cursor.fetchone()['total'] or 0)

            # 4. Total Ajustes (RETIRO) del día
            cursor.execute("""
                SELECT SUM(ajuste_monto) as total 
                FROM historial_ajustes_caja 
                WHERE DATE(ajuste_fecha) = %s AND ajuste_suc_fk = %s AND ajuste_tipo = 'RETIRO'
            """, (fecha_reporte, sucursal_id))
            resumen['ajustes_retiro'] = float(cursor.fetchone()['total'] or 0)

            # 5. Total Retiros por Corte de Turno del día
            cursor.execute("""
                SELECT SUM(efectivo_retirado) as total 
                FROM historial_cortes 
                WHERE DATE(corte_fecha) = %s AND corte_suc_fk = %s
            """, (fecha_reporte, sucursal_id))
            resumen['cortes_turno_retiro'] = float(cursor.fetchone()['total'] or 0)

            # 6. Saldos FINALES de la caja (esto es el estado actual, no histórico)
            # Nota: Esto mostrará el saldo al momento de la consulta, 
            # que si es el mismo día, será el saldo actual.
            cursor.execute("SELECT caja_efectivo, caja_tarjeta FROM CAJA WHERE caja_suc_fk = %s", (sucursal_id,))
            caja_actual = cursor.fetchone()
            if caja_actual:
                resumen['saldo_final_efectivo'] = float(caja_actual['caja_efectivo'])
                resumen['saldo_final_tarjeta'] = float(caja_actual['caja_tarjeta'])

        return jsonify(resumen)
        
    except Exception as e:
        print(f"Error en api_reporte_caja_dia: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()

#--------------------------------------------------
# FIN MODULO DE REPORTES

#--------------------------------------------------------------
# INICIO MODULO DE ENCARGADO

@app.route('/encargado')
def encargado():
    return render_template('encargado.jinja2')

@app.route('/crearCuentaEmpleado', methods=['GET', 'POST'])
def crear_empleado():
    # 1. VERIFICAR PERMISOS (Esto está bien)
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        flash('No tienes permiso para acceder a esta página.', 'error')
        return redirect(url_for('login')) 

    # --- LÓGICA POST (Procesar el formulario) ---
    if request.method == 'POST':
        connection = None
        try:
            # 2. OBTENER DATOS DEL FORMULARIO
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')
            correo = request.form.get('correo')
            telefono = request.form.get('telefono')
            sucursal_id_str = request.form.get('sucursal')
            rol_principal = request.form.get('rol_principal')
            contraseña = request.form.get('contraseña')
            confirmacion = request.form.get('confirmacion_de_contraseña')
            fecha_contratacion = date.today()

            if contraseña != confirmacion:
                raise Exception("Las contraseñas no coinciden.")
            
            sucursal_id = int(sucursal_id_str)
            
            # --- INICIO DE TRANSACCIÓN SEGURA ---
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                connection.begin()

                # 3. Validar correo y teléfono
                cursor.execute("SELECT emp_correo FROM empleados WHERE emp_correo = %s", (correo,))
                if cursor.fetchone():
                    raise Exception("El correo electrónico ya está registrado.")
                
                cursor.execute("SELECT emp_telefono FROM empleados WHERE emp_telefono = %s", (telefono,))
                if cursor.fetchone():
                    raise Exception("El número de teléfono ya está registrado.")

                # 4. Generar ID de empleado
                cursor.execute("SELECT proximo_id_empleado FROM contadores_sucursal WHERE sucursal_id = %s FOR UPDATE", (sucursal_id,))
                contador = cursor.fetchone()
                if not contador:
                    raise Exception(f"Error de configuración: No se encontró un contador para la sucursal {sucursal_id}.")
                
                proximo_sufijo = contador['proximo_id_empleado']
                base_id = sucursal_id * 100000
                nuevo_emp_id = base_id + proximo_sufijo
                
                cursor.execute("UPDATE contadores_sucursal SET proximo_id_empleado = %s WHERE sucursal_id = %s", (proximo_sufijo + 1, sucursal_id))

                # 5. Hashear contraseña e Insertar
                hashed_password = generate_password_hash(contraseña)
                sql = "INSERT INTO empleados (emp_id, emp_nombre, emp_apellido, emp_correo, emp_contrasenia, emp_telefono, emp_rol_principal, emp_sucursal,emp_contrat) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)"
                cursor.execute(sql, (nuevo_emp_id, nombre, apellido, correo, hashed_password, telefono, rol_principal, sucursal_id,fecha_contratacion))
            
            connection.commit()
            flash(f'Empleado "{nombre} {apellido}" (ID: {nuevo_emp_id}) creado exitosamente.', 'success')
            
        except Exception as e:
            if connection: connection.rollback()
            flash(f'Error al crear empleado: {e}', 'error')
        
        finally:
            if connection:
                connection.close()
        
        # Después de un POST (exitoso o fallido), siempre redirigir a la vista GET
        return redirect(url_for('crear_empleado'))

    # --- LÓGICA GET (Mostrar la página y el formulario) ---
    # Esto solo se ejecuta si request.method es 'GET'
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
            sucursales = cursor.fetchall()
            
            # --- CORRECCIÓN SQL AQUÍ ---
            # 'G' debe ir entre comillas para ser un string
            cursor.execute("SELECT rol_id as id, rol_nombre as nombre FROM roles WHERE rol_id != 'U' AND rol_id != 'G' ORDER BY rol_nombre")
            roles = cursor.fetchall()
        
        return render_template('encCrearCuentaEmpleado.jinja2', sucursales=sucursales, roles=roles)
    
    except Exception as e:
        # Si la carga GET falla, mostramos el error y redirigimos a una página segura (ej. 'encargado')
        flash(f'Error al cargar la página de creación: {e}', 'error')
        print(f"Error en GET crear_empleado: {e}")
        # NO redirigir a sí mismo, ¡redirigir a una página anterior!
        return redirect(url_for('encargado')) # Reemplaza 'encargado' por tu ruta del menú de encargado
    finally:
        if connection:
            connection.close()



@app.route('/gestionEmpleados')
def gestion_empleados_vista():
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        flash('No tienes permiso para acceder a esta página.', 'error')
        return redirect(url_for('login'))
        
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Obtenemos todas las sucursales para el filtro
            cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
            sucursales = cursor.fetchall()
        
        # Pasamos la sucursal del empleado para seleccionarla por defecto
        return render_template('encGestionEmpleados.jinja2', 
                            sucursales=sucursales, 
                            sucursal_actual_id=session['sucursal'])
    except Exception as e:
        flash(f"Error al cargar la página: {e}", 'error')
        return redirect(url_for('encargado')) # Redirige al menú de encargado
    finally:
        if connection:
            connection.close()

# En tu archivo app.py

@app.route('/api/empleados_por_sucursal/<int:sucursal_id>')
def api_empleados_por_sucursal(sucursal_id):
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    # Un Gerente puede ver cualquier sucursal, un Encargado solo la suya
    if 'G' not in session['roles'] and session['sucursal'] != sucursal_id:
        return jsonify({'error': 'No tienes permiso para ver esta sucursal'}), 403

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # --- CONSULTA MEJORADA ---
            # Esta consulta obtiene los datos del empleado, su rol principal,
            # y usa GROUP_CONCAT para juntar todos sus roles adicionales en una sola cadena.
            query = """
                SELECT 
                    e.emp_id, 
                    e.emp_nombre, 
                    e.emp_apellido, 
                    e.emp_activo, 
                    r_principal.rol_nombre AS rol_principal,
                    GROUP_CONCAT(r_adicional.rol_nombre SEPARATOR ', ') AS roles_adicionales
                FROM empleados e
                LEFT JOIN roles r_principal ON e.emp_rol_principal = r_principal.rol_id
                LEFT JOIN empleados_roles er ON e.emp_id = er.emprol_emp_fk
                LEFT JOIN roles r_adicional ON er.emprol_rol_fk = r_adicional.rol_id
                WHERE e.emp_sucursal = %s
                GROUP BY e.emp_id, e.emp_nombre, e.emp_apellido, e.emp_activo, r_principal.rol_nombre
                ORDER BY e.emp_id
            """
            cursor.execute(query, (sucursal_id,))
            empleados = cursor.fetchall()
            
            return jsonify(empleados)
    except Exception as e:
        print(f"Error en api_empleados_por_sucursal: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()



@app.route('/api/empleado/actualizar_estado', methods=['POST'])
def api_actualizar_estado_empleado():
    # 1. Verificar permisos (solo Encargados o Gerentes)
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401
    data = request.json
    emp_id = data.get('emp_id')
    nuevo_estado = bool(data.get('nuevo_estado')) # Convierte true/false de JS a 1/0 para SQL

    if not emp_id:
        return jsonify({'success': False, 'message': 'Falta ID de empleado'}), 400
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            sql = "UPDATE empleados SET emp_activo = %s WHERE emp_id = %s"
            cursor.execute(sql, (nuevo_estado, emp_id))
            connection.commit()
        accion = "activado" if nuevo_estado else "desactivado"
        return jsonify({'success': True, 'message': f'Empleado {emp_id} ha sido {accion}.'})
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en api_actualizar_estado_empleado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()

@app.route('/api/empleado/cambiar_password', methods=['POST'])
def api_cambiar_password():
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401
    data = request.json
    emp_id = data.get('emp_id')
    nueva_password = data.get('nueva_password')
    if not emp_id or not nueva_password:
        return jsonify({'success': False, 'message': 'Faltan datos (ID o nueva contraseña).'}), 400
    hashed_password = generate_password_hash(nueva_password)
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            sql = "UPDATE empleados SET emp_contrasenia = %s WHERE emp_id = %s"
            cursor.execute(sql, (hashed_password, emp_id))
            connection.commit()
        return jsonify({'success': True, 'message': f'Contraseña del empleado {emp_id} actualizada.'})
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en api_cambiar_password: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()

# En tu archivo app.py

@app.route('/api/empleado_detalle/<int:emp_id>', methods=['GET'])
def api_empleado_detalle(emp_id):
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        return jsonify({'error': 'Acceso no autorizado'}), 401
    
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # 1. Obtener la información básica del empleado
            cursor.execute("SELECT emp_nombre, emp_apellido, emp_correo, emp_telefono, emp_rol_principal FROM empleados WHERE emp_id = %s", (emp_id,))
            empleado_info = cursor.fetchone()
            if not empleado_info:
                return jsonify({'error': 'Empleado no encontrado'}), 404

            # 2. Obtener la lista de TODOS los roles posibles para el formulario
            cursor.execute("SELECT rol_id, rol_nombre FROM roles WHERE rol_id != 'U'")
            roles_posibles = cursor.fetchall()
            
            # 3. Obtener los roles ADICIONALES que este empleado ya tiene
            cursor.execute("SELECT emprol_rol_fk FROM empleados_roles WHERE emprol_emp_fk = %s", (emp_id,))
            roles_actuales = [row['emprol_rol_fk'] for row in cursor.fetchall()]

        return jsonify({
            'info_basica': empleado_info,
            'roles_posibles': roles_posibles,
            'roles_actuales': roles_actuales
        })

    except Exception as e:
        print(f"Error en api_empleado_detalle: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection: connection.close()
        


# En tu archivo app.py

@app.route('/api/empleado/actualizar', methods=['POST'])
def api_actualizar_empleado():
    if 'roles' not in session or not ('E' in session['roles'] or 'G' in session['roles']):
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401
    data = request.json
    emp_id = data.get('emp_id')
    # Datos básicos
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    correo = data.get('correo')
    telefono = data.get('telefono')
    rol_principal = data.get('rol_principal')
    # Lista de roles adicionales (ej: ['R', 'EV'])
    roles_adicionales = data.get('roles_adicionales', []) 
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # --- INICIA TRANSACCIÓN ---
            connection.begin()
            # 1. Actualizar la tabla principal 'empleados'
            sql_update_emp = """
                UPDATE empleados 
                SET emp_nombre = %s, emp_apellido = %s, emp_correo = %s, emp_telefono = %s, emp_rol_principal = %s
                WHERE emp_id = %s
            """
            cursor.execute(sql_update_emp, (nombre, apellido, correo, telefono, rol_principal, emp_id))
            # 2. Borrar TODOS los roles adicionales antiguos de este empleado
            cursor.execute("DELETE FROM empleados_roles WHERE emprol_emp_fk = %s", (emp_id,))
            # 3. Insertar los nuevos roles adicionales (si hay)
            if roles_adicionales:
                # Preparamos los datos para una inserción múltiple
                datos_roles = [(emp_id, rol_id) for rol_id in roles_adicionales]
                sql_insert_roles = "INSERT INTO empleados_roles (emprol_emp_fk, emprol_rol_fk) VALUES (%s, %s)"
                cursor.executemany(sql_insert_roles, datos_roles)
            # --- FINALIZA TRANSACCIÓN ---
            connection.commit()
        return jsonify({'success': True, 'message': f'Datos del empleado {emp_id} actualizados.'})
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error en api_actualizar_empleado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection: connection.close()


if __name__ == '__main__':
    #app.run(host 'ip' ,  port = 5555, debug = true)
    app.run(host='0.0.0.0',port=5555, debug=True)