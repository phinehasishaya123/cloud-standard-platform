import os
import json
import time
import psycopg2
import redis
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# --- Database Configuration ---
# Variables loaded from docker-compose.yml environment section
DB_NAME = os.environ.get('POSTGRES_DB', 'companydb')
DB_USER = os.environ.get('POSTGRES_USER', 'user')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '&&1234HT')
DB_HOST = os.environ.get('DB_HOST', 'localhost') # This MUST match the service name in docker-compose.yml

# --- REDIS CONFIGURATION ---
REDIS_HOST = 'caching-layer' 
REDIS_PORT = 6379
CACHE_TTL = 300

def get_redis_connection():
    """Attempts to connect to Redis."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_connect_timeout=1)
        r.ping()
        return r
    except Exception:
        return None

# --- Database Connection Functions ---

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def get_data_from_db():
    """Fetches data from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # This query simulates a complex data calculation
        query = "SELECT COUNT(*) FROM subsidiaries;"
        cur.execute(query)
        count = cur.fetchone()[0]

        # Simulate a slow database operation to prove caching works
        time.sleep(0.5) 

        data = {
            "status": "ok",
            "message": "Data successfully retrieved from PostgreSQL (SLOW DB HIT)",
            "data": {"total_subsidiaries": count, "timestamp": time.time()}
        }
        return data

    except Exception as e:
        return {"status": "error", "message": f"Database error: {e}"}
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """
    API endpoint that fetches status, using Redis cache if available.
    """
    r = get_redis_connection()
    CACHE_KEY = "api_status_data"

    # 1. CHECK CACHE (Fast)
    if r:
        cached_data = r.get(CACHE_KEY)
        if cached_data:
            # CACHE HIT
            data = json.loads(cached_data)
            data["message"] = "Data retrieved from Redis cache (FAST CACHE HIT)"
            return jsonify(data)

    # 2. CACHE MISS / REDIS DOWN (Slow)
    db_data = get_data_from_db()

    # 3. SAVE TO CACHE (If Redis is available)
    if r and db_data["status"] == "ok":
        try:
            r.setex(CACHE_KEY, CACHE_TTL, json.dumps(db_data))
        except Exception as e:
            print(f"Error saving to Redis: {e}")

    # Return the database data
    return jsonify(db_data)

# --- STARTUP ---
# We moved init_db() to a separate script or run it conditionally to avoid Gunicorn conflicts
# For this step, we rely on the database already being initialized from previous runs.

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
