from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql

# ✅ IMPORTACIONES CLAVE: Traemos las funciones necesarias desde 'produccion.py'.
from produccion import solicitarMateriaPrima as solicitarMateriaPrima_Produccion, \
    buscar_materias_logic

# Se crea la app Flask. Se recomienda usar un puerto diferente al de Producción (5004).
app = Flask(__name__, template_folder='HTML')

# -----------------------------------------------------------
# Función auxiliar para conectarse a la base de datos MySQL
# -----------------------------------------------------------
def get_db_connection():
    # NOTA: Usamos las mismas credenciales de Producción
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Bakedata',
        db='mydb'
    )

# -----------------------------------------------------------
# Rutas de la aplicación de Almacén
# -----------------------------------------------------------

@app.route('/almacen.html')
def almacen():
    return render_template('almacen.html')

@app.route("/materias_primas.html")
def materias_primas():
    # Reutiliza la función de BD
    materias = get_materias_primas_almacen()
    return render_template('materias_primas.html', materias=materias)

# 1. RUTA HTML REUTILIZADA
@app.route('/solicitarMateriaPrima.html')
def solicitarMateriaPrima():
    """
    Ruta para la página de solicitud.
    Reutiliza la función 'solicitarMateriaPrima' del módulo Producción 
    para servir el mismo HTML.
    """
    return solicitarMateriaPrima_Produccion()

# 2. RUTA API REUTILIZADA: /buscar_materias
@app.route('/buscar_materias')
def buscar_materias_almacen():
    """
    Endpoint llamado por el JS. Reutiliza la lógica de BD del módulo Producción.
    Esto resuelve el error 'Unexpected token <' que tenías, ya que ahora 
    el servidor de Almacén (Puerto 5001) responde a esta ruta.
    """
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])
        
    # Llamamos a la función de lógica que trajimos de produccion.py
    try:
        resultados = buscar_materias_logic(query)
        return jsonify(resultados)
    except Exception as e:
        # Manejo de error de BD, vital para que el frontend no reciba HTML
        print(f"Error en la búsqueda de materias primas (Almacén): {e}")
        return jsonify({"error": "Fallo en la conexión o consulta a la base de datos"}), 500
    
@app.route("/productos.html")
def productos():
    """
    Obtiene la lista completa de productos y la sirve en la plantilla HTML.
    Esta ruta responde al clic del botón 'Ver Productos'.
    """
    # Llama a la lógica de BD importada
    try:
        productos = get_all_productos()
    except Exception as e:
        # En caso de error de BD, devuelve una lista vacía para no romper el template
        print(f"Error al cargar productos para la vista: {e}")
        productos = []
        
    # Servimos la plantilla HTML (productos.html) pasándole los datos
    return render_template('productos.html', productos=productos)


def get_all_productos():
    conn = get_db_connection()
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

# Rutas para archivos estáticos (CSS, JS)
@app.route('/CSS/<path:filename>')
def serve_css(filename):
    return send_from_directory('CSS', filename)

@app.route('/JS/<path:filename>')
def serve_js(filename):
    return send_from_directory('JS', filename)


@app.route('/api/inventario/<int:sucursal_id>')
def obtener_inventario(sucursal_id):
    """Obtiene el inventario de materias primas para una sucursal específica (API Restful)."""
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
# ... (tu función get_db_connection() termina aquí) ...

# ✅ NUEVA FUNCIÓN LOCAL - Esta es la que usaremos
def get_materias_primas_almacen():
    """Obtiene una lista de TODAS las materias primas, INCLUYENDO EL COSTO."""
    conn = get_db_connection()
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

# ... (tus otras rutas como /almacen.html, /materias_primas.html, etc.) ...
UNIDADES_DE_MEDIDA = [
    ('KG', 'Kilogramo'),
    ('GR', 'Gramo'),
    ('PZA', 'Pieza'),
    ('L', 'Litro'),
    ('ml', 'Mililitro'),
    ('M', 'Metro')
]
# -----------------------------------------------------------
# PASO 3: RUTA PARA SERVIR LA NUEVA PÁGINA DE EDICIÓN
# -----------------------------------------------------------
@app.route('/almActMatPrim.html')
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
        'almActMatPrim.html', 
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

    conn = get_db_connection()
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
# ALMACÉN: ACTUALIZAR PRODUCTOS
# ===========================================================

@app.route('/almActProductos.html')
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
        'almActProductos.html', 
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

    conn = get_db_connection()
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
# -----------------------------------------------------------
# Punto de entrada de la aplicación
# -----------------------------------------------------------
if __name__ == '__main__':
    # Usar un puerto diferente al de Producción (5004)
    app.run(port=5001, debug=True)