# import fitz

# pdf_path = "example.pdf"
# doc = fitz.open(pdf_path)

# all_chunks = []

# for page_num, page in enumerate(doc, start=1):
#     # Extract blocks of text with coordinates
#     blocks = page.get_text("dict")["blocks"]
    
#     for b in blocks:
#         if "lines" not in b:
#             continue
#         block_text = ""
#         for line in b["lines"]:
#             for span in line["spans"]:
#                 block_text += span["text"] + " "
        
#         block_text = block_text.strip()
#         if not block_text:
#             continue

#         # Save with metadata
#         chunk = {
#             "page": page_num,
#             "bbox": b["bbox"],  # (x0, y0, x1, y1)
#             "text": block_text,
#         }
#         all_chunks.append(chunk)

# doc.close()

# print(f"Extracted {len(all_chunks)} chunks.")

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any


class PDFChunker:
    def __init__(self, path: str, proximity_threshold: int = 20):
        self.path = path
        self.proximity_threshold = proximity_threshold

    def _extract_blocks(self) -> List[Dict[str, Any]]:
        """Extract text blocks with layout info and preserve bullets."""
        doc = fitz.open(self.path)
        blocks = []

        for page_num, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")

            for block in page_dict["blocks"]:
                if "lines" not in block:
                    continue

                lines_text = []
                font_sizes = []
                is_bold = False

                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        txt = span["text"]

                        # --- Preserve bullets and leading symbols ---
                        # Some PDFs render bullets as individual spans (•, ●, ▪, etc.)
                        if txt.strip() in {"•", "●", "▪", "-", "–"}:
                            line_text += txt.strip() + " "
                            continue

                        line_text += txt
                        font_sizes.append(span["size"])
                        if "Bold" in span["font"]:
                            is_bold = True

                    # Keep line separation to better preserve structure
                    if line_text.strip():
                        lines_text.append(line_text.strip())

                text = "\n".join(lines_text).strip()
                if not text:
                    continue

                avg_font = sum(font_sizes) / len(font_sizes) if font_sizes else 10
                blocks.append({
                    "page": page_num,
                    "bbox": block["bbox"],
                    "text": text,
                    "avg_font": avg_font,
                    "is_bold": is_bold,
                })

        doc.close()
        blocks.sort(key=lambda b: (b["page"], b["bbox"][1]))
        return blocks

    def _detect_headers(self, blocks: List[Dict]) -> float:
        sizes = [b["avg_font"] for b in blocks if b["avg_font"] < 40]
        if not sizes:
            return 12.0
        avg, max_size = sum(sizes) / len(sizes), max(sizes)
        return max(avg * 1.25, max_size - 2)

    def _merge_nearby_blocks(self, blocks: List[Dict], header_threshold: float) -> List[Dict]:
        if not blocks:
            return []

        merged = [blocks[0]]
        for nxt in blocks[1:]:
            prev = merged[-1]

            # Don't merge across headers, bolds, or new sections
            if (
                nxt["page"] != prev["page"]
                or nxt["avg_font"] >= header_threshold
                or prev["avg_font"] >= header_threshold
                or nxt["is_bold"]
                or prev["is_bold"]
            ):
                merged.append(nxt)
                continue

            vertical_gap = nxt["bbox"][1] - prev["bbox"][3]
            if vertical_gap < self.proximity_threshold:
                prev["text"] += "\n" + nxt["text"]  # keep newline to retain bullets
                prev["bbox"] = (
                    prev["bbox"][0],
                    prev["bbox"][1],
                    max(prev["bbox"][2], nxt["bbox"][2]),
                    nxt["bbox"][3],
                )
            else:
                merged.append(nxt)
        return merged

    def extract_chunks(self) -> List[Dict]:
        blocks = self._extract_blocks()
        header_threshold = self._detect_headers(blocks)
        merged_blocks = self._merge_nearby_blocks(blocks, header_threshold)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "!", "?", ";", " "],
        )

        chunks = []
        for b in merged_blocks:
            splits = text_splitter.split_text(b["text"])
            for s in splits:
                chunks.append({
                    "page": b["page"],
                    "text": s.strip(),
                    "bbox": b["bbox"],
                    "avg_font": b["avg_font"],
                    "is_bold": b["is_bold"],
                    "type": "header" if b["avg_font"] >= header_threshold or b["is_bold"] else "body",
                })
        return chunks


# Example usage
if __name__ == "__main__":
    pdf_path = "example.pdf"
    chunker = PDFChunker(pdf_path)
    chunks = chunker.extract_chunks()

    print(f"✅ Extracted {len(chunks)} intelligent chunks (bullets preserved)\n")
    for i, c in enumerate(chunks, 1):
        tag = "HEADER" if c["type"] == "header" else "BODY"
        print(f"[{tag}] Page {c['page']}\n{c['text'][:300]}\n")
