import pymysql
from datetime import datetime
import pytz

# Configuración de conexión
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Bakedata',
    'db': 'mydb'
}

# Fecha actual con hora en 00:00:00
fecha_actual = datetime.now(pytz.timezone('America/Mexico_City')).strftime('%Y-%m-%d 00:00:00')

try:
    connection = pymysql.connect(**db_config)
    with connection.cursor() as cursor:
        print(f"🔍 Buscando actividades de limpieza para el día: {fecha_actual}")

        # Consulta que simula tu backend
        cursor.execute("""
            SELECT l.lim_actividad, ld.limdia_act_estado
            FROM limpieza_dia ld
            JOIN limpieza l ON ld.limdia_lim_fk = l.lim_id
            WHERE ld.limdia_limcal_fecha = %s
        """, (fecha_actual,))
        
        resultados = cursor.fetchall()

        if resultados:
            print("✅ Actividades encontradas para hoy:")
            for actividad, estado in resultados:
                print(f" - {actividad} (Estado: {estado})")
        else:
            print("⚠️ No se encontraron actividades para hoy.")

except Exception as e:
    print(f"❌ Error en la consulta: {e}")

finally:
    connection.close()
