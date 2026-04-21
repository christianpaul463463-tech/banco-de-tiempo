import psycopg2

conn = psycopg2.connect(
    dbname="banco_tiempo_db",
    user="postgres",
    password="postgres",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("DROP SCHEMA public CASCADE;")
cur.execute("CREATE SCHEMA public;")
cur.execute("GRANT ALL ON SCHEMA public TO postgres;")
cur.execute("GRANT ALL ON SCHEMA public TO public;")
cur.close()
conn.close()
print("Schema dropped and recreated.")
