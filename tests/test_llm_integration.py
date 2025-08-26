#!/usr/bin/env python3
"""
Test script to verify LLM integration with nerd-dictation
"""

import sys
import os

# Import the configuration file directly
config_path = os.path.expanduser('~/.config/nerd-dictation/nerd-dictation.py')

try:
    # Load the configuration module using importlib
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    
    # Test cases with deliberately imperfect grammar/speech recognition errors
    test_cases = [
        "this are a test of the speech to text system",
        "i want to create a new file called my document dot txt",
        "the weather is nice today and i am happy",
        "can you help me with this problem that i having",
        "hello world this is a simple test",
        "the quick brown fox jump over the lazy dog",
        "i need to by some groceries at the store",
        "there car is parked in the garage",
        "we was going to the movies but it was closed"
    ]
    
    print("Testing LLM integration with nerd-dictation configuration...")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original:  {test_text}")
        
        # Process through the nerd-dictation configuration
        processed_text = config.nerd_dictation_process(test_text)
        
        print(f"Processed: {processed_text}")
        
        if processed_text != test_text:
            print("✓ Text was modified by processing")
        else:
            print("- Text unchanged")
        
        print("-" * 40)
    
    print("\nConfiguration test completed successfully!")
    print("\nTo use with nerd-dictation:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Run: nerd-dictation begin")
    print("3. Speak your text")
    print("4. Run: nerd-dictation end")
    print("5. The text will be processed through the LLM before being typed")

except (ImportError, FileNotFoundError) as e:
    print(f"Error loading configuration: {e}")
    print("Make sure the configuration file exists at ~/.config/nerd-dictation/nerd-dictation.py")
except Exception as e:
    print(f"Error during testing: {e}")
    print("Check that Ollama is running and the mistral:7b-instruct model is available")