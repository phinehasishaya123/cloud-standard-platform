from flask import Flask, jsonify

app = Flask(__name__)

# Data mimicking your 29 subsidiaries
subsidiaries = [
    {"id": 1, "name": "Subsidiary A", "status": "Operational"},
    {"id": 2, "name": "Subsidiary B", "status": "Maintenance"},
    {"id": 3, "name": "Subsidiary C", "status": "Operational"},
]

@app.route('/')
def home():
    return """
    <h1>Central IT Hub</h1>
    <p>System is Online.</p>
    <p><a href='/api/status'>View Subsidiary Status</a></p>
    """

@app.route('/api/status')
def get_status():
    # Return the data as JSON (Standard for Cloud APIs)
    return jsonify(subsidiaries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
