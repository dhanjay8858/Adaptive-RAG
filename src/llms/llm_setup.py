"""
LLM initialization and configuration with fallback support.
"""

from typing import Any
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from src.core.config import settings

# Initialize individual LLMs
groq_llm = ChatGroq(model=settings.PRIMARY_MODEL)

gemini_llm = ChatGoogleGenerativeAI(model=settings.FALLBACK_MODEL)

ollama_llm = ChatOllama(
    model=settings.LOCAL_MODEL, 
    base_url=settings.OLLAMA_BASE_URL
)

# Create standard fallback chain
# Groq -> Gemini -> Ollama
llm = groq_llm.with_fallbacks([gemini_llm, ollama_llm])

def get_structured_llm(schema: Any):
    """
    Helper function to apply structured output schema to each LLM 
    before creating the fallback chain.
    """
    structured_groq = groq_llm.with_structured_output(schema)
    structured_gemini = gemini_llm.with_structured_output(schema)
    structured_ollama = ollama_llm.with_structured_output(schema)
    
    return structured_groq.with_fallbacks([structured_gemini, structured_ollama])
