from app import get_db, get_filter_options

conn = get_db()
opts = get_filter_options(conn)
print(f"Počet řádů: {len(opts['rady'])}")
print(f"Počet typů potravy: {len(opts['potravys'])}")
print(f"Počet kontinentů: {len(opts['kontinenty'])}")
print(f"Počet statusů: {len(opts['statusy'])}")
print(f"Celkem filtrů: {sum(len(v) for v in opts.values())}")
conn.close()
