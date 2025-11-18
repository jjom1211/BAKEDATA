
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
