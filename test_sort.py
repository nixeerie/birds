from app import get_sort_order, ALLOWED_SORT_COLUMNS

# Test 1: Platný sloupec a směr
result1 = get_sort_order({'razeni': 'hmotnost_g', 'smer': 'DESC'})
print(f"Test 1 (hmotnost_g DESC): {result1}")

# Test 2: Neplatný sloupec (měl by se zařadit na 'nazev')
result2 = get_sort_order({'razeni': 'neexistujici', 'smer': 'ASC'})
print(f"Test 2 (invalid column): {result2}")

# Test 3: Neplatný směr
result3 = get_sort_order({'razeni': 'nazev', 'smer': 'INVALID'})
print(f"Test 3 (invalid direction): {result3}")

# Test 4: Výchozí hodnoty
result4 = get_sort_order({})
print(f"Test 4 (defaults): {result4}")

# Test 5: Všechny povolené sloupce
print(f"\nPovolené sloupce ({len(ALLOWED_SORT_COLUMNS)}):")
for col in sorted(ALLOWED_SORT_COLUMNS):
    print(f"  - {col}")
