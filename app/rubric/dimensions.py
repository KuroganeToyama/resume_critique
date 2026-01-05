"""
Fixed rubric dimension definitions.

This module defines the canonical superset of all possible rubric dimensions.
Dimensions are never created dynamically.
"""
from typing import Dict, List
from enum import Enum


class DimensionCategory(str, Enum):
    """Categories of rubric dimensions."""
    CORE = "core"
    ALIGNMENT = "alignment"
    RISK = "risk"
    CONTEXTUAL = "contextual"


class RubricDimension:
    """A single rubric dimension with its configuration."""
    
    def __init__(
        self,
        name: str,
        category: DimensionCategory,
        default_enabled: bool,
        signals: List[str],
        scoring_scale: Dict[int, str],
        feedback_templates: List[str],
        default_weight: float = 1.0
    ):
        self.name = name
        self.category = category
        self.default_enabled = default_enabled
        self.signals = signals
        self.scoring_scale = scoring_scale
        self.feedback_templates = feedback_templates
        self.default_weight = default_weight


# Scoring scale templates
STANDARD_SCALE = {
    1: "Critical issues present",
    2: "Significant gaps",
    3: "Meets basic expectations",
    4: "Strong performance",
    5: "Exceptional quality"
}

ALIGNMENT_SCALE = {
    1: "No relevant match",
    2: "Weak alignment",
    3: "Moderate alignment",
    4: "Strong alignment",
    5: "Perfect match"
}

RISK_SCALE = {
    1: "High risk / red flags",
    2: "Moderate concerns",
    3: "Acceptable",
    4: "Low risk",
    5: "No concerns"
}


# Define all dimensions
DIMENSIONS: Dict[str, RubricDimension] = {
    # CORE dimensions (always enabled)
    "clarity": RubricDimension(
        name="clarity",
        category=DimensionCategory.CORE,
        default_enabled=True,
        signals=[
            "clear_action_verbs",
            "specific_technologies",
            "quantified_outcomes",
            "no_jargon_overload",
            "readable_structure"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Bullet uses vague language: '{text}'",
            "Consider replacing '{word}' with specific action",
            "Add specific tools/technologies used",
            "Clarify your role vs team contribution"
        ],
        default_weight=1.2
    ),
    
    "evidence": RubricDimension(
        name="evidence",
        category=DimensionCategory.CORE,
        default_enabled=True,
        signals=[
            "has_metrics",
            "has_timeframes",
            "has_scale_indicators",
            "specific_technologies_named",
            "verifiable_claims"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Missing metrics in: '{text}'",
            "Add specific numbers or percentages",
            "Include timeframe (e.g., 'over 6 months')",
            "Specify scale (e.g., 'for 10M users')"
        ],
        default_weight=1.3
    ),
    
    "impact": RubricDimension(
        name="impact",
        category=DimensionCategory.CORE,
        default_enabled=True,
        signals=[
            "business_outcome",
            "user_impact",
            "performance_improvement",
            "cost_reduction",
            "time_saved"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Focus on outcomes, not just activities",
            "Add business impact to: '{text}'",
            "Quantify user or system improvement",
            "Connect technical work to business value"
        ],
        default_weight=1.4
    ),
    
    "structure": RubricDimension(
        name="structure",
        category=DimensionCategory.CORE,
        default_enabled=True,
        signals=[
            "consistent_formatting",
            "logical_ordering",
            "appropriate_length",
            "no_redundancy",
            "clear_sections"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Inconsistent bullet format",
            "Redundant content across bullets",
            "Section ordering could be improved",
            "Bullet is too long (>2 lines)"
        ],
        default_weight=1.0
    ),
    
    # ALIGNMENT dimensions (job-activated)
    "skill_alignment": RubricDimension(
        name="skill_alignment",
        category=DimensionCategory.ALIGNMENT,
        default_enabled=False,
        signals=[
            "required_skills_present",
            "skill_depth_matches_level",
            "recent_skill_usage",
            "complementary_skills"
        ],
        scoring_scale=ALIGNMENT_SCALE,
        feedback_templates=[
            "Missing required skill: {skill}",
            "Highlight {skill} experience more prominently",
            "Add recency indicator for {skill}",
            "Demonstrate {skill} depth with examples"
        ],
        default_weight=1.0
    ),
    
    "tooling_match": RubricDimension(
        name="tooling_match",
        category=DimensionCategory.ALIGNMENT,
        default_enabled=False,
        signals=[
            "exact_tool_match",
            "equivalent_tool",
            "tool_category_match",
            "demonstrated_tool_proficiency"
        ],
        scoring_scale=ALIGNMENT_SCALE,
        feedback_templates=[
            "Add experience with {tool}",
            "Mention {equivalent} (similar to {tool})",
            "Emphasize {tool} usage in recent roles",
            "Include {tool} certifications if applicable"
        ],
        default_weight=0.9
    ),
    
    "domain_relevance": RubricDimension(
        name="domain_relevance",
        category=DimensionCategory.ALIGNMENT,
        default_enabled=False,
        signals=[
            "industry_match",
            "problem_domain_match",
            "system_scale_match",
            "architecture_pattern_match"
        ],
        scoring_scale=ALIGNMENT_SCALE,
        feedback_templates=[
            "Highlight {domain} experience",
            "Connect past work to {domain} challenges",
            "Emphasize transferable {domain} skills",
            "Add context about {domain} systems"
        ],
        default_weight=1.1
    ),
    
    "level_appropriateness": RubricDimension(
        name="level_appropriateness",
        category=DimensionCategory.ALIGNMENT,
        default_enabled=False,
        signals=[
            "scope_matches_level",
            "autonomy_indicators",
            "leadership_if_senior",
            "mentorship_if_senior",
            "learning_if_junior"
        ],
        scoring_scale=ALIGNMENT_SCALE,
        feedback_templates=[
            "Add scope indicators for {level} level",
            "Include leadership examples for senior role",
            "Show autonomous decision-making",
            "Demonstrate cross-team collaboration"
        ],
        default_weight=1.2
    ),
    
    # RISK dimensions
    "signal_density": RubricDimension(
        name="signal_density",
        category=DimensionCategory.RISK,
        default_enabled=True,
        signals=[
            "high_info_per_line",
            "no_filler_words",
            "every_bullet_valuable",
            "no_obvious_statements"
        ],
        scoring_scale=RISK_SCALE,
        feedback_templates=[
            "Remove filler: '{text}'",
            "Every word should add value",
            "Combine sparse bullets",
            "Remove obvious statement: '{text}'"
        ],
        default_weight=0.8
    ),
    
    "overclaim_risk": RubricDimension(
        name="overclaim_risk",
        category=DimensionCategory.RISK,
        default_enabled=True,
        signals=[
            "claims_without_evidence",
            "extreme_superlatives",
            "unclear_personal_contribution",
            "timeline_inconsistencies"
        ],
        scoring_scale=RISK_SCALE,
        feedback_templates=[
            "Claim needs evidence: '{text}'",
            "Tone down superlative: '{word}'",
            "Clarify your specific contribution",
            "Avoid unverifiable claims"
        ],
        default_weight=1.1
    ),
    
    "consistency": RubricDimension(
        name="consistency",
        category=DimensionCategory.RISK,
        default_enabled=True,
        signals=[
            "timeline_coherence",
            "skill_progression_logical",
            "role_titles_appropriate",
            "no_contradictions"
        ],
        scoring_scale=RISK_SCALE,
        feedback_templates=[
            "Timeline gap or overlap detected",
            "Skill progression seems inconsistent",
            "Verify role title accuracy",
            "Conflicting information between bullets"
        ],
        default_weight=0.9
    ),
    
    # CONTEXTUAL dimensions (off by default)
    "leadership": RubricDimension(
        name="leadership",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "led_team",
            "mentored_others",
            "drove_initiative",
            "influenced_strategy",
            "managed_stakeholders"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Add team size and leadership scope",
            "Include mentorship examples",
            "Show initiative ownership",
            "Demonstrate strategic influence"
        ],
        default_weight=1.0
    ),
    
    "research_quality": RubricDimension(
        name="research_quality",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "publications_cited",
            "experimental_rigor",
            "novel_contributions",
            "peer_review"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Include publication venue and citations",
            "Describe experimental methodology",
            "Highlight novel contributions",
            "Mention peer review or awards"
        ],
        default_weight=1.0
    ),
    
    "communication": RubricDimension(
        name="communication",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "documentation_work",
            "presentations_given",
            "cross_team_collaboration",
            "technical_writing"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Highlight documentation contributions",
            "Include presentation/speaking experience",
            "Show cross-functional collaboration",
            "Mention technical writing or blog posts"
        ],
        default_weight=0.8
    ),
    
    "product_thinking": RubricDimension(
        name="product_thinking",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "user_focus",
            "product_metrics",
            "feature_ownership",
            "user_research"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Connect work to user outcomes",
            "Include product metrics impact",
            "Show feature ownership end-to-end",
            "Mention user research involvement"
        ],
        default_weight=1.0
    ),
    
    "data_rigor": RubricDimension(
        name="data_rigor",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "statistical_methods",
            "ab_testing",
            "data_quality",
            "analysis_depth"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Specify statistical methods used",
            "Include A/B test results and sample sizes",
            "Describe data quality processes",
            "Show depth of analysis"
        ],
        default_weight=1.0
    ),
    
    "security_awareness": RubricDimension(
        name="security_awareness",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "security_practices",
            "compliance_work",
            "threat_modeling",
            "security_audits"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Highlight security best practices",
            "Include compliance frameworks (SOC2, etc.)",
            "Mention threat modeling or security reviews",
            "Show security audit results"
        ],
        default_weight=1.0
    ),
    
    "open_source": RubricDimension(
        name="open_source",
        category=DimensionCategory.CONTEXTUAL,
        default_enabled=False,
        signals=[
            "oss_contributions",
            "maintained_projects",
            "community_involvement",
            "pull_requests"
        ],
        scoring_scale=STANDARD_SCALE,
        feedback_templates=[
            "Include OSS project links and stars",
            "Mention contribution statistics",
            "Highlight maintained projects",
            "Show community involvement (issues, PRs, reviews)"
        ],
        default_weight=0.7
    ),
}


def get_dimension(name: str) -> RubricDimension:
    """Get a dimension by name."""
    return DIMENSIONS[name]


def get_all_dimensions() -> Dict[str, RubricDimension]:
    """Get all available dimensions."""
    return DIMENSIONS.copy()


def get_enabled_dimensions() -> Dict[str, RubricDimension]:
    """Get dimensions that are enabled by default."""
    return {
        name: dim for name, dim in DIMENSIONS.items()
        if dim.default_enabled
    }


def get_dimensions_by_category(category: DimensionCategory) -> Dict[str, RubricDimension]:
    """Get all dimensions in a category."""
    return {
        name: dim for name, dim in DIMENSIONS.items()
        if dim.category == category
    }
