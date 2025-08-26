#!/usr/bin/env python3
"""
Test script to verify LLM integration doesn't repeatedly process during progressive typing
"""

import sys
import os
import importlib.util

# Load config
config_path = os.path.expanduser('~/.config/nerd-dictation/nerd-dictation.py')
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

print("Testing progressive typing scenario...")
print("This simulates how nerd-dictation processes text during live dictation")
print("=" * 70)

# Simulate progressive text building (like during live dictation)
progressive_texts = [
    "this are",
    "this are a", 
    "this are a test",
    "this are a test and",
    "this are a test and i",
    "this are a test and i want",
    "this are a test and i want to",
    "this are a test and i want to by",
    "this are a test and i want to by groceries"
]

print("Simulating progressive typing...")
for i, text in enumerate(progressive_texts):
    result = config.nerd_dictation_process(text)
    print(f"Step {i+1:2d}: '{text}' → '{result}'")

print("\nTesting same text multiple times (should use cache)...")
test_text = "this are a test"
for i in range(3):
    result = config.nerd_dictation_process(test_text)
    print(f"Call {i+1}: '{test_text}' → '{result}'")

print("\n✓ Progressive typing test completed!")
print("Look for 'LLM improved' messages in the output above.")
print("Each unique text should only be processed once by the LLM.")