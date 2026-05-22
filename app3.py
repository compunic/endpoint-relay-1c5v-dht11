# =====================================================
# app.py
# =====================================================

from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# =====================================================
# DATABASE
# =====================================================

DB = "relaydht.db"

# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        temperature REAL,
        humidity REAL,
        relay INTEGER,

        sensor_status TEXT,

        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =====================================================
# GLOBAL RELAY
# =====================================================

relay_status = 1

# =====================================================
# DASHBOARD
# =====================================================

@app.route('/')
def index():

    return render_template('index3.html')

# =====================================================
# ESP32 GET RELAY
# =====================================================

@app.route('/esp32')
def esp32():

    global relay_status

    return jsonify({
        "relay": relay_status
    })

# =====================================================
# UPDATE DATA FROM ESP32
# =====================================================

@app.route('/update', methods=['POST'])
def update():

    data = request.json

    suhu = data.get('temperature', 0)
    kelembaban = data.get('humidity', 0)
    relay = data.get('relay', 0)

    sensor_status = data.get(
        'sensor_status',
        'UNKNOWN'
    )

    print("========================")
    print("Temperature :", suhu)
    print("Humidity    :", kelembaban)
    print("Relay       :", relay)
    print("Sensor      :", sensor_status)
    print("========================")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO sensor_data (

        temperature,
        humidity,
        relay,
        sensor_status,
        created_at

    ) VALUES (?, ?, ?, ?, ?)
    """, (

        suhu,
        kelembaban,
        relay,
        sensor_status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success"
    })

# =====================================================
# GET LATEST DATA
# =====================================================

@app.route('/latest')
def latest():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT

        temperature,
        humidity,
        relay,
        sensor_status,
        created_at

    FROM sensor_data

    ORDER BY id DESC
    LIMIT 20
    """)

    rows = c.fetchall()

    conn.close()

    rows.reverse()

    data = []

    for row in rows:

        data.append({

            "temperature": row[0],
            "humidity": row[1],
            "relay": row[2],
            "sensor_status": row[3],
            "created_at": row[4]

        })

    return jsonify(data)

# =====================================================
# RELAY CONTROL
# =====================================================

@app.route('/relay/<int:status>')
def relay(status):

    global relay_status

    relay_status = status

    print("Relay:", relay_status)

    return jsonify({
        "relay": relay_status
    })

# =====================================================
# STATUS
# =====================================================

@app.route('/status')
def status():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    SELECT

        temperature,
        humidity,
        relay,
        sensor_status,
        created_at

    FROM sensor_data

    ORDER BY id DESC
    LIMIT 1
    """)

    row = c.fetchone()

    conn.close()

    if row:

        return jsonify({

            "temperature": row[0],
            "humidity": row[1],
            "relay": row[2],
            "sensor_status": row[3],
            "created_at": row[4]

        })

    return jsonify({

        "temperature": 0,
        "humidity": 0,
        "relay": 0,
        "sensor_status": "NO DATA",
        "created_at": "-"

    })

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5008,
        debug=True
    )