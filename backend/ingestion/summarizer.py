import os
import json
import asyncio
import base64
import re
import random
from pathlib import Path
from typing import List, Dict
from langchain_aws import ChatBedrock
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from tqdm.asyncio import tqdm_asyncio  # For progress bars

load_dotenv()

class MultiModalSummarizer:
    def __init__(self, processed_dir: str = "backend/data/processed"):
        self.processed_dir = Path(processed_dir)
        
        # --- RATE LIMIT CONTROL ---
        # Limit to 5 concurrent requests (Safe for Free Tier)
        self.semaphore = asyncio.Semaphore(5) 
        
        # self.text_llm = ChatGoogleGenerativeAI(
        #     model="gemini-2.0-flash-exp",
        #     temperature=0.3,
        #     max_retries=1 # We handle retries manually for better control
        # )
        self.text_llm = ChatBedrock(
            model_id="amazon.nova-lite-v1:0",  # Or "anthropic.claude-3-haiku-20240307-v1:0"
            model_kwargs={"temperature": 0.3},
            region_name="us-east-1" # Or your specific region
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". "]
        )

    async def _safe_api_call(self, coroutine_func, *args):
        """
        Wrapper to handle Rate Limits (429) with exponential backoff.
        """
        max_retries = 5
        base_delay = 2
        
        async with self.semaphore:  # Only allow 5 active calls at once
            for attempt in range(max_retries):
                try:
                    # Add a tiny jitter so they don't all hit exactly at once
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    return await coroutine_func(*args)
                
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        # Extract wait time if available, otherwise exponential backoff
                        wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"\n⚠️ Rate Limit Hit. Waiting {wait_time:.1f}s before retry {attempt+1}/{max_retries}...")
                        await asyncio.sleep(wait_time)
                    else:
                        # Genuine error (not rate limit), raise it
                        print(f"\n❌ API Error: {e}")
                        return None
            return None

    async def process_document(self, doc_id: str):
        doc_path = self.processed_dir / doc_id
        print(f"\n🚀 Starting Summarization for: {doc_id}")

        # 1. Text Processing
        await self._process_text_section(doc_path, doc_id)
        
        # 2. Table Processing
        await self._process_tables_section(doc_path, doc_id)
        
        # 3. Image Processing
        await self._process_images_section(doc_path, doc_id)

        print(f"✅ Finished summarizing {doc_id}")

    # ---------------------------------------------------------
    # 1. Text Processing
    # ---------------------------------------------------------
    async def _process_text_section(self, doc_path: Path, doc_id: str):
        text_file = doc_path / "text" / f"{doc_id}.md"
        if not text_file.exists():
            return

        print("   📄 Chunking Text...")
        with open(text_file, "r", encoding="utf-8") as f:
            full_text = f.read()

        chunks = self.splitter.create_documents([full_text])
        print(f"   generating summaries for {len(chunks)} chunks (this will take time)...")
        
        tasks = []
        for i, chunk in enumerate(chunks):
            tasks.append(self._summarize_text_chunk(chunk.page_content, i))
        
        # Use tqdm for a progress bar
        summaries = await tqdm_asyncio.gather(*tasks, desc="Summarizing Text")
        
        # Filter out failed calls (None)
        summaries = [s for s in summaries if s]
        
        output_file = doc_path / "text_summaries.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)

    async def _summarize_text_chunk(self, content: str, index: int) -> Dict:
        prompt = f"""You are a financial analyst. Summarize this excerpt from a 10-K document.
        Rules: Concise (2-3 sentences max). Capture key metrics/dates.
        Excerpt: {content}
        Summary:"""
        
        response = await self._safe_api_call(self.text_llm.ainvoke, prompt)
        
        if response:
            return {
                "chunk_index": index,
                "parent_content": content,
                "summary": response.content,
                "type": "text"
            }
        return None

    # ---------------------------------------------------------
    # 2. Table Processing
    # ---------------------------------------------------------
    async def _process_tables_section(self, doc_path: Path, doc_id: str):
        tables_dir = doc_path / "tables"
        json_files = list(tables_dir.glob("*.json"))
        
        if not json_files:
            return

        print(f"   📊 Summarizing {len(json_files)} Tables...")
        tasks = [self._summarize_single_table(f) for f in json_files]
        summaries = await tqdm_asyncio.gather(*tasks, desc="Summarizing Tables")
        summaries = [s for s in summaries if s]
        
        output_file = doc_path / "table_summaries.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)

    async def _summarize_single_table(self, json_path: Path) -> Dict:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        prompt = f"""Analyze this financial table.
        Context: {data.get('title')} | {data.get('caption')}
        Markdown Data: {data.get('markdown')}
        Instructions: Identify significant trends, comparisons, or outliers. Max 4 sentences."""
        
        response = await self._safe_api_call(self.text_llm.ainvoke, prompt)
        
        if response:
            return {
                "table_id": data.get("id"),
                "original_data": data,
                "summary": response.content,
                "type": "table"
            }
        return None

    # ---------------------------------------------------------
    # 3. Image Processing
    # ---------------------------------------------------------
    async def _process_images_section(self, doc_path: Path, doc_id: str):
        images_dir = doc_path / "images"
        image_files = list(images_dir.glob("*.png"))
        
        if not image_files:
            return

        print(f"   🖼️  Summarizing {len(image_files)} Images...")
        tasks = [self._describe_image(img) for img in image_files]
        descriptions = await tqdm_asyncio.gather(*tasks, desc="Summarizing Images")
        descriptions = [d for d in descriptions if d]
        
        output_file = doc_path / "image_summaries.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, indent=2)

    async def _describe_image(self, image_path: Path) -> Dict:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe this financial chart/image in detail. What trends, axes, or key data points are shown?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
            ]
        )

        response = await self._safe_api_call(self.text_llm.ainvoke, [message])
        
        if response:
            return {
                "image_filename": image_path.name,
                "image_path": str(image_path),
                "summary": response.content,
                "type": "image"
            }
        return None

if __name__ == "__main__":
    summarizer = MultiModalSummarizer()
    processed_root = Path("backend/data/processed")
    doc_folders = [d.name for d in processed_root.iterdir() if d.is_dir()]
    
    async def main():
        for doc in doc_folders:
            await summarizer.process_document(doc)
            
    asyncio.run(main())