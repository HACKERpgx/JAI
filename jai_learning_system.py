"""
JAI Advanced Learning and Adaptation System
Implements machine learning capabilities for continuous improvement
through user feedback and behavior analysis.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np
from collections import defaultdict, Counter
import re

class LearningType(Enum):
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    UNSUPERVISED = "unsupervised"
    TRANSFER = "transfer"

class FeedbackType(Enum):
    EXPLICIT = "explicit"  # User directly provides feedback
    IMPLICIT = "implicit"   # Learned from user behavior
    CORRECTIVE = "corrective"  # User corrections
    PREFERENCE = "preference"  # User preferences

@dataclass
class LearningExample:
    """Training example for machine learning"""
    input_text: str
    intent: str
    entities: Dict[str, Any]
    context: Dict[str, Any]
    outcome: bool
    confidence: float
    timestamp: datetime
    feedback_type: FeedbackType
    user_satisfaction: Optional[int] = None  # 1-5 rating

@dataclass
class Pattern:
    """Learned pattern for prediction"""
    pattern_id: str
    pattern_type: str
    regex: str
    confidence: float
    usage_count: int
    success_rate: float
    last_used: datetime
    created_at: datetime

@dataclass
class UserPreference:
    """User preference data"""
    preference_id: str
    category: str
    key: str
    value: Any
    confidence: float
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    usage_count: int

class IntentClassifier:
    """Machine learning based intent classifier"""
    
    def __init__(self):
        self.training_data: List[LearningExample] = []
        self.intent_patterns: Dict[str, List[str]] = defaultdict(list)
        self.feature_weights: Dict[str, float] = defaultdict(float)
        self.confidence_threshold = 0.7
        
    def add_training_example(self, example: LearningExample):
        """Add training example"""
        self.training_data.append(example)
        self._update_patterns(example)
        self._update_weights(example)
    
    def _update_patterns(self, example: LearningExample):
        """Update intent patterns based on example"""
        words = example.input_text.lower().split()
        
        # Extract n-grams
        for n in range(1, 4):  # 1-gram to 3-gram
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                if len(ngram) > 2:  # Filter short patterns
                    self.intent_patterns[example.intent].append(ngram)
    
    def _update_weights(self, example: LearningExample):
        """Update feature weights based on feedback"""
        weight_delta = 0.1 if example.outcome else -0.05
        weight_delta *= example.confidence
        
        words = example.input_text.lower().split()
        for word in words:
            self.feature_weights[word] += weight_delta
    
    def predict_intent(self, text: str, context: Dict[str, Any] = None) -> Tuple[str, float]:
        """Predict intent with confidence"""
        text_lower = text.lower()
        words = text_lower.split()
        
        intent_scores = defaultdict(float)
        
        # Score based on learned patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    intent_scores[intent] += 1.0
        
        # Score based on feature weights
        for word in words:
            for intent in self.intent_patterns.keys():
                intent_scores[intent] += self.feature_weights.get(f"{word}_{intent}", 0)
        
        # Normalize scores
        if intent_scores:
            max_score = max(intent_scores.values())
            if max_score > 0:
                intent_scores = {k: v/max_score for k, v in intent_scores.items()}
        
        # Get best intent
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence
        
        return "unknown", 0.0

class EntityExtractor:
    """Machine learning based entity extractor"""
    
    def __init__(self):
        self.entity_patterns: Dict[str, List[Pattern]] = defaultdict(list)
        self.context_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    def add_entity_pattern(self, entity_type: str, pattern: Pattern):
        """Add learned entity pattern"""
        self.entity_patterns[entity_type].append(pattern)
    
    def extract_entities(self, text: str, context: Dict[str, Any] = None) -> Dict[str, List[str]]:
        """Extract entities using learned patterns"""
        entities = defaultdict(list)
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.findall(pattern.regex, text, re.IGNORECASE)
                    entities[entity_type].extend(matches)
                    
                    # Update pattern usage
                    pattern.usage_count += 1
                    pattern.last_used = datetime.now()
                    
                except re.error:
                    continue
        
        return dict(entities)

class BehaviorAnalyzer:
    """Analyzes user behavior to learn preferences"""
    
    def __init__(self):
        self.behavior_history: List[Dict[str, Any]] = []
        self.usage_patterns: Dict[str, Counter] = defaultdict(Counter)
        self.time_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.correction_patterns: List[Dict[str, Any]] = []
    
    def record_interaction(self, interaction: Dict[str, Any]):
        """Record user interaction"""
        interaction['timestamp'] = datetime.now()
        self.behavior_history.append(interaction)
        
        # Update usage patterns
        intent = interaction.get('intent', 'unknown')
        self.usage_patterns[intent][interaction.get('action', 'unknown')] += 1
        
        # Update time patterns
        self.time_patterns[intent].append(interaction['timestamp'])
    
    def record_correction(self, original: str, corrected: str, context: Dict[str, Any]):
        """Record user correction"""
        self.correction_patterns.append({
            'original': original,
            'corrected': corrected,
            'context': context,
            'timestamp': datetime.now()
        })
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        stats = {}
        
        for intent, actions in self.usage_patterns.items():
            total = sum(actions.values())
            stats[intent] = {
                'total_uses': total,
                'most_common_action': actions.most_common(1)[0] if actions else None,
                'action_distribution': dict(actions)
            }
        
        return stats
    
    def get_time_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze time-based usage patterns"""
        patterns = {}
        
        for intent, times in self.time_patterns.items():
            if len(times) > 1:
                hours = [t.hour for t in times]
                days = [t.weekday() for t in times]
                
                patterns[intent] = {
                    'peak_hour': Counter(hours).most_common(1)[0][0],
                    'peak_day': Counter(days).most_common(1)[0][0],
                    'usage_frequency': len(times)
                }
        
        return patterns

class AdaptiveLearningSystem:
    """Main adaptive learning system"""
    
    def __init__(self):
        self.logger = logging.getLogger('JAILearningSystem')
        
        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # Data storage
        self.data_dir = Path("jai_learning_data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.preferences_file = self.data_dir / "user_preferences.json"
        self.patterns_file = self.data_dir / "learned_patterns.json"
        self.examples_file = self.data_dir / "training_examples.json"
        
        # Load existing data
        self.user_preferences: Dict[str, UserPreference] = {}
        self.learned_patterns: Dict[str, Pattern] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load existing learning data"""
        try:
            # Load preferences
            if self.preferences_file.exists():
                data = json.loads(self.preferences_file.read_text())
                for pref_data in data:
                    pref = UserPreference(**pref_data)
                    self.user_preferences[pref.preference_id] = pref
            
            # Load patterns
            if self.patterns_file.exists():
                data = json.loads(self.patterns_file.read_text())
                for pattern_data in data:
                    pattern = Pattern(**pattern_data)
                    self.learned_patterns[pattern.pattern_id] = pattern
                    
                    # Add to entity extractor
                    self.entity_extractor.add_entity_pattern(
                        pattern.pattern_type, pattern
                    )
            
            # Load training examples
            if self.examples_file.exists():
                data = json.loads(self.examples_file.read_text())
                for example_data in data:
                    example = LearningExample(**example_data)
                    self.intent_classifier.add_training_example(example)
                    
        except Exception as e:
            self.logger.warning(f"Error loading learning data: {e}")
    
    def _save_data(self):
        """Save learning data"""
        try:
            # Save preferences
            pref_data = [asdict(pref) for pref in self.user_preferences.values()]
            self.preferences_file.write_text(json.dumps(pref_data, indent=2, default=str))
            
            # Save patterns
            pattern_data = [asdict(pattern) for pattern in self.learned_patterns.values()]
            self.patterns_file.write_text(json.dumps(pattern_data, indent=2, default=str))
            
            # Save training examples
            example_data = [asdict(example) for example in self.intent_classifier.training_data]
            self.examples_file.write_text(json.dumps(example_data, indent=2, default=str))
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    async def learn_from_feedback(self, feedback: Dict[str, Any]):
        """Learn from user feedback"""
        try:
            feedback_type = FeedbackType(feedback.get('type', 'explicit'))
            
            if feedback_type == FeedbackType.EXPLICIT:
                await self._learn_explicit_feedback(feedback)
            elif feedback_type == FeedbackType.IMPLICIT:
                await self._learn_implicit_feedback(feedback)
            elif feedback_type == FeedbackType.CORRECTIVE:
                await self._learn_corrective_feedback(feedback)
            elif feedback_type == FeedbackType.PREFERENCE:
                await self._learn_preference_feedback(feedback)
            
            self._save_data()
            
        except Exception as e:
            self.logger.error(f"Error learning from feedback: {e}")
    
    async def _learn_explicit_feedback(self, feedback: Dict[str, Any]):
        """Learn from explicit user feedback"""
        task_id = feedback.get('task_id')
        rating = feedback.get('rating', 0)
        comment = feedback.get('comment', '')
        
        # Create training example
        example = LearningExample(
            input_text=feedback.get('input_text', ''),
            intent=feedback.get('intent', ''),
            entities=feedback.get('entities', {}),
            context=feedback.get('context', {}),
            outcome=rating >= 3,  # 3+ is considered successful
            confidence=feedback.get('confidence', 0.0),
            timestamp=datetime.now(),
            feedback_type=FeedbackType.EXPLICIT,
            user_satisfaction=rating
        )
        
        self.intent_classifier.add_training_example(example)
        
        # Adjust confidence thresholds based on feedback
        if rating < 3:
            self.intent_classifier.confidence_threshold = max(
                0.5, self.intent_classifier.confidence_threshold - 0.05
            )
        elif rating > 4:
            self.intent_classifier.confidence_threshold = min(
                0.9, self.intent_classifier.confidence_threshold + 0.02
            )
    
    async def _learn_implicit_feedback(self, feedback: Dict[str, Any]):
        """Learn from implicit user behavior"""
        interaction = {
            'intent': feedback.get('intent'),
            'action': feedback.get('action'),
            'duration': feedback.get('duration'),
            'success': feedback.get('success', True),
            'context': feedback.get('context', {})
        }
        
        self.behavior_analyzer.record_interaction(interaction)
    
    async def _learn_corrective_feedback(self, feedback: Dict[str, Any]):
        """Learn from user corrections"""
        original = feedback.get('original', '')
        corrected = feedback.get('corrected', '')
        context = feedback.get('context', {})
        
        self.behavior_analyzer.record_correction(original, corrected, context)
        
        # Extract patterns from corrections
        if original and corrected:
            pattern_id = f"corr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(original)}"
            pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type='correction',
                regex=re.escape(original),
                confidence=0.8,
                usage_count=1,
                success_rate=1.0,
                last_used=datetime.now(),
                created_at=datetime.now()
            )
            
            self.learned_patterns[pattern_id] = pattern
    
    async def _learn_preference_feedback(self, feedback: Dict[str, Any]):
        """Learn user preferences"""
        category = feedback.get('category', 'general')
        key = feedback.get('key', '')
        value = feedback.get('value', '')
        context = feedback.get('context', {})
        
        preference_id = f"{category}_{key}"
        
        # Update existing preference or create new one
        if preference_id in self.user_preferences:
            pref = self.user_preferences[preference_id]
            pref.value = value
            pref.updated_at = datetime.now()
            pref.usage_count += 1
            # Increase confidence with repeated usage
            pref.confidence = min(1.0, pref.confidence + 0.1)
        else:
            pref = UserPreference(
                preference_id=preference_id,
                category=category,
                key=key,
                value=value,
                confidence=0.5,
                context=context,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                usage_count=1
            )
            self.user_preferences[preference_id] = pref
    
    def get_preference(self, category: str, key: str, default: Any = None) -> Any:
        """Get user preference"""
        preference_id = f"{category}_{key}"
        pref = self.user_preferences.get(preference_id)
        return pref.value if pref else default
    
    def improve_intent_classification(self, text: str, context: Dict[str, Any] = None) -> Tuple[str, float]:
        """Improve intent classification using learning"""
        # Use learned classifier
        intent, confidence = self.intent_classifier.predict_intent(text, context)
        
        # Apply user preferences if available
        preferred_intent = self.get_preference('intent', 'default')
        if preferred_intent and confidence < 0.6:
            intent = preferred_intent
            confidence = 0.6
        
        return intent, confidence
    
    def improve_entity_extraction(self, text: str, context: Dict[str, Any] = None) -> Dict[str, List[str]]:
        """Improve entity extraction using learning"""
        entities = self.entity_extractor.extract_entities(text, context)
        
        # Apply learned preferences for entity values
        for entity_type, values in entities.items():
            preferred_values = self.get_preference('entity', entity_type, [])
            if preferred_values and isinstance(preferred_values, list):
                # Boost confidence for preferred values
                for pref_val in preferred_values:
                    if pref_val in values:
                        # Move preferred value to front
                        values.remove(pref_val)
                        values.insert(0, pref_val)
        
        return entities
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data"""
        return {
            'total_preferences': len(self.user_preferences),
            'total_patterns': len(self.learned_patterns),
            'training_examples': len(self.intent_classifier.training_data),
            'usage_stats': self.behavior_analyzer.get_usage_statistics(),
            'time_patterns': self.behavior_analyzer.get_time_patterns(),
            'confidence_threshold': self.intent_classifier.confidence_threshold,
            'recent_corrections': len(self.behavior_analyzer.correction_patterns[-10:])
        }
    
    async def auto_improve(self):
        """Automatically improve based on collected data"""
        try:
            # Analyze recent corrections to identify patterns
            recent_corrections = self.behavior_analyzer.correction_patterns[-50:]
            
            # Group similar corrections
            correction_groups = defaultdict(list)
            for correction in recent_corrections:
                key = f"{correction['original']}->{correction['corrected']}"
                correction_groups[key].append(correction)
            
            # Create patterns for frequent corrections
            for correction_key, corrections in correction_groups.items():
                if len(corrections) >= 3:  # Pattern appears at least 3 times
                    original, corrected = correction_key.split('->')
                    
                    pattern_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(correction_key)}"
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type='auto_correction',
                        regex=re.escape(original),
                        confidence=0.9,
                        usage_count=len(corrections),
                        success_rate=1.0,
                        last_used=datetime.now(),
                        created_at=datetime.now()
                    )
                    
                    self.learned_patterns[pattern_id] = pattern
                    self.entity_extractor.add_entity_pattern('auto_correction', pattern)
            
            self._save_data()
            self.logger.info(f"Auto-improvement completed. Added {len(correction_groups)} new patterns.")
            
        except Exception as e:
            self.logger.error(f"Error in auto-improvement: {e}")

# Global learning system instance
learning_system = AdaptiveLearningSystem()
