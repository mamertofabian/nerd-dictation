#!/usr/bin/env python3
"""
Test script to verify the more conservative LLM prompt behavior
"""

import sys
import os
import importlib.util

# Load config
config_path = os.path.expanduser('~/.config/nerd-dictation/nerd-dictation.py')
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

print("Testing Conservative LLM Prompt")
print("=" * 40)

# Test cases to ensure LLM is not overly aggressive
conservative_test_cases = [
    # Cases that should be corrected (clear errors)
    "this are a clear grammar error",
    "i want to by some groceries", 
    "we was going to the store",
    
    # Cases that should be minimally changed or unchanged
    "create a react component",
    "initialize git repository",
    "const api equals fetch url",
    "use arrow function syntax",
    "run npm install command",
    "the server is responding correctly", 
    "deploy to production environment",
    "implement authentication middleware",
    "configure database connection",
    "optimize query performance",
]

print("Testing conservative corrections...")
print()

for i, test_text in enumerate(conservative_test_cases, 1):
    print(f"Test {i:2d}: {test_text}")
    
    try:
        processed_text = config.nerd_dictation_process(test_text)
        print(f"Result:  {processed_text}")
        
        # Check if changes were minimal or appropriate
        if processed_text != test_text:
            word_diff = len(processed_text.split()) - len(test_text.split())
            if abs(word_diff) <= 2:  # Allow small changes
                print("✓ Minimal correction applied")
            else:
                print("⚠ Significant changes made - may be too aggressive")
        else:
            print("- No changes (appropriate for good text)")
        
        print("-" * 30)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("-" * 30)

print()
print("Conservative Prompt Guidelines:")
print("✓ Only fix obvious grammar errors")
print("✓ Preserve technical terminology") 
print("✓ Minimal changes to good text")
print("✓ Maintain original meaning and style")
print("✓ Lower temperature for consistency")