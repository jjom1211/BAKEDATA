from flask import Flask, jsonify, request, render_template, send_from_directory
import pymysql

# ✅ IMPORTACIONES CLAVE: Traemos las funciones necesarias desde 'produccion.py'.
from produccion_server import get_materias_primas, solicitarMateriaPrima as solicitarMateriaPrima_Produccion, \
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
    materias = get_materias_primas()
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

# -----------------------------------------------------------
# Punto de entrada de la aplicación
# -----------------------------------------------------------
if __name__ == '__main__':
    # Usar un puerto diferente al de Producción (5004)
    app.run(port=5001, debug=True)