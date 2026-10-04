import fitz  # PyMuPDF
import io
from typing import Union

def extract_pdf_text(pdf_input: Union[str, bytes]) -> str:
    """
    Extracts clean text from a PDF file path or bytes buffer using PyMuPDF (fitz).
    Falls back gracefully if pypdf is needed.
    """
    extracted_text = []
    
    try:
        if isinstance(pdf_input, bytes):
            doc = fitz.open(stream=pdf_input, filetype="pdf")
        else:
            doc = fitz.open(pdf_input)
            
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                extracted_text.append(f"--- Page {page_num + 1} ---\n{text.strip()}")
        doc.close()
    except Exception as e:
        # Fallback using pypdf if fitz fails
        try:
            import pypdf
            if isinstance(pdf_input, bytes):
                reader = pypdf.PdfReader(io.BytesIO(pdf_input))
            else:
                reader = pypdf.PdfReader(pdf_input)
            for page_num, page in enumerate(reader.pages):
                t = page.extract_text()
                if t:
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{t.strip()}")
        except Exception as e_inner:
            raise RuntimeError(f"Failed to extract PDF text: {str(e)} | Fallback error: {str(e_inner)}")

    return "\n\n".join(extracted_text)
