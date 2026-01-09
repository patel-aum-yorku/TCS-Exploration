import os
import json
import uuid
import psycopg2
import boto3
from pathlib import Path
from typing import List, Dict
from psycopg2.extras import Json
from langchain_aws import BedrockEmbeddings
from tqdm import tqdm

# Database Config
DB_PARAMS = {
    "dbname": "financial_rag_db",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

class DataLoader:
    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        
        # Initialize Bedrock Embeddings (Titan v2)
        # Using us-east-1 as it is the standard region for Bedrock features
        self.embedder = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name="us-east-1"
        )
        
        # Connect to DB
        self.conn = psycopg2.connect(**DB_PARAMS)
        self.cursor = self.conn.cursor()

    def load_all_documents(self):
        """Scans processed folder and loads any documents found."""
        doc_folders = [d for d in self.processed_dir.iterdir() if d.is_dir()]
        
        for doc_folder in doc_folders:
            doc_id = doc_folder.name
            print(f"\n📥 Loading Document: {doc_id}")
            
            # 1. Register Document
            self._register_document(doc_id)
            
            # 2. Load Text Chunks
            self._load_text_summaries(doc_folder, doc_id)
            
            # 3. Load Tables
            self._load_table_summaries(doc_folder, doc_id)
            
            # 4. Load Images
            self._load_image_summaries(doc_folder, doc_id)
            
            print(f"✅ {doc_id} loaded successfully.")

    def _register_document(self, doc_id):
        """Inserts into 'documents' table."""
        try:
            self.cursor.execute(
                "INSERT INTO documents (doc_id) VALUES (%s) ON CONFLICT (doc_id) DO NOTHING",
                (doc_id,)
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error registering doc: {e}")

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings using Bedrock"""
        try:
            return self.embedder.embed_documents(texts)
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    # ---------------------------------------------------------
    # 1. LOAD TEXT
    # ---------------------------------------------------------
    def _load_text_summaries(self, folder: Path, doc_id: str):
        file_path = folder / "text_summaries.json"
        if not file_path.exists(): return

        with open(file_path, 'r') as f:
            chunks = json.load(f)

        if not chunks: return

        print(f"   📄 Embedding {len(chunks)} Text Chunks...")
        
        # Prepare data for insertion
        summaries = [c['summary'] for c in chunks]
        embeddings = self._generate_embeddings(summaries)
        
        for chunk, vector in zip(chunks, embeddings):
            parent_id = str(uuid.uuid4()) # Create a unique link ID
            
            # A. Insert Parent (Full Content) -> document_store
            self.cursor.execute(
                """
                INSERT INTO document_store 
                (doc_id, parent_chunk_id, content_type, full_content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    doc_id, 
                    parent_id, 
                    'text', 
                    chunk['parent_content'], 
                    Json({'chunk_index': chunk['chunk_index']})
                )
            )
            
            # B. Insert Child (Vector) -> document_chunks
            self.cursor.execute(
                """
                INSERT INTO document_chunks 
                (doc_id, parent_chunk_id, content, embedding, modality, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    parent_id,
                    chunk['summary'],
                    vector, # pgvector adapter handles list -> vector
                    'text',
                    Json({'chunk_index': chunk['chunk_index']})
                )
            )
        self.conn.commit()

    # ---------------------------------------------------------
    # 2. LOAD TABLES
    # ---------------------------------------------------------
    def _load_table_summaries(self, folder: Path, doc_id: str):
        file_path = folder / "table_summaries.json"
        if not file_path.exists(): return

        with open(file_path, 'r') as f:
            tables = json.load(f)
            
        if not tables: return
        print(f"   📊 Embedding {len(tables)} Tables...")

        summaries = [t['summary'] for t in tables]
        embeddings = self._generate_embeddings(summaries)

        for table, vector in zip(tables, embeddings):
            parent_id = str(uuid.uuid4())
            original_data = table['original_data']

            # A. Insert Parent (Structured Data) -> financial_tables
            self.cursor.execute(
                """
                INSERT INTO financial_tables 
                (doc_id, parent_chunk_id, table_data, table_markdown, summary, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    parent_id,
                    Json(original_data.get('data', {})),
                    original_data.get('markdown', ''),
                    table['summary'],
                    Json({
                        'title': original_data.get('title'),
                        'page': original_data.get('page')
                    })
                )
            )

            # B. Insert Child (Vector) -> document_chunks
            self.cursor.execute(
                """
                INSERT INTO document_chunks 
                (doc_id, parent_chunk_id, content, embedding, modality, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    parent_id,
                    table['summary'], # We search against the summary
                    vector,
                    'table',
                    Json({'table_id': table['table_id']})
                )
            )
        self.conn.commit()

    # ---------------------------------------------------------
    # 3. LOAD IMAGES
    # ---------------------------------------------------------
    def _load_image_summaries(self, folder: Path, doc_id: str):
        file_path = folder / "image_summaries.json"
        if not file_path.exists(): return

        with open(file_path, 'r') as f:
            images = json.load(f)
            
        if not images: return
        print(f"   🖼️  Embedding {len(images)} Images...")

        summaries = [img['summary'] for img in images]
        embeddings = self._generate_embeddings(summaries)

        for img, vector in zip(images, embeddings):
            parent_id = str(uuid.uuid4())

            # A. Insert Parent (Image Path) -> document_store
            self.cursor.execute(
                """
                INSERT INTO document_store 
                (doc_id, parent_chunk_id, content_type, full_content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    parent_id,
                    'image',
                    img['image_path'], # Store path to the PNG
                    Json({'filename': img['image_filename']})
                )
            )

            # B. Insert Child (Vector) -> document_chunks
            self.cursor.execute(
                """
                INSERT INTO document_chunks 
                (doc_id, parent_chunk_id, content, embedding, modality, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    parent_id,
                    img['summary'], # We search against the description
                    vector,
                    'image',
                    Json({'filename': img['image_filename']})
                )
            )
        self.conn.commit()

if __name__ == "__main__":
    loader = DataLoader()
    loader.load_all_documents()