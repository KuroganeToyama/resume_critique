"""
Job posting processing service.

Handles section splitting and tag extraction using LLM.
"""
from typing import Dict
from app.services.llm_client import llm_client
from app.schemas.schemas import JobSectionSplit, JobTagsResponse, JobTag
from app.rubric.vocabulary import VOCABULARY


class JobProcessingService:
    """Service for processing job postings."""
    
    def split_sections(self, job_posting: str) -> Dict[str, str]:
        """
        Split job posting into sections using LLM.
        
        Falls back to deterministic parsing if LLM fails.
        """
        system_prompt = """You are a job posting parser. Extract sections from the job posting.
Return a JSON object with these keys:
- required: Content from Requirements/Qualifications/Must-have sections
- preferred: Content from Preferred/Bonus/Nice-to-have sections
- responsibilities: Content from Responsibilities/Duties sections
- other: Any other content

If a section is not present, use an empty string.
All content must come directly from the posting - do not invent content."""
        
        prompt = f"""Parse this job posting into sections:

{job_posting}

Return JSON with keys: required, preferred, responsibilities, other"""
        
        try:
            result = llm_client.extract_structured(
                prompt=prompt,
                response_model=JobSectionSplit,
                system_prompt=system_prompt,
                temperature=0.0
            )
            return {
                "required": result.required,
                "preferred": result.preferred,
                "responsibilities": result.responsibilities,
                "other": result.other
            }
        except Exception as e:
            print(f"LLM section split failed: {e}. Using fallback.")
            # Fallback to deterministic parsing would be handled by compiler
            raise
    
    def extract_tags(self, job_posting: str, sections: Dict[str, str]) -> JobTagsResponse:
        """
        Extract vocabulary tags from job posting with evidence.
        
        This is for UI/audit purposes - the actual rubric compilation
        uses deterministic vocabulary matching.
        """
        # Get allowlist of tags
        all_tags = set()
        for tags in VOCABULARY.values():
            all_tags.update(tags)
        
        tag_list = sorted(list(all_tags))
        
        system_prompt = f"""You are a job posting analyzer. Identify technical skills and domains.

Use ONLY these tags: {', '.join(tag_list)}

For each tag you identify, provide:
- tag: The tag name (must be from the list above)
- section: Which section it appeared in (required/preferred/responsibilities/other)
- evidence: A list of direct quotes from the posting that support this tag

Only include tags that are clearly present. Do not invent tags."""
        
        prompt = f"""Analyze this job posting and identify relevant tags with evidence:

{job_posting}

Return JSON with format:
{{
  "tags": [
    {{
      "tag": "backend",
      "section": "required",
      "evidence": [{{"quote": "5+ years of backend development"}}]
    }}
  ]
}}"""
        
        try:
            result = llm_client.extract_structured(
                prompt=prompt,
                response_model=JobTagsResponse,
                system_prompt=system_prompt,
                temperature=0.0
            )
            
            # Validate that quotes actually appear in posting
            validated_tags = []
            for tag in result.tags:
                validated_evidence = []
                for evidence in tag.evidence:
                    # Check if quote appears in the posting (case insensitive)
                    if evidence.quote.lower() in job_posting.lower():
                        validated_evidence.append(evidence)
                
                if validated_evidence:
                    validated_tags.append(JobTag(
                        tag=tag.tag,
                        section=tag.section,
                        evidence=validated_evidence
                    ))
            
            return JobTagsResponse(tags=validated_tags)
        
        except Exception as e:
            print(f"LLM tag extraction failed: {e}")
            # Return empty tags as fallback
            return JobTagsResponse(tags=[])
