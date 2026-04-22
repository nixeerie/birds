import csv
import sqlite3
import os

# Smazat starší databázi, pokud existuje
if os.path.exists('ptaci.db'):
    os.remove('ptaci.db')

# Vytvoření/připojení k SQLite databázi
conn = sqlite3.connect('ptaci.db')
cursor = conn.cursor()

# Vytvoření tabulky
cursor.execute('''
CREATE TABLE ptaci (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nazev TEXT,
    vedecky_nazev TEXT,
    rad TEXT,
    celed TEXT,
    delka_cm INTEGER,
    rozpeti_cm INTEGER,
    hmotnost_g INTEGER,
    status_ohrozeni TEXT,
    typ_potravy TEXT,
    migrace INTEGER,
    vyskyt_kontinent TEXT,
    snuska_ks REAL
)
''')

# Čtení CSV a vkládání záznamů
count = 0
try:
    with open('dataset_ptaci_final.csv', 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Konverze prázdných stringů na None pro numerická pole
            try:
                delka_cm = int(row['delka_cm']) if row['delka_cm'] else None
                rozpeti_cm = int(row['rozpeti_cm']) if row['rozpeti_cm'] else None
                hmotnost_g = int(row['hmotnost_g']) if row['hmotnost_g'] else None
                migrace = int(row['migrace']) if row['migrace'] else None
                snuska_ks = float(row['snuska_ks']) if row['snuska_ks'] else None
            except (ValueError, KeyError) as e:
                print(f"Chyba při konverzi řádku {count + 1}: {e}")
                continue
            
            cursor.execute('''
            INSERT INTO ptaci (nazev, vedecky_nazev, rad, celed, delka_cm, rozpeti_cm, 
                             hmotnost_g, status_ohrozeni, typ_potravy, migrace, 
                             vyskyt_kontinent, snuska_ks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('nazev', ''),
                row.get('vedecky_nazev', ''),
                row.get('rad', ''),
                row.get('celed', ''),
                delka_cm,
                rozpeti_cm,
                hmotnost_g,
                row.get('status_ohrozeni', ''),
                row.get('typ_potravy', ''),
                migrace,
                row.get('vyskyt_kontinent', ''),
                snuska_ks
            ))
            count += 1
        
        conn.commit()
        print(f"✓ Úspěšně importováno {count} záznamů do ptaci.db")
        
except FileNotFoundError:
    print("✗ Soubor 'dataset_ptaci_final.csv' nebyl nalezen!")
except Exception as e:
    print(f"✗ Chyba při importu: {e}")
    conn.rollback()
    
finally:
    conn.close()
