"""
Resume processing service.

Handles resume extraction and rewrite suggestions using LLM.
"""
from typing import Dict, List
import PyPDF2
import docx
import io
from app.services.llm_client import llm_client
from app.schemas.schemas import (
    ResumeExtraction,
    RewriteSuggestionsResponse
)


class ResumeProcessingService:
    """Service for processing resumes."""
    
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from PDF or DOCX file.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
        
        Returns:
            Extracted text
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.pdf'):
            return self._extract_from_pdf(file_content)
        elif filename_lower.endswith('.docx'):
            return self._extract_from_docx(file_content)
        elif filename_lower.endswith('.txt'):
            return file_content.decode('utf-8')
        else:
            raise ValueError(f"Unsupported file type: {filename}")
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF."""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = []
        for page in pdf_reader.pages:
            text.append(page.extract_text())
        
        return '\n'.join(text)
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX."""
        doc_file = io.BytesIO(file_content)
        doc = docx.Document(doc_file)
        
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        
        return '\n'.join(text)
    
    def extract_structure(self, resume_text: str) -> ResumeExtraction:
        """
        Extract structured data from resume using LLM.
        
        Returns:
            ResumeExtraction with sections and bullets
        """
        system_prompt = """You are a resume parser. Extract structured information from the resume.

Identify sections (experience, education, skills, projects, etc.) and extract bullets.

For each bullet:
- bullet_index: Sequential number (starting from 1)
- text: The full bullet text
- has_metric: True if the bullet contains quantifiable metrics (numbers, percentages, etc.)
- tools: List of specific technologies/tools mentioned

Return JSON format:
{
  "sections": {
    "experience": [
      {
        "bullet_index": 1,
        "text": "Built system using Docker...",
        "has_metric": true,
        "tools": ["Docker", "AWS"]
      }
    ],
    "education": [...],
    "skills": [...]
  }
}

Only extract information that is actually in the resume."""
        
        prompt = f"""Parse this resume into structured sections:

{resume_text}

Extract all bullets with their metrics and tools."""
        
        try:
            result = llm_client.extract_structured(
                prompt=prompt,
                response_model=ResumeExtraction,
                system_prompt=system_prompt,
                temperature=0.0
            )
            return result
        except Exception as e:
            print(f"LLM resume extraction failed: {e}")
            # Return minimal structure as fallback
            return ResumeExtraction(sections={"experience": []})
    
    def generate_rewrite_suggestions(
        self,
        resume_text: str,
        failed_checks: List[Dict],
        max_suggestions: int = 5
    ) -> RewriteSuggestionsResponse:
        """
        Generate bounded rewrite suggestions for failed checks.
        
        Args:
            resume_text: Full resume text
            failed_checks: List of failed checks with bullet references
            max_suggestions: Maximum number of suggestions to generate
        
        Returns:
            RewriteSuggestionsResponse with suggestions
        """
        if not failed_checks:
            return RewriteSuggestionsResponse(suggestions=[])
        
        # Prepare context about failed checks
        check_context = "\n".join([
            f"- Bullet {check.get('bullet_index')}: {check.get('issue')}"
            for check in failed_checks[:max_suggestions]
        ])
        
        system_prompt = f"""You are a resume improvement assistant. Suggest rewrites for specific bullets.

Rules:
1. DO NOT add new facts or experiences
2. Only improve clarity, structure, or metric presentation
3. Keep suggestions realistic and grounded in the original text
4. Explain why each rewrite is better

Return JSON format:
{{
  "suggestions": [
    {{
      "bullet_index": 1,
      "original": "Built system...",
      "rewrite": "Built system resulting in...",
      "why": "Adds outcome without new facts"
    }}
  ]
}}

Maximum {max_suggestions} suggestions."""
        
        prompt = f"""Here is a resume with some issues:

{resume_text}

Failed checks:
{check_context}

Provide up to {max_suggestions} rewrite suggestions that improve these bullets WITHOUT adding new information."""
        
        try:
            result = llm_client.extract_structured(
                prompt=prompt,
                response_model=RewriteSuggestionsResponse,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Limit to max_suggestions
            result.suggestions = result.suggestions[:max_suggestions]
            return result
        
        except Exception as e:
            print(f"LLM rewrite generation failed: {e}")
            return RewriteSuggestionsResponse(suggestions=[])
    
    def generate_explanation(
        self,
        failed_check: Dict,
        dimension_name: str,
        feedback_template: str
    ) -> str:
        """
        Generate human-readable explanation for a failed check.
        
        Args:
            failed_check: The failed check details
            dimension_name: Name of the dimension
            feedback_template: Template from dimension
        
        Returns:
            Readable explanation
        """
        system_prompt = """You are a resume feedback assistant. Explain why a check failed in clear, helpful language.

Keep explanations:
- Specific and actionable
- 1-2 sentences
- Focused on the issue
- Constructive and helpful"""
        
        prompt = f"""Explain this resume issue:

Dimension: {dimension_name}
Issue: {failed_check.get('issue', 'Unknown issue')}
Context: {failed_check.get('context', '')}
Template: {feedback_template}

Provide a clear, 1-2 sentence explanation."""
        
        try:
            explanation = llm_client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=150
            )
            return explanation.strip()
        except Exception as e:
            print(f"LLM explanation generation failed: {e}")
            # Fallback to template
            return feedback_template
