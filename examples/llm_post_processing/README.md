# LLM Post-Processing Configuration

This directory contains a nerd-dictation configuration that integrates local LLM post-processing for grammar correction and text improvement using Ollama.

## Overview

This configuration creates a two-stage speech-to-text pipeline:
1. **VOSK Speech Recognition** → Raw text with potential errors
2. **Local LLM Processing** → Grammar-corrected, improved text
3. **Final Output** → Clean, natural text

## Features

- ✅ **Grammar correction**: Fixes speech recognition grammar errors
- ✅ **Pronunciation correction**: Corrects similar-sounding words (e.g., "by" → "buy")  
- ✅ **Smart caching**: Prevents repeated processing during progressive typing
- ✅ **Privacy-focused**: Uses local Ollama LLM (no external API calls)
- ✅ **Fallback handling**: Gracefully handles LLM failures
- ✅ **Memory management**: Cache size limits prevent memory issues

## Prerequisites

1. **nerd-dictation** installed and working
2. **Ollama** installed and running
3. **mistral:7b-instruct** model available

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull mistral:7b-instruct

# Start Ollama server
ollama serve
```

## Development Workflow

### During Development
The active configuration is located at:
```
~/.config/nerd-dictation/nerd-dictation.py
```

This is where you make changes and test the integration. The configuration is automatically loaded by nerd-dictation.

### Updating the Repository
When development is complete and the configuration is stable:

```bash
# Copy the working configuration to the project
cp ~/.config/nerd-dictation/nerd-dictation.py examples/llm_post_processing/nerd-dictation.py

# Commit the changes
git add examples/llm_post_processing/nerd-dictation.py
git commit -m "Update: LLM post-processing configuration"
```

### Installation from Repository
To use this configuration:

```bash
# Copy from repository to user config
cp examples/llm_post_processing/nerd-dictation.py ~/.config/nerd-dictation/nerd-dictation.py
```

## Configuration Options

Edit the configuration file to customize behavior:

```python
# LLM settings
LLM_ENABLED = True                    # Enable/disable LLM processing
LLM_MIN_WORDS = 3                    # Only process text with 3+ words  
OLLAMA_TIMEOUT = 10                  # Timeout for LLM requests (seconds)
OLLAMA_MODEL = "mistral:7b-instruct"  # Model to use
LLM_CACHE_MAX_SIZE = 100             # Cache size limit
```

## Usage

The configuration works seamlessly with nerd-dictation's normal workflow:

```bash
# Start dictation (no changes needed to your existing shortcuts)
nerd-dictation begin

# Speak with any errors: "this are a test and i want to by groceries"
# End dictation - LLM processing happens automatically  
nerd-dictation end

# Result: "This is a test, and I want to buy groceries."
```

## Testing

Test the configuration:

```bash
# Test basic functionality
python3 test_llm_integration.py

# Test progressive typing behavior
python3 test_progressive.py

# Quick verification
./quick_test.sh
```

## Troubleshooting

**LLM not processing:**
- Check Ollama is running: `ollama ps`
- Verify model is available: `ollama list`
- Test Ollama directly: `ollama run mistral:7b-instruct "fix: i are happy"`

**Performance issues:**
- Use smaller model: `ollama pull mistral:7b-instruct-q4_0`
- Reduce timeout: `OLLAMA_TIMEOUT = 5`
- Increase minimum words: `LLM_MIN_WORDS = 5`

**Memory issues:**
- Reduce cache size: `LLM_CACHE_MAX_SIZE = 50`

## Example Corrections

| Original Speech Recognition | LLM Corrected |
|---------------------------|--------------|
| "this are a test" | "This is a test" |
| "i want to by groceries" | "I want to buy groceries" |
| "there car is red" | "Their car is red" |
| "can you help me with this problem that i having" | "Can you help me with this problem I'm having?" |

## Architecture

This configuration follows nerd-dictation's built-in configuration system:
- Integrates with the existing `nerd_dictation_process()` function
- Applies traditional text processing first (punctuation, word replacements)
- Then applies LLM improvements as a final step
- Handles progressive typing without repeated LLM processing
- Includes proper error handling and fallbacks

## Comparison with External Approaches

Unlike running nerd-dictation as a subprocess, this approach:
- ✅ Uses nerd-dictation's native configuration system
- ✅ Integrates seamlessly with existing workflows  
- ✅ Handles progressive typing correctly
- ✅ Follows project architecture patterns
- ❌ No subprocess complexity or workflow changes needed