

from flask import Flask, jsonify, request, render_template, session,send_from_directory,redirect, url_for,flash
import pymysql
from datetime import datetime
from datetime import date, datetime


# Inicialización de la aplicación Flask
app = Flask(__name__, template_folder='HTML')

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata',
    'db': 'mydb'
}


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
# FIN ENDPOINT REPARTO