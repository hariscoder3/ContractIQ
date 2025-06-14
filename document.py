from docx import Document
import re
from typing import List
import os

# Import PyPDF2 properly
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: PyPDF2 not installed. PDF support will be limited.")

def extract_clauses_from_file(file_path: str) -> List[str]:
    """Extract clauses from a document file (DOCX or PDF)."""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.docx':
        return extract_clauses_from_docx(file_path)
    elif file_extension == '.pdf':
        if PDF_SUPPORT:
            return extract_clauses_from_pdf(file_path)
        else:
            return ["PDF processing requires PyPDF2. Please install it with: pip install PyPDF2==3.0.1"]
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Only .docx and .pdf files are supported.")

def extract_clauses_from_docx(file_path: str) -> List[str]:
    """Extract clauses from a DOCX file."""
    doc = Document(file_path)
    text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
    return split_into_clauses(text)

def extract_clauses_from_pdf(file_path: str) -> List[str]:
    """Extract clauses from a PDF file."""
    if not PDF_SUPPORT:
        return ["PDF processing requires PyPDF2. Please install it with: pip install PyPDF2==3.0.1"]
    
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():  # Only add if text was extracted and not empty
                        text += page_text + "\n"
                except Exception as page_error:
                    print(f"Warning: Could not extract text from page {page_num + 1}: {page_error}")
                    continue
    except Exception as e:
        return [f"Error reading PDF file: {str(e)}. Please ensure the file is a valid PDF."]
    
    if not text.strip():
        return ["No readable text found in the PDF. The PDF might be image-based or corrupted."]
    
    return split_into_clauses(text)

def split_into_clauses(text: str) -> List[str]:
    """Split text into meaningful clauses."""
    if not text or text.strip() == "":
        return ["No readable text found in the document."]
    
    # Split by common clause markers
    clause_markers = [
        r'\d+\.\s+',  # Numbered clauses (1., 2., etc.)
        r'[A-Z][a-z]+\.\s+',  # Capitalized words followed by period
        r'WHEREAS',  # Legal document markers
        r'THEREFORE',
        r'IN WITNESS WHEREOF',
        r'IN CONSIDERATION OF',
    ]
    
    # Combine all markers into a single pattern
    pattern = '|'.join(f'({marker})' for marker in clause_markers)
    
    # Split the text
    clauses = re.split(pattern, text)
    
    # Clean up clauses
    cleaned_clauses = []
    for clause in clauses:
        if clause is not None:  # Check for None values
            clause = clause.strip()
            if len(clause) > 50:  # Only keep substantial clauses
                cleaned_clauses.append(clause)
    
    # If no substantial clauses found, return the original text in chunks
    if not cleaned_clauses:
        # Split by sentences or paragraphs as fallback
        sentences = re.split(r'[.!?]\s+', text)
        for sentence in sentences:
            if sentence and sentence.strip() and len(sentence.strip()) > 50:
                cleaned_clauses.append(sentence.strip())
    
    # If still no clauses, return the whole text in manageable chunks
    if not cleaned_clauses and text.strip():
        # Split into chunks of reasonable size
        words = text.split()
        chunk_size = 100  # words per chunk
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                cleaned_clauses.append(chunk.strip())
    
    return cleaned_clauses if cleaned_clauses else ["No readable content found in the document."] 