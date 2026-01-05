"""
LLM client for bounded and validated interactions.

Uses OpenAI API with JSON schema validation.
"""
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
import json
from app.core.config import settings
from openai import OpenAI

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """Client for bounded LLM interactions with validation."""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.LLM_MODEL
    
    def extract_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        """
        Extract structured data from LLM with validation.
        
        Args:
            prompt: User prompt
            response_model: Pydantic model for response validation
            system_prompt: Optional system prompt
            temperature: LLM temperature (default 0 for determinism)
        
        Returns:
            Validated instance of response_model
        
        Raises:
            ValidationError if LLM output doesn't match schema
            ValueError if LLM fails to produce valid JSON
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        try:
            data = json.loads(content)
            return response_model(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")
        except ValidationError as e:
            raise ValidationError(f"LLM output validation failed: {e}")
    
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate free-form text (for explanations).
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content


# Global client instance
llm_client = LLMClient()
