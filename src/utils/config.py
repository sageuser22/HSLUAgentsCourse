"""
Utility module for OpenAI API configuration and client setup.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_openai_client():
    """
    Initialize and return an OpenAI client.
    
    Returns:
        OpenAI: Configured OpenAI client instance
    
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in your .env file or environment."
        )
    return OpenAI(api_key=api_key)


def get_model_name():
    """
    Get the model name from environment or use default.
    
    Returns:
        str: Model name to use for API calls
    """
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_temperature():
    """
    Get the temperature setting from environment or use default.
    
    Returns:
        float: Temperature value for generation
    """
    return float(os.getenv("TEMPERATURE", "0.7"))
