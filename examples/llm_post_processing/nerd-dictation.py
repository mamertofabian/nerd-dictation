# User configuration file with LLM post-processing
# Located at ~/.config/nerd-dictation/nerd-dictation.py

import re
import requests
import json
import sys

# -----------------------------------------------------------------------------
# LLM Post-Processing Configuration

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_TIMEOUT = 10  # seconds

# LLM post-processing settings
LLM_ENABLED = True
LLM_MIN_WORDS = 3  # Only process with LLM if text has at least this many words

# Cache to prevent multiple LLM processing of the same text
_llm_cache = {}
_last_processed_text = ""
LLM_CACHE_MAX_SIZE = 100  # Limit cache size to prevent memory issues

def improve_text_with_llm(text: str) -> str:
    """Send text to local Ollama for grammar correction and improvement"""
    
    if not LLM_ENABLED:
        return text
        
    # Skip LLM processing for very short text
    if len(text.split()) < LLM_MIN_WORDS:
        return text
    
    # Check cache to avoid reprocessing the same text
    if text in _llm_cache:
        return _llm_cache[text]
    
    prompt = f"""Fix grammar errors and pronunciation mistakes in this dictated text. Return ONLY the corrected text with no explanations, notes, or commentary.

Input: {text}
Output:"""
    
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for consistent corrections
            "top_p": 0.9,
            "num_predict": 256,  # Limit response length
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
# Traditional Text Processing (from default example)

# Replace Multiple Words
TEXT_REPLACE_REGEX = (
    ("\\b" "data type" "\\b", "data-type"),
    ("\\b" "copy on write" "\\b", "copy-on-write"),
    ("\\b" "key word" "\\b", "keyword"),
)
TEXT_REPLACE_REGEX = tuple(
    (re.compile(match), replacement)
    for (match, replacement) in TEXT_REPLACE_REGEX
)

# Replace Single Words
WORD_REPLACE = {
    "i": "I",
    "api": "API",
    "linux": "Linux",
    "um": "",
}

# Regular expressions for partial word replacement
WORD_REPLACE_REGEX = (
    ("^i'(.*)", "I'\\1"),
)
WORD_REPLACE_REGEX = tuple(
    (re.compile(match), replacement)
    for (match, replacement) in WORD_REPLACE_REGEX
)

# Add Punctuation
CLOSING_PUNCTUATION = {
    "period": ".",
    "comma": ",",
    "question mark": "?",
    "close quote": '"',
}

OPENING_PUNCTUATION = {
    "open quote": '"',
}

# -----------------------------------------------------------------------------
# Main Processing Function

def nerd_dictation_process(text: str) -> str:
    """
    Main text processing function that integrates LLM post-processing
    with traditional text replacement and punctuation handling.
    """
    global _last_processed_text
    
    # First, apply basic text replacements (pre-LLM processing)
    for match, replacement in TEXT_REPLACE_REGEX:
        text = match.sub(replacement, text)
    
    # Apply punctuation replacements
    for match, replacement in CLOSING_PUNCTUATION.items():
        text = text.replace(" " + match, replacement)
    
    for match, replacement in OPENING_PUNCTUATION.items():
        text = text.replace(match + " ", replacement)
    
    # Apply word replacements
    words = text.split(" ")
    for i, w in enumerate(words):
        w_init = w
        w_test = WORD_REPLACE.get(w)
        if w_test is not None:
            w = w_test
        if w_init == w:
            for match, replacement in WORD_REPLACE_REGEX:
                w_test = match.sub(replacement, w)
                if w_test != w:
                    w = w_test
                    break
        words[i] = w
    
    # Strip any words that were replaced with empty strings
    words[:] = [w for w in words if w]
    text = " ".join(words)
    
    # Only apply LLM processing if this is a new/different text
    # This prevents multiple processing during progressive typing
    if text != _last_processed_text and text.strip():
        text = improve_text_with_llm(text)
        _last_processed_text = text
    
    return text