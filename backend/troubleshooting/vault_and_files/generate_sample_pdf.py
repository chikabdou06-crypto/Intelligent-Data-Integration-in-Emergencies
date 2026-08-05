"""One-off script to create documents/RAG_first_paper.pdf for demo verification."""
from pathlib import Path

PDF_BYTES = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>stream
BT /F1 12 Tf 72 720 Td (RAG: Retrieval-Augmented Generation) Tj ET
BT /F1 10 Tf 72 690 Td (Retriever fetches chunks; generator answers from context.) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
trailer<</Size 6/Root 1 0 R>>
startxref
400
%%EOF"""

out = Path(__file__).resolve().parent.parent / "documents" / "RAG_first_paper.pdf"
out.write_bytes(PDF_BYTES)
print(f"Created {out}")
