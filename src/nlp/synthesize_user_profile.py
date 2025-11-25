import os
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from src.nlp.prompts import user_profile_synthesizer_prompt

logger = logging.getLogger(__name__)

# Try to initialize Google Gemini first, fall back to OpenAI if needed
try:
    _llm = ChatGoogleGenerativeAI(
        temperature=0, 
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        timeout=120,
        max_retries=2
    )
    _using_openai = False
    logger.info("Using Google Gemini model for profile synthesis")
except Exception as e:
    logger.warning(f"Failed to initialize Google Gemini: {e}. Falling back to OpenAI.")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY is configured")
    
    _llm = ChatOpenAI(
        temperature=0,
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        timeout=120,
        max_retries=2
    )
    _using_openai = True
    logger.info("Using OpenAI model for profile synthesis")

_prompt_template = PromptTemplate.from_template(user_profile_synthesizer_prompt)
_output_parser = StrOutputParser()

class LLMAnalysisResult(BaseModel):
    user_profile_summary: str
    user_profile_metadata: str

# Construct the chain
_profile_synthesis_chain = _prompt_template | _llm.with_structured_output(LLMAnalysisResult)

def get_llm_profile_synthesis(
    user_messages_str: str,
    existing_metadata_json_str: str,
    existing_summary_text: str
) -> str:
    """
    Invokes an LLM chain to synthesize a user profile based on messages and existing data.

    Args:
        user_messages_str: A string containing formatted user messages
        existing_metadata_json_str: A JSON string of the user's existing metadata profile.
        existing_summary_text: A string of the user's existing context summary.

    Returns:
        The raw string response from the LLM.
    """
    
    try:
        response_content = _profile_synthesis_chain.invoke({
            "existing_metadata_json": existing_metadata_json_str,
            "existing_summary_text": existing_summary_text,
            "user_messages_chronological": user_messages_str
        })
        return response_content
    except Exception as e:
        # If we're already using OpenAI or if OpenAI is not available, re-raise the error
        if _using_openai or not os.getenv("OPENAI_API_KEY"):
            logger.error(f"Profile synthesis failed: {e}")
            raise
        
        # Try with OpenAI as backup
        logger.warning(f"Primary model failed: {e}. Attempting with OpenAI backup.")
        
        backup_llm = ChatOpenAI(
            temperature=0,
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            timeout=120,
            max_retries=2
        )
        backup_chain = _prompt_template | backup_llm.with_structured_output(LLMAnalysisResult)
        
        try:
            response_content = backup_chain.invoke({
                "existing_metadata_json": existing_metadata_json_str,
                "existing_summary_text": existing_summary_text,
                "user_messages_chronological": user_messages_str
            })
            logger.info("Successfully used OpenAI backup for profile synthesis")
            return response_content
        except Exception as backup_error:
            logger.error(f"Both primary and backup models failed: {backup_error}")
            raise



if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    sample_user_id = "00000000-0000-0000-0000-000000000000"
    
    mock_user_messages = (
        "Timestamp: 2025-05-29T10:00:00Z\nUser: Hello, I'm Arda and im interested in AI.\n\n" 
        "---\n\nTimestamp: 2025-05-29T10:05:00Z\nUser: Specifically, I want to learn about Langchain."
        "---\n\nTimestamp: 2025-05-29T10:10:00Z\nUser: I'm also interested in AI ethics."
        "---\n\nTimestamp: 2025-05-29T10:15:00Z\nUser: I like playing tennis."
        "---\n\nTimestamp: 2025-05-29T10:15:00Z\nUser: I hate watching cinema."
    )
    mock_existing_metadata = ''
    mock_existing_summary = "User previously expressed interest in photography."

    print(f"Synthesizing profile for user based on new messages...")
    raw_llm_response = get_llm_profile_synthesis(
        user_messages_str=mock_user_messages,
        existing_metadata_json_str=mock_existing_metadata,
        existing_summary_text=mock_existing_summary
    )

    print("\n--- Raw LLM Response ---")
    print(raw_llm_response.user_profile_summary)
    print(raw_llm_response.user_profile_metadata)