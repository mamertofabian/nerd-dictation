#!/usr/bin/env python3
"""
Test race conditions and progressive text handling in LLM configuration.
This test validates the LLM-first architecture with debouncing and progressive text detection.
"""

import sys
import os
import time
import threading
import unittest
import importlib.util
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the configuration
config_path = os.path.expanduser("~/.config/nerd-dictation/nerd-dictation.py")
if os.path.exists(config_path):
    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
else:
    print("Configuration file not found. Please ensure ~/.config/nerd-dictation/nerd-dictation.py exists")
    sys.exit(1)

class TestRaceConditions(unittest.TestCase):
    """Test race condition handling and progressive text processing."""
    
    def setUp(self):
        """Reset global state before each test."""
        config._last_processed_text = ""
        config._last_llm_processed_text = ""
        config._last_llm_call_time = 0
        config._llm_cache.clear()
        
    @patch('requests.post')
    def test_progressive_text_detection(self, mock_post):
        """Test that progressive text updates don't cause multiple LLM calls."""
        # Mock successful LLM response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is a test"}
        mock_post.return_value = mock_response
        
        # Simulate progressive typing
        texts = [
            "this are",           # Should NOT process (too short)
            "this are a",         # Should NOT process (too short) 
            "this are a test",    # Should process (first complete phrase)
            "this are a test and", # Should NOT process (extension)
            "this are a test and i want", # Should NOT process (extension)
        ]
        
        llm_call_count = 0
        original_improve = config.improve_text_with_llm
        
        def count_llm_calls(text):
            nonlocal llm_call_count
            result = original_improve(text)
            if mock_post.called and mock_post.call_count > llm_call_count:
                llm_call_count = mock_post.call_count
            return result
        
        config.improve_text_with_llm = count_llm_calls
        
        results = []
        for text in texts:
            result = config.nerd_dictation_process(text)
            results.append((text, result))
        
        # Should only call LLM once for the complete phrase
        self.assertLessEqual(llm_call_count, 1, "LLM should only be called once for progressive text")
        
        # Restore original function
        config.improve_text_with_llm = original_improve
        
    @patch('requests.post')
    def test_debouncing(self, mock_post):
        """Test that debouncing prevents rapid LLM calls."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is a test"}
        mock_post.return_value = mock_response
        
        # Make rapid calls
        texts = ["this are a test", "that was a test", "here is a test"]
        
        start_time = time.time()
        for text in texts:
            config.nerd_dictation_process(text)
        
        # Should be debounced - not all calls should go through
        # The exact count depends on timing, but it should be less than total texts
        self.assertLess(mock_post.call_count, len(texts), 
                       "Debouncing should prevent all rapid calls from reaching LLM")
                       
    def test_cache_effectiveness(self):
        """Test that caching prevents duplicate LLM processing."""
        # Mock the LLM function to track calls
        call_count = 0
        original_improve = config.improve_text_with_llm
        
        def mock_improve(text):
            nonlocal call_count
            call_count += 1
            return text.replace("this are", "this is")
        
        config.improve_text_with_llm = mock_improve
        
        # Process same text multiple times
        test_text = "this are a test for caching"
        
        for _ in range(3):
            config.nerd_dictation_process(test_text)
        
        # Should only call LLM once due to caching
        self.assertEqual(call_count, 1, "Cache should prevent duplicate LLM calls")
        
        # Restore original function
        config.improve_text_with_llm = original_improve
        
    def test_progressive_substring_handling(self):
        """Test handling of text that looks like progressive extensions."""
        # Set up initial processed text
        config._last_llm_processed_text = "I need to create a file"
        
        # Test extensions of the processed text
        extensions = [
            "I need to create a file called",
            "I need to create a file called test.py",
            "I need to create a file called test.py in the project"
        ]
        
        for extension in extensions:
            should_process = config.should_process_with_llm(extension)
            self.assertFalse(should_process, 
                           f"Should not process extension: '{extension}'")
                           
    def test_new_sentence_detection(self):
        """Test that completely new sentences are still processed."""
        # Set up initial processed text
        config._last_llm_processed_text = "I need to create a file"
        
        # Test completely different text
        new_texts = [
            "The weather is nice today",
            "Let me check the database",
            "Run the test suite please"
        ]
        
        for new_text in new_texts:
            should_process = config.should_process_with_llm(new_text)
            self.assertTrue(should_process, 
                          f"Should process new sentence: '{new_text}'")
    
    @patch('requests.post')                      
    def test_concurrent_access(self, mock_post):
        """Test thread safety of cache and global state."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Thread safe test"}
        mock_post.return_value = mock_response
        
        results = []
        errors = []
        
        def process_text(text):
            try:
                result = config.nerd_dictation_process(f"this are test {text}")
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_text, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Concurrent access caused errors: {errors}")
        self.assertEqual(len(results), 5, "All threads should complete successfully")

def main():
    """Run the race condition tests."""
    print("Testing Race Conditions and Progressive Text Handling")
    print("=" * 60)
    print("This test validates the LLM-first architecture improvements:")
    print("- Progressive text detection")
    print("- Debouncing mechanism") 
    print("- Cache effectiveness")
    print("- Thread safety")
    print("")
    
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()