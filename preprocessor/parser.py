import fitz  # type: ignore # PyMuPDF
from pathlib import Path
from docx import Document # type: ignore
import streamlit as st

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(stream = pdf_bytes, filetype = "pdf")
    text = ""
    for page in doc:
        text += page.get_text() # type: ignore
    return text

def extract_text_from_docx(docx_bytes):
    from io import BytesIO
    document = Document(BytesIO(docx_bytes))
    text = "\n".join([para.text for para in document.paragraphs])
    return text

def extract_text_from_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file.read())
    elif uploaded_file.name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file.read())
    else:
        return ""