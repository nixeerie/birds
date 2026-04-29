from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'tajny_kluc_pre_flash'  # For flash messages

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

def get_statistics(conn, where_clause, values):
    """Vrací agregační statistiky pro filtrovaná data."""
    query = f'''
    SELECT
        COUNT(*) as pocet,
        ROUND(AVG(delka_cm), 1) as prum_delka,
        MAX(hmotnost_g) as max_hmotnost,
        MIN(hmotnost_g) as min_hmotnost,
        ROUND(AVG(hmotnost_g), 1) as prum_hmotnost,
        ROUND(AVG(rozpeti_cm), 1) as prum_rozpeti
    FROM ptaci WHERE {where_clause}
    '''
    
    cursor = conn.cursor()
    cursor.execute(query, values)
    result = cursor.fetchone()
    
    # Konverze do dictionary pro snazší přístup v šabloně
    stats = {
        'pocet': result[0] if result[0] else 0,
        'prum_delka': result[1] if result[1] else 0,
        'max_hmotnost': result[2] if result[2] else 0,
        'min_hmotnost': result[3] if result[3] else 0,
        'prum_hmotnost': result[4] if result[4] else 0,
        'prum_rozpeti': result[5] if result[5] else 0
    }
    
    return stats

def get_druhy_podle_radu(conn, where_clause, values):
    """Vrací počet druhů podle řádu."""
    query = f'''
    SELECT rad, COUNT(*) as pocet FROM ptaci 
    WHERE {where_clause}
    GROUP BY rad ORDER BY pocet DESC
    '''
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()
    
    labels = [row[0] for row in rows if row[0]]
    data = [row[1] for row in rows if row[0]]
    
    return labels, data

def get_hmotnost_podle_potravy(conn, where_clause, values):
    """Vrací průměrnou hmotnost podle typu potravy."""
    query = f'''
    SELECT typ_potravy, ROUND(AVG(hmotnost_g), 0) as prum
    FROM ptaci WHERE {where_clause}
    GROUP BY typ_potravy ORDER BY prum DESC
    '''
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()
    
    labels = [row[0] for row in rows if row[0]]
    data = [row[1] for row in rows if row[0]]
    
    return labels, data

def get_migrace_rozdel(conn, where_clause, values):
    """Vrací rozdělení tažních vs. netažních ptáků."""
    query = f'''
    SELECT migrace, COUNT(*) as pocet FROM ptaci
    WHERE {where_clause}
    GROUP BY migrace
    '''
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()
    
    labels = []
    data = []
    
    for row in rows:
        if row[0] == 1:
            labels.append('Tažný')
        elif row[0] == 0:
            labels.append('Netažný')
        else:
            continue
        data.append(row[1])
    
    return labels, data

def get_druhy_podle_kontinentu(conn, where_clause, values):
    """Vrací počet druhů podle kontinentu."""
    query = f'''
    SELECT vyskyt_kontinent, COUNT(*) as pocet FROM ptaci
    WHERE {where_clause}
    GROUP BY vyskyt_kontinent ORDER BY pocet DESC
    '''
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()
    
    labels = [row[0] for row in rows if row[0]]
    data = [row[1] for row in rows if row[0]]
    
    return labels, data

@app.route("/pridat_ptaka", methods=["GET", "POST"])
def pridat_ptaka():
    """Formulář pro přidání nového ptáka."""
    if request.method == "POST":
        # Získání dat z formuláře
        nazev = request.form.get('nazev', '').strip()
        vedecky_nazev = request.form.get('vedecky_nazev', '').strip()
        rad = request.form.get('rad', '').strip()
        celed = request.form.get('celed', '').strip()
        
        # Základní validace
        if not nazev or not vedecky_nazev:
            flash("Název a vědecký název jsou povinné!", "error")
            return redirect(url_for('pridat_ptaka'))
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Kontrola duplicity
            cursor.execute('SELECT id, nazev, vedecky_nazev FROM ptaci WHERE nazev = ? OR vedecky_nazev = ?', 
                         (nazev, vedecky_nazev))
            existing = cursor.fetchone()
            
            if existing:
                flash(f"Tento pták už možná existuje: {existing[1]} ({existing[2]})", "warning")
            
            # Vložení nového ptáka
            cursor.execute('''
                INSERT INTO ptaci (nazev, vedecky_nazev, rad, celed) 
                VALUES (?, ?, ?, ?)
            ''', (nazev, vedecky_nazev, rad if rad else None, celed if celed else None))
            
            conn.commit()
            conn.close()
            
            flash("Pták úspěšně přidán! 🐦", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f"Chyba při ukládání: {e}", "error")
            return redirect(url_for('pridat_ptaka'))
    
    # GET request - zobrazit formulář
    try:
        conn = get_db()
        filter_options = get_filter_options(conn)
        conn.close()
    except Exception as e:
        filter_options = {'rady': [], 'celedi': []}
    
    return render_template('pridat_ptaka.html', filter_options=filter_options)

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
        
        # Agregační statistiky
        stats = get_statistics(conn, where_clause, values)
        
        # Data pro grafy
        graf_rad_labels, graf_rad_data = get_druhy_podle_radu(conn, where_clause, values)
        graf_potrava_labels, graf_potrava_data = get_hmotnost_podle_potravy(conn, where_clause, values)
        graf_migrace_labels, graf_migrace_data = get_migrace_rozdel(conn, where_clause, values)
        graf_kontinent_labels, graf_kontinent_data = get_druhy_podle_kontinentu(conn, where_clause, values)
        
        query = f'SELECT * FROM ptaci WHERE {where_clause} ORDER BY {order_by}'
        
        cursor = conn.cursor()
        cursor.execute(query, values)
        ptaci = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             ptaci=ptaci, 
                             filter_options=filter_options,
                             filters=request.args,
                             stats=stats,
                             graf_rad_labels=graf_rad_labels,
                             graf_rad_data=graf_rad_data,
                             graf_potrava_labels=graf_potrava_labels,
                             graf_potrava_data=graf_potrava_data,
                             graf_migrace_labels=graf_migrace_labels,
                             graf_migrace_data=graf_migrace_data,
                             graf_kontinent_labels=graf_kontinent_labels,
                             graf_kontinent_data=graf_kontinent_data)
    except Exception as e:
        return f"Chyba: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)