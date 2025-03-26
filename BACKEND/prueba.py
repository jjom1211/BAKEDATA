import pymysql

# Establecemos la conexión con la base de datos
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='bakedata',
    db='mydb'
)

# Creamos un cursor
cur = conn.cursor()

# Realizamos una consulta
cur.execute("SELECT * FROM mydb.usuarios")

# Obtenemos los resultados de la consulta
results = cur.fetchall()

# Imprimimos los resultados
for row in results:
    print(row)


try:
    with conn.cursor() as cursor:
        # Obtener el siguiente valor de la secuencia
        cursor.execute("UPDATE user_sequence SET valor = LAST_INSERT_ID(valor + 1)")
        cursor.execute("SELECT LAST_INSERT_ID()")
        next_id = cursor.fetchone()[0]

        # Insertar un nuevo usuario
        sql = """
        INSERT INTO usuarios (usu_id, usu_nombre, usu_apellido, usu_correo, usu_contrasenia, usu_telefono)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (next_id, 'Grace', 'Reparto', 'gracereparto@example.com', 'reparto', '0000000002'))
        conn.commit()
finally:
    conn.close()