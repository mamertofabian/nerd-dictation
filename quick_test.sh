#!/bin/bash
# Quick test script to verify LLM integration is working

echo "Testing nerd-dictation with LLM integration..."
echo "This will simulate a dictation session with intentional errors"

# Create a temporary audio-like test by using the configuration directly
python3 -c "
import sys
sys.path.insert(0, '/home/atomrem/.config/nerd-dictation')
import importlib.util

# Load config
spec = importlib.util.spec_from_file_location('config', '/home/atomrem/.config/nerd-dictation/nerd-dictation.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# Test with a sentence that has obvious errors
test_text = 'this are a test and i want to by some groceries'
result = config.nerd_dictation_process(test_text)
print(f'Original: {test_text}')
print(f'Processed: {result}')
print('✓ LLM integration is active!' if result != test_text else '✗ No LLM processing detected')
"