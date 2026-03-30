from flask import Flask, jsonify, send_from_directory
import mysql.connector

# serves data to frontend 

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        database="dsci560_wells"
    )

@app.route("/api/wells")
def wells():
    cnx = get_connection()
    cur = cnx.cursor(dictionary=True)

    cur.execute("""
        SELECT w.*, s.stage, s.fluid_vol, s.proppant_lbs
        FROM wells w
        LEFT JOIN stimulation s ON s.well_api = w.api
    """)

    rows = cur.fetchall()
    cur.close()
    cnx.close()

    return jsonify(rows)

# Serve index.html
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

if __name__ == "__main__":
    app.run(debug=True)