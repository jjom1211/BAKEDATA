from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pymysql
from datetime import date, datetime
import pytz
import json
import decimal

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
    return render_template('proProduccionDelDia.jinja2')
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
@app.route("/registrarProduccion", methods=["GET", "POST"])
def registrar_produccion():
    """
    Ruta para servir la página HTML (GET) o registrar producción simple (POST).
    NOTA: La lógica POST de esta ruta es una implementación API simple.
    """
    if request.method == "GET":
        return render_template("proRegistrarProduccion.jinja2")
    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        producto_id = data.get("producto_id")
        cantidad = data.get("cantidad")
        if not producto_id or not cantidad:
            return jsonify({"error": "Faltan datos"}), 400

        # Aquí se debería guardar en la base de datos o llamar a una función de lógica
        # (La implementación se deja como un mensaje de confirmación simple, como en el original)
        return jsonify({"message": f"Producto {producto_id} registrado con cantidad {cantidad}"})


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

@app.route('/api/registrar_produccion', methods=['POST'])
def api_registrar_produccion():
    """Registra una lista de productos producidos en la tabla produccion_del_dia."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"success": False, "message": "Datos no válidos. Se espera una lista de productos."}), 400

    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # SQL para insertar en mydb.produccion_del_dia
            sql = "INSERT INTO produccion_del_dia (pro_dia_nombre, pro_dia_cantidad, pro_dia_estado) VALUES (%s, %s, %s)"
            
            for producto in data:
                nombre = producto.get('pro_dia_nombre')
                cantidad = producto.get('pro_dia_cantidad')
                estado = producto.get('pro_dia_estado', 'P') # Por defecto, 'P' (Pendiente)

                if nombre and cantidad is not None:
                    # Ejecutar el INSERT por cada producto
                    cursor.execute(sql, (nombre, cantidad, estado))
            
            conn.commit() # Confirmar la transacción
            return jsonify({"success": True, "message": "Producción registrada exitosamente."})
            
    except Exception as e:
        conn.rollback() # Revertir si hay un error
        print(f"Error al registrar producción: {e}")
        return jsonify({"success": False, "message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/obtener_produccion_hoy', methods=['GET'])
def api_obtener_produccion_hoy():
    """Obtiene todos los registros de la tabla produccion_del_dia."""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = "SELECT pro_dia_nombre, pro_dia_cantidad, pro_dia_estado FROM produccion_del_dia"
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            produccion = []
            for row in rows:
                produccion.append({
                    'pro_dia_nombre': row[0],
                    'pro_dia_cantidad': float(row[1]), # Convertir DECIMAL a float
                    'pro_dia_estado': row[2]
                })
            
            return jsonify(produccion)
            
    except Exception as e:
        print(f"Error al obtener producción: {e}")
        return jsonify({"success": False, "message": "Error al consultar la base de datos."}), 500
    finally:
        conn.close()
        
@app.route('/api/confirmar_produccion', methods=['POST'])
def api_confirmar_produccion():
    """
    Actualiza el estado de los productos de 'P' a 'C' (Completado/Confirmado) 
    en la tabla `produccion_del_dia`.
    """
    data = request.get_json()
    
    if not data or 'productos' not in data or not isinstance(data['productos'], list):
        return jsonify({"success": False, "message": "Datos no válidos. Se espera una lista de productos."}), 400

    productos_a_confirmar = data['productos']
    
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # Crear los placeholders de %s necesarios para la cláusula IN
            placeholders = ', '.join(['%s'] * len(productos_a_confirmar))
            
            sql = f"""
            UPDATE produccion_del_dia 
            SET pro_dia_estado = 'C' 
            WHERE pro_dia_nombre IN ({placeholders}) AND pro_dia_estado = 'P'
            """
            
            # Ejecutar la actualización
            cursor.execute(sql, productos_a_confirmar)
            
            rows_affected = cursor.rowcount
            conn.commit()
            
            return jsonify({
                "success": True, 
                "message": f"Se confirmaron {rows_affected} productos como Realizados."
            })
            
    except Exception as e:
        conn.rollback()
        print(f"Error al confirmar producción: {e}")
        return jsonify({"success": False, "message": f"Error interno del servidor: {str(e)}"}), 500
    finally:
        conn.close()


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

    if not carrito:
        return jsonify({'success': False, 'message': 'No hay materias primas en la solicitud.'}), 400
    if not tipo_origen or not origen_id:
        return jsonify({'success': False, 'message': 'No se seleccionó un origen válido.'}), 400

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
            
            # --- CORRECCIÓN DE LÓGICA DE ORIGEN ---
            proveedor_fk = None
            sucursal_origen_fk = None # Inicia como None
            asunto = ""

            if tipo_origen == 'proveedor':
                proveedor_fk = int(origen_id)
                sucursal_origen_fk = 1 # <-- ¡CORRECCIÓN! Asignamos ID 1 (Paseos del Bosque) como origen
                asunto = "Pedido a Proveedor"
                for item in carrito:
                     monto_total_solicitud += decimal.Decimal(costos.get(int(item['id']), 0)) * decimal.Decimal(item['cantidad'])
            
            elif tipo_origen == 'sucursal':
                sucursal_origen_fk = int(origen_id) # Asignamos el ID de la otra sucursal
                asunto = "Solicitud de Traslado"
                monto_total_solicitud = 0 
            
            # --- FIN DE LA CORRECCIÓN ---

            # 3. Insertar el Pedido principal
            sql_pedido = """
                INSERT INTO pedidos 
                (ped_emp_id, ped_sucursal_origen, ped_sucursal_destino, ped_prov_fk, ped_fecha_pedido, ped_monto_total, ped_estado_pedido, ped_asunto, ped_comentarios) 
                VALUES (%s, %s, %s, %s, %s, %s, 'P', %s, %s)
            """
            today = date.today()
            # Ahora sucursal_origen_fk NUNCA será None, resolviendo el error
            cursor.execute(sql_pedido, (empleado_id, sucursal_origen_fk, sucursal_id_destino, proveedor_fk, today, monto_total_solicitud, asunto, comentarios))
            pedido_id = cursor.lastrowid 

            # 4. Insertar detalles (sin cambios)
            sql_detalle = """
                INSERT INTO detalle_pedido_materias_primas 
                (detpedmat_ped_id, detpedmat_matprim_id, detpedmat_cantidad, detpedmat_precio_unitario) 
                VALUES (%s, %s, %s, %s)
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



# --- RUTA PARA MOSTRAR LA INTERFAZ DE "SOLICITAR PRODUCTOS" ---
@app.route('/solicitarProductos')
def solicitar_productos_vista():
    if 'sucursal' not in session or 'emp_id' not in session:
            return redirect(url_for('login'))
            
    connection = None
    try:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 1. Obtenemos TODOS los productos (para seleccionar)
                query_productos = """
                    SELECT pro_id as id, pro_nombre as nombre, pro_costo_unit as costo, pro_unimed as unidad
                    FROM productos ORDER BY pro_nombre
                """
                cursor.execute(query_productos)
                productos_disponibles = cursor.fetchall()
                for prod in productos_disponibles:
                    prod['costo'] = float(prod['costo'])
                
                # 2. Obtenemos TODAS las sucursales (para el selector de ORIGEN)
                cursor.execute("SELECT suc_id, suc_nombre FROM sucursales")
                sucursales = cursor.fetchall()
                
            # Pasamos productos y sucursales a la plantilla
            return render_template('venSolicitarProductos.jinja2', 
                                productos=productos_disponibles,
                                sucursales=sucursales)
    except Exception as e:
            print(f"Error en solicitar_productos_vista: {e}")
            return "Error al cargar la página", 500
    finally:
            if connection:
                connection.close()

# --- API PARA PROCESAR Y REGISTRAR LA SOLICITUD (PEDIDO) ---
@app.route('/api/finalizar_solicitud', methods=['POST'])
def api_finalizar_solicitud():
    if 'emp_id' not in session or 'sucursal' not in session:
        return jsonify({'success': False, 'message': 'Acceso no autorizado'}), 401

    # Obtenemos datos de la sesión y del JSON
    empleado_id = session['emp_id']
    sucursal_id_destino = session['sucursal'] # La sucursal que HACE la solicitud
    data = request.json
    carrito = data.get('carrito')
    comentarios = data.get('comentarios', '') # Un campo de comentarios opcional
    sucursal_id_origen = data.get('sucursal_origen_id') # El ORIGEN se recibe del formulario

    if not carrito:
        return jsonify({'success': False, 'message': 'No hay productos en la solicitud.'}), 400
    
    # Calculamos el monto total basado en el COSTO, no en el precio de venta
    monto_total_solicitud = sum(decimal.Decimal(item['costo']) * int(item['cantidad']) for item in carrito)

    connection = None
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            connection.begin() # INICIA TRANSACCIÓN

            # 1. Insertar el Pedido principal
            sql_pedido = """
                INSERT INTO pedidos 
                (ped_emp_id, ped_sucursal_origen, ped_sucursal_destino, ped_fecha_pedido, ped_monto_total, ped_estado_pedido, ped_asunto, ped_comentarios) 
                VALUES (%s, %s, %s, %s, %s, 'P', 'Solicitud de Productos', %s)
            """
            today = date.today()
            cursor.execute(sql_pedido, (empleado_id, sucursal_id_origen, sucursal_id_destino, today, monto_total_solicitud, comentarios))
            pedido_id = cursor.lastrowid # Obtenemos el ID del pedido

            # 2. Insertar los detalles del pedido
            # (Asumiendo que tienes la tabla 'detalle_pedido_productos' de nuestras conversaciones anteriores)
            sql_detalle = """
                INSERT INTO detalle_pedido_productos 
                (detpedpro_ped_id, detpedpro_pro_id, detpedpro_cantidad, detpedpro_precio_unitario) 
                VALUES (%s, %s, %s, %s)
            """
            detalles_para_insertar = []
            for item in carrito:
                costo_unitario = decimal.Decimal(item['costo'])
                cantidad = int(item['cantidad'])
                detalles_para_insertar.append((
                    pedido_id, item['id'], cantidad, costo_unitario
                ))
            cursor.executemany(sql_detalle, detalles_para_insertar)
            
            connection.commit() # TERMINA TRANSACCIÓN CON ÉXITO
            
        return jsonify({'success': True, 'message': f'Solicitud #{pedido_id} registrada exitosamente.'}), 200
    except Exception as e:
        if connection: connection.rollback()
        print(f"Error al finalizar solicitud: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if connection:
            connection.close()

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
    app.run(debug=True)