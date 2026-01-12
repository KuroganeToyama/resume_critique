"""
Hybrid job rubric compiler.

Uses LLM for job analysis and dimension mapping (universal job support).
Falls back to deterministic regex rules if LLM fails.
"""
import re
import hashlib
from typing import Dict, List, Any, Optional
from app.rubric.dimensions import DIMENSIONS
from app.rubric.vocabulary import find_tags_in_text
from app.services.llm_client import llm_client
from app.schemas.schemas import JobAnalysis, DimensionMapping


class RubricCompiler:
    """Hybrid rubric compiler with LLM support."""
    
    # Weighting formula coefficients (for fallback)
    ALPHA = 0.3  # Required hits
    BETA = 0.15  # Preferred hits
    GAMMA = 0.2  # Phrase strength
    DELTA = 0.1  # Role level adjustment
    
    def __init__(self, use_llm: bool = True):
        self.dimensions = DIMENSIONS
        self.use_llm = use_llm
    
    def compile_rubric(self, job_posting: str) -> Dict[str, Any]:
        """
        Compile a job posting into a rubric.
        
        Uses LLM for universal job support, falls back to regex for tech jobs.
        
        Returns:
            Dictionary with rubric configuration
        """
        if self.use_llm:
            try:
                # Try LLM-based compilation (works for all job types)
                return self._compile_with_llm(job_posting)
            except Exception as e:
                print(f"LLM compilation failed, falling back to regex: {e}")
        
        # Fallback: Original regex-based compilation (tech-focused)
        return self._compile_with_regex(job_posting)
    
    def _compile_with_regex(self, job_posting: str) -> Dict[str, Any]:
        """
        Original regex-based compilation (tech-focused).
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
    
    def _compile_with_llm(self, job_posting: str) -> Dict[str, Any]:
        """
        LLM-based compilation for universal job support.
        """
        # Phase 1: Analyze job posting
        job_analysis = self._llm_analyze_job(job_posting)
        
        # Phase 2: Map to dimensions
        dimension_mapping = self._llm_map_to_dimensions(job_analysis, job_posting)
        
        # Phase 3: Build dimension configs
        dimension_configs = self._build_dimension_configs(dimension_mapping)
        
        # Generate hash
        job_hash = self._hash_job_posting(job_posting)
        
        return {
            "job_posting_hash": job_hash,
            "role_level": job_analysis.role_level,
            "domain": job_analysis.domain,
            "job_function": job_analysis.job_function,
            "sections": {"analysis": "LLM-based"},
            "tags": {"requirements": job_analysis.key_requirements},
            "dimension_configs": dimension_configs
        }
    
    def _llm_analyze_job(self, job_posting: str) -> JobAnalysis:
        """
        Use LLM to analyze job posting and extract key information.
        """
        system_prompt = """You are a job posting analyst. Extract structured information from any type of job posting.

Analyze the role level, domain, job function, and requirements.

For evaluation_priorities, assess which dimensions matter most:
- impact: importance of measurable outcomes
- evidence: need for quantified achievements
- clarity: importance of clear communication
- skill_alignment: criticality of specific skills
- tooling_match: importance of specific tools/technologies
- domain_relevance: importance of industry experience
- leadership: need for leadership/mentorship
- communication: importance of interpersonal skills

Rate each as "high", "medium", or "low"."""
        
        prompt = f"""Analyze this job posting:

{job_posting}

Extract:
1. Role level (junior/mid/senior/lead)
2. Domain (technology/healthcare/finance/sales/marketing/education/etc)
3. Job function (engineering/nursing/accounting/sales/teaching/etc)
4. Key requirements (top 5-7 main requirements)
5. Required skills (must-have skills)
6. Preferred skills (nice-to-have skills)
7. Evaluation priorities (which dimensions matter most)"""
        
        result = llm_client.extract_structured(
            prompt=prompt,
            response_model=JobAnalysis,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        return result
    
    def _llm_map_to_dimensions(self, job_analysis: JobAnalysis, job_posting: str) -> DimensionMapping:
        """
        Use LLM to map job requirements to rubric dimensions.
        """
        # Build dimension descriptions for LLM
        dim_descriptions = []
        for name, dim in self.dimensions.items():
            signals_str = ", ".join(dim.signals[:3])  # First 3 signals
            dim_descriptions.append(
                f"- {name} ({dim.category.value}): Checks {signals_str}"
            )
        
        system_prompt = """You are a rubric designer. Map job requirements to evaluation dimensions.

For each dimension, decide:
1. Should it be enabled? (true/false)
2. How important is it? (weight: 0.5-2.0, default 1.0)
3. Why does it matter for this job?

Higher weights (1.5-2.0) for critical dimensions.
Lower weights (0.5-0.8) for less relevant dimensions.
Disable dimensions that don't apply."""
        
        prompt = f"""Job Analysis:
- Role: {job_analysis.role_level} {job_analysis.job_function}
- Domain: {job_analysis.domain}
- Key requirements: {', '.join(job_analysis.key_requirements[:5])}
- Priority dimensions: {job_analysis.evaluation_priorities}

Available dimensions:
{chr(10).join(dim_descriptions)}

Map these job requirements to dimensions with weights and reasoning."""
        
        result = llm_client.extract_structured(
            prompt=prompt,
            response_model=DimensionMapping,
            system_prompt=system_prompt,
            temperature=0.2
        )
        
        return result
    
    def _build_dimension_configs(self, dimension_mapping: DimensionMapping) -> Dict[str, Dict[str, Any]]:
        """
        Build final dimension configs from LLM mapping.
        """
        dimension_configs = {}
        
        for dim_name, dimension in self.dimensions.items():
            # Get LLM recommendation
            llm_weight = dimension_mapping.dimensions.get(dim_name)
            
            if llm_weight:
                # Use LLM's decision
                config = {
                    "enabled": llm_weight.enabled,
                    "weight": max(0.5, min(2.0, llm_weight.weight)),  # Clamp
                    "category": dimension.category.value,
                    "signals": dimension.signals,
                    "scoring_scale": dimension.scoring_scale,
                    "feedback_templates": dimension.feedback_templates,
                    "relevant_tags": [],
                    "activation_score": llm_weight.weight,
                    "reasoning": llm_weight.reasoning
                }
            else:
                # Fallback to default
                config = {
                    "enabled": dimension.default_enabled,
                    "weight": dimension.default_weight,
                    "category": dimension.category.value,
                    "signals": dimension.signals,
                    "scoring_scale": dimension.scoring_scale,
                    "feedback_templates": dimension.feedback_templates,
                    "relevant_tags": [],
                    "activation_score": 0.0,
                    "reasoning": "Default configuration"
                }
            
            dimension_configs[dim_name] = config
        
        return dimension_configs
