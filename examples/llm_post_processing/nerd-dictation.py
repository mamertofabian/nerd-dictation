# User configuration file with LLM post-processing
# Located at ~/.config/nerd-dictation/nerd-dictation.py

import re
import requests
import json
import sys
import time

# -----------------------------------------------------------------------------
# LLM Post-Processing Configuration

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_MODEL = "phi3.5:3.8b-mini-instruct-q6_K"
OLLAMA_TIMEOUT = 10  # seconds

# LLM post-processing settings
LLM_ENABLED = True
LLM_MIN_WORDS = 3  # Only process with LLM if text has at least this many words

# Cache to prevent multiple LLM processing of the same text
_llm_cache = {}  # Cleared cache for conservative prompt
_last_processed_text = ""
LLM_CACHE_MAX_SIZE = 100  # Limit cache size to prevent memory issues

# Debouncing to prevent rapid LLM calls
_last_llm_call_time = 0
LLM_DEBOUNCE_DELAY = 2  # 2000ms minimum between LLM calls

# Progressive text detection
_last_llm_processed_text = ""
MIN_TEXT_LENGTH_FOR_LLM = 15  # Minimum characters before considering LLM processing

def should_process_with_llm(text: str) -> bool:
    """Determine if text should be processed with LLM"""
    global _last_llm_processed_text
    
    # Skip very short text
    if len(text.split()) < LLM_MIN_WORDS or len(text) < MIN_TEXT_LENGTH_FOR_LLM:
        return False
    
    # Skip if this looks like progressive typing of previously processed text
    if _last_llm_processed_text and text.startswith(_last_llm_processed_text.rstrip('.,!?')):
        # This appears to be an extension of previously processed text
        return False
    
    # Skip if this looks like a substring of what we just processed
    if _last_llm_processed_text and _last_llm_processed_text.startswith(text.rstrip('.,!?')):
        return False
        
    return True

def improve_text_with_llm(text: str) -> str:
    """Send text to local Ollama for grammar correction and improvement"""
    global _last_llm_call_time, _last_llm_processed_text
    
    if not LLM_ENABLED:
        return text
        
    # Check if we should process this text
    if not should_process_with_llm(text):
        return text
    
    # Debouncing: prevent rapid successive LLM calls
    current_time = time.time()
    if current_time - _last_llm_call_time < LLM_DEBOUNCE_DELAY:
        return text
    _last_llm_call_time = current_time
    
    # Check cache to avoid reprocessing the same text
    if text in _llm_cache:
        return _llm_cache[text]
    
    prompt = f"""
    You are a helpful assistant that fixes speech recognition errors.
    
    You will be given a text (partial or full sentence) that has been transcribed from speech by a software engineer who is not a native English speaker.
    
    Your task is to fix only obvious speech recognition errors.
    
    DO NOT change technical terms, proper nouns, or already correct formatting.

    Return the same text with only minimal speech recognition fixes.

Text: {text}
Fixed:"""
    
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Extremely low temperature for conservative corrections
            "top_p": 0.7,
            "num_predict": 128,  # Shorter responses to prevent over-elaboration
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, 
                               json=data, 
                               timeout=OLLAMA_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            improved_text = result["response"].strip()
            
            # Basic validation and cleanup
            if improved_text and len(improved_text) > 0:
                # Remove any quotes that might have been added by the LLM
                improved_text = improved_text.strip('"\'')
                
                # Remove common unwanted commentary patterns
                import re
                # Remove text in parentheses that contains explanatory words
                improved_text = re.sub(r'\s*\([^)]*(?:changes needed|pronunciation|grammar|correct)[^)]*\)', '', improved_text, flags=re.IGNORECASE)
                # Remove sentences that start with explanatory phrases
                improved_text = re.sub(r'\s*(No changes needed|Pronunciation:|Grammar:|Note:)[^.]*\.?', '', improved_text, flags=re.IGNORECASE)
                
                # Clean up extra whitespace
                improved_text = ' '.join(improved_text.split())
                
                # Validate that the result isn't too different in length or empty
                if improved_text and 0.3 <= len(improved_text) <= len(text) * 2:
                    # Cache the result (with size limit)
                    if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                        # Remove oldest entry (simple FIFO)
                        _llm_cache.pop(next(iter(_llm_cache)))
                    _llm_cache[text] = improved_text
                    
                    # Log the improvement to stderr for debugging (optional)
                    if improved_text != text:
                        print(f"LLM improved: '{text}' → '{improved_text}'", file=sys.stderr)
                    
                    # Update last processed text tracking
                    _last_llm_processed_text = improved_text
                    return improved_text
                else:
                    # Validation failed, fall back to original text
                    print(f"LLM output validation failed, using original: '{text}'", file=sys.stderr)
                    # Cache the fallback too (with size limit)
                    if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                        _llm_cache.pop(next(iter(_llm_cache)))
                    _llm_cache[text] = text
                    return text
            else:
                return text
        else:
            print(f"LLM API error: {response.status_code}", file=sys.stderr)
            # Cache the fallback (with size limit)
            if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
                _llm_cache.pop(next(iter(_llm_cache)))
            _llm_cache[text] = text
            return text
    except Exception as e:
        print(f"LLM processing failed: {e}", file=sys.stderr)
        # Cache the fallback (with size limit)
        if len(_llm_cache) >= LLM_CACHE_MAX_SIZE:
            _llm_cache.pop(next(iter(_llm_cache)))
        _llm_cache[text] = text
        return text

# -----------------------------------------------------------------------------
# Main Processing Function

def nerd_dictation_process(text: str) -> str:
    """
    Main text processing function with LLM.
    LLM handles grammar on raw speech.
    """
    global _last_processed_text
    
    # Store original text for cache comparison
    original_text = text
    
    # Apply LLM processing to raw dictated text
    if original_text != _last_processed_text and original_text.strip():
        text = improve_text_with_llm(text)
        _last_processed_text = original_text  # Use original for comparison
    
    return text
