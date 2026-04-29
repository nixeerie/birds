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

def get_ptak_by_id(conn, ptak_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ptaci WHERE id = ?', (ptak_id,))
    return cursor.fetchone()

@app.route('/ptak/<int:ptak_id>')
def detail_ptaka(ptak_id):
    try:
        conn = get_db()
        ptak = get_ptak_by_id(conn, ptak_id)
        conn.close()
    except Exception as e:
        return f"Chyba: {e}", 500

    if not ptak:
        return "Pták nebyl nalezen.", 404

    return render_template('detail_ptaka.html', ptak=ptak)


@app.route('/upravit_ptaka/<int:ptak_id>', methods=['GET', 'POST'])
def upravit_ptaka(ptak_id):
    try:
        conn = get_db()
        ptak = get_ptak_by_id(conn, ptak_id)
    except Exception as e:
        return f"Chyba: {e}", 500

    if not ptak:
        return "Pták nebyl nalezen.", 404

    if request.method == 'POST':
        action = request.form.get('action', 'save')
        nazev = request.form.get('nazev', '').strip()
        vedecky_nazev = request.form.get('vedecky_nazev', '').strip()
        rad = request.form.get('rad', '').strip()
        celed = request.form.get('celed', '').strip()
        delka_cm = request.form.get('delka_cm', '').strip()
        rozpeti_cm = request.form.get('rozpeti_cm', '').strip()
        hmotnost_g = request.form.get('hmotnost_g', '').strip()
        vyskyt_kontinent = request.form.get('vyskyt_kontinent', '').strip()
        migrace = request.form.get('migrace', '').strip()
        typ_potravy = request.form.get('typ_potravy', '').strip()
        status_ohrozeni = request.form.get('status_ohrozeni', '').strip()
        snuska_ks = request.form.get('snuska_ks', '').strip()

        if not nazev:
            flash("Název je povinný!", "error")
            conn.close()
            return redirect(url_for('upravit_ptaka', ptak_id=ptak_id))

        if not vedecky_nazev:
            flash("Vědecký název chybí, uložíno jako neúplný záznam.", "warning")

        def safe_int(value):
            try:
                return int(value) if value else None
            except ValueError:
                return None

        parsed_delka = safe_int(delka_cm)
        parsed_rozpeti = safe_int(rozpeti_cm)
        parsed_hmotnost = safe_int(hmotnost_g)
        parsed_migrace = safe_int(migrace) if migrace else None
        parsed_snuska = safe_int(snuska_ks)

        warnings = build_form_warnings(
            parsed_delka,
            parsed_rozpeti,
            parsed_hmotnost,
            parsed_snuska,
            vyskyt_kontinent or None,
            parsed_migrace,
            typ_potravy or None,
            status_ohrozeni or None
        )

        for warning in warnings:
            flash(warning, 'warning')

        cursor = conn.cursor()
        cursor.execute('''
            UPDATE ptaci SET nazev = ?, vedecky_nazev = ?, rad = ?, celed = ?, delka_cm = ?,
                            rozpeti_cm = ?, hmotnost_g = ?, vyskyt_kontinent = ?, migrace = ?,
                            typ_potravy = ?, status_ohrozeni = ?, snuska_ks = ?
            WHERE id = ?
        ''', (
            nazev, vedecky_nazev, rad or None, celed or None,
            parsed_delka, parsed_rozpeti, parsed_hmotnost,
            vyskyt_kontinent or None, parsed_migrace,
            typ_potravy or None, status_ohrozeni or None, parsed_snuska,
            ptak_id
        ))
        conn.commit()
        conn.close()

        flash("Pták úspěšně upraven! 🐦", "success")
        return redirect(url_for('detail_ptaka', ptak_id=ptak_id))

    try:
        filter_options = get_filter_options(conn)
        conn.close()
    except Exception:
        filter_options = {'rady': [], 'celedi': []}

    return render_template('pridat_ptaka.html',
                           ptak=ptak,
                           filter_options=filter_options,
                           action_url=url_for('upravit_ptaka', ptak_id=ptak_id),
                           page_title='Upravit ptáka',
                           page_header='🛠️ Upravit ptáka',
                           button_text='Uložit změny',
                           edit_mode=True)


def build_form_warnings(delka_cm, rozpeti_cm, hmotnost_g, snuska_ks, vyskyt_kontinent, migrace, typ_potravy, status_ohrozeni):
    warnings = []

    if delka_cm is not None:
        if delka_cm < 5:
            warnings.append('Zadaná délka je velmi nízká, zkontroluj prosím, zda je hodnota správná.')
        elif delka_cm > 120:
            warnings.append('Zadaná délka je velmi vysoká, ověř si prosím tento údaj.')

    if rozpeti_cm is not None:
        if rozpeti_cm < 15:
            warnings.append('Rozpětí je velmi malé, ověř, zda to není překlep.')
        elif rozpeti_cm > 320:
            warnings.append('Rozpětí je neobvykle velké, zkontroluj prosím hodnotu.')

    if hmotnost_g is not None:
        if hmotnost_g < 10:
            warnings.append('Hmotnost je nízká pro většinu ptáků, může jít o chybu.')
        elif hmotnost_g > 12000:
            warnings.append('Hmotnost je velmi vysoká, zkontroluj prosím údaj.')

    if snuska_ks is not None:
        if snuska_ks < 1 or snuska_ks > 20:
            warnings.append('Počet vajec je mimo běžné rozmezí, ale může být stále platný.')

    if not any([delka_cm, rozpeti_cm, hmotnost_g, vyskyt_kontinent, migrace, typ_potravy, status_ohrozeni, snuska_ks]):
        warnings.append('Právě ukládáš záznam bez volitelných detailů. Můžeš je doplnit později.')

    return warnings

@app.route("/pridat_ptaka", methods=["GET", "POST"])
def pridat_ptaka():
    """Formulář pro přidání nového ptáka."""
    if request.method == "POST":
        action = request.form.get('action', 'save')

        # Získání dat z formuláře
        nazev = request.form.get('nazev', '').strip()
        vedecky_nazev = request.form.get('vedecky_nazev', '').strip()
        rad = request.form.get('rad', '').strip()
        celed = request.form.get('celed', '').strip()
        
        # Volitelné detaily
        delka_cm = request.form.get('delka_cm', '').strip()
        rozpeti_cm = request.form.get('rozpeti_cm', '').strip()
        hmotnost_g = request.form.get('hmotnost_g', '').strip()
        vyskyt_kontinent = request.form.get('vyskyt_kontinent', '').strip()
        migrace = request.form.get('migrace', '').strip()
        typ_potravy = request.form.get('typ_potravy', '').strip()
        status_ohrozeni = request.form.get('status_ohrozeni', '').strip()
        snuska_ks = request.form.get('snuska_ks', '').strip()
        
        # Základní validace
        if not nazev:
            flash("Název je povinný!", "error")
            return redirect(url_for('pridat_ptaka'))

        if not vedecky_nazev:
            flash("Vědecký název chybí, uložíno jako neúplný záznam.", "warning")
        
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Kontrola duplicity
            cursor.execute('SELECT id, nazev, vedecky_nazev FROM ptaci WHERE nazev = ? OR vedecky_nazev = ?', 
                         (nazev, vedecky_nazev))
            existing = cursor.fetchone()
            
            if existing:
                flash(f"Tento pták už možná existuje: {existing[1]} ({existing[2]})", "warning")
            
            # Příprava hodnot pro volitelné pole
            def safe_int(value):
                try:
                    return int(value) if value else None
                except ValueError:
                    return None

            parsed_delka = safe_int(delka_cm)
            parsed_rozpeti = safe_int(rozpeti_cm)
            parsed_hmotnost = safe_int(hmotnost_g)
            parsed_migrace = safe_int(migrace) if migrace else None
            parsed_snuska = safe_int(snuska_ks)

            warnings = build_form_warnings(
                parsed_delka,
                parsed_rozpeti,
                parsed_hmotnost,
                parsed_snuska,
                vyskyt_kontinent or None,
                parsed_migrace,
                typ_potravy or None,
                status_ohrozeni or None
            )

            for warning in warnings:
                flash(warning, 'warning')

            # Vložení nového ptáka
            cursor.execute('''
                INSERT INTO ptaci (nazev, vedecky_nazev, rad, celed, delka_cm, rozpeti_cm, 
                                 hmotnost_g, vyskyt_kontinent, migrace, typ_potravy, 
                                 status_ohrozeni, snuska_ks) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nazev, vedecky_nazev, rad or None, celed or None, 
                  parsed_delka, parsed_rozpeti, parsed_hmotnost,
                  vyskyt_kontinent or None, parsed_migrace,
                  typ_potravy or None, status_ohrozeni or None, parsed_snuska))
            
            new_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash("Pták úspěšně přidán! 🐦", "success")
            if action == 'save_and_add':
                return redirect(url_for('pridat_ptaka'))
            return redirect(url_for('detail_ptaka', ptak_id=new_id))
            
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
    
    return render_template('pridat_ptaka.html',
                           filter_options=filter_options,
                           action_url=url_for('pridat_ptaka'),
                           page_title='Přidat ptáka',
                           page_header='➕ Přidat ptáka',
                           button_text='Uložit ptáka',
                           edit_mode=False,
                           ptak=None)

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