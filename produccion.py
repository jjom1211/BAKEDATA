from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql

# ==============================================================================
# 1. CONFIGURACIÓN DE LA APLICACIÓN
# ==============================================================================
app = Flask(__name__, template_folder='HTML')

# ==============================================================================
# 2. CONEXIÓN A LA BASE DE DATOS (UTILITY)
# ==============================================================================
def get_db_connection():
    """Establece la conexión a la base de datos MySQL."""
    # Asegúrate de que los credenciales sean correctos
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Bakedata',
        db='mydb'
    )

# ==============================================================================
# 3. FUNCIONES DE LÓGICA DE NEGOCIO (BD Utilities)
#    Funciones que contienen lógica de BD pura, no son rutas de Flask.
# ==============================================================================

def get_materias_primas():
    """Obtiene una lista de todas las materias primas de la base de datos."""
    conn = get_db_connection()
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
    conn = get_db_connection()
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

# ==============================================================================
# 4. RUTAS DE PÁGINAS HTML (VISTAS)
#    Rutas que renderizan plantillas Jinja2 (archivos .html).
# ==============================================================================

@app.route('/')
def index():
    """Ruta principal (si aplica, puede redirigir o mostrar un índice)."""
    return render_template('login.html')

@app.route('/produccion.html')
def produccion():
    """Página de inicio de Producción."""
    return render_template('produccion.html')

@app.route('/solicitarMateriaPrima.html')
def solicitarMateriaPrima():
    """Página para solicitar materia prima."""
    return render_template('solicitarMateriaPrima.html')

@app.route("/materias_primas.html")
def materias_primas():
    """Página que lista todas las materias primas."""
    materias = get_materias_primas()
    return render_template('materias_primas.html', materias=materias)

@app.route('/produccion-hoy.html')
def produccionHoy():
    """Página que muestra la producción del día."""
    return render_template('produccion-hoy.html')
@app.route('/api/inventario/<int:sucursal_id>')

def obtener_inventario(sucursal_id):
    """Obtiene el inventario de materias primas para una sucursal específica (API Restful)."""
    conn = get_db_connection()
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
@app.route("/registrar-produccion.html", methods=["GET", "POST"])
def registrar_produccion():
    """
    Ruta para servir la página HTML (GET) o registrar producción simple (POST).
    NOTA: La lógica POST de esta ruta es una implementación API simple.
    """
    if request.method == "GET":
        return render_template("registrar-produccion.html")
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

    conn = get_db_connection()
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

    conn = get_db_connection()
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

    conn = get_db_connection()
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

    conn = get_db_connection()
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
    conn = get_db_connection()
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
    
    conn = get_db_connection()
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
# 7. RUTAS DE ARCHIVOS ESTÁTICOS
#    Rutas para servir CSS y JS.
# ==============================================================================

@app.route('/CSS/<path:filename>')
def serve_css(filename):
    """Sirve archivos CSS desde el directorio 'CSS'."""
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    """Sirve archivos JavaScript desde el directorio 'JS'."""
    return send_from_directory('JS', filename)

# ==============================================================================
# 8. EJECUCIÓN PRINCIPAL
# ==============================================================================

if __name__ == '__main__':
    app.run(port=5004, debug=True)
