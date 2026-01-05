import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database Config (Matches your Docker command)
DB_CONFIG = {
    "dbname": "postgres", # Connect to default 'postgres' db first to create the specific one if needed
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

TARGET_DB = "financial_rag_db"

def init_database():
    # 1. Connect to default DB to create the target DB
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if DB exists
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{TARGET_DB}'")
    exists = cursor.fetchone()
    
    if not exists:
        print(f"📦 Creating database: {TARGET_DB}")
        cursor.execute(f"CREATE DATABASE {TARGET_DB}")
    else:
        print(f"📦 Database {TARGET_DB} already exists.")
    
    cursor.close()
    conn.close()

    # 2. Connect to the Target DB to create Tables
    conn = psycopg2.connect(
        dbname=TARGET_DB, 
        user=DB_CONFIG["user"], 
        password=DB_CONFIG["password"], 
        host=DB_CONFIG["host"], 
        port=DB_CONFIG["port"]
    )
    cursor = conn.cursor()
    
    print("🛠️  Creating Schema...")

    # Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # --- 1. DOCUMENTS (Metadata) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        doc_id VARCHAR(255) PRIMARY KEY,
        processed_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # --- 2. DOCUMENT STORE (The "Parent" Content) ---
    # Stores the raw text, image paths, or JSON
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_store (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        doc_id VARCHAR(255) REFERENCES documents(doc_id) ON DELETE CASCADE,
        parent_chunk_id UUID UNIQUE,  -- The key we use to link to vectors
        content_type VARCHAR(50),     -- 'text', 'table', 'image'
        full_content TEXT,            -- Raw text or Image Path
        metadata JSONB DEFAULT '{}'
    );
    """)

    # --- 3. FINANCIAL TABLES (Structured Parent Data) ---
    # Dedicated table for JSON table data to allow for better querying later
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_tables (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        doc_id VARCHAR(255) REFERENCES documents(doc_id) ON DELETE CASCADE,
        parent_chunk_id UUID UNIQUE,
        table_data JSONB,             -- The structured JSON
        table_markdown TEXT,          -- The markdown version
        summary TEXT,
        metadata JSONB DEFAULT '{}'
    );
    """)

    # --- 4. DOCUMENT CHUNKS (The "Child" Vectors) ---
    # This is what we actually search against
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        doc_id VARCHAR(255) REFERENCES documents(doc_id) ON DELETE CASCADE,
        parent_chunk_id UUID,         -- Link to Parent (Store or Table)
        content TEXT,                 -- The Summary Text
        embedding VECTOR(1024),       -- Titan v2 uses 1024 dimensions
        modality VARCHAR(50),         -- 'text', 'table', 'image'
        metadata JSONB DEFAULT '{}'
    );
    """)
    
    # Create Index for faster search (IVFFlat)
    # We use vector_cosine_ops for cosine similarity
    try:
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
        ON document_chunks 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
        """)
    except Exception as e:
        print("   (Index creation skipped - usually needs data first, skipping for now)")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database Schema Initialized Successfully!")

if __name__ == "__main__":
    init_database()