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
