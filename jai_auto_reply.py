"""
JAI Auto-Reply System
Smart auto-reply functionality using Hugging Face language models
"""

import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    HF_AVAILABLE = True
except ImportError:
    print("Hugging Face transformers not available. Install with: pip install transformers torch")
    HF_AVAILABLE = False

try:
    from jai_email_categorizer import email_categorizer, EmailContent
except ImportError:
    print("Email categorizer not available")
    email_categorizer = None

@dataclass
class ConversationContext:
    """Maintains conversation context for smart replies"""
    conversation_id: str
    messages: List[Dict]
    last_reply_time: datetime
    user_preferences: Dict
    context_summary: str = ""
    
@dataclass
class AutoReplyConfig:
    """Configuration for auto-reply behavior"""
    enabled: bool = True
    max_replies_per_hour: int = 10
    delay_seconds: int = 30
    confidence_threshold: float = 0.7
    auto_reply_categories: List[str] = None
    exclude_senders: List[str] = None
    working_hours_only: bool = True
    working_hours: Tuple[int, int] = (9, 17)  # 9 AM to 5 PM
    timezone: str = "UTC"
    
    def __post_init__(self):
        if self.auto_reply_categories is None:
            self.auto_reply_categories = ["work", "finance", "health", "urgent"]
        if self.exclude_senders is None:
            self.exclude_senders = ["noreply@", "no-reply@", "spam@", "notifications@"]

class AutoReplyEngine:
    """Advanced auto-reply engine with Hugging Face integration"""
    
    def __init__(self, config: AutoReplyConfig = None):
        self.logger = logging.getLogger('AutoReplyEngine')
        self.config = config or AutoReplyConfig()
        
        # Conversation contexts
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Reply rate limiting
        self.reply_counts: Dict[str, int] = {}
        self.last_reset = datetime.now()
        
        # Hugging Face model
        self.model = None
        self.tokenizer = None
        self.generator = None
        
        # Load model
        if HF_AVAILABLE:
            self._load_huggingface_model()
        
        # Load conversation history
        self._load_conversation_history()
        
        # Auto-reply templates for fallback
        self.reply_templates = self._load_reply_templates()
    
    def _load_huggingface_model(self):
        """Load Hugging Face model for smart replies"""
        try:
            # Use a smaller, efficient model for auto-replies
            model_name = "microsoft/DialoGPT-medium"  # Good for conversational AI
            
            self.logger.info(f"Loading Hugging Face model: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                padding_side='left',
                truncation=True,
                max_length=512
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=150,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            self.logger.info("Hugging Face model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Hugging Face model: {e}")
            self.logger.info("Falling back to template-based replies")
    
    def _load_conversation_history(self):
        """Load conversation history from file"""
        try:
            history_file = Path("auto_reply_conversations.json")
            if history_file.exists():
                with open(history_file, "r") as f:
                    data = json.load(f)
                    
                # Convert back to ConversationContext objects
                for conv_id, conv_data in data.items():
                    conv_data['last_reply_time'] = datetime.fromisoformat(conv_data['last_reply_time'])
                    self.conversations[conv_id] = ConversationContext(**conv_data)
                
                self.logger.info(f"Loaded {len(self.conversations)} conversation contexts")
        except Exception as e:
            self.logger.error(f"Error loading conversation history: {e}")
    
    def _save_conversation_history(self):
        """Save conversation history to file"""
        try:
            history_file = Path("auto_reply_conversations.json")
            data = {}
            
            for conv_id, context in self.conversations.items():
                conv_dict = asdict(context)
                conv_dict['last_reply_time'] = context.last_reply_time.isoformat()
                data[conv_id] = conv_dict
            
            with open(history_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving conversation history: {e}")
    
    def _load_reply_templates(self) -> Dict[str, List[str]]:
        """Load fallback reply templates"""
        return {
            "work": [
                "Thank you for your message. I've received your {subject} and will review it shortly.",
                "I appreciate you reaching out about {subject}. I'll get back to you within 24 hours.",
                "Got your message regarding {subject}. Let me look into this and respond appropriately."
            ],
            "personal": [
                "Thanks for reaching out! I'll respond when I'm available.",
                "Received your message. I'll get back to you soon.",
                "Thanks for the message! I appreciate you thinking of me."
            ],
            "finance": [
                "Thank you for the financial information. I'll review and process accordingly.",
                "I've received your financial document and will address it promptly.",
                "Your financial communication has been received and is under review."
            ],
            "health": [
                "Thank you for the health-related information. I'll review and respond as needed.",
                "I've received your health communication and will address it appropriately.",
                "Your health-related message has been received and will be handled with priority."
            ],
            "urgent": [
                "I've received your urgent message and am addressing it immediately.",
                "Thank you for the urgent notification. I'm taking action now.",
                "Your urgent message has been received and is being handled with priority."
            ],
            "travel": [
                "Thank you for the travel information. I'll review the details and respond.",
                "I've received your travel-related message and will process accordingly.",
                "Your travel communication has been received and is under review."
            ],
            "shopping": [
                "Thank you for the order/shopping information. I'll review and respond as needed.",
                "I've received your shopping-related message and will address it.",
                "Your shopping communication has been received and is being processed."
            ],
            "newsletter": [
                "Thank you for the newsletter. I appreciate the updates.",
                "I've received your newsletter and appreciate the information.",
                "Thanks for keeping me informed with your newsletter."
            ]
        }
    
    def _should_auto_reply(self, email: EmailContent) -> Tuple[bool, str]:
        """Determine if email should be auto-replied"""
        if not self.config.enabled:
            return False, "Auto-reply disabled"
        
        # Check excluded senders
        sender_lower = email.sender.lower()
        for exclude in self.config.exclude_senders:
            if exclude in sender_lower:
                return False, f"Sender excluded: {exclude}"
        
        # Check working hours
        if self.config.working_hours_only:
            current_hour = datetime.now().hour
            start_hour, end_hour = self.config.working_hours
            if not (start_hour <= current_hour < end_hour):
                return False, "Outside working hours"
        
        # Check rate limiting
        self._reset_reply_counts_if_needed()
        sender_domain = email.sender.split('@')[-1] if '@' in email.sender else email.sender
        if self.reply_counts.get(sender_domain, 0) >= self.config.max_replies_per_hour:
            return False, "Rate limit exceeded"
        
        # Check category
        if email_categorizer:
            category = email_categorizer.categorize_email(email)
            if category.category not in self.config.auto_reply_categories:
                return False, f"Category not auto-replied: {category.category}"
        
        # Check if recently replied to this conversation
        conv_id = self._get_conversation_id(email)
        if conv_id in self.conversations:
            last_reply = self.conversations[conv_id].last_reply_time
            if datetime.now() - last_reply < timedelta(hours=1):
                return False, "Recently replied to this conversation"
        
        return True, "Should auto-reply"
    
    def _get_conversation_id(self, email: EmailContent) -> str:
        """Generate conversation ID from email"""
        # Use thread_id if available, otherwise use sender
        return email.thread_id or email.sender
    
    def _update_conversation_context(self, email: EmailContent, reply: str):
        """Update conversation context with new message and reply"""
        conv_id = self._get_conversation_id(email)
        
        if conv_id not in self.conversations:
            self.conversations[conv_id] = ConversationContext(
                conversation_id=conv_id,
                messages=[],
                last_reply_time=datetime.now(),
                user_preferences={}
            )
        
        context = self.conversations[conv_id]
        context.messages.append({
            "timestamp": datetime.now().isoformat(),
            "sender": email.sender,
            "subject": email.subject,
            "body": email.body,
            "reply": reply,
            "type": "incoming"
        })
        
        # Keep only last 10 messages to avoid context bloat
        if len(context.messages) > 10:
            context.messages = context.messages[-10:]
        
        context.last_reply_time = datetime.now()
        
        # Update reply count
        sender_domain = email.sender.split('@')[-1] if '@' in email.sender else email.sender
        self.reply_counts[sender_domain] = self.reply_counts.get(sender_domain, 0) + 1
    
    def _reset_reply_counts_if_needed(self):
        """Reset reply counts every hour"""
        if datetime.now() - self.last_reset > timedelta(hours=1):
            self.reply_counts.clear()
            self.last_reset = datetime.now()
    
    def _generate_smart_reply(self, email: EmailContent) -> str:
        """Generate smart reply using Hugging Face model"""
        if not self.generator:
            return self._generate_template_reply(email)
        
        try:
            # Build conversation context
            conv_id = self._get_conversation_id(email)
            context = self.conversations.get(conv_id, ConversationContext(
                conversation_id=conv_id,
                messages=[],
                last_reply_time=datetime.now(),
                user_preferences={}
            ))
            
            # Create prompt with context
            recent_messages = context.messages[-3:]  # Last 3 messages for context
            context_text = ""
            
            for msg in recent_messages:
                context_text += f"Previous: {msg.get('body', '')[:100]}...\n"
            
            prompt = f"""You are a helpful assistant generating an auto-reply. Be professional, concise, and natural.

Context: {context_text}
New message from {email.sender} with subject "{email.subject}":
{email.body[:200]}...

Generate a brief, professional reply:"""
            
            # Generate response
            responses = self.generator(
                prompt,
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9,
                num_return_sequences=1,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            if responses and len(responses) > 0:
                reply = responses[0]['generated_text'].strip()
                
                # Clean up the reply
                reply = reply.replace(prompt, "").strip()
                
                # Take only the first sentence or two
                sentences = re.split(r'[.!?]+', reply)
                if len(sentences) > 2:
                    reply = '. '.join(sentences[:2]) + '.'
                
                return reply if reply else self._generate_template_reply(email)
            
        except Exception as e:
            self.logger.error(f"Error generating smart reply: {e}")
        
        return self._generate_template_reply(email)
    
    def _generate_template_reply(self, email: EmailContent) -> str:
        """Generate template-based reply as fallback"""
        if email_categorizer:
            category = email_categorizer.categorize_email(email)
            category_name = category.category
        else:
            category_name = "personal"
        
        templates = self.reply_templates.get(category_name, self.reply_templates["personal"])
        
        # Select template based on time of day and previous replies
        import random
        template = random.choice(templates)
        
        # Personalize template
        reply = template.format(
            subject=email.subject[:50] + "..." if len(email.subject) > 50 else email.subject,
            sender_name=email.sender.split('@')[0] if '@' in email.sender else email.sender
        )
        
        return reply
    
    async def process_incoming_email(self, email: EmailContent) -> Dict:
        """Process incoming email and generate auto-reply if appropriate"""
        try:
            # Check if should auto-reply
            should_reply, reason = self._should_auto_reply(email)
            
            if not should_reply:
                return {
                    "success": True,
                    "auto_replied": False,
                    "reason": reason,
                    "message_id": email.message_id
                }
            
            # Generate reply
            reply = self._generate_smart_reply(email)
            
            # Update conversation context
            self._update_conversation_context(email, reply)
            
            # Save conversation history
            self._save_conversation_history()
            
            # In a real implementation, this would send the email
            # For now, we'll return the reply for sending
            sent_success = await self._send_reply(email, reply)
            
            return {
                "success": True,
                "auto_replied": True,
                "reply": reply,
                "message_id": email.message_id,
                "sent": sent_success,
                "confidence": 0.85 if self.generator else 0.6
            }
            
        except Exception as e:
            self.logger.error(f"Error processing incoming email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": email.message_id
            }
    
    async def _send_reply(self, email: EmailContent, reply: str) -> bool:
        """Send auto-reply (placeholder for actual email sending)"""
        try:
            # This would integrate with Gmail API to send actual reply
            self.logger.info(f"Auto-reply to {email.sender}: {reply[:50]}...")
            
            # Simulate sending delay
            await asyncio.sleep(0.1)
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending reply: {e}")
            return False
    
    def get_conversation_stats(self) -> Dict:
        """Get conversation and auto-reply statistics"""
        total_conversations = len(self.conversations)
        total_messages = sum(len(ctx.messages) for ctx in self.conversations.values())
        
        category_counts = {}
        for context in self.conversations.values():
            for msg in context.messages:
                # This would be enhanced with actual categorization
                category = "unknown"
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "active_conversations_24h": len([
                ctx for ctx in self.conversations.values()
                if datetime.now() - ctx.last_reply_time < timedelta(hours=24)
            ]),
            "category_distribution": category_counts,
            "reply_counts_current_hour": dict(self.reply_counts),
            "model_loaded": self.generator is not None,
            "config": asdict(self.config)
        }
    
    def update_config(self, new_config: Dict):
        """Update auto-reply configuration"""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config: {key} = {value}")
        
        # Reload model if needed
        if new_config.get("reload_model") and HF_AVAILABLE:
            self._load_huggingface_model()

# Global auto-reply engine instance
auto_reply_engine = AutoReplyEngine()
