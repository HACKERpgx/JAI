#!/usr/bin/env python3
"""Quick test for YouTube auto-play functionality."""
import sys
from jai_media import YouTubeController

def test_youtube_play():
    """Test YouTube play with yt-dlp."""
    print("Testing YouTube auto-play with yt-dlp...")
    print("="*60)
    
    youtube = YouTubeController()
    
    test_queries = [
        "No Love Song",
        "Nasha by Talwinder",
        "Bohemian Rhapsody"
    ]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        result = youtube.play(query)
        print(f"Result: {result}")
        print("-"*60)
        
        # Wait for user confirmation
        input("Press Enter to test next query (or Ctrl+C to exit)...")
    
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    try:
        test_youtube_play()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
        sys.exit(0)
