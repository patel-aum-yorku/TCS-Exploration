import psycopg2
import json
import numpy as np
from typing import List, Dict, Any
from psycopg2.extras import DictCursor
from langchain_aws import BedrockEmbeddings
from sentence_transformers import CrossEncoder

# Database Config
DB_PARAMS = {
    "dbname": "financial_rag_db",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": "5432"
}

class MultiModalRetriever:
    def __init__(self):
        # 1. Initialize Bedrock
        self.embedder = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name="us-east-1"
        )
        
        # 2. Initialize Reranker
        print("⏳ Loading Reranker model...")
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Reranker ready.")
        
        # 3. Connect to DB
        self.conn = psycopg2.connect(**DB_PARAMS)

    def retrieve(self, query: str, top_k: int = 5, rerank_top_n: int = 20) -> List[Dict]:
        """
        Retrieves and reranks documents.
        
        Args:
            query: Search query
            top_k: Final number of results to return
            rerank_top_n: Number of candidates to fetch for reranking (should be > top_k)
        """
        print(f"\n🔍 Searching for: '{query}'")
        
        # A. Vector Search - Get more candidates for reranking
        query_vector = self.embedder.embed_query(query)
        candidates = self._vector_search(query_vector, limit=rerank_top_n)
        
        if not candidates:
            print("⚠️ No candidates found in vector search")
            return []
        
        print(f"📊 Retrieved {len(candidates)} candidates from vector search")
            
        # B. Fetch Parent Content (with titles and full context)
        enriched_candidates = self._fetch_parent_content(candidates)
        
        if not enriched_candidates:
            print("⚠️ No enriched content found")
            return []
        
        print(f"📦 Enriched {len(enriched_candidates)} candidates with parent content")
        
        # C. Rerank with proper scoring
        ranked_results = self._rerank_results(query, enriched_candidates)
        
        # D. Return top K after reranking
        final_results = ranked_results[:top_k]
        
        print(f"✅ Returning top {len(final_results)} results after reranking")
        return final_results

    def _vector_search(self, vector: List[float], limit: int) -> List[Dict]:
        """Vector similarity search using pgvector."""
        cursor = self.conn.cursor(cursor_factory=DictCursor)
        query = """
            SELECT 
                id, doc_id, parent_chunk_id, content as summary, modality, metadata,
                (embedding <=> %s::vector) as distance
            FROM document_chunks
            ORDER BY distance ASC
            LIMIT %s
        """
        cursor.execute(query, (vector, limit))
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return results

    def _fetch_parent_content(self, candidates: List[Dict]) -> List[Dict]:
        """
        Retrieves Parent content and merges metadata including titles.
        """
        cursor = self.conn.cursor(cursor_factory=DictCursor)
        enriched = []
        
        for cand in candidates:
            parent_id = cand['parent_chunk_id']
            modality = cand['modality']
            
            # Start with Child metadata
            final_metadata = dict(cand['metadata']) if cand['metadata'] else {}
            
            item = {
                "summary": cand['summary'],
                "modality": modality,
                "vector_score": 1 - cand['distance'],  # Cosine similarity
                "doc_id": cand['doc_id'],
                "parent_chunk_id": parent_id
            }
            
            if modality == 'table':
                # Fetch table data from parent
                cursor.execute(
                    "SELECT table_data, table_markdown, summary, metadata FROM financial_tables WHERE parent_chunk_id = %s",
                    (parent_id,)
                )
                row = cursor.fetchone()
                if row:
                    item['content'] = row['table_markdown']
                    item['table_data'] = row['table_data']
                    
                    # Merge parent metadata (contains title, caption, etc.)
                    if row['metadata']:
                        final_metadata.update(row['metadata'])
            
            elif modality == 'image':
                # Fetch image description from parent
                cursor.execute(
                    "SELECT full_content, metadata FROM document_store WHERE parent_chunk_id = %s",
                    (parent_id,)
                )
                row = cursor.fetchone()
                if row:
                    item['content'] = row['full_content']
                    
                    if row['metadata']:
                        final_metadata.update(row['metadata'])
            
            else:  # text
                # Fetch full text content from parent
                cursor.execute(
                    "SELECT full_content, metadata FROM document_store WHERE parent_chunk_id = %s",
                    (parent_id,)
                )
                row = cursor.fetchone()
                if row:
                    item['content'] = row['full_content']
                    
                    if row['metadata']:
                        final_metadata.update(row['metadata'])
            
            item['metadata'] = final_metadata
            enriched.append(item)
            
        cursor.close()
        return enriched

    def _rerank_results(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """
        Reranks results using CrossEncoder with proper score normalization.
        """
        if not candidates:
            return []
        
        print(f"\n🔄 Reranking {len(candidates)} candidates...")
        
        # Build query-document pairs for reranking
        pairs = []
        for c in candidates:
            rerank_text = self._build_rerank_context(c)
            pairs.append([query, rerank_text])
        
        # Get raw cross-encoder scores
        raw_scores = self.reranker.predict(pairs)
        
        # Normalize scores to 0-1 range using sigmoid
        # Cross-encoder scores are typically in range [-10, 10]
        normalized_scores = self._normalize_scores(raw_scores)
        
        # Attach scores to candidates
        for i, candidate in enumerate(candidates):
            candidate['raw_rerank_score'] = float(raw_scores[i])
            candidate['rerank_score'] = normalized_scores[i]
            
            # Optional: Combine vector similarity with rerank score
            # Using weighted average (70% rerank, 30% vector)
            candidate['final_score'] = (
                0.7 * candidate['rerank_score'] + 
                0.3 * candidate['vector_score']
            )
        
        # Sort by final score (descending)
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x['final_score'], 
            reverse=True
        )
        
        # Debug: Print score distribution
        self._print_score_distribution(sorted_candidates)
        
        return sorted_candidates

    def _build_rerank_context(self, candidate: Dict) -> str:
        """
        Builds rich context for reranking including title, summary, and content preview.
        """
        modality = candidate['modality']
        metadata = candidate['metadata']
        
        # Extract key metadata
        title = metadata.get('title', 'Untitled')
        doc_id = candidate.get('doc_id', 'Unknown')
        
        # Build context based on modality
        context_parts = [f"Document: {doc_id}"]
        
        if modality == 'table':
            context_parts.append(f"Table Title: {title}")
            
            # Add caption if available
            caption = metadata.get('caption')
            if caption:
                context_parts.append(f"Caption: {caption}")
            
            # Add summary
            context_parts.append(f"Summary: {candidate['summary']}")
            
            # Add first few rows of table for context
            content = candidate.get('content', '')
            if content:
                # Take first 300 characters of markdown table
                table_preview = content[:300]
                context_parts.append(f"Content Preview:\n{table_preview}")
        
        elif modality == 'image':
            context_parts.append(f"Image Description: {title}")
            context_parts.append(f"Summary: {candidate['summary']}")
            
            # Add full content for images (usually descriptions)
            content = candidate.get('content', '')
            if content:
                context_parts.append(f"Details: {content[:300]}")
        
        else:  # text
            context_parts.append(f"Section: {title}")
            context_parts.append(f"Summary: {candidate['summary']}")
            
            # Add content preview
            content = candidate.get('content', '')
            if content:
                context_parts.append(f"Content: {content[:400]}")
        
        return "\n".join(context_parts)

    def _normalize_scores(self, scores: np.ndarray) -> List[float]:
        """
        Normalizes cross-encoder scores to 0-1 range using sigmoid function.
        
        Cross-encoder scores are typically unbounded and can be negative.
        Sigmoid transforms them to probabilities.
        """
        def sigmoid(x):
            return 1 / (1 + np.exp(-x))
        
        # Apply sigmoid to transform to 0-1 range
        normalized = sigmoid(np.array(scores))
        
        return normalized.tolist()

    def _print_score_distribution(self, candidates: List[Dict]):
        """Prints score distribution for debugging."""
        if not candidates:
            return
        
        print("\n📊 Score Distribution (Top 5):")
        print("-" * 80)
        print(f"{'Rank':<6} {'Modality':<10} {'Vector':<10} {'Rerank':<10} {'Final':<10} {'Title':<30}")
        print("-" * 80)
        
        for i, c in enumerate(candidates[:5], 1):
            title = c['metadata'].get('title', 'N/A')
            title_short = title[:27] + "..." if len(title) > 30 else title
            
            print(f"{i:<6} {c['modality']:<10} "
                  f"{c['vector_score']:<10.4f} "
                  f"{c['rerank_score']:<10.4f} "
                  f"{c['final_score']:<10.4f} "
                  f"{title_short:<30}")
        
        print("-" * 80)
        print(f"Raw Rerank Score Range: [{min(c['raw_rerank_score'] for c in candidates):.2f}, "
              f"{max(c['raw_rerank_score'] for c in candidates):.2f}]")
        print(f"Normalized Range: [{min(c['rerank_score'] for c in candidates):.4f}, "
              f"{max(c['rerank_score'] for c in candidates):.4f}]")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("🔌 Database connection closed")


# Example usage with different query types
if __name__ == "__main__":
    retriever = MultiModalRetriever()
    
    # Example queries
    queries = [
        "What is the revenue breakdown by segments?",
        "Show me the operating income data",
        "What are the key financial metrics?"
    ]
    
    for query in queries:
        print("\n" + "="*80)
        results = retriever.retrieve(query, top_k=5, rerank_top_n=15)
        
        print(f"\n✅ Top {len(results)} Results for: '{query}'")
        print("="*80)
        
        for i, res in enumerate(results, 1):
            print(f"\n🏆 Rank {i} - {res['modality'].upper()}")
            print(f"{'─'*60}")
            print(f"📊 Scores:")
            print(f"   Vector Similarity: {res['vector_score']:.4f}")
            print(f"   Rerank Score:      {res['rerank_score']:.4f}")
            print(f"   Final Score:       {res['final_score']:.4f}")
            print(f"\n📌 Title: {res['metadata'].get('title', 'N/A')}")
            print(f"📝 Summary: {res['summary'][:150]}...")
            
            if res['modality'] == 'table':
                print(f"📋 Table Preview:")
                content = res.get('content', '')
                lines = content.split('\n')[:5]  # First 5 lines
                print('\n'.join(lines))
    
    retriever.close()