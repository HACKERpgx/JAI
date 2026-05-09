"""
JAI Emotional Intelligence Module

This module provides internal emotional-context analysis for JAI.
It runs silently on every user message before generating a response.

The system detects emotional state, intent, and chooses appropriate response modes
to provide emotionally aware, empathetic, and context-sensitive interactions.
"""

import re
import logging
from typing import Optional, Dict, Tuple, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class EmotionalState(Enum):
    """Detected emotional states"""
    NEUTRAL = "neutral"
    CURIOUS_EXCITED = "curious_excited"
    FRUSTRATED_ANNOYED = "frustrated_annoyed"
    SAD_LOW = "sad_low"
    ANXIOUS_OVERWHELMED = "anxious_overwhelmed"
    HAPPY_PLAYFUL = "happy_playful"
    ANGRY = "angry"
    GRATEFUL = "grateful"


class UserIntent(Enum):
    """Detected user intents"""
    INFORMATION = "information"
    TASK_HELP = "task_help"
    VENTING = "venting"
    VALIDATION = "validation"
    CASUAL_CHAT = "casual_chat"
    CREATIVE_COLLABORATION = "creative_collaboration"


@dataclass
class EmotionalContext:
    """Container for emotional analysis results"""
    emotional_state: EmotionalState
    intent: UserIntent
    confidence: float
    response_mode: str
    should_acknowledge: bool
    acknowledgment_phrase: Optional[str] = None


class EmotionalIntelligenceEngine:
    """
    Main engine for emotional intelligence processing.
    
    This class analyzes user messages for emotional signals and determines
    the appropriate response style. It operates silently and internally.
    """
    
    def __init__(self):
        self.emotional_memory: Dict[str, Dict] = {}
        self.conversation_history: List[Dict] = []
        
        # Emotional signal patterns
        self._init_emotional_patterns()
        
    def _init_emotional_patterns(self):
        """Initialize pattern dictionaries for emotion detection"""
        
        # Frustrated/Annoyed patterns
        self.frustrated_patterns = [
            r'\b(stupid|idiotic|dumb|useless|pointless|waste|broken|doesn\'t work|not working)\b',
            r'\b(frustrat|annoy|irritat|bother|upset|mad|pissed)\w*\b',
            r'\b(why can\'t|why doesn\'t|how do i|why is this)\b.*\?',
            r'[!?]{2,}',  # Multiple punctuation marks
            r'\b(hate|can\'t stand|sick of|tired of)\b',
            r'\b(again|still|yet)\b.*\b(not working|broken|wrong|error)\b',
            r'\b(never|always)\b.*\b(work|fail|wrong)\b',
        ]
        
        # Sad/Low patterns
        self.sad_patterns = [
            r'\b(sad|depress|unhappy|down|low|lonely|empty|hopeless)\w*\b',
            r'\b(cry|tears|hurt|pain|suffer)\w*\b',
            r'\b(don\'t feel|not feeling|feeling)\b.*(good|well|okay|better)\b',
            r'\b(tired|exhausted|drained|burned out)\b',
            r'\b(lose|lost|failure|fail|disappoint)\w*\b',
            r'\b(wish|hope|want)\b.*(better|different)\b',
        ]
        
        # Anxious/Overwhelmed patterns
        self.anxious_patterns = [
            r'\b(anxious|nervous|worried|stress|overwhelm|panic|scared|afraid)\w*\b',
            r'\b(too much|can\'t handle|can\'t cope|drowning|suffocat)\w*\b',
            r'\b(deadline|due|running out|pressure|urgent)\b',
            r'\b(don\'t know|confused|lost|unsure|uncertain)\b',
            r'\b(what if|worried about|stress about)\b',
            r'\b(too many|so much|a lot of|all these)\b',
            r'\b(stuck|trapped)\b',
        ]
        
        # Happy/Playful patterns
        self.happy_patterns = [
            r'\b(happy|excited|great|awesome|amazing|wonderful|fantastic)\b',
            r'\b(love|enjoy|fun|yay|hooray|celebrat)\b',
            r'\b(lol|haha|hehe|😊|😄|🎉|👏)\b',
            r'\b(can\'t wait|looking forward\b)',
            r'\b(finally|did it|success|won|accomplish)\b',
            r'\b(thank|thanks|appreciate|grateful)\b',
        ]
        
        # Angry patterns
        self.angry_patterns = [
            r'\b(angry|furious|rage|outraged|livid|irate)\b',
            r'\b(damn|hell|crap|bullshit\w*)\b',
            r'\b(unbelievable|ridiculous|absurd|insane)\b',
            r'\b(wtf|wth)\b',
            r'\b(seriously|actually)\b.*\!{2,}',  # Must have exclamation marks
        ]
        
        # Grateful patterns
        self.grateful_patterns = [
            r'\b(thank|thanks|thank you|appreciate|grateful)\b',
            r'\b(helpful|useful|great job|well done|good work)\b',
            r'\b(saved me|fixed it|worked perfectly)\b',
        ]
        
        # Curious/Excited patterns
        self.curious_patterns = [
            r'\b(curious|interested|wonder|fascinated|intrigued)\b',
            r'\b(how does|what is|why does|tell me about|explain)\b',
            r'\b(really\?|wow|amazing|incredible)\b',
            r'\b(can you|could you|is it possible)\b',
            r'\?{2,}',  # Multiple question marks
        ]
        
        # Intent patterns
        self.venting_patterns = [
            r'\b(just|simply)\b.*(need to|want to)\b.*(talk|say|tell|vent)\b',
            r'\b(don\'t|do not)\b.*(need|want)\b.*(advice|help|solution)\b',
            r'\b(just|simply)\b.*(need)\b.*(someone to listen|to be heard)\b',
            r'\b(not looking for|don\'t want)\b.*(solution|fix|advice)\b',
        ]
        
        self.validation_patterns = [
            r'\b(right\?|correct\?|is that|am i|do you think)\b',
            r'\b(validate|confirm|agree with|understand)\b',
            r'\b(normal|okay|fine)\b.*(to feel|to think)\b',
        ]
        
        self.creative_patterns = [
            r'\b(imagine|brainstorm|collaborate|together)\b',
            r'\b(story|poem|song|art|creative)\b',
            r'\b(idea|concept|design)\b.*(with you|together)',
        ]
        
        self.task_patterns = [
            r'\b(how to|help me|fix|solve|resolve)\b',
            r'\b(need to|want to|have to)\b.*(do|make|get|find|create)\b',
            r'\b(can you|could you)\b.*(help|assist|do)\b',
        ]
    
    def analyze_message(self, message: str, session_context: Optional[Dict] = None) -> EmotionalContext:
        """
        Analyze a user message for emotional context.
        
        Args:
            message: The user's message text
            session_context: Optional session context (memory, history, etc.)
            
        Returns:
            EmotionalContext object with analysis results
        """
        if not message or not isinstance(message, str):
            return EmotionalContext(
                emotional_state=EmotionalState.NEUTRAL,
                intent=UserIntent.INFORMATION,
                confidence=0.0,
                response_mode="direct",
                should_acknowledge=False
            )
        
        # Detect emotional state
        emotional_state = self._detect_emotional_state(message)
        
        # Detect intent
        intent = self._detect_intent(message)
        
        # Calculate confidence
        confidence = self._calculate_confidence(message, emotional_state)
        
        # Choose response mode
        response_mode = self._choose_response_mode(emotional_state, intent)
        
        # Determine if acknowledgment is needed
        should_acknowledge, acknowledgment_phrase = self._should_acknowledge(
            emotional_state, intent, message
        )
        
        # Store in conversation history
        self._update_conversation_history(message, emotional_state, intent)
        
        # Update emotional memory if significant
        self._update_emotional_memory(message, emotional_state, intent, session_context)
        
        return EmotionalContext(
            emotional_state=emotional_state,
            intent=intent,
            confidence=confidence,
            response_mode=response_mode,
            should_acknowledge=should_acknowledge,
            acknowledgment_phrase=acknowledgment_phrase
        )
    
    def _detect_emotional_state(self, message: str) -> EmotionalState:
        """Detect the dominant emotional state from the message"""
        message_lower = message.lower()
        
        # Priority check: grateful (thank/thanks) should override anxious/help patterns
        if re.search(r'\b(thank|thanks|grateful|appreciate)\b', message_lower, re.IGNORECASE):
            return EmotionalState.GRATEFUL
        
        # Priority check: angry emotion when strong indicators are present (swear words)
        angry_indicators = r'\b(damn|hell|crap|bullshit|wtf|wth|furious|rage)\b'
        if re.search(angry_indicators, message_lower, re.IGNORECASE):
            return EmotionalState.ANGRY
        
        # Score each emotion
        scores = {
            EmotionalState.FRUSTRATED_ANNOYED: self._score_pattern(message_lower, self.frustrated_patterns),
            EmotionalState.SAD_LOW: self._score_pattern(message_lower, self.sad_patterns),
            EmotionalState.ANXIOUS_OVERWHELMED: self._score_pattern(message_lower, self.anxious_patterns),
            EmotionalState.HAPPY_PLAYFUL: self._score_pattern(message_lower, self.happy_patterns),
            EmotionalState.ANGRY: self._score_pattern(message_lower, self.angry_patterns),
            EmotionalState.GRATEFUL: self._score_pattern(message_lower, self.grateful_patterns),
            EmotionalState.CURIOUS_EXCITED: self._score_pattern(message_lower, self.curious_patterns),
        }
        
        # Find highest scoring emotion
        max_score = max(scores.values())
        
        # Threshold for detection
        if max_score < 1:
            return EmotionalState.NEUTRAL
        
        # Return the emotion with highest score
        for emotion, score in scores.items():
            if score == max_score:
                return emotion
        
        return EmotionalState.NEUTRAL
    
    def _detect_intent(self, message: str) -> UserIntent:
        """Detect the user's primary intent"""
        message_lower = message.lower()
        
        # Check for venting (highest priority for intent classification)
        if self._score_pattern(message_lower, self.venting_patterns) >= 1:
            return UserIntent.VENTING
        
        # Check for validation
        if self._score_pattern(message_lower, self.validation_patterns) >= 1:
            return UserIntent.VALIDATION
        
        # Check for creative collaboration
        if self._score_pattern(message_lower, self.creative_patterns) >= 1:
            return UserIntent.CREATIVE_COLLABORATION
        
        # Check for task help
        if self._score_pattern(message_lower, self.task_patterns) >= 1:
            return UserIntent.TASK_HELP
        
        # Check for casual chat indicators
        casual_indicators = [
            r'\b(hi|hello|hey|how are you|what\'s up|good morning|good evening)\b',
            r'\b(just|simply)\b.*(wanted to|thought I\'d)\b',
            r'\b(by the way|btw|anyway)\b',
        ]
        if self._score_pattern(message_lower, casual_indicators) >= 1:
            return UserIntent.CASUAL_CHAT
        
        # Default to information seeking
        return UserIntent.INFORMATION
    
    def _score_pattern(self, text: str, patterns: List[str]) -> int:
        """Score how many patterns match in the text"""
        score = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        return score
    
    def _calculate_confidence(self, message: str, emotional_state: EmotionalState) -> float:
        """Calculate confidence score for the emotion detection"""
        if emotional_state == EmotionalState.NEUTRAL:
            return 0.5
        
        # Check for multiple emotional indicators
        message_lower = message.lower()
        indicator_count = 0
        
        # Count exclamation marks
        if '!' in message:
            indicator_count += min(message.count('!'), 3)
        
        # Count question marks
        if '?' in message:
            indicator_count += min(message.count('?'), 2)
        
        # Check for capitalization
        if any(c.isupper() for c in message):
            if sum(1 for c in message if c.isupper()) > len(message) * 0.3:
                indicator_count += 2
        
        # Normalize confidence to 0-1 range
        confidence = min(indicator_count / 5.0, 1.0)
        
        return max(confidence, 0.3)  # Minimum confidence of 0.3 if emotion detected
    
    def _choose_response_mode(self, emotional_state: EmotionalState, intent: UserIntent) -> str:
        """Choose the appropriate response mode based on emotion and intent"""
        
        # Angry + Any intent: de-escalate, stay calm, never argue or defend (highest priority)
        if emotional_state == EmotionalState.ANGRY:
            return "de_escalate"
        
        # Venting + Any emotion (except angry): acknowledge first, do not immediately solve
        if intent == UserIntent.VENTING and emotional_state != EmotionalState.ANGRY:
            return "acknowledge_listen"
        
        # Frustrated + Task help: calm, concise, skip filler, focus on fixing
        if emotional_state == EmotionalState.FRUSTRATED_ANNOYED and intent == UserIntent.TASK_HELP:
            return "calm_fix"
        
        # Anxious/Overwhelmed + Any intent: grounding tone, simple next steps, avoid overload
        if emotional_state == EmotionalState.ANXIOUS_OVERWHELMED:
            return "grounding"
        
        # Sad/Low + Any intent: warm, gentle, patient, no rushing
        if emotional_state == EmotionalState.SAD_LOW:
            return "gentle"
        
        # Grateful + Any intent: brief warm acknowledgment, then continue
        if emotional_state == EmotionalState.GRATEFUL:
            return "warm_acknowledge"
        
        # Happy/Playful + Casual chat: light, playful, match tone
        if emotional_state == EmotionalState.HAPPY_PLAYFUL and intent == UserIntent.CASUAL_CHAT:
            return "playful"
        
        # Curious/Excited + Any intent: match energy, then assist
        if emotional_state == EmotionalState.CURIOUS_EXCITED:
            return "energetic"
        
        # Neutral or Curious + Information/Task help: direct, clear, helpful
        if emotional_state in [EmotionalState.NEUTRAL, EmotionalState.CURIOUS_EXCITED]:
            if intent in [UserIntent.INFORMATION, UserIntent.TASK_HELP]:
                return "direct"
        
        # Default: direct and helpful
        return "direct"
    
    def _should_acknowledge(self, emotional_state: EmotionalState, intent: UserIntent, message: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if an acknowledgment is needed and generate an appropriate phrase.
        
        Returns:
            Tuple of (should_acknowledge, acknowledgment_phrase)
        """
        # Don't acknowledge neutral emotions
        if emotional_state == EmotionalState.NEUTRAL:
            return False, None
        
        # Generate acknowledgment based on emotion
        acknowledgment_phrases = {
            EmotionalState.FRUSTRATED_ANNOYED: [
                "I understand this is frustrating.",
                "I see this has been challenging.",
                "Let's work through this together.",
            ],
            EmotionalState.SAD_LOW: [
                "I'm here to help.",
                "Take your time.",
                "I understand.",
            ],
            EmotionalState.ANXIOUS_OVERWHELMED: [
                "Let's take this one step at a time.",
                "We'll figure this out together.",
                "Let me help you break this down.",
            ],
            EmotionalState.HAPPY_PLAYFUL: [
                "That's great!",
                "Wonderful!",
                "Excellent!",
            ],
            EmotionalState.ANGRY: [
                "I understand your concern.",
                "Let me help you with this.",
                "I appreciate your patience.",
            ],
            EmotionalState.GRATEFUL: [
                "You're welcome.",
                "Happy to help.",
                "Glad I could assist.",
            ],
            EmotionalState.CURIOUS_EXCITED: [
                "Great question!",
                "Interesting!",
                "Let's explore this.",
            ],
        }
        
        phrases = acknowledgment_phrases.get(emotional_state, [])
        if phrases:
            import random
            return True, random.choice(phrases)
        
        return False, None
    
    def _update_conversation_history(self, message: str, emotional_state: EmotionalState, intent: UserIntent):
        """Update the conversation history for context tracking"""
        self.conversation_history.append({
            'message': message,
            'emotional_state': emotional_state.value,
            'intent': intent.value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 entries
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def _update_emotional_memory(self, message: str, emotional_state: EmotionalState, intent: UserIntent, session_context: Optional[Dict]):
        """
        Update emotional memory with significant patterns.
        
        This stores only meaningful ongoing emotional context, not fleeting moods.
        """
        # Check for recurring frustration patterns
        if emotional_state == EmotionalState.FRUSTRATED_ANNOYED:
            # Count recent frustration in history
            recent_frustrations = sum(
                1 for h in self.conversation_history[-10:]
                if h['emotional_state'] == EmotionalState.FRUSTRATED_ANNOYED.value
            )
            
            if recent_frustrations >= 3:
                self.emotional_memory['recurring_frustration'] = {
                    'pattern': 'User has repeatedly felt blocked by implementation complexity.',
                    'last_updated': datetime.now().isoformat(),
                    'count': recent_frustrations
                }
        
        # Check for ongoing stress/overwhelm patterns
        if emotional_state == EmotionalState.ANXIOUS_OVERWHELMED:
            recent_anxiety = sum(
                1 for h in self.conversation_history[-10:]
                if h['emotional_state'] == EmotionalState.ANXIOUS_OVERWHELMED.value
            )
            
            if recent_anxiety >= 3:
                self.emotional_memory['ongoing_stress'] = {
                    'pattern': 'User has been feeling pressure and may need clearer, smaller steps.',
                    'last_updated': datetime.now().isoformat(),
                    'count': recent_anxiety
                }
        
        # Check for project-specific stress (if context available)
        if session_context and 'project_context' in session_context:
            if emotional_state in [EmotionalState.FRUSTRATED_ANNOYED, EmotionalState.ANXIOUS_OVERWHELMED]:
                self.emotional_memory['project_stress'] = {
                    'pattern': 'User has been feeling pressure around this project.',
                    'last_updated': datetime.now().isoformat(),
                    'project': session_context.get('project_context', 'unknown')
                }
    
    def get_emotional_memory(self) -> Dict:
        """Get the current emotional memory (internal use only)"""
        return self.emotional_memory.copy()
    
    def get_response_guidance(self, emotional_context: EmotionalContext) -> str:
        """
        Generate response guidance based on emotional context.
        
        This guidance is added to the system prompt to guide the AI's response style.
        """
        response_mode = emotional_context.response_mode
        
        guidance_map = {
            "direct": "Provide a direct, clear, and helpful response. Be concise and focused.",
            "energetic": "Match the user's energy and enthusiasm. Be engaging and dynamic while still being helpful.",
            "calm_fix": "Stay calm and focused. Skip filler words. Provide a clear, step-by-step solution. Be concise and practical.",
            "acknowledge_listen": "First acknowledge the user's feelings without immediately jumping to solutions. Listen and validate before offering help if appropriate.",
            "gentle": "Use a warm, gentle tone. Be patient and understanding. Don't rush. Provide supportive and considerate responses.",
            "grounding": "Use a grounding, steady tone. Break down complex information into simple, clear steps. Avoid overwhelming the user with too much information at once.",
            "playful": "Keep the tone light and playful. Match the user's energy while being helpful.",
            "de_escalate": "Stay calm and professional. Never argue or defend. Acknowledge the concern and focus on helping constructively.",
            "warm_acknowledge": "Provide a brief, warm acknowledgment, then continue with the task or conversation naturally.",
        }
        
        base_guidance = guidance_map.get(response_mode, "Provide a helpful and appropriate response.")
        
        # Add acknowledgment if needed
        if emotional_context.should_acknowledge and emotional_context.acknowledgment_phrase:
            base_guidance = f"{emotional_context.acknowledgment_phrase} {base_guidance}"
        
        # Add emotional memory context if available
        if self.emotional_memory:
            memory_contexts = []
            for key, value in self.emotional_memory.items():
                if value.get('pattern'):
                    memory_contexts.append(value['pattern'])
            
            if memory_contexts:
                base_guidance += f" Context note: {' '.join(memory_contexts)}"
        
        return base_guidance


# Global instance
_emotional_engine = None

def get_emotional_engine() -> EmotionalIntelligenceEngine:
    """Get or create the global emotional intelligence engine instance"""
    global _emotional_engine
    if _emotional_engine is None:
        _emotional_engine = EmotionalIntelligenceEngine()
    return _emotional_engine


def analyze_emotional_context(message: str, session_context: Optional[Dict] = None) -> EmotionalContext:
    """
    Analyze emotional context for a message.
    
    This is the main entry point for the emotional intelligence system.
    
    Args:
        message: The user's message text
        session_context: Optional session context
        
    Returns:
        EmotionalContext object with analysis results
    """
    engine = get_emotional_engine()
    return engine.analyze_message(message, session_context)


def get_response_guidance(emotional_context: EmotionalContext) -> str:
    """
    Get response guidance based on emotional context.
    
    Args:
        emotional_context: The emotional context analysis result
        
    Returns:
        Guidance string to be added to system prompt
    """
    engine = get_emotional_engine()
    return engine.get_response_guidance(emotional_context)
