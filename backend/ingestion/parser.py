import pymupdf4llm
import fitz  # PyMuPDF
import pathlib
import json
import shutil
import re
from typing import List, Dict, Any, Tuple, Optional

class PDFParser:
    """
    Parses PDFs and organizes Text, Tables, and Images into 
    separate, structured directories per document.
    """
    
    def __init__(self, base_dir: str = "backend/data"):
        self.base_dir = pathlib.Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.processed_dir = self.base_dir / "processed"
        
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def process_all(self):
        pdf_files = list(self.uploads_dir.glob("*.pdf"))
        print(f"📂 Found {len(pdf_files)} PDF(s) in {self.uploads_dir}")
        
        results = []
        for pdf_file in pdf_files:
            try:
                data = self.process_single_pdf(pdf_file)
                results.append(data)
                print(f"✅ Successfully processed: {pdf_file.name}")
            except Exception as e:
                print(f"❌ Failed to process {pdf_file.name}: {str(e)}")
        return results

    def process_single_pdf(self, file_path: pathlib.Path) -> Dict[str, Any]:
        doc_name = file_path.stem 
        doc_output_dir = self.processed_dir / doc_name
        text_dir = doc_output_dir / "text"
        tables_dir = doc_output_dir / "tables"
        images_dir = doc_output_dir / "images"
        
        if doc_output_dir.exists():
            shutil.rmtree(doc_output_dir)
            
        text_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔄 Processing {doc_name}...")

        # 1. Extract Text & Images
        md_text = pymupdf4llm.to_markdown(
            str(file_path),
            write_images=True,
            image_path=str(images_dir),
            image_format="png"
        )
        
        # 2. Extract Tables with Context
        tables = self._extract_tables_with_context(file_path)
        
        # 3. Save Assets
        self._save_text(text_dir, doc_name, md_text)
        self._save_tables(tables_dir, tables)
        
        return {
            "doc_id": doc_name,
            "text_path": str(text_dir / f"{doc_name}.md"),
            "tables_path": str(tables_dir),
            "images_path": str(images_dir)
        }

    def _extract_tables_with_context(self, file_path: pathlib.Path) -> List[Dict]:
        """
        Enhanced table extraction with comprehensive title and caption detection.
        """
        doc = fitz.open(file_path)
        extracted_tables = []
        
        for page_index, page in enumerate(doc):
            tabs = page.find_tables()
            if tabs.tables:
                # Get all text blocks on the page with positioning info
                text_blocks = page.get_text("dict")["blocks"]
                
                for i, table in enumerate(tabs):
                    table_bbox = table.bbox
                    
                    # Multi-strategy title detection
                    title = self._find_table_title_multi_strategy(
                        page, table_bbox, text_blocks
                    )
                    
                    # Extract caption (text below table)
                    caption = self._find_table_caption(page, table_bbox, text_blocks)
                    
                    # Get surrounding context for better understanding
                    context = self._get_table_context(page, table_bbox, text_blocks)
                    
                    extracted_tables.append({
                        "id": f"page{page_index+1}_table{i+1}",
                        "page": page_index + 1,
                        "title": title,
                        "caption": caption,
                        "context": context,
                        "data": table.extract(),
                        "markdown": table.to_markdown(),
                        "bbox": list(table_bbox)
                    })
        
        return extracted_tables

    def _find_table_title_multi_strategy(
        self, 
        page, 
        table_bbox: tuple, 
        text_blocks: List[Dict]
    ) -> str:
        """
        Uses multiple strategies to find the most appropriate table title.
        """
        x0, y0, x1, y1 = table_bbox
        
        # Strategy 1: Look for bold/larger text above table
        title_candidates = []
        
        for block in text_blocks:
            if block.get("type") != 0:  # Skip non-text blocks
                continue
                
            block_bbox = block["bbox"]
            bx0, by0, bx1, by1 = block_bbox
            
            # Check if block is above the table and horizontally aligned
            if by1 <= y0 and by0 >= (y0 - 200):  # Within 200 pixels above
                # Check for horizontal overlap
                if not (bx1 < x0 or bx0 > x1):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if not text:
                                continue
                            
                            # Calculate quality score based on multiple factors
                            score = self._score_title_candidate(
                                text, 
                                span, 
                                by1, 
                                y0
                            )
                            
                            if score > 0:
                                title_candidates.append({
                                    "text": text,
                                    "score": score,
                                    "distance": y0 - by1,
                                    "font_size": span.get("size", 0)
                                })
        
        # Sort by score (descending) and distance (ascending)
        title_candidates.sort(key=lambda x: (-x["score"], x["distance"]))
        
        if title_candidates:
            best_title = title_candidates[0]["text"]
            return self._clean_title(best_title)
        
        # Strategy 2: Simple text extraction fallback
        return self._fallback_title_extraction(page, table_bbox)

    def _score_title_candidate(
        self, 
        text: str, 
        span: Dict, 
        text_bottom: float, 
        table_top: float
    ) -> float:
        """
        Scores a potential title based on multiple heuristics.
        Higher score = more likely to be the actual title.
        """
        score = 0.0
        text_lower = text.lower()
        
        # Positive signals
        if span.get("flags", 0) & 2**4:  # Bold text
            score += 3.0
        
        font_size = span.get("size", 0)
        if font_size >= 11:  # Larger than typical body text
            score += 2.0
        
        # Length check - titles are usually between 3-100 characters
        if 10 <= len(text) <= 100:
            score += 2.0
        elif len(text) < 10:
            score += 0.5
        
        # Keywords that suggest this is a title
        title_keywords = [
            "revenue", "income", "balance", "cash flow", "segment",
            "assets", "liabilities", "equity", "expenses", "summary",
            "statement", "schedule", "breakdown", "analysis"
        ]
        if any(keyword in text_lower for keyword in title_keywords):
            score += 2.5
        
        # Capitalization patterns (Title Case or ALL CAPS)
        if text.istitle() or text.isupper():
            score += 1.5
        
        # Negative signals - things that are NOT titles
        
        # Dates
        if re.search(r'\b(20\d{2}|19\d{2})\b', text):
            score -= 2.0
        
        # "Year Ended", "Months Ended", etc.
        if re.search(r'\b(year|month|quarter|period)\s+ended\b', text_lower):
            score -= 3.0
        
        # Currency markers
        if re.search(r'[\$€£¥]|million|billion|thousand', text_lower):
            score -= 2.0
        
        # Mostly numbers and symbols
        if re.match(r'^[\d\s\%\$\(\)\-\,\.]+$', text):
            score -= 5.0
        
        # Too close or too far from table
        distance = table_top - text_bottom
        if distance < 5:  # Too close, might be part of table
            score -= 2.0
        elif distance > 150:  # Too far, probably unrelated
            score -= 1.0
        
        # Short phrases that are likely not titles
        if len(text) < 5 or text.lower() in ['table', 'continued', 'note']:
            score -= 3.0
        
        return score

    def _fallback_title_extraction(self, page, table_bbox: tuple) -> str:
        """
        Fallback method using simple text extraction above table.
        """
        x0, y0, x1, y1 = table_bbox
        search_rect = fitz.Rect(x0, y0 - 150, x1, y0)
        text_above = page.get_text("text", clip=search_rect)
        
        lines = [line.strip() for line in text_above.split('\n') if line.strip()]
        
        if not lines:
            return "Table (No Title Found)"
        
        # Try to find the best line working backwards
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            
            # Skip obvious non-titles
            if any([
                "ended" in line.lower() and len(line) < 50,
                re.search(r'^\d{4}$', line),  # Just a year
                "$" in line or "million" in line.lower(),
                re.match(r'^[\d\s\%\$\(\)\-\,\.]+$', line),
                len(line) < 3
            ]):
                continue
            
            return self._clean_title(line)
        
        return self._clean_title(lines[-1]) if lines else "Table (No Title Found)"

    def _find_table_caption(
        self, 
        page, 
        table_bbox: tuple, 
        text_blocks: List[Dict]
    ) -> Optional[str]:
        """
        Finds caption or note text below the table.
        """
        x0, y0, x1, y1 = table_bbox
        
        caption_lines = []
        
        for block in text_blocks:
            if block.get("type") != 0:
                continue
            
            block_bbox = block["bbox"]
            bx0, by0, bx1, by1 = block_bbox
            
            # Check if block is below table and within 100 pixels
            if by0 >= y1 and by0 <= (y1 + 100):
                if not (bx1 < x0 or bx0 > x1):
                    for line in block.get("lines", []):
                        line_text = " ".join(
                            span.get("text", "") for span in line.get("spans", [])
                        ).strip()
                        
                        if line_text and len(line_text) > 5:
                            caption_lines.append(line_text)
        
        if caption_lines:
            return " ".join(caption_lines)
        
        return None

    def _get_table_context(
        self, 
        page, 
        table_bbox: tuple, 
        text_blocks: List[Dict]
    ) -> Dict[str, str]:
        """
        Extracts surrounding context for better table understanding.
        """
        x0, y0, x1, y1 = table_bbox
        
        context = {
            "preceding_paragraph": "",
            "section_header": ""
        }
        
        # Look for text in wider area above table
        for block in text_blocks:
            if block.get("type") != 0:
                continue
            
            block_bbox = block["bbox"]
            bx0, by0, bx1, by1 = block_bbox
            
            # Text 50-250 pixels above (likely preceding paragraph)
            if by1 <= (y0 - 50) and by0 >= (y0 - 250):
                text = " ".join(
                    span.get("text", "") 
                    for line in block.get("lines", [])
                    for span in line.get("spans", [])
                ).strip()
                
                if len(text) > 20:  # Substantial text
                    context["preceding_paragraph"] = text
                    break
        
        return context

    def _clean_title(self, title: str) -> str:
        """
        Cleans and normalizes the extracted title.
        """
        # Remove extra whitespace
        title = " ".join(title.split())
        
        # Remove common artifacts
        title = re.sub(r'\s*\(continued\)\s*', '', title, flags=re.IGNORECASE)
        
        # Capitalize properly if all caps
        if title.isupper() and len(title) > 10:
            title = title.title()
        
        return title

    def _save_text(self, folder: pathlib.Path, filename: str, content: str):
        with open(folder / f"{filename}.md", "w", encoding="utf-8") as f:
            f.write(content)

    def _save_tables(self, folder: pathlib.Path, tables: List[Dict]):
        """
        Saves tables with enriched metadata including title and context.
        """
        for tbl in tables:
            # Create a human-readable version with context
            enriched_content = {
                "id": tbl["id"],
                "page": tbl["page"],
                "title": tbl["title"],
                "caption": tbl["caption"],
                "context": tbl["context"],
                "markdown": tbl["markdown"],
                "data": tbl["data"],
                "bbox": tbl["bbox"]
            }
            
            file_name = f"{tbl['id']}.json"
            with open(folder / file_name, "w", encoding="utf-8") as f:
                json.dump(enriched_content, f, indent=2, ensure_ascii=False)
            
            # Also save a markdown version for easy reading
            md_file_name = f"{tbl['id']}.md"
            with open(folder / md_file_name, "w", encoding="utf-8") as f:
                f.write(f"# {tbl['title']}\n\n")
                if tbl['caption']:
                    f.write(f"*{tbl['caption']}*\n\n")
                f.write(tbl['markdown'])
                if tbl['context']['preceding_paragraph']:
                    f.write(f"\n\n---\n**Context:** {tbl['context']['preceding_paragraph']}")

if __name__ == "__main__":
    parser = PDFParser()
    parser.process_all()