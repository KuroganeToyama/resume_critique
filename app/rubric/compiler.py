"""
Deterministic job rubric compiler (Option A1).

Compiles job postings into rubrics using deterministic rules.
Same posting + same ruleset = same rubric.
"""
import re
import hashlib
from typing import Dict, List, Any
from app.rubric.dimensions import DIMENSIONS
from app.rubric.vocabulary import find_tags_in_text


class RubricCompiler:
    """Deterministic rubric compiler."""
    
    # Weighting formula coefficients
    ALPHA = 0.3  # Required hits
    BETA = 0.15  # Preferred hits
    GAMMA = 0.2  # Phrase strength
    DELTA = 0.1  # Role level adjustment
    
    def __init__(self):
        self.dimensions = DIMENSIONS
    
    def compile_rubric(self, job_posting: str) -> Dict[str, Any]:
        """
        Compile a job posting into a rubric.
        
        Returns:
            Dictionary with rubric configuration
        """
        # 1. Parse sections
        sections = self._parse_sections(job_posting)
        
        # 2. Infer role level
        role_level = self._infer_role_level(job_posting)
        
        # 3. Extract tags from each section
        section_tags = {}
        for section_name, section_text in sections.items():
            section_tags[section_name] = find_tags_in_text(section_text)
        
        # 4. Calculate dimension weights
        dimension_configs = self._calculate_dimension_weights(
            sections,
            section_tags,
            role_level
        )
        
        # 5. Generate job posting hash
        job_hash = self._hash_job_posting(job_posting)
        
        return {
            "job_posting_hash": job_hash,
            "role_level": role_level,
            "sections": sections,
            "tags": section_tags,
            "dimension_configs": dimension_configs
        }
    
    def _parse_sections(self, job_posting: str) -> Dict[str, str]:
        """
        Parse job posting into sections using regex.
        
        Fallback parsing if sections aren't clearly marked.
        """
        sections = {
            "required": "",
            "preferred": "",
            "responsibilities": "",
            "other": ""
        }
        
        # Regex patterns for section headers
        required_pattern = r'(?i)(requirements?|qualifications?|must[- ]have|required skills?)'
        preferred_pattern = r'(?i)(preferred|bonus|nice[- ]to[- ]have|optional)'
        responsibilities_pattern = r"(?i)(responsibilities|duties|what you'll do|role)"
        
        lines = job_posting.split('\n')
        current_section = "other"
        
        for line in lines:
            # Check for section headers
            if re.search(required_pattern, line):
                current_section = "required"
                continue
            elif re.search(preferred_pattern, line):
                current_section = "preferred"
                continue
            elif re.search(responsibilities_pattern, line):
                current_section = "responsibilities"
                continue
            
            # Add line to current section
            sections[current_section] += line + "\n"
        
        # If required is empty, assume most of posting is required
        if not sections["required"].strip() and sections["other"].strip():
            sections["required"] = sections["other"]
            sections["other"] = ""
        
        return sections
    
    def _infer_role_level(self, job_posting: str) -> str:
        """
        Infer role level from job posting using regex.
        
        Returns: "junior", "mid", "senior", or "unknown"
        """
        text_lower = job_posting.lower()
        
        # Patterns for different levels
        if re.search(r'\b(intern|internship|student|entry[- ]level|0-?2\s*years?)\b', text_lower):
            return "junior"
        elif re.search(r'\b(senior|staff|principal|lead|7\+\s*years?|8\+\s*years?)\b', text_lower):
            return "senior"
        elif re.search(r'\b(3-?5\s*years?|mid[- ]level|intermediate)\b', text_lower):
            return "mid"
        
        return "unknown"
    
    def _calculate_phrase_strength(self, text: str, term: str) -> float:
        """
        Calculate phrase strength based on nearby modifiers.
        
        Returns: Multiplier (0.7 - 1.5)
        """
        # Find the term in text (case insensitive)
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(text))
        
        if not matches:
            return 1.0
        
        max_strength = 1.0
        
        for match in matches:
            # Get surrounding context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].lower()
            
            # Check for strong modifiers
            if re.search(r'\b(must|required|minimum|essential|mandatory)\b', context):
                max_strength = max(max_strength, 1.5)
            # Check for weak modifiers
            elif re.search(r'\b(preferred|nice|bonus|optional|familiarity)\b', context):
                max_strength = max(max_strength, 0.7)
        
        return max_strength
    
    def _get_section_strength(self, section_name: str) -> float:
        """Get base strength for a section."""
        strengths = {
            "required": 1.5,
            "responsibilities": 1.0,
            "preferred": 0.7,
            "other": 0.5
        }
        return strengths.get(section_name, 0.5)
    
    def _calculate_dimension_weights(
        self,
        sections: Dict[str, str],
        section_tags: Dict[str, Dict[str, List[str]]],
        role_level: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate weights for each dimension based on job posting.
        
        Returns:
            Dict mapping dimension_name -> config dict
        """
        # Tag to dimension mapping
        tag_to_dimensions = {
            "infra": ["tooling_match", "skill_alignment"],
            "devops": ["tooling_match", "skill_alignment"],
            "iac": ["tooling_match"],
            "cicd": ["tooling_match"],
            "cloud": ["tooling_match", "skill_alignment"],
            "backend": ["domain_relevance", "skill_alignment"],
            "frontend": ["domain_relevance", "skill_alignment"],
            "database": ["tooling_match", "skill_alignment"],
            "api": ["skill_alignment"],
            "data": ["data_rigor", "skill_alignment"],
            "ml": ["data_rigor", "skill_alignment"],
            "science": ["data_rigor", "research_quality"],
            "security": ["security_awareness", "consistency"],
            "auth": ["security_awareness"],
            "compliance": ["security_awareness"],
            "research": ["research_quality", "evidence"],
            "testing": ["consistency", "signal_density"],
            "observability": ["impact", "data_rigor"],
            "leadership": ["leadership"],
            "collaboration": ["communication"],
            "mobile": ["domain_relevance", "skill_alignment"],
        }
        
        # Count tag occurrences by section
        tag_scores: Dict[str, Dict[str, float]] = {}
        
        for section_name, tags in section_tags.items():
            section_strength = self._get_section_strength(section_name)
            
            for tag, terms in tags.items():
                if tag not in tag_scores:
                    tag_scores[tag] = {"required": 0, "preferred": 0, "other": 0}
                
                # Calculate phrase strength for each term
                section_text = sections[section_name]
                phrase_strengths = [
                    self._calculate_phrase_strength(section_text, term)
                    for term in terms
                ]
                avg_phrase_strength = sum(phrase_strengths) / len(phrase_strengths)
                
                # Accumulate score
                score = len(terms) * section_strength * avg_phrase_strength
                
                if section_name == "required":
                    tag_scores[tag]["required"] += score
                elif section_name == "preferred":
                    tag_scores[tag]["preferred"] += score
                else:
                    tag_scores[tag]["other"] += score
        
        # Calculate dimension weights
        dimension_configs = {}
        
        for dim_name, dimension in self.dimensions.items():
            # Start with default configuration
            config = {
                "enabled": dimension.default_enabled,
                "weight": dimension.default_weight,
                "category": dimension.category.value,
                "signals": dimension.signals,
                "scoring_scale": dimension.scoring_scale,
                "feedback_templates": dimension.feedback_templates
            }
            
            # Calculate activation score for this dimension
            activation_score = 0.0
            relevant_tags = []
            
            for tag, dims in tag_to_dimensions.items():
                if dim_name in dims and tag in tag_scores:
                    scores = tag_scores[tag]
                    tag_contribution = (
                        self.ALPHA * scores["required"] +
                        self.BETA * scores["preferred"] +
                        0.05 * scores["other"]
                    )
                    activation_score += tag_contribution
                    if tag_contribution > 0:
                        relevant_tags.append(tag)
            
            # Apply role level adjustment for specific dimensions
            if dim_name == "level_appropriateness":
                if role_level in ["senior", "lead"]:
                    activation_score += self.DELTA * 5
                    config["enabled"] = True
            
            if dim_name == "leadership":
                if role_level in ["senior", "lead"]:
                    activation_score += self.DELTA * 5
                    config["enabled"] = True
            
            # Update weight based on activation score
            if activation_score > 0:
                # Enable dimension if it has relevant tags
                if dim_name in ["skill_alignment", "tooling_match", "domain_relevance"]:
                    config["enabled"] = True
                
                # Adjust weight (clamp between 0.5 and 2.0)
                weight_adjustment = min(activation_score, 1.0)
                config["weight"] = max(0.5, min(2.0, 
                    config["weight"] + weight_adjustment
                ))
            
            config["relevant_tags"] = relevant_tags
            config["activation_score"] = round(activation_score, 2)
            
            dimension_configs[dim_name] = config
        
        return dimension_configs
    
    def _hash_job_posting(self, job_posting: str) -> str:
        """Generate deterministic hash of job posting."""
        return hashlib.sha256(job_posting.encode()).hexdigest()[:16]
