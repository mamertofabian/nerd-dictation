# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**nerd-dictation** is an offline speech-to-text utility for desktop Linux using the VOSK-API. It provides manual activation speech recognition without background processes, designed as a single-file Python script with minimal dependencies.

## Architecture

**Single-File Design**: The main application (`nerd-dictation`) is a single executable Python file containing all core functionality. This design prioritizes hackability and simplicity.

**Configuration System**: User configuration is handled through Python scripts at `~/.config/nerd-dictation/nerd-dictation.py` that can manipulate text using Python's full feature set.

**External Dependencies**: 
- VOSK-API for speech recognition
- Audio recording utilities (parec, sox, or pw-cat)
- Input simulation tools (xdotool, ydotool, dotool, or wtype)

## Development Commands

**Code Quality**:
```bash
# Format code
black nerd-dictation

# Type checking
mypy --strict nerd-dictation

# Linting
pylint nerd-dictation --disable=C0103,C0111,C0301,C0302,C0415,E0401,E0611,I1101,R0801,R0902,R0903,R0912,R0913,R0914,R0915,R1705,W0212,W0703
```

**Testing**:
```bash
# Run number conversion tests
./tests/from_words_to_digits.py

# Test dictation functionality
./nerd-dictation begin --vosk-model-dir=./model &
./nerd-dictation end
```

**Setup for Development**:
```bash
# Install dependencies
pip3 install vosk

# Download and setup model
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
```

## Code Conventions

- All messages must be displayed via `sys.stderr` to keep `sys.stdout` clean for text output
- Recording should start as quickly as possible - delay expensive imports like `vosk` until after recording begins
- Only built-in Python modules are used (except for `vosk`)
- Type hints are required for all functions
- Line length: 119 characters (configured in pyproject.toml)

## Key Components

**Command Structure**: The application uses subcommands (begin, end, cancel, suspend, resume) managed through argparse.

**User Configuration**: Examples are provided in the `examples/` directory showing different configuration approaches:
- `default/`: Basic word replacement
- `begin_end_commands/`: Custom start/finish commands  
- `vosk_grammar/`: Grammar-restricted recognition
- `language_tool_auto_grammar/`: Grammar integration

**Text Processing**: Core functionality includes number-to-digit conversion, punctuation handling, and user-defined text manipulation through configuration scripts.