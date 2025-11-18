import pymysql
from werkzeug.security import generate_password_hash

# --- ¡CONFIGURA ESTO! ---
# Copia y pega la configuración de tu base de datos desde app.py
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'bakedata', # <-- CAMBIA ESTO
    'db': 'mydb',          # <-- CAMBIA ESTO
    'cursorclass': pymysql.cursors.DictCursor
}

# --- FIN DE LA CONFIGURACIÓN ---
def migrar_contraseñas():
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            # 1. Buscar solo empleados con contraseñas en TEXTO PLANO.
            # (Las contraseñas hasheadas empiezan con 'pbkdf2:sha256...')
            print("Buscando empleados con contraseñas sin hashear...")
            cursor.execute("SELECT emp_id, emp_contrasenia FROM empleados WHERE emp_contrasenia NOT LIKE 'scrypt:%'")
            empleados_a_migrar = cursor.fetchall()

            if not empleados_a_migrar:
                print("\n¡Felicidades! Todas las contraseñas ya están hasheadas.")
                return

            print(f"Se encontraron {len(empleados_a_migrar)} contraseñas para migrar.")
            
            # 2. Recorrer cada empleado y hashear su contraseña
            for empleado in empleados_a_migrar:
                emp_id = empleado['emp_id']
                contraseña_plana = empleado['emp_contrasenia']

                # Pequeña validación para no hashear contraseñas vacías
                if not contraseña_plana or len(contraseña_plana) < 4:
                    print(f"  - Omitiendo empleado {emp_id} (contraseña vacía o muy corta).")
                    continue
                
                print(f"  - Migrando contraseña para empleado {emp_id}...")
                
                # 3. Generar el hash seguro
                hashed_password = generate_password_hash(contraseña_plana)
                
                # 4. Actualizar la base de datos con el nuevo hash
                cursor.execute("UPDATE empleados SET emp_contrasenia = %s WHERE emp_id = %s", (hashed_password, emp_id))
            
            # 5. Guardar todos los cambios
            connection.commit()
            
            print(f"\n¡Migración completada! Se actualizaron {len(empleados_a_migrar)} contraseñas.")

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"\n--- ¡ERROR! ---")
        print(f"Ocurrió un error: {e}")
        print("No se realizó ningún cambio en la base de datos (rollback).")
    finally:
        if connection:
            connection.close()
            print("Conexión cerrada.")

# --- Ejecutar la función ---
if __name__ == "__main__":
    migrar_contraseñas()