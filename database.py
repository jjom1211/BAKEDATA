# database.py
import pymysql

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Bakedata',
        db='mydb'
    )

def get_materias_primas():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT matprim_id, matprim_nombre, matprim_unimed FROM materias_primas")
            rows = cursor.fetchall()
            materias = []
            for row in rows:
                materias.append({
                    'id': row[0],
                    'nombre': row[1],
                    'unidad': row[2]
                })
            return materias
    finally:
        conn.close()
