"""
Test script for JAI Emotional Intelligence Module

This script tests the emotional intelligence system to ensure it correctly
detects emotions, intents, and generates appropriate response guidance.
"""

from jai_emotional_intelligence import analyze_emotional_context, get_response_guidance, get_emotional_engine


def test_emotional_detection():
    """Test emotion detection for various message types"""
    print("=" * 60)
    print("Testing Emotional Intelligence System")
    print("=" * 60)
    
    test_cases = [
        # Frustrated messages
        ("This is so stupid! Why doesn't it work???", "frustrated_annoyed"),
        ("I'm getting really annoyed with this broken code", "frustrated_annoyed"),
        ("Why can't I just get this to work! It's pointless!", "frustrated_annoyed"),
        
        # Sad/Low messages
        ("I'm feeling really down today", "sad_low"),
        ("I just feel so empty and lonely", "sad_low"),
        ("I'm exhausted and burned out from all this work", "sad_low"),
        
        # Anxious/Overwhelmed messages
        ("I'm so overwhelmed with all these deadlines", "anxious_overwhelmed"),
        ("I don't know what to do, I'm so stressed", "anxious_overwhelmed"),
        ("There's too much to do and I'm running out of time", "anxious_overwhelmed"),
        
        # Happy/Playful messages
        ("This is amazing! I'm so excited!", "happy_playful"),
        ("Haha that's great! I love it!", "happy_playful"),
        ("Finally got it working! Yay!", "happy_playful"),
        
        # Angry messages
        ("This is RIDICULOUS! I can't believe this!", "angry"),
        ("What the hell is wrong with this system??", "angry"),
        ("I am so furious right now!", "angry"),
        
        # Grateful messages
        ("Thank you so much for your help!", "grateful"),
        ("This was really helpful, thanks!", "grateful"),
        ("I appreciate your assistance with this", "grateful"),
        
        # Curious/Excited messages
        ("How does this work? I'm really curious!", "curious_excited"),
        ("What is this?? I want to know more!", "curious_excited"),
        ("Can you explain this to me??", "curious_excited"),
        
        # Neutral/Curious messages
        ("What time is it?", "neutral"),
        ("Tell me about Python", "curious_excited"),  # Questions show curiosity
        ("What is the capital of France?", "curious_excited"),  # Questions show curiosity
    ]
    
    engine = get_emotional_engine()
    passed = 0
    failed = 0
    
    for message, expected_emotion in test_cases:
        context = analyze_emotional_context(message)
        detected_emotion = context.emotional_state.value
        
        if detected_emotion == expected_emotion:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  Message: {message[:50]}...")
        print(f"  Expected: {expected_emotion}")
        print(f"  Detected: {detected_emotion}")
        print(f"  Intent: {context.intent.value}")
        print(f"  Response Mode: {context.response_mode}")
        print(f"  Confidence: {context.confidence:.2f}")
        if context.should_acknowledge:
            print(f"  Acknowledgment: {context.acknowledgment_phrase}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)
    
    return failed == 0


def test_intent_detection():
    """Test intent detection"""
    print("\n" + "=" * 60)
    print("Testing Intent Detection")
    print("=" * 60)
    
    test_cases = [
        ("I just need to vent about my day", "venting"),
        ("I don't want advice, just someone to listen", "venting"),
        ("Am I right about this?", "validation"),
        ("Can you help me fix this bug?", "task_help"),
        ("I need to create a new file", "task_help"),
        ("Let's create a story together", "creative_collaboration"),
        ("Hi there! How are you?", "casual_chat"),
        ("What is the capital of France?", "information"),
    ]
    
    passed = 0
    failed = 0
    
    for message, expected_intent in test_cases:
        context = analyze_emotional_context(message)
        detected_intent = context.intent.value
        
        if detected_intent == expected_intent:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  Message: {message}")
        print(f"  Expected Intent: {expected_intent}")
        print(f"  Detected Intent: {detected_intent}")
    
    print("\n" + "=" * 60)
    print(f"Intent Test Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)
    
    return failed == 0


def test_response_guidance():
    """Test response guidance generation"""
    print("\n" + "=" * 60)
    print("Testing Response Guidance")
    print("=" * 60)
    
    # Clear emotional memory for clean test
    engine = get_emotional_engine()
    engine.emotional_memory.clear()
    engine.conversation_history.clear()
    
    test_cases = [
        ("This code is so frustrating! I need to fix it", "calm_fix"),
        ("I just need to talk about my day, don't give me advice", "acknowledge_listen"),
        ("I'm feeling really overwhelmed with everything", "grounding"),
        ("This is amazing! Thank you!", "warm_acknowledge"),
        ("Tell me about Python", "energetic"),  # Curious questions get energetic mode
    ]
    
    for message, expected_mode in test_cases:
        context = analyze_emotional_context(message)
        guidance = get_response_guidance(context)
        
        print(f"\nMessage: {message}")
        print(f"Emotion: {context.emotional_state.value}, Intent: {context.intent.value}")
        print(f"Response Mode: {context.response_mode}")
        print(f"Expected Mode: {expected_mode}")
        print(f"Guidance: {guidance[:100]}...")
    
    print("\n" + "=" * 60)
    print("Response Guidance Test Complete")
    print("=" * 60)


def test_emotional_memory():
    """Test emotional memory system"""
    print("\n" + "=" * 60)
    print("Testing Emotional Memory")
    print("=" * 60)
    
    engine = get_emotional_engine()
    
    # Simulate recurring frustration
    for i in range(5):
        analyze_emotional_context("This is so frustrating! It's not working!")
    
    memory = engine.get_emotional_memory()
    
    print(f"\nEmotional Memory Entries: {len(memory)}")
    for key, value in memory.items():
        print(f"  {key}: {value.get('pattern', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Emotional Memory Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    print("\nJAI Emotional Intelligence Test Suite\n")
    
    emotion_pass = test_emotional_detection()
    intent_pass = test_intent_detection()
    test_response_guidance()
    test_emotional_memory()
    
    print("\n" + "=" * 60)
    print("OVERALL TEST SUMMARY")
    print("=" * 60)
    print(f"Emotion Detection: {'PASSED' if emotion_pass else 'FAILED'}")
    print(f"Intent Detection: {'PASSED' if intent_pass else 'FAILED'}")
    print("=" * 60)
    
    if emotion_pass and intent_pass:
        print("\n✓ All tests passed! Emotional intelligence system is working correctly.")
    else:
        print("\n✗ Some tests failed. Please review the results above.")
