# check_db.py
import psycopg2

conn = psycopg2.connect("dbname=financial_rag_db user=postgres password=root host=localhost")
cur = conn.cursor()

# Check counts
cur.execute("SELECT modality, COUNT(*) FROM document_chunks GROUP BY modality")
print("\n--- Vector Counts ---")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]}")

# Check one table entry
cur.execute("SELECT metadata->>'title' FROM financial_tables LIMIT 3")
print("\n--- Sample Table Title ---")
print([row[0] for row in cur.fetchall()])

conn.close()