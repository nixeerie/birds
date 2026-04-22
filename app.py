from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Povolené sloupce pro řazení (prevence SQL injection)
ALLOWED_SORT_COLUMNS = {
    "nazev", "vedecky_nazev", "rad", "celed",
    "delka_cm", "rozpeti_cm", "hmotnost_g",
    "status_ohrozeni", "typ_potravy", "migrace",
    "vyskyt_kontinent", "snuska_ks",
}

def get_db():
    """Otevře spojení na databázi s row_factory pro přístup ke sloupcům podle názvu."""
    conn = sqlite3.connect('ptaci.db')
    conn.row_factory = sqlite3.Row
    return conn

def build_query(params):
    """Sestaví WHERE klauzuli a seznam hodnot podle parametrů filtru."""
    where_conditions = []
    values = []
    
    if params.get('rad'):
        where_conditions.append('rad = ?')
        values.append(params['rad'])
    
    if params.get('typ_potravy'):
        where_conditions.append('typ_potravy = ?')
        values.append(params['typ_potravy'])
    
    if params.get('kontinent'):
        where_conditions.append('vyskyt_kontinent = ?')
        values.append(params['kontinent'])
    
    if params.get('migrace') in ['0', '1']:
        where_conditions.append('migrace = ?')
        values.append(int(params['migrace']))
    
    if params.get('status'):
        where_conditions.append('status_ohrozeni = ?')
        values.append(params['status'])
    
    if params.get('hmotnost_min'):
        try:
            where_conditions.append('hmotnost_g >= ?')
            values.append(int(params['hmotnost_min']))
        except ValueError:
            pass
    
    if params.get('hmotnost_max'):
        try:
            where_conditions.append('hmotnost_g <= ?')
            values.append(int(params['hmotnost_max']))
        except ValueError:
            pass
    
    where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
    return where_clause, values

def get_sort_order(params):
    """Vracuje bezpečný ORDER BY klauzuli z parametrů."""
    razeni = params.get('razeni', 'nazev')
    smer = params.get('smer', 'ASC')
    
    # Validace sloupce
    if razeni not in ALLOWED_SORT_COLUMNS:
        razeni = 'nazev'
    
    # Validace směru
    if smer.upper() not in ['ASC', 'DESC']:
        smer = 'ASC'
    else:
        smer = smer.upper()
    
    return f'{razeni} {smer}'

def get_filter_options(conn):
    """Načte unikátní hodnoty pro filtry z databáze."""
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT rad FROM ptaci WHERE rad IS NOT NULL AND rad != "" ORDER BY rad')
    rady = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT celed FROM ptaci WHERE celed IS NOT NULL AND celed != "" ORDER BY celed')
    celedi = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT typ_potravy FROM ptaci WHERE typ_potravy IS NOT NULL AND typ_potravy != "" ORDER BY typ_potravy')
    potravys = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT vyskyt_kontinent FROM ptaci WHERE vyskyt_kontinent IS NOT NULL AND vyskyt_kontinent != "" ORDER BY vyskyt_kontinent')
    kontinenty = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT status_ohrozeni FROM ptaci WHERE status_ohrozeni IS NOT NULL AND status_ohrozeni != "" ORDER BY status_ohrozeni')
    statusy = [row[0] for row in cursor.fetchall()]
    
    return {
        'rady': rady,
        'celedi': celedi,
        'potravys': potravys,
        'kontinenty': kontinenty,
        'statusy': statusy
    }

@app.route("/")
def dashboard():
    """Načte ptáky z databáze s příslušnými filtry a řazením a zobrazí je v dashboardu."""
    try:
        conn = get_db()
        
        # Načtení filtrovacích možností
        filter_options = get_filter_options(conn)
        
        # Sestavení query s filtry
        where_clause, values = build_query(request.args)
        
        # Bezpečné řazení
        order_by = get_sort_order(request.args)
        
        query = f'SELECT * FROM ptaci WHERE {where_clause} ORDER BY {order_by}'
        
        cursor = conn.cursor()
        cursor.execute(query, values)
        ptaci = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             ptaci=ptaci, 
                             filter_options=filter_options,
                             filters=request.args)
    except Exception as e:
        return f"Chyba: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)