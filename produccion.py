from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql

app = Flask(__name__, template_folder='HTML')

# Conexión a la base de datos
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Bakedata',
        db='mydb'
    )

# -------------------------
# Rutas de páginas HTML
# -------------------------
@app.route('/produccion.html')
def produccion():
    return render_template('produccion.html')

@app.route('/solicitarMateriaPrima.html')
def solicitarMateriaPrima():
    """Ruta para servir la página HTML de solicitud (Exportable)"""
    return render_template('solicitarMateriaPrima.html')

@app.route("/materias_primas.html")
def materias_primas():
    materias = get_materias_primas()
    return render_template('materias_primas.html', materias=materias)

@app.route("/registrar-produccion.html", methods=["GET", "POST"])
def registrar_produccion():
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

        # Aquí guardas en base de datos...
        return jsonify({"message": f"Producto {producto_id} registrado con cantidad {cantidad}"})

@app.route('/produccion-hoy.html')
def produccionHoy():
    return render_template('produccion-hoy.html')

# -------------------------
# Materias primas
# -------------------------
def get_materias_primas():
    # ... (lógica existente) ...
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
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

@app.route('/get_materias_por_sucursal')
def get_materias_por_sucursal():
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

# ✅ FUNCIÓN DE LÓGICA (EXPORTABLE): No es una ruta de Flask.
def buscar_materias_logic(query):
    """Contiene la lógica de la BD para buscar materias primas."""
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

# ✅ RUTA API DE PRODUCCIÓN: Llama a la lógica exportable
@app.route('/buscar_materias')
def buscar_materias():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])
    # Llama a la lógica de la BD
    resultados = buscar_materias_logic(query)
    return jsonify(resultados)

# ... (rest of the functions: buscar_productos, get_proveedores, etc.) ...

# -------------------------
# Archivos estáticos
# -------------------------
@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    return send_from_directory('JS', filename)

@app.route('/api/inventario/<int:sucursal_id>')
def obtener_inventario(sucursal_id):
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

@app.route('/buscar_productos')
def buscar_productos():
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

# -------------------------
# Main
# -------------------------
if __name__ == '__main__':
    app.run(port=5004, debug=True)
