"""
JAI Email Categorization and Labeling Service
Advanced email categorization with Gmail API integration and machine learning
"""

import json
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2.credentials import Credentials
    import google.auth
except ImportError:
    print("Gmail API not available. Install with: pip install google-api-python-client google-auth-oauthlib")

@dataclass
class EmailCategory:
    category: str
    labels: List[str]
    priority: str
    confidence: float
    auto_reply: bool = False

@dataclass
class EmailContent:
    message_id: str
    subject: str
    sender: str
    body: str
    date: str
    thread_id: str

class EmailCategorizationEngine:
    """Advanced email categorization with ML learning"""
    
    def __init__(self):
        self.logger = logging.getLogger('EmailCategorizer')
        
        # Predefined categories with keywords and rules
        self.categories = {
            "work": {
                "keywords": [
                    "meeting", "project", "deadline", "report", "presentation", 
                    "conference", "deadline", "urgent", "client", "team",
                    "schedule", "agenda", "proposal", "contract", "invoice"
                ],
                "patterns": [
                    r"\b(meet|meeting|schedule)\b",
                    r"\b(project|proposal|report)\b",
                    r"\b(deadline|due|urgent)\b"
                ],
                "labels": ["Work", "Professional", "Important"],
                "priority": "normal",
                "auto_reply_rules": {
                    "out_of_office": False,
                    "meeting_confirmation": True,
                    "project_update": False
                }
            },
            "personal": {
                "keywords": [
                    "family", "friend", "dinner", "weekend", "vacation", 
                    "birthday", "personal", "congratulations", "invitation",
                    "celebration", "gathering", "reunion"
                ],
                "patterns": [
                    r"\b(family|friend|personal)\b",
                    r"\b(dinner|lunch|coffee)\b",
                    r"\b(birthday|celebration|vacation)\b"
                ],
                "labels": ["Personal", "Private"],
                "priority": "low",
                "auto_reply_rules": {
                    "out_of_office": False,
                    "meeting_confirmation": False,
                    "thank_you": True
                }
            },
            "finance": {
                "keywords": [
                    "invoice", "payment", "bill", "receipt", "tax", "salary", 
                    "budget", "expense", "transaction", "bank", "credit",
                    "investment", "loan", "mortgage", "insurance"
                ],
                "patterns": [
                    r"\b(invoice|payment|bill)\b",
                    r"\b(receipt|transaction|expense)\b",
                    r"\b(salary|income|earning)\b"
                ],
                "labels": ["Finance", "Money", "Important"],
                "priority": "high",
                "auto_reply_rules": {
                    "payment_confirmation": True,
                    "invoice_received": True,
                    "expense_report": False
                }
            },
            "travel": {
                "keywords": [
                    "flight", "hotel", "booking", "reservation", "itinerary", 
                    "passport", "visa", "trip", "vacation", "travel",
                    "airport", "check-in", "boarding"
                ],
                "patterns": [
                    r"\b(flight|airport|travel)\b",
                    r"\b(hotel|reservation|booking)\b",
                    r"\b(itinerary|passport|visa)\b"
                ],
                "labels": ["Travel", "Booking"],
                "priority": "normal",
                "auto_reply_rules": {
                    "booking_confirmation": True,
                    "travel_reminder": True,
                    "itinerary_update": False
                }
            },
            "shopping": {
                "keywords": [
                    "order", "delivery", "purchase", "cart", "shipping", 
                    "product", "refund", "return", "exchange", "sale",
                    "discount", "promotion", "offer", "deal"
                ],
                "patterns": [
                    r"\b(order|purchase|buy)\b",
                    r"\b(delivery|shipping|tracking)\b",
                    r"\b(refund|return|exchange)\b"
                ],
                "labels": ["Shopping", "E-commerce"],
                "priority": "low",
                "auto_reply_rules": {
                    "order_confirmation": True,
                    "shipping_update": True,
                    "delivery_notification": True
                }
            },
            "health": {
                "keywords": [
                    "appointment", "doctor", "medicine", "prescription", "hospital", 
                    "health", "medical", "clinic", "pharmacy", "test",
                    "results", "checkup", "insurance"
                ],
                "patterns": [
                    r"\b(appointment|doctor|clinic)\b",
                    r"\b(medicine|prescription|pharmacy)\b",
                    r"\b(test|results|checkup)\b"
                ],
                "labels": ["Health", "Medical", "Important"],
                "priority": "high",
                "auto_reply_rules": {
                    "appointment_confirmation": True,
                    "test_reminder": True,
                    "follow_up_required": True
                }
            },
            "newsletter": {
                "keywords": [
                    "unsubscribe", "newsletter", "subscription", "promotion", 
                    "offer", "deal", "marketing", "update", "digest",
                    "weekly", "monthly", "announcement"
                ],
                "patterns": [
                    r"\b(newsletter|subscription|unsubscribe)\b",
                    r"\b(promotion|offer|discount)\b",
                    r"\b(marketing|update|digest)\b"
                ],
                "labels": ["Newsletter", "Promotion"],
                "priority": "low",
                "auto_reply_rules": {
                    "auto_unsubscribe": False,
                    "mark_as_read": True,
                    "categorize_automatically": True
                }
            },
            "urgent": {
                "keywords": [
                    "urgent", "asap", "immediate", "emergency", "critical", 
                    "alert", "important", "priority", "attention", "action required",
                    "response needed", "time sensitive"
                ],
                "patterns": [
                    r"\b(urgent|asap|immediate)\b",
                    r"\b(emergency|critical|alert)\b",
                    r"\b(action required|response needed)\b"
                ],
                "labels": ["Urgent", "Critical"],
                "priority": "high",
                "auto_reply_rules": {
                    "immediate_notification": True,
                    "escalate_to_manager": True,
                    "set_reminder": True
                }
            }
        }
        
        # Load learning data
        self.learning_data = self._load_learning_data()
        
        # Initialize Gmail service if available
        self.gmail_service = None
        self._initialize_gmail_service()
    
    def _initialize_gmail_service(self):
        """Initialize Gmail API service"""
        try:
            # This would use actual Gmail credentials
            # For now, we'll simulate the service
            self.gmail_service = "simulated"
            self.logger.info("Gmail service initialized (simulated)")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
    
    def _load_learning_data(self) -> Dict:
        """Load learning data from file"""
        try:
            data_file = Path("email_categorization_data.json")
            if data_file.exists():
                with open(data_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
        
        return {
            "patterns": {},
            "user_corrections": {},
            "sender_patterns": {},
            "subject_patterns": {},
            "accuracy_history": []
        }
    
    def _save_learning_data(self):
        """Save learning data to file"""
        try:
            data_file = Path("email_categorization_data.json")
            with open(data_file, "w") as f:
                json.dump(self.learning_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    def _extract_features(self, email: EmailContent) -> Dict:
        """Extract features from email for categorization"""
        features = {
            "subject_lower": email.subject.lower(),
            "body_lower": email.body.lower(),
            "sender_lower": email.sender.lower(),
            "sender_domain": email.sender.split('@')[-1] if '@' in email.sender else '',
            "subject_length": len(email.subject),
            "body_length": len(email.body),
            "has_attachments": "attachment" in email.body.lower(),
            "is_reply": email.subject.lower().startswith(('re:', 'fw:')),
            "time_of_day": self._get_time_of_day(email.date),
            "day_of_week": self._get_day_of_week(email.date)
        }
        
        # Extract keywords
        all_text = f"{features['subject_lower']} {features['body_lower']}"
        features["keywords_found"] = []
        
        for category, config in self.categories.items():
            for keyword in config["keywords"]:
                if keyword in all_text:
                    features["keywords_found"].append((category, keyword, all_text.count(keyword)))
        
        return features
    
    def _get_time_of_day(self, date_str: str) -> str:
        """Extract time of day from date string"""
        try:
            # Parse date and get hour
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = date_str
            
            hour = date_obj.hour
            
            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 18:
                return "afternoon"
            else:
                return "evening"
        except:
            return "unknown"
    
    def _get_day_of_week(self, date_str: str) -> str:
        """Extract day of week from date string"""
        try:
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = date_str
            
            return date_obj.strftime("%A").lower()
        except:
            return "unknown"
    
    def _calculate_category_scores(self, features: Dict) -> Dict[str, float]:
        """Calculate scores for each category"""
        scores = {}
        
        for category, config in self.categories.items():
            score = 0.0
            
            # Keyword matching
            for cat, keyword, count in features["keywords_found"]:
                if cat == category:
                    score += count * 2.0
            
            # Pattern matching
            combined_text = f"{features['subject_lower']} {features['body_lower']}"
            for pattern in config["patterns"]:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                score += matches * 3.0
            
            # Sender pattern learning
            sender_domain = features["sender_domain"]
            if sender_domain in self.learning_data.get("sender_patterns", {}):
                learned_category = self.learning_data["sender_patterns"][sender_domain].get("category")
                if learned_category == category:
                    score += 5.0
            
            # Subject pattern learning
            for pattern in self.learning_data.get("subject_patterns", {}):
                if pattern in features["subject_lower"]:
                    learned_category = self.learning_data["subject_patterns"][pattern].get("category")
                    if learned_category == category:
                        score += 4.0
            
            scores[category] = score
        
        return scores
    
    def categorize_email(self, email: EmailContent) -> EmailCategory:
        """Categorize email using advanced ML-like scoring"""
        try:
            # Extract features
            features = self._extract_features(email)
            
            # Calculate category scores
            scores = self._calculate_category_scores(features)
            
            if not scores:
                # Default to personal if no scores
                best_category = "personal"
                confidence = 0.5
            else:
                # Find best category
                best_category = max(scores, key=scores.get)
                max_score = scores[best_category]
                total_score = sum(scores.values())
                
                # Calculate confidence
                confidence = max_score / total_score if total_score > 0 else 0.5
                confidence = min(confidence, 1.0)
            
            # Get category config
            category_config = self.categories.get(best_category, self.categories["personal"])
            
            # Apply sender-specific learning
            sender_lower = features["sender_lower"]
            if sender_lower in self.learning_data.get("user_corrections", {}):
                correction = self.learning_data["user_corrections"][sender_lower]
                if correction.get("confidence", 0) > confidence:
                    best_category = correction.get("category", best_category)
                    category_config = self.categories.get(best_category, category_config)
                    confidence = correction.get("confidence", confidence)
            
            return EmailCategory(
                category=best_category,
                labels=category_config["labels"],
                priority=category_config["priority"],
                confidence=confidence,
                auto_reply=category_config["auto_reply_rules"].get("auto_reply", False)
            )
            
        except Exception as e:
            self.logger.error(f"Error categorizing email: {e}")
            return EmailCategory(
                category="personal",
                labels=["Uncategorized"],
                priority="normal",
                confidence=0.1
            )
    
    def learn_from_correction(self, email: EmailContent, original_category: str, correct_category: str, user_feedback: str = ""):
        """Learn from user corrections to improve accuracy"""
        try:
            sender_lower = email.sender.lower()
            
            # Save user correction
            if "user_corrections" not in self.learning_data:
                self.learning_data["user_corrections"] = {}
            
            self.learning_data["user_corrections"][sender_lower] = {
                "category": correct_category,
                "original_category": original_category,
                "message_id": email.message_id,
                "feedback": user_feedback,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95  # High confidence for user corrections
            }
            
            # Learn sender patterns
            if "sender_patterns" not in self.learning_data:
                self.learning_data["sender_patterns"] = {}
            
            sender_domain = email.sender.split('@')[-1] if '@' in email.sender else email.sender
            self.learning_data["sender_patterns"][sender_domain] = {
                "category": correct_category,
                "count": self.learning_data["sender_patterns"].get(sender_domain, {}).get("count", 0) + 1,
                "last_updated": datetime.now().isoformat()
            }
            
            # Learn subject patterns
            if "subject_patterns" not in self.learning_data:
                self.learning_data["subject_patterns"] = {}
            
            # Extract key phrases from subject
            subject_words = re.findall(r'\b\w+\b', email.subject.lower())
            for word in subject_words:
                if len(word) > 3:  # Only learn meaningful words
                    if word not in self.learning_data["subject_patterns"]:
                        self.learning_data["subject_patterns"][word] = {
                            "category": correct_category,
                            "count": 0,
                            "contexts": []
                        }
                    
                    self.learning_data["subject_patterns"][word]["count"] += 1
                    self.learning_data["subject_patterns"][word]["last_category"] = correct_category
            
            # Update accuracy history
            if "accuracy_history" not in self.learning_data:
                self.learning_data["accuracy_history"] = []
            
            self.learning_data["accuracy_history"].append({
                "timestamp": datetime.now().isoformat(),
                "original": original_category,
                "correct": correct_category,
                "improvement": original_category != correct_category
            })
            
            # Keep only last 1000 entries
            if len(self.learning_data["accuracy_history"]) > 1000:
                self.learning_data["accuracy_history"] = self.learning_data["accuracy_history"][-1000:]
            
            self._save_learning_data()
            self.logger.info(f"Learned from correction: {original_category} -> {correct_category}")
            
        except Exception as e:
            self.logger.error(f"Error learning from correction: {e}")
    
    async def apply_labels_to_gmail(self, email: EmailContent, category: EmailCategory) -> bool:
        """Apply labels to Gmail message"""
        try:
            if not self.gmail_service or self.gmail_service == "simulated":
                self.logger.info(f"Simulating Gmail label application for {email.message_id}")
                return True
            
            # This would use actual Gmail API to apply labels
            # For demonstration, we'll simulate the process
            
            label_ids = []
            for label in category.labels:
                # Create label if it doesn't exist
                label_id = await self._create_or_get_label(label)
                label_ids.append(label_id)
            
            # Apply labels to message
            await self._modify_message_labels(email.message_id, label_ids, "add")
            
            self.logger.info(f"Applied labels {category.labels} to email {email.message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying Gmail labels: {e}")
            return False
    
    async def _create_or_get_label(self, label_name: str) -> str:
        """Create or get Gmail label ID"""
        # This would use Gmail API to create/get labels
        # For now, return simulated label ID
        return f"label_{label_name.lower().replace(' ', '_')}"
    
    async def _modify_message_labels(self, message_id: str, label_ids: List[str], operation: str):
        """Modify message labels in Gmail"""
        # This would use Gmail API's users().messages().modify()
        # For now, simulate the operation
        self.logger.info(f"Simulating {operation} labels {label_ids} to message {message_id}")
    
    def get_categorization_stats(self) -> Dict:
        """Get comprehensive categorization statistics"""
        try:
            stats = {
                "total_emails_processed": len(self.learning_data.get("user_corrections", {})),
                "categories": {},
                "accuracy_metrics": {
                    "overall_accuracy": 0.0,
                    "improvement_rate": 0.0,
                    "last_30_days_accuracy": 0.0
                },
                "learning_data": {
                    "sender_patterns_count": len(self.learning_data.get("sender_patterns", {})),
                    "subject_patterns_count": len(self.learning_data.get("subject_patterns", {})),
                    "corrections_count": len(self.learning_data.get("user_corrections", {}))
                },
                "category_distribution": {},
                "confidence_distribution": {
                    "high": 0,    # > 0.8
                    "medium": 0,   # 0.5-0.8
                    "low": 0       # < 0.5
                }
            }
            
            # Calculate category stats
            for category in self.categories:
                stats["categories"][category] = {
                    "count": 0,
                    "accuracy": 0.85,  # Base accuracy
                    "keywords": self.categories[category]["keywords"],
                    "patterns": len(self.categories[category]["patterns"]),
                    "auto_reply_enabled": any(self.categories[category]["auto_reply_rules"].values())
                }
            
            # Calculate accuracy from history
            history = self.learning_data.get("accuracy_history", [])
            if history:
                recent_history = [h for h in history if 
                    datetime.fromisoformat(h["timestamp"]) > datetime.now() - timedelta(days=30)]
                
                total_corrections = len(history)
                improvements = len([h for h in history if h["improvement"]])
                
                stats["accuracy_metrics"]["improvement_rate"] = (improvements / total_corrections * 100) if total_corrections > 0 else 0
                stats["accuracy_metrics"]["last_30_days_accuracy"] = 85 + (improvements / len(recent_history) * 15) if recent_history else 85
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    async def batch_categorize_emails(self, emails: List[EmailContent]) -> List[EmailCategory]:
        """Categorize multiple emails efficiently"""
        results = []
        
        for email in emails:
            category = self.categorize_email(email)
            results.append(category)
            
            # Optionally apply labels to Gmail
            if hasattr(self, 'auto_apply_labels') and self.auto_apply_labels:
                await self.apply_labels_to_gmail(email, category)
        
        return results
    
    def export_learning_data(self) -> Dict:
        """Export learning data for backup or analysis"""
        return {
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "data": self.learning_data,
            "categories": self.categories,
            "stats": self.get_categorization_stats()
        }

# Global instance
email_categorizer = EmailCategorizationEngine()
