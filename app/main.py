import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

# 1. Get DB details from Environment Variables (The Cloud Way)
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

# 2. Initialize the Database (Create Table if not exists)
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subsidiaries (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                status VARCHAR(50)
            );
        """)
        # Add initial data if empty
        cur.execute("SELECT count(*) FROM subsidiaries;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO subsidiaries (name, status) VALUES (%s, %s)", ('Subsidiary A', 'Operational'))
            cur.execute("INSERT INTO subsidiaries (name, status) VALUES (%s, %s)", ('Subsidiary B', 'Maintenance'))

        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing DB: {e}")

# Run init on startup
init_db()

@app.route('/')

def home():
    return "<h1>Central IT Hub - Connected to PostgreSQL Database</h1>"

@app.route('/api/status')
def get_status():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, status FROM subsidiaries;')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert Database rows to JSON
    results = []
    for row in rows:
        results.append({"id": row[0], "name": row[1], "status": row[2]})

    return jsonify(subsidiaries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
