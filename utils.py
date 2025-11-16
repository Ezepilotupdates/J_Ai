# app/utils.py
from PyPDF2 import PdfReader
import io

def extract_text_from_pdf_bytes(b: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(b))
        return "\n\n".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""

def send_health_check():
    return {"status": "ok"}