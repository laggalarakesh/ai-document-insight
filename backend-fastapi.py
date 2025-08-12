# AI-Powered Document Insight Tool - FastAPI Backend
# Full Stack Developer Assessment Solution

import os
import uuid
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
import re
from pathlib import Path

# FastAPI imports
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Database imports
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# PDF processing imports
import PyPDF2
from io import BytesIO

# Google AI imports
from google import genai
from google.genai import types
import httpx

# Environment and configuration
from pydantic import BaseModel
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# =============================================================================
# DATABASE SETUP
# =============================================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./documents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DocumentRecord(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    original_filename = Column(String, index=True)
    stored_filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    content_type = Column(String)
    insights = Column(Text)  # JSON string
    processing_status = Column(String, default="pending")  # pending, completed, failed
    error_message = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class DocumentInsight(BaseModel):
    summary: str
    key_skills: List[str] = []
    experience_level: str = ""
    education: str = ""
    highlights: List[str] = []
    word_frequency: Optional[Dict[str, int]] = None
    processing_method: str  # "ai" or "fallback"

class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    file_size: int
    insights: Optional[DocumentInsight] = None
    processing_status: str
    error_message: Optional[str] = None

class UploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    processing_status: str

# =============================================================================
# FASTAPI APP CONFIGURATION
# =============================================================================

app = FastAPI(
    title="AI-Powered Document Insight Tool",
    description="Upload PDF documents and receive AI-generated insights and summaries",
    version="1.0.0"
)

# CORS configuration for React frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "http://localhost:8080",
    # Add your frontend URL here
    "https://ppl-ai-code-interpreter-files.s3.amazonaws.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# GOOGLE AI STUDIO / GEMINI CONFIGURATION
# =============================================================================

# Set your Google AI Studio API key as environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "your-google-ai-api-key-here")

def setup_gemini_client():
    """Initialize Gemini AI client"""
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        return client
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        return None

gemini_client = setup_gemini_client()

# =============================================================================
# PDF PROCESSING UTILITIES
# =============================================================================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from PDF bytes"""
    try:
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\\n"
        
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {str(e)}")

def get_word_frequency_fallback(text: str, top_n: int = 5) -> Dict[str, int]:
    """Fallback method: Get top N most frequent words"""
    try:
        # Clean and tokenize text
        text_lower = text.lower()
        words = word_tokenize(text_lower)
        
        # Remove punctuation and stopwords
        stop_words = set(stopwords.words('english'))
        filtered_words = [
            word for word in words 
            if word.isalnum() and len(word) > 2 and word not in stop_words
        ]
        
        # Get word frequency
        word_freq = Counter(filtered_words)
        return dict(word_freq.most_common(top_n))
    
    except Exception as e:
        print(f"Error in word frequency analysis: {e}")
        return {}

# =============================================================================
# AI PROCESSING FUNCTIONS
# =============================================================================

def analyze_document_with_gemini(pdf_bytes: bytes, filename: str) -> DocumentInsight:
    """Analyze document using Google Gemini AI"""
    try:
        if not gemini_client:
            raise Exception("Gemini client not available")
        
        # Create the prompt for resume analysis
        prompt = """Analyze this PDF document (likely a resume or CV) and provide a structured summary with the following information:

1. A concise summary of the candidate's background and experience
2. Key skills mentioned in the document
3. Experience level (e.g., "2+ years", "Senior level", "Entry level")  
4. Education background
5. Key highlights or achievements

Please format your response as a JSON object with these exact keys:
- summary: string
- key_skills: array of strings
- experience_level: string
- education: string
- highlights: array of strings

Focus on extracting the most relevant information for recruiters and hiring managers."""

        # Send document to Gemini for analysis
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(
                    data=pdf_bytes,
                    mime_type='application/pdf'
                ),
                prompt
            ]
        )
        
        # Parse the response
        if response and response.text:
            # Try to extract JSON from the response
            import json
            try:
                # Clean the response text to extract JSON
                response_text = response.text.strip()
                if "```json" in response_text:
                    json_part = response_text.split("```json")[1].split("```")[0]
                else:
                    json_part = response_text
                
                parsed_response = json.loads(json_part)
                
                return DocumentInsight(
                    summary=parsed_response.get("summary", "No summary available"),
                    key_skills=parsed_response.get("key_skills", []),
                    experience_level=parsed_response.get("experience_level", "Not specified"),
                    education=parsed_response.get("education", "Not specified"),
                    highlights=parsed_response.get("highlights", []),
                    processing_method="ai"
                )
                
            except json.JSONDecodeError:
                # If JSON parsing fails, create a basic insight from the raw response
                return DocumentInsight(
                    summary=response.text[:500] + "..." if len(response.text) > 500 else response.text,
                    key_skills=[],
                    experience_level="Not specified",
                    education="Not specified",
                    highlights=[],
                    processing_method="ai"
                )
        
        else:
            raise Exception("No response from Gemini AI")
    
    except Exception as e:
        print(f"Gemini AI analysis failed: {e}")
        raise e

def analyze_document_fallback(text: str) -> DocumentInsight:
    """Fallback analysis using word frequency"""
    word_freq = get_word_frequency_fallback(text, top_n=5)
    
    return DocumentInsight(
        summary="AI service temporarily unavailable. Document processed using fallback analysis.",
        key_skills=list(word_freq.keys()) if word_freq else [],
        experience_level="Unable to determine",
        education="Unable to determine",
        highlights=[f"Frequent term: {word} ({count} occurrences)" for word, count in word_freq.items()][:3],
        word_frequency=word_freq,
        processing_method="fallback"
    )

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI-Powered Document Insight Tool API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload-resume",
            "insights": "/insights"
        }
    }

@app.post("/upload-resume", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a PDF resume/document"""
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    # Validate file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum 10MB allowed."
        )
    
    # Generate unique ID and filename
    document_id = str(uuid.uuid4())
    stored_filename = f"{document_id}_{file.filename}"
    
    # Create database record
    doc_record = DocumentRecord(
        id=document_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_size=len(file_content),
        content_type=file.content_type,
        processing_status="processing"
    )
    
    db.add(doc_record)
    db.commit()
    
    # Process the document asynchronously (in a real app, use background tasks)
    try:
        # Try AI analysis first
        try:
            insights = analyze_document_with_gemini(file_content, file.filename)
        except Exception as ai_error:
            print(f"AI analysis failed, using fallback: {ai_error}")
            # Extract text and use fallback
            text_content = extract_text_from_pdf(file_content)
            insights = analyze_document_fallback(text_content)
        
        # Update database with results
        import json
        doc_record.insights = json.dumps(insights.dict())
        doc_record.processing_status = "completed"
        db.commit()
        
    except Exception as e:
        doc_record.processing_status = "failed"
        doc_record.error_message = str(e)
        db.commit()
        
        return UploadResponse(
            message="Document upload successful, but processing failed",
            document_id=document_id,
            filename=file.filename,
            processing_status="failed"
        )
    
    return UploadResponse(
        message="Document uploaded and processed successfully",
        document_id=document_id,
        filename=file.filename,
        processing_status="completed"
    )

@app.get("/insights", response_model=List[DocumentResponse])
async def get_insights(
    document_id: Optional[str] = Query(None, description="Specific document ID to retrieve"),
    limit: int = Query(50, description="Maximum number of documents to return"),
    db: Session = Depends(get_db)
):
    """Retrieve document insights"""
    
    if document_id:
        # Get specific document
        doc_record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        documents = [doc_record]
    else:
        # Get all documents (limited)
        documents = db.query(DocumentRecord).order_by(
            DocumentRecord.upload_date.desc()
        ).limit(limit).all()
    
    # Format response
    response_data = []
    for doc in documents:
        insights = None
        if doc.insights:
            import json
            try:
                insights_data = json.loads(doc.insights)
                insights = DocumentInsight(**insights_data)
            except Exception as e:
                print(f"Failed to parse insights for document {doc.id}: {e}")
        
        response_data.append(DocumentResponse(
            id=doc.id,
            filename=doc.original_filename,
            upload_date=doc.upload_date,
            file_size=doc.file_size,
            insights=insights,
            processing_status=doc.processing_status,
            error_message=doc.error_message
        ))
    
    return response_data

@app.delete("/insights/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its insights"""
    
    doc_record = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(doc_record)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "gemini_available": gemini_client is not None
    }

# =============================================================================
# DEVELOPMENT SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

# =============================================================================
# INSTALLATION AND SETUP INSTRUCTIONS
# =============================================================================
"""
Installation Instructions:

1. Create a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate

2. Install dependencies:
   pip install fastapi uvicorn python-multipart
   pip install sqlalchemy PyPDF2 nltk google-genai httpx

3. Set environment variable:
   export GOOGLE_API_KEY="your-google-ai-api-key-here"
   # On Windows: set GOOGLE_API_KEY=your-google-ai-api-key-here

4. Run the server:
   python main.py
   
   Or using uvicorn directly:
   uvicorn main:app --reload

5. API will be available at:
   http://127.0.0.1:8000
   Interactive docs: http://127.0.0.1:8000/docs
   
6. For production deployment:
   - Use a proper database (PostgreSQL, MySQL)
   - Implement proper authentication
   - Use async background tasks for document processing
   - Add proper logging and monitoring
   - Configure proper CORS origins
   - Use environment-based configuration
"""