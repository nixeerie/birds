from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

def get_db():
    """Otevře spojení na databázi s row_factory pro přístup ke sloupcům podle názvu."""
    conn = sqlite3.connect('ptaci.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def dashboard():
    """Načte všechny ptáky z databáze a zobrazí je v dashboardu."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ptaci ORDER BY nazev ASC')
        ptaci = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', ptaci=ptaci)
    except Exception as e:
        return f"Chyba: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)