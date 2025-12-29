import os
import glob
import boto3
import pdfplumber
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings

# --- CONFIG ---
DOCS_FOLDER = "Docs"
INDEX_FOLDER = "faiss_index_hybrid"

def table_to_markdown(table):
    """
    Converts a list-of-lists (from pdfplumber) into a Markdown table string.
    """
    if not table or len(table) < 2: return None

    # Clean None values to empty strings
    cleaned_table = [[str(cell) if cell is not None else "" for cell in row] for row in table]
    
    # Identify headers (Assume first row is header)
    headers = cleaned_table[0]
    
    # Generate Markdown
    # | Header 1 | Header 2 |
    md = "| " + " | ".join(headers) + " |\n"
    # | --- | --- |
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    # | Row 1 | Data |
    for row in cleaned_table[1:]:
        md += "| " + " | ".join(row) + " |\n"
        
    return md

def process_pdf(pdf_path):
    print(f"📄 Scanning {os.path.basename(pdf_path)}...")
    
    table_docs = []
    text_docs = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            
            # --- STRATEGY PART 1: EXTRACT TABLES ---
            # find_tables looks for grid lines to identify table boundaries
            tables = page.find_tables()
            
            for table in tables:
                # Extract the data from the identified table
                table_data = table.extract()
                
                # Convert to Markdown (LLM friendly format)
                md_table = table_to_markdown(table_data)
                
                if md_table:
                    # Create a specific 'Table Chunk'
                    doc = Document(
                        page_content=f"FINANCIAL TABLE (Page {page_num+1}):\n{md_table}",
                        metadata={
                            "source": os.path.basename(pdf_path),
                            "page": page_num + 1,
                            "type": "table" # Tag it so we know it's a table
                        }
                    )
                    table_docs.append(doc)
            
            # --- STRATEGY PART 2: EXTRACT TEXT ---
            # We extract the full page text. 
            # Note: This might include the messy text version of the table, 
            # but that's actually okay—it adds keyword redundancy for search.
            text = page.extract_text()
            if text:
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": page_num + 1,
                        "type": "text"
                    }
                )
                text_docs.append(doc)

    return table_docs, text_docs

def main():
    # 1. Setup Bedrock
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
    embeddings = BedrockEmbeddings(
        client=bedrock,
        model_id="amazon.titan-embed-text-v2:0" 
    )

    # 2. Find PDFs
    pdf_files = glob.glob(os.path.join(DOCS_FOLDER, "*.pdf"))
    if not pdf_files:
        print(f"❌ No PDFs found in {DOCS_FOLDER}")
        return

    all_table_chunks = []
    all_text_chunks = []

    # 3. Process each file
    for pdf_file in pdf_files:
        tables, texts = process_pdf(pdf_file)
        all_table_chunks.extend(tables)
        all_text_chunks.extend(texts)
        print(f"   -> Found {len(tables)} tables and {len(texts)} text pages.")

    # 4. Apply Hybrid Splitting Strategy
    print("✂️ Applying Hybrid Chunking...")

    # A. Tables: DO NOT SPLIT. Keep them whole.
    # We add them directly to the final list.
    final_chunks = all_table_chunks[:]

    # B. Text: Split normally.
    # 1000 chars is good for narrative (Management Discussion, Risks, etc.)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_text_chunks = text_splitter.split_documents(all_text_chunks)
    
    final_chunks.extend(split_text_chunks)

    print(f"   -> Final Index contains {len(final_chunks)} total chunks ({len(all_table_chunks)} are pure tables).")

    # 5. Indexing
    print("🧠 Generating embeddings (Titan V2)...")
    if final_chunks:
        vectorstore = FAISS.from_documents(final_chunks, embeddings)
        vectorstore.save_local(INDEX_FOLDER)
        print(f"✅ Success! Hybrid index saved to '{INDEX_FOLDER}/'")
    else:
        print("❌ No data found to index.")

if __name__ == "__main__":
    main()