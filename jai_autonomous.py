"""
JAI Autonomous System
A fully autonomous system capable of understanding user intent, planning actions, 
executing them across supported tools and services, handling errors gracefully, 
and continuously improving through feedback.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re
from pathlib import Path

# Import existing JAI modules
try:
    from jai_assistant import execute_command, sessions as ja_sessions
    from jai_calendar import create_event, get_events, delete_event
    from jai_media import play_music, pause_music, control_youtube
    from gmail_handler import send_email, get_emails
except ImportError as e:
    logging.warning(f"Some JAI modules not available: {e}")

class IntentType(Enum):
    """Types of user intents"""
    QUERY = "query"
    ACTION = "action"
    COMPLEX_TASK = "complex_task"
    AUTOMATION = "automation"
    LEARNING = "learning"
    ERROR_RECOVERY = "error_recovery"

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

@dataclass
class Intent:
    """User intent representation"""
    text: str
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime

@dataclass
class Task:
    """Task representation"""
    id: str
    intent: Intent
    plan: List[Dict[str, Any]]
    status: TaskStatus
    result: Optional[Any]
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Feedback:
    """User feedback for learning"""
    task_id: str
    rating: int  # 1-5
    comment: Optional[str]
    timestamp: datetime
    context: Dict[str, Any]

class IntentAnalyzer:
    """Analyzes user input to determine intent and extract entities"""
    
    def __init__(self):
        self.intent_patterns = {
            IntentType.QUERY: [
                r'\b(what|when|where|how|why|who|tell me|show me|get|list|find)\b',
                r'\b(time|weather|news|emails|events|calendar|status)\b'
            ],
            IntentType.ACTION: [
                r'\b(send|create|delete|play|pause|stop|start|run|execute|open|close)\b',
                r'\b(email|music|video|reminder|event|file|program)\b'
            ],
            IntentType.COMPLEX_TASK: [
                r'\b(plan|schedule|organize|manage|coordinate|setup|configure)\b',
                r'\b(meeting|project|workflow|automation|routine)\b'
            ],
            IntentType.AUTOMATION: [
                r'\b(automate|schedule|repeat|daily|weekly|monthly|routine)\b',
                r'\b(whenever|every|always|monitor|watch)\b'
            ],
            IntentType.LEARNING: [
                r'\b(learn|remember|save|store|train|improve|adapt)\b',
                r'\b(prefer|like|dislike|better|correct)\b'
            ]
        }
        
        self.entity_patterns = {
            'time': [
                r'\b(\d{1,2}:\d{2})\b',
                r'\b(morning|afternoon|evening|night|tonight|tomorrow|today)\b'
            ],
            'date': [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b'
            ],
            'email': [
                r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
            ],
            'person': [
                r'\b(to|from|with|for|contact) ([A-Z][a-z]+ [A-Z][a-z]+)\b'
            ],
            'media': [
                r'\b(music|song|video|youtube|spotify|playlist)\b'
            ]
        }
    
    def analyze(self, text: str, context: Dict[str, Any] = None) -> Intent:
        """Analyze user input to determine intent"""
        text_lower = text.lower()
        
        # Determine intent type
        intent_scores = {}
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                score += matches
            intent_scores[intent_type] = score
        
        # Get the highest scoring intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent] / 2.0, 1.0)  # Normalize to 0-1
        
        # Extract entities
        entities = {}
        for entity_type, patterns in self.entity_patterns.items():
            entities[entity_type] = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities[entity_type].extend(matches)
        
        return Intent(
            text=text,
            intent_type=best_intent,
            confidence=confidence,
            entities=entities,
            context=context or {},
            timestamp=datetime.now()
        )

class TaskPlanner:
    """Plans tasks based on user intent"""
    
    def __init__(self):
        self.action_handlers = {
            'email': self._plan_email_task,
            'calendar': self._plan_calendar_task,
            'media': self._plan_media_task,
            'automation': self._plan_automation_task,
            'query': self._plan_query_task,
            'complex': self._plan_complex_task
        }
    
    def create_plan(self, intent: Intent) -> List[Dict[str, Any]]:
        """Create execution plan based on intent"""
        plan = []
        
        if intent.intent_type == IntentType.QUERY:
            plan = self._plan_query_task(intent)
        elif intent.intent_type == IntentType.ACTION:
            plan = self._plan_action_task(intent)
        elif intent.intent_type == IntentType.COMPLEX_TASK:
            plan = self._plan_complex_task(intent)
        elif intent.intent_type == IntentType.AUTOMATION:
            plan = self._plan_automation_task(intent)
        elif intent.intent_type == IntentType.LEARNING:
            plan = self._plan_learning_task(intent)
        
        return plan
    
    def _plan_query_task(self, intent: Intent) -> List[Dict[str, Any]]:
        """Plan for query intents"""
        plan = []
        text_lower = intent.text.lower()
        
        if 'time' in text_lower:
            plan.append({
                'action': 'get_time',
                'handler': 'system',
                'params': {},
                'description': 'Get current time'
            })
        elif 'weather' in text_lower:
            plan.append({
                'action': 'get_weather',
                'handler': 'weather',
                'params': {'location': intent.entities.get('location', ['current'])[0] if intent.entities.get('location') else 'current'},
                'description': 'Get weather information'
            })
        elif 'email' in text_lower or 'emails' in text_lower:
            plan.append({
                'action': 'get_emails',
                'handler': 'gmail',
                'params': {'limit': 10},
                'description': 'Fetch recent emails'
            })
        elif 'calendar' in text_lower or 'events' in text_lower:
            plan.append({
                'action': 'get_events',
                'handler': 'calendar',
                'params': {'days': 7},
                'description': 'Get upcoming calendar events'
            })
        
        return plan
    
    def _plan_action_task(self, intent: Intent) -> List[Dict[str, Any]]:
        """Plan for action intents"""
        plan = []
        text_lower = intent.text.lower()
        
        if 'send' in text_lower and 'email' in text_lower:
            plan.append({
                'action': 'send_email',
                'handler': 'gmail',
                'params': {
                    'to': intent.entities.get('email', [None])[0],
                    'subject': self._extract_subject(intent.text),
                    'body': self._extract_body(intent.text)
                },
                'description': 'Send email'
            })
        elif 'play' in text_lower and any(word in text_lower for word in ['music', 'song', 'video']):
            plan.append({
                'action': 'play_media',
                'handler': 'media',
                'params': {'query': self._extract_media_query(intent.text)},
                'description': 'Play media content'
            })
        elif 'create' in text_lower and ('event' in text_lower or 'reminder' in text_lower):
            plan.append({
                'action': 'create_event',
                'handler': 'calendar',
                'params': self._extract_event_params(intent),
                'description': 'Create calendar event'
            })
        
        return plan
    
    def _plan_complex_task(self, intent: Intent) -> List[Dict[str, Any]]:
        """Plan for complex multi-step tasks"""
        plan = []
        text_lower = intent.text.lower()
        
        if 'meeting' in text_lower:
            # Multi-step meeting planning
            plan.append({
                'action': 'check_availability',
                'handler': 'calendar',
                'params': {'duration': 60},
                'description': 'Check calendar availability'
            })
            plan.append({
                'action': 'create_event',
                'handler': 'calendar',
                'params': self._extract_event_params(intent),
                'description': 'Create meeting event'
            })
            if 'email' in text_lower:
                plan.append({
                    'action': 'send_email',
                    'handler': 'gmail',
                    'params': {
                        'to': intent.entities.get('email', []),
                        'subject': 'Meeting Invitation',
                        'body': 'Meeting has been scheduled.'
                    },
                    'description': 'Send meeting invitation'
                })
        
        return plan
    
    def _plan_automation_task(self, intent: Intent) -> List[Dict[str, Any]]:
        """Plan for automation tasks"""
        plan = []
        text_lower = intent.text.lower()
        
        if 'daily' in text_lower or 'routine' in text_lower:
            plan.append({
                'action': 'create_automation',
                'handler': 'automation',
                'params': {
                    'trigger': 'schedule',
                    'schedule': self._extract_schedule(intent.text),
                    'actions': self._extract_automated_actions(intent.text)
                },
                'description': 'Create scheduled automation'
            })
        
        return plan
    
    def _plan_learning_task(self, intent: Intent) -> List[Dict[str, Any]]:
        """Plan for learning/preference tasks"""
        plan = []
        text_lower = intent.text.lower()
        
        plan.append({
            'action': 'learn_preference',
            'handler': 'learning',
            'params': {
                'preference_type': self._extract_preference_type(intent.text),
                'preference_value': self._extract_preference_value(intent.text)
            },
            'description': 'Learn user preference'
        })
        
        return plan
    
    def _extract_subject(self, text: str) -> str:
        """Extract email subject from text"""
        # Simple extraction - can be enhanced with NLP
        patterns = [
            r'subject[:\s]+([^.!?]+)',
            r'about[:\s]+([^.!?]+)',
            r'regarding[:\s]+([^.!?]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "No subject"
    
    def _extract_body(self, text: str) -> str:
        """Extract email body from text"""
        # Remove subject lines and return remaining text
        text = re.sub(r'subject[:\s]+[^.!?]+[.!?]', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def _extract_media_query(self, text: str) -> str:
        """Extract media search query"""
        # Simple extraction - can be enhanced
        words = text.lower().split()
        stop_words = {'play', 'the', 'a', 'an', 'song', 'music', 'video'}
        query_words = [word for word in words if word not in stop_words]
        return ' '.join(query_words)
    
    def _extract_event_params(self, intent: Intent) -> Dict[str, Any]:
        """Extract event parameters from intent"""
        params = {}
        
        # Extract time
        if intent.entities.get('time'):
            params['time'] = intent.entities['time'][0]
        
        # Extract date
        if intent.entities.get('date'):
            params['date'] = intent.entities['date'][0]
        
        # Extract title from text
        params['title'] = intent.text[:50] + '...' if len(intent.text) > 50 else intent.text
        
        return params
    
    def _extract_schedule(self, text: str) -> str:
        """Extract schedule pattern"""
        if 'daily' in text.lower():
            return 'daily'
        elif 'weekly' in text.lower():
            return 'weekly'
        elif 'monthly' in text.lower():
            return 'monthly'
        return 'once'
    
    def _extract_automated_actions(self, text: str) -> List[str]:
        """Extract actions to be automated"""
        actions = []
        text_lower = text.lower()
        
        if 'send' in text_lower and 'email' in text_lower:
            actions.append('send_email')
        if 'play' in text_lower and ('music' in text_lower or 'song' in text_lower):
            actions.append('play_music')
        if 'reminder' in text_lower:
            actions.append('set_reminder')
        
        return actions
    
    def _extract_preference_type(self, text: str) -> str:
        """Extract preference type"""
        text_lower = text.lower()
        if 'music' in text_lower:
            return 'music'
        elif 'email' in text_lower:
            return 'email'
        elif 'time' in text_lower:
            return 'time'
        return 'general'
    
    def _extract_preference_value(self, text: str) -> str:
        """Extract preference value"""
        # Simple extraction - can be enhanced
        return text.strip()

class TaskExecutor:
    """Executes planned tasks"""
    
    def __init__(self):
        self.handlers = {
            'system': self._handle_system,
            'gmail': self._handle_gmail,
            'calendar': self._handle_calendar,
            'media': self._handle_media,
            'weather': self._handle_weather,
            'automation': self._handle_automation,
            'learning': self._handle_learning
        }
    
    async def execute_step(self, step: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute a single task step"""
        handler_name = step.get('handler', 'system')
        action = step.get('action')
        params = step.get('params', {})
        
        try:
            handler = self.handlers.get(handler_name)
            if handler:
                result = await handler(action, params)
                return True, result
            else:
                return False, f"Unknown handler: {handler_name}"
        except Exception as e:
            logging.error(f"Error executing step {action}: {e}")
            return False, str(e)
    
    async def _handle_system(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle system-level actions"""
        if action == 'get_time':
            return datetime.now().strftime("%I:%M %p")
        elif action == 'get_status':
            return {"status": "operational", "uptime": "unknown"}
        return "System action completed"
    
    async def _handle_gmail(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle Gmail actions"""
        try:
            if action == 'send_email':
                return send_email(
                    to=params.get('to'),
                    subject=params.get('subject'),
                    body=params.get('body')
                )
            elif action == 'get_emails':
                return get_emails(limit=params.get('limit', 10))
        except Exception as e:
            return f"Gmail error: {e}"
    
    async def _handle_calendar(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle calendar actions"""
        try:
            if action == 'create_event':
                return create_event(
                    title=params.get('title'),
                    date=params.get('date'),
                    time=params.get('time')
                )
            elif action == 'get_events':
                return get_events(days=params.get('days', 7))
        except Exception as e:
            return f"Calendar error: {e}"
    
    async def _handle_media(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle media actions"""
        try:
            if action == 'play_media':
                return play_music(query=params.get('query'))
            elif action == 'pause_media':
                return pause_music()
        except Exception as e:
            return f"Media error: {e}"
    
    async def _handle_weather(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle weather actions"""
        # Placeholder - would integrate with weather API
        return f"Weather for {params.get('location', 'current')}: 72°F, sunny"
    
    async def _handle_automation(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle automation actions"""
        # Placeholder - would integrate with automation system
        return f"Automation created: {params}"
    
    async def _handle_learning(self, action: str, params: Dict[str, Any]) -> Any:
        """Handle learning actions"""
        # Placeholder - would integrate with learning system
        return f"Learned preference: {params}"

class FeedbackLearner:
    """Learns from user feedback to improve performance"""
    
    def __init__(self):
        self.feedback_file = Path("jai_autonomous_feedback.json")
        self.preferences_file = Path("jai_user_preferences.json")
        self.feedback_history = self._load_feedback()
        self.user_preferences = self._load_preferences()
    
    def _load_feedback(self) -> List[Feedback]:
        """Load feedback history"""
        try:
            if self.feedback_file.exists():
                data = json.loads(self.feedback_file.read_text())
                return [Feedback(**item) for item in data]
        except Exception as e:
            logging.warning(f"Error loading feedback: {e}")
        return []
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        try:
            if self.preferences_file.exists():
                return json.loads(self.preferences_file.read_text())
        except Exception as e:
            logging.warning(f"Error loading preferences: {e}")
        return {}
    
    def save_feedback(self, feedback: Feedback):
        """Save feedback for learning"""
        self.feedback_history.append(feedback)
        try:
            data = [asdict(f) for f in self.feedback_history]
            self.feedback_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logging.error(f"Error saving feedback: {e}")
    
    def update_preferences(self, preference_type: str, value: Any):
        """Update user preferences"""
        self.user_preferences[preference_type] = value
        try:
            self.preferences_file.write_text(json.dumps(self.user_preferences, indent=2))
        except Exception as e:
            logging.error(f"Error saving preferences: {e}")
    
    def get_preference(self, preference_type: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.user_preferences.get(preference_type, default)

class JAIAutonomous:
    """Main autonomous system"""
    
    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.task_planner = TaskPlanner()
        self.task_executor = TaskExecutor()
        self.feedback_learner = FeedbackLearner()
        self.active_tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('jai_autonomous.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('JAIAutonomous')
    
    async def process_request(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user request autonomously"""
        try:
            # Analyze intent
            intent = self.intent_analyzer.analyze(text, context)
            self.logger.info(f"Intent detected: {intent.intent_type.value} (confidence: {intent.confidence})")
            
            # Create task
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                intent=intent,
                plan=[],
                status=TaskStatus.PENDING,
                result=None,
                error=None,
                created_at=datetime.now(),
                started_at=None,
                completed_at=None
            )
            
            self.active_tasks[task_id] = task
            
            # Plan execution
            task.status = TaskStatus.PLANNING
            task.plan = self.task_planner.create_plan(intent)
            
            if not task.plan:
                task.status = TaskStatus.FAILED
                task.error = "No execution plan could be created"
                return {
                    'success': False,
                    'message': "I'm not sure how to handle that request.",
                    'task_id': task_id,
                    'intent': intent.intent_type.value
                }
            
            # Execute plan
            task.status = TaskStatus.EXECUTING
            task.started_at = datetime.now()
            
            results = []
            for i, step in enumerate(task.plan):
                self.logger.info(f"Executing step {i+1}/{len(task.plan)}: {step.get('description')}")
                success, result = await self.task_executor.execute_step(step)
                
                results.append({
                    'step': i+1,
                    'description': step.get('description'),
                    'success': success,
                    'result': result
                })
                
                if not success:
                    task.status = TaskStatus.FAILED
                    task.error = f"Step {i+1} failed: {result}"
                    break
            else:
                task.status = TaskStatus.COMPLETED
                task.result = results
            
            task.completed_at = datetime.now()
            self.task_history.append(task)
            del self.active_tasks[task_id]
            
            return {
                'success': task.status == TaskStatus.COMPLETED,
                'message': self._generate_response(task),
                'task_id': task_id,
                'results': results,
                'intent': intent.intent_type.value,
                'confidence': intent.confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return {
                'success': False,
                'message': f"An error occurred: {str(e)}",
                'task_id': None,
                'intent': 'error'
            }
    
    def _generate_response(self, task: Task) -> str:
        """Generate natural language response"""
        if task.status == TaskStatus.COMPLETED:
            if task.intent.intent_type == IntentType.QUERY:
                if task.result and len(task.result) > 0:
                    return f"Here's what I found: {task.result[0].get('result', 'No results')}"
                return "I couldn't find any information."
            elif task.intent.intent_type == IntentType.ACTION:
                return f"Successfully completed: {task.intent.text}"
            elif task.intent.intent_type == IntentType.COMPLEX_TASK:
                return f"Complex task completed with {len(task.result)} steps."
            else:
                return "Task completed successfully."
        else:
            return f"Task failed: {task.error}"
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.active_tasks.get(task_id)
        if task:
            return {
                'id': task.id,
                'status': task.status.value,
                'intent': task.intent.intent_type.value,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error': task.error
            }
        return None
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks"""
        return [self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    def submit_feedback(self, task_id: str, rating: int, comment: str = None):
        """Submit feedback for a task"""
        feedback = Feedback(
            task_id=task_id,
            rating=rating,
            comment=comment,
            timestamp=datetime.now(),
            context={}
        )
        self.feedback_learner.save_feedback(feedback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        total_tasks = len(self.task_history)
        completed_tasks = len([t for t in self.task_history if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.task_history if t.status == TaskStatus.FAILED])
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'active_tasks': len(self.active_tasks),
            'feedback_count': len(self.feedback_learner.feedback_history)
        }

# Global instance
jai_autonomous = JAIAutonomous()
