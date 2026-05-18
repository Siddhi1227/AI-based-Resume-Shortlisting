import pdfplumber
from docx import Document
from io import BytesIO
import warnings

warnings.filterwarnings('ignore')


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using pdfplumber.
    
    Args:
        file_bytes: PDF file content as bytes
        
    Returns:
        Extracted text as string, empty string on error
    """
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = '\n'.join(text_parts)
            # Clean up excessive whitespace
            full_text = '\n'.join(
                line.strip() for line in full_text.split('\n') if line.strip()
            )
            return full_text
    except Exception as e:
        print(f"Warning: Failed to extract text from PDF: {str(e)}")
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX bytes using python-docx.
    
    Args:
        file_bytes: DOCX file content as bytes
        
    Returns:
        Extracted text as string, empty string on error
    """
    try:
        doc = Document(BytesIO(file_bytes))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        full_text = '\n'.join(text_parts)
        return full_text
    except Exception as e:
        print(f"Warning: Failed to extract text from DOCX: {str(e)}")
        return ""


def parse_resume(uploaded_file) -> str:
    """
    Parse an uploaded resume file (PDF or DOCX).
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        Extracted resume text as string
    """
    try:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.pdf'):
            return extract_text_from_pdf(file_bytes)
        elif file_name.endswith('.docx'):
            return extract_text_from_docx(file_bytes)
        else:
            print(f"Warning: Unsupported file format: {uploaded_file.name}")
            return ""
    except Exception as e:
        print(f"Warning: Failed to parse resume {uploaded_file.name}: {str(e)}")
        return ""
