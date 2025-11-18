
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for,flash
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import pymysql
from datetime import date, datetime
import pytz
import json
import decimal


# Inicialización de la aplicación Flask
app = Flask(__name__, template_folder='HTML')

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata',
    'db': 'mydb'
}





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