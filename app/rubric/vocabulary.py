"""
Vocabulary tags for job posting analysis.

Fixed dictionary mapping terms to category tags.
"""
from typing import Dict, List

# Vocabulary dictionary: term -> tags
VOCABULARY: Dict[str, List[str]] = {
    # Infrastructure
    "docker": ["infra", "devops"],
    "kubernetes": ["infra", "devops", "cloud"],
    "k8s": ["infra", "devops", "cloud"],
    "terraform": ["infra", "iac"],
    "ansible": ["infra", "iac"],
    "jenkins": ["infra", "cicd"],
    "gitlab": ["infra", "cicd"],
    "circleci": ["infra", "cicd"],
    "github actions": ["infra", "cicd"],
    
    # Cloud
    "aws": ["cloud"],
    "amazon web services": ["cloud"],
    "gcp": ["cloud"],
    "google cloud": ["cloud"],
    "azure": ["cloud"],
    "cloudflare": ["cloud"],
    "ec2": ["cloud"],
    "s3": ["cloud"],
    "lambda": ["cloud"],
    "rds": ["cloud"],
    
    # Backend
    "postgres": ["backend", "database"],
    "postgresql": ["backend", "database"],
    "mysql": ["backend", "database"],
    "mongodb": ["backend", "database"],
    "redis": ["backend", "cache"],
    "grpc": ["backend", "api"],
    "rest api": ["backend", "api"],
    "graphql": ["backend", "api"],
    "microservices": ["backend", "architecture"],
    "kafka": ["backend", "messaging"],
    "rabbitmq": ["backend", "messaging"],
    
    # Frontend
    "react": ["frontend"],
    "vue": ["frontend"],
    "angular": ["frontend"],
    "typescript": ["frontend", "backend"],
    "javascript": ["frontend", "backend"],
    "html": ["frontend"],
    "css": ["frontend"],
    "webpack": ["frontend", "build"],
    "next.js": ["frontend"],
    "nextjs": ["frontend"],
    
    # Data
    "metrics": ["data", "observability"],
    "experiments": ["data", "science"],
    "a/b test": ["data", "science"],
    "ab test": ["data", "science"],
    "a/b testing": ["data", "science"],
    "machine learning": ["data", "ml"],
    "ml": ["data", "ml"],
    "deep learning": ["data", "ml"],
    "neural network": ["data", "ml"],
    "data pipeline": ["data", "engineering"],
    "etl": ["data", "engineering"],
    "spark": ["data", "engineering"],
    "airflow": ["data", "engineering"],
    "sql": ["data", "backend"],
    "analytics": ["data"],
    "tableau": ["data", "visualization"],
    "looker": ["data", "visualization"],
    
    # Security
    "oauth": ["security", "auth"],
    "authentication": ["security", "auth"],
    "authorization": ["security", "auth"],
    "compliance": ["security", "governance"],
    "soc2": ["security", "compliance"],
    "gdpr": ["security", "compliance"],
    "hipaa": ["security", "compliance"],
    "threat": ["security"],
    "vulnerability": ["security"],
    "penetration test": ["security"],
    "security audit": ["security"],
    "encryption": ["security"],
    "ssl": ["security"],
    "tls": ["security"],
    
    # Research
    "paper": ["research"],
    "publication": ["research"],
    "conference": ["research"],
    "journal": ["research"],
    "phd": ["research"],
    "research": ["research"],
    "experiment": ["research", "data"],
    
    # Programming Languages
    "python": ["backend", "data"],
    "java": ["backend"],
    "go": ["backend"],
    "golang": ["backend"],
    "rust": ["backend"],
    "c++": ["backend", "systems"],
    "c#": ["backend"],
    "ruby": ["backend"],
    "php": ["backend"],
    "swift": ["mobile"],
    "kotlin": ["mobile"],
    "objective-c": ["mobile"],
    
    # Mobile
    "ios": ["mobile"],
    "android": ["mobile"],
    "mobile": ["mobile"],
    "react native": ["mobile"],
    "flutter": ["mobile"],
    
    # Testing
    "test": ["testing"],
    "testing": ["testing"],
    "pytest": ["testing"],
    "jest": ["testing"],
    "unit test": ["testing"],
    "integration test": ["testing"],
    "e2e": ["testing"],
    
    # Observability
    "monitoring": ["observability"],
    "logging": ["observability"],
    "tracing": ["observability"],
    "datadog": ["observability"],
    "prometheus": ["observability"],
    "grafana": ["observability"],
    "splunk": ["observability"],
    "new relic": ["observability"],
    
    # Leadership
    "lead": ["leadership"],
    "manage": ["leadership"],
    "mentor": ["leadership"],
    "team": ["collaboration"],
    "cross-functional": ["collaboration"],
}


def get_tags_for_term(term: str) -> List[str]:
    """Get tags for a given term (case-insensitive)."""
    return VOCABULARY.get(term.lower(), [])


def find_tags_in_text(text: str) -> Dict[str, List[str]]:
    """
    Find all vocabulary terms in text and return their tags.
    
    Returns:
        Dict mapping tag -> list of terms that triggered it
    """
    text_lower = text.lower()
    tag_sources: Dict[str, List[str]] = {}
    
    for term, tags in VOCABULARY.items():
        if term in text_lower:
            for tag in tags:
                if tag not in tag_sources:
                    tag_sources[tag] = []
                tag_sources[tag].append(term)
    
    return tag_sources
