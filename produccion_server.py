from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pymysql
from datetime import date, datetime
import pytz
import json
import decimal

app = Flask(__name__, template_folder='HTML')

# Conexión a la base de datos
# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata',
    'db': 'mydb'
}

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
