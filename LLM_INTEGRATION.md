# LLM Integration for nerd-dictation

This setup provides local LLM post-processing for speech-to-text output using Ollama, creating a two-stage pipeline: **speech-to-text → LLM correction → final output**.

## Benefits

- **Grammar correction**: Fixes common speech recognition grammar errors
- **Pronunciation correction**: Corrects words that sound similar but are wrong (e.g., "by" → "buy")
- **Natural improvements**: Makes text sound more natural and fluent
- **Privacy-focused**: Uses local LLM (no data sent to external services)
- **Seamless integration**: Works with nerd-dictation's existing workflow

## Setup

### Prerequisites

1. **nerd-dictation** installed and working
2. **Ollama** installed and running
3. **mistral:7b-instruct** model downloaded

### Installation Steps

1. **Install and start Ollama:**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model
   ollama pull mistral:7b-instruct
   
   # Start Ollama server
   ollama serve
   ```

2. **The configuration file is already created at:**
   ```
   ~/.config/nerd-dictation/nerd-dictation.py
   ```

3. **Test the integration:**
   ```bash
   python3 test_llm_integration.py
   ```

## Usage

The setup works seamlessly with nerd-dictation's normal workflow:

```bash
# Start dictation
nerd-dictation begin

# Speak your text (with any grammar errors or mispronunciations)
# Example: "this are a test and i want to by some groceries"

# End dictation - text will be processed through LLM before output
nerd-dictation end
# Result: "This is a test, and I want to buy some groceries."
```

## Configuration Options

Edit `~/.config/nerd-dictation/nerd-dictation.py` to customize:

```python
# LLM settings
LLM_ENABLED = True              # Enable/disable LLM processing
LLM_MIN_WORDS = 3              # Only process text with 3+ words
OLLAMA_TIMEOUT = 10            # Timeout for LLM requests (seconds)
OLLAMA_MODEL = "mistral:7b-instruct"  # Model to use
```

## How It Works

1. **Speech Recognition**: nerd-dictation captures audio and converts to text using VOSK
2. **Basic Processing**: Traditional text replacements (punctuation, word corrections)
3. **LLM Enhancement**: Local LLM corrects grammar and pronunciation errors
4. **Output**: Final corrected text is typed/output

## Troubleshooting

**LLM not working:**
- Check Ollama is running: `ollama ps`
- Verify model is available: `ollama list`
- Test Ollama directly: `ollama run mistral:7b-instruct "correct this: i are happy"`

**Slow performance:**
- Use a smaller model: `ollama pull mistral:7b-instruct-q4_0`
- Reduce timeout: set `OLLAMA_TIMEOUT = 5`
- Disable for short text: increase `LLM_MIN_WORDS = 5`

**Too many changes:**
- The LLM may occasionally be overly creative
- Disable with `LLM_ENABLED = False` if needed
- The system falls back to original text on errors

## Example Corrections

| Original (Speech Recognition) | LLM Corrected |
|------------------------------|---------------|
| "this are a test" | "This is a test" |
| "i want to by groceries" | "I want to buy groceries" |
| "there car is red" | "Their car is red" |
| "can you help me with this problem that i having" | "Can you help me with this problem I'm having?" |

## Architecture Advantage

This approach is much cleaner than the original script because it:
- ✅ Uses nerd-dictation's built-in configuration system
- ✅ Integrates seamlessly with the existing workflow
- ✅ Follows nerd-dictation's architecture patterns
- ✅ Handles errors gracefully with fallbacks
- ❌ No subprocess complexity
- ❌ No manual workflow steps
- ❌ No incorrect `nerd-dictation end` calls