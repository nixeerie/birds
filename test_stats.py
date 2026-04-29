from app import get_db, get_statistics, build_query

conn = get_db()
where_clause, values = build_query({})
stats = get_statistics(conn, where_clause, values)

print("Statistiky:")
for key, value in stats.items():
    print(f"  {key}: {value}")

conn.close()
