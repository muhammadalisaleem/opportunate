from io import BytesIO
from pathlib import Path
from docx import Document # type: ignore
import streamlit as st
from pypdf import PdfReader


def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using pypdf."""
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

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