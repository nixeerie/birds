from app import (
    get_db, 
    get_druhy_podle_radu, 
    get_hmotnost_podle_potravy,
    get_migrace_rozdel,
    get_druhy_podle_kontinentu,
    build_query
)

conn = get_db()
where_clause, values = build_query({})

# Test všech 4 grafů
graf_rad_labels, graf_rad_data = get_druhy_podle_radu(conn, where_clause, values)
print(f"✓ Druhy podle řádu: {len(graf_rad_labels)} řádů")

graf_potrava_labels, graf_potrava_data = get_hmotnost_podle_potravy(conn, where_clause, values)
print(f"✓ Hmotnost podle potravy: {len(graf_potrava_labels)} typů")

graf_migrace_labels, graf_migrace_data = get_migrace_rozdel(conn, where_clause, values)
print(f"✓ Migrace rozdělení: {len(graf_migrace_labels)} kategorií")

graf_kontinent_labels, graf_kontinent_data = get_druhy_podle_kontinentu(conn, where_clause, values)
print(f"✓ Druhy podle kontinentu: {len(graf_kontinent_labels)} kontinentů")

conn.close()

print("\n✓ Všechny grafy jsou funkční!")
