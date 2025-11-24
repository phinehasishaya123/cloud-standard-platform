import os
import time
import psycopg2
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# --- Database Configuration ---
# Variables loaded from docker-compose.yml environment section
DB_NAME = os.environ.get('POSTGRES_DB', 'companydb')
DB_USER = os.environ.get('POSTGRES_USER', 'user')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')
DB_HOST = os.environ.get('DB_HOST', 'company-database') # This MUST match the service name in docker-compose.yml

# --- Database Connection Functions ---

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    """Initializes the database by creating the subsidiaries table and inserting initial data."""
    # Attempt connection with a retry loop, necessary for Docker startup dependencies
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Create the table if it doesn't exist (ensures persistence works)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subsidiaries (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL
                );
            """)

            # Check if data already exists to prevent duplicate entries on restart
            cur.execute("SELECT COUNT(*) FROM subsidiaries;")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO subsidiaries (name, status) VALUES
                        ('Subsidiary A', 'Operational'),
                        ('Subsidiary B', 'Maintenance'),
                        ('Subsidiary C', 'Operational');
                """)
                print("Initial data inserted.")
            
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully!")
            return # Exit the function after successful initialization

        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"Error initializing DB: {e}. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Failed to connect to database after {max_retries} attempts.")
                raise e # Re-raise error if all retries fail

# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the simple HTML front page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """
    Fetches the status of all subsidiaries from the database and returns it as JSON.
    This function was fixed to resolve the NameError.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Execute the SQL query
    cur.execute('SELECT id, name, status FROM subsidiaries;')
    
    # 2. Fetch all rows from the cursor
    subsidiary_rows = cur.fetchall() 

    cur.close()
    conn.close()

    # 3. Convert Database rows (tuples) to a list of Dictionaries (JSON structure)
    results = []
    for row in subsidiary_rows: 
        results.append({
            "id": row[0], 
            "name": row[1], 
            "status": row[2]
        })

    # 4. Return the fully processed list
    return jsonify(results) 

# --- Application Startup ---
if __name__ == '__main__':
    # Initialize the database and then run the Flask app.
    # Docker entrypoint uses 'sh -c 'sleep 10 && python main.py'' 
    # to ensure the database starts first.
    init_db()
    # This line ensures the process stays running to serve HTTP requests.
    app.run(host='0.0.0.0', port=5000)
