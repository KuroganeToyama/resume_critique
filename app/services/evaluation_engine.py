"""
Resume evaluation engine.

Deterministic scoring based on extracted resume structure and rubric configuration.
"""
from typing import Dict, List, Any, Tuple
from app.schemas.schemas import ResumeExtraction, ResumeBullet
from app.rubric.dimensions import get_dimension


class EvaluationEngine:
    """Deterministic resume evaluation engine."""
    
    def evaluate(
        self,
        resume_extraction: ResumeExtraction,
        rubric_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate resume against rubric.
        
        Args:
            resume_extraction: Structured resume data
            rubric_config: Rubric configuration with dimension weights
        
        Returns:
            Evaluation results with scores and recommendations
        """
        dimension_configs = rubric_config["dimension_configs"]
        
        # Evaluate each enabled dimension
        dimension_scores = {}
        all_failed_checks = []
        
        for dim_name, dim_config in dimension_configs.items():
            if not dim_config["enabled"]:
                continue
            
            score, failed_checks = self._evaluate_dimension(
                dim_name,
                dim_config,
                resume_extraction
            )
            
            dimension_scores[dim_name] = {
                "score": score,
                "weight": dim_config["weight"],
                "failed_checks": failed_checks
            }
            
            all_failed_checks.extend(failed_checks)
        
        # Calculate overall weighted score
        overall_score = self._calculate_overall_score(dimension_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            dimension_scores,
            all_failed_checks
        )
        
        return {
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "recommendations": recommendations,
            "failed_checks": all_failed_checks
        }
    
    def _evaluate_dimension(
        self,
        dim_name: str,
        dim_config: Dict[str, Any],
        resume_extraction: ResumeExtraction
    ) -> Tuple[float, List[Dict]]:
        """
        Evaluate a single dimension.
        
        Returns:
            (score, failed_checks)
        """
        # Get all bullets from resume
        all_bullets = []
        experience_bullets = []
        for section_name, bullets in resume_extraction.sections.items():
            all_bullets.extend(bullets)
            if section_name.lower() in ['experience', 'work experience', 'professional experience']:
                experience_bullets.extend(bullets)
        
        if not all_bullets:
            return 1.0, [{"issue": "No content to evaluate", "dimension": dim_name}]
        
        # Penalize critical dimensions if no experience section
        critical_dimensions = ['skill_alignment', 'tooling_match', 'domain_relevance', 'level_appropriateness', 'impact', 'evidence']
        if dim_name in critical_dimensions and len(experience_bullets) == 0:
            return 1.0, [{"issue": "No work experience section found", "dimension": dim_name, "context": "Resume must have work experience for this role"}]
        
        # Penalize if very few experience bullets (< 3)
        if dim_name in critical_dimensions and len(experience_bullets) < 3:
            return 1.5, [{"issue": f"Insufficient work experience ({len(experience_bullets)} bullets)", "dimension": dim_name, "context": "Need at least 3 experience bullets for meaningful evaluation"}]
        
        # Run checks based on dimension signals
        failed_checks = []
        
        for signal in dim_config["signals"]:
            check_failures = self._run_signal_check(
                signal,
                dim_name,
                all_bullets
            )
            failed_checks.extend(check_failures)
        
        # Calculate score based on pass rate
        total_checks = len(dim_config["signals"]) * max(1, len(all_bullets))
        failed_count = len(failed_checks)
        pass_rate = 1.0 - (failed_count / total_checks)
        
        # Apply content quantity penalty for critical dimensions
        content_penalty = 1.0
        if dim_name in ['skill_alignment', 'tooling_match', 'domain_relevance', 'impact', 'evidence']:
            if len(experience_bullets) < 5:
                content_penalty = 0.7  # 30% penalty for sparse content
            elif len(experience_bullets) < 8:
                content_penalty = 0.85  # 15% penalty
        
        # Map pass rate to 1-5 scale (more strict thresholds)
        if pass_rate >= 0.95:
            base_score = 5.0
        elif pass_rate >= 0.85:
            base_score = 4.0
        elif pass_rate >= 0.7:
            base_score = 3.0
        elif pass_rate >= 0.5:
            base_score = 2.0
        else:
            base_score = 1.0
        
        # Apply content penalty
        final_score = max(1.0, base_score * content_penalty)
        
        return final_score, failed_checks
    
    def _run_signal_check(
        self,
        signal: str,
        dimension: str,
        bullets: List[ResumeBullet]
    ) -> List[Dict]:
        """
        Run a specific signal check on bullets.
        
        Returns:
            List of failed check dictionaries
        """
        failed = []
        
        # Implement checks for each signal type
        if signal == "clear_action_verbs":
            for bullet in bullets:
                if not self._has_clear_action_verb(bullet.text):
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "Missing clear action verb",
                        "context": bullet.text[:100]
                    })
        
        elif signal == "has_metrics":
            for bullet in bullets:
                if not bullet.has_metric:
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "Missing quantifiable metrics",
                        "context": bullet.text[:100]
                    })
        
        elif signal == "specific_technologies":
            for bullet in bullets:
                if not bullet.tools or len(bullet.tools) == 0:
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "No specific technologies mentioned",
                        "context": bullet.text[:100]
                    })
        
        elif signal == "business_outcome":
            for bullet in bullets:
                if not self._has_business_outcome(bullet.text):
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "Missing business outcome or impact",
                        "context": bullet.text[:100]
                    })
        
        elif signal == "appropriate_length":
            for bullet in bullets:
                if len(bullet.text) > 200:  # Roughly 2-3 lines
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "Bullet too long (should be 1-2 lines)",
                        "context": bullet.text[:100]
                    })
        
        elif signal == "no_jargon_overload":
            for bullet in bullets:
                if self._has_jargon_overload(bullet.text):
                    failed.append({
                        "signal": signal,
                        "dimension": dimension,
                        "bullet_index": bullet.bullet_index,
                        "issue": "Too much jargon or buzzwords",
                        "context": bullet.text[:100]
                    })
        
        # New skill/tool matching signals
        elif signal == "required_skills_present":
            # Check if resume mentions required skills from job
            all_text = " ".join([b.text.lower() for b in bullets])
            required_skills = ['python', 'java', 'c++', 'sql', 'database', 'backend', 'api']
            missing_skills = [skill for skill in required_skills if skill not in all_text]
            if len(missing_skills) > len(required_skills) * 0.5:  # Missing >50% of required
                failed.append({
                    "signal": signal,
                    "dimension": dimension,
                    "issue": f"Missing critical skills: {', '.join(missing_skills[:3])}",
                    "context": "Required skills not found in resume"
                })
        
        elif signal == "exact_tool_match":
            # Check for specific tools mentioned in job
            all_tools = set()
            for bullet in bullets:
                if bullet.tools:
                    all_tools.update([t.lower() for t in bullet.tools])
            
            common_tools = ['docker', 'kubernetes', 'aws', 'gcp', 'redis', 'postgresql', 'git']
            tool_mentions = sum(1 for tool in common_tools if tool in all_tools)
            if tool_mentions == 0:
                failed.append({
                    "signal": signal,
                    "dimension": dimension,
                    "issue": "No modern development tools mentioned",
                    "context": "Resume should mention relevant tools and technologies"
                })
        
        elif signal == "demonstrated_tool_proficiency":
            # Check if tools are actually used in context, not just listed
            tools_in_bullets = sum(1 for b in bullets if b.tools and len(b.tools) > 0)
            if len(bullets) > 0 and tools_in_bullets / len(bullets) < 0.3:
                failed.append({
                    "signal": signal,
                    "dimension": dimension,
                    "issue": "Tools mentioned but not demonstrated in context",
                    "context": f"Only {tools_in_bullets}/{len(bullets)} bullets show tool usage"
                })
        
        return failed
    
    def _has_clear_action_verb(self, text: str) -> bool:
        """Check if text starts with a clear action verb."""
        strong_verbs = [
            "built", "developed", "designed", "implemented", "created",
            "led", "managed", "improved", "optimized", "reduced",
            "increased", "launched", "delivered", "architected", "established",
            "migrated", "automated", "scaled", "collaborated", "drove"
        ]
        
        text_lower = text.lower().strip()
        return any(text_lower.startswith(verb) for verb in strong_verbs)
    
    def _has_business_outcome(self, text: str) -> bool:
        """Check if text mentions business outcomes."""
        outcome_indicators = [
            "resulting in", "achieved", "improved", "reduced", "increased",
            "revenue", "cost", "efficiency", "user", "customer", "time",
            "performance", "conversion", "retention", "satisfaction"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in outcome_indicators)
    
    def _has_jargon_overload(self, text: str) -> bool:
        """Check if text has too many buzzwords without substance."""
        buzzwords = [
            "synergy", "leverage", "utilize", "dynamic", "innovative",
            "cutting-edge", "world-class", "best-in-class", "disruptive"
        ]
        
        text_lower = text.lower()
        buzzword_count = sum(1 for word in buzzwords if word in text_lower)
        
        # If more than 2 buzzwords in a single bullet, flag it
        return buzzword_count > 2
    
    def _calculate_overall_score(
        self,
        dimension_scores: Dict[str, Dict]
    ) -> float:
        """
        Calculate weighted overall score.
        
        Returns:
            Score from 1.0 to 5.0
        """
        if not dimension_scores:
            return 1.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for dim_data in dimension_scores.values():
            score = dim_data["score"]
            weight = dim_data["weight"]
            total_weighted_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 1.0
        
        overall = total_weighted_score / total_weight
        return round(overall, 2)
    
    def _generate_recommendations(
        self,
        dimension_scores: Dict[str, Dict],
        failed_checks: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on evaluation.
        
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            "top_priorities": [],
            "dimension_feedback": {},
            "quick_wins": []
        }
        
        # Find dimensions with lowest scores
        sorted_dims = sorted(
            dimension_scores.items(),
            key=lambda x: x[1]["score"]
        )
        
        # Top 3 priorities (lowest scoring dimensions)
        for dim_name, dim_data in sorted_dims[:3]:
            if dim_data["score"] < 4.0:
                dimension = get_dimension(dim_name)
                recommendations["top_priorities"].append({
                    "dimension": dim_name,
                    "score": dim_data["score"],
                    "advice": dimension.feedback_templates[0] if dimension.feedback_templates else "Improve this dimension"
                })
        
        # Dimension-specific feedback
        for dim_name, dim_data in dimension_scores.items():
            if dim_data["failed_checks"]:
                recommendations["dimension_feedback"][dim_name] = {
                    "score": dim_data["score"],
                    "failed_count": len(dim_data["failed_checks"]),
                    "sample_issues": [
                        check["issue"] for check in dim_data["failed_checks"][:3]
                    ]
                }
        
        # Quick wins (common issues that are easy to fix)
        quick_win_signals = ["has_metrics", "specific_technologies", "appropriate_length"]
        for check in failed_checks:
            if check.get("signal") in quick_win_signals:
                recommendations["quick_wins"].append({
                    "bullet_index": check.get("bullet_index"),
                    "issue": check["issue"],
                    "fix": f"Address {check['signal']}"
                })
        
        # Limit quick wins to top 5
        recommendations["quick_wins"] = recommendations["quick_wins"][:5]
        
        return recommendations
