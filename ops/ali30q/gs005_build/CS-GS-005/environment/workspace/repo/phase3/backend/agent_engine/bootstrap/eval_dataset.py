"""
Evaluation Dataset - Fixed test data for measuring prompt performance.

Like autoresearch's prepare.py: this is the constant against which
improvements are measured. Never modified by the agent.
"""
import json
from typing import List, Dict


def get_sentiment_eval_set() -> List[Dict]:
    """20 sentiment classification items with ground truth labels."""
    return [
        {"id": 1, "text": "This product is absolutely amazing, best purchase ever!", "label": "positive"},
        {"id": 2, "text": "Terrible experience. Will never buy again.", "label": "negative"},
        {"id": 3, "text": "It works as expected, nothing special.", "label": "neutral"},
        {"id": 4, "text": "Love it! Changed my life completely.", "label": "positive"},
        {"id": 5, "text": "Broke after one day. Total waste of money.", "label": "negative"},
        {"id": 6, "text": "Decent quality for the price.", "label": "neutral"},
        {"id": 7, "text": "Exceeded all my expectations!", "label": "positive"},
        {"id": 8, "text": "Worst customer service I've ever dealt with.", "label": "negative"},
        {"id": 9, "text": "Average product, does what it says.", "label": "neutral"},
        {"id": 10, "text": "Five stars! Everyone should get one!", "label": "positive"},
        {"id": 11, "text": "Arrived damaged and seller refused refund.", "label": "negative"},
        {"id": 12, "text": "It's fine. Neither good nor bad.", "label": "neutral"},
        {"id": 13, "text": "Incredible value, highly recommend!", "label": "positive"},
        {"id": 14, "text": "Stopped working after a week. Junk.", "label": "negative"},
        {"id": 15, "text": "Standard item, meets basic needs.", "label": "neutral"},
        {"id": 16, "text": "My kids love it, great gift idea!", "label": "positive"},
        {"id": 17, "text": "Misleading description. Not as advertised.", "label": "negative"},
        {"id": 18, "text": "Functional but nothing to write home about.", "label": "neutral"},
        {"id": 19, "text": "This is the best thing since sliced bread!", "label": "positive"},
        {"id": 20, "text": "Complete disaster from start to finish.", "label": "negative"},
    ]


def get_spam_eval_set() -> List[Dict]:
    """15 spam classification items with ground truth labels."""
    return [
        {"id": 1, "text": "Congratulations! You've won $1,000,000! Click NOW!", "label": "SPAM"},
        {"id": 2, "text": "Hi team, the quarterly report is ready for review.", "label": "HAM"},
        {"id": 3, "text": "URGENT: Your account will be suspended unless you verify", "label": "SPAM"},
        {"id": 4, "text": "Reminder: dentist appointment tomorrow at 2pm.", "label": "HAM"},
        {"id": 5, "text": "Make $5000/day working from home! No experience needed!", "label": "SPAM"},
        {"id": 6, "text": "Can you pick up milk on your way home?", "label": "HAM"},
        {"id": 7, "text": "FREE iPhone 15! Limited time offer! Act fast!", "label": "SPAM"},
        {"id": 8, "text": "The meeting has been moved to 3pm in Conference Room B.", "label": "HAM"},
        {"id": 9, "text": "You have been selected for an exclusive investment opportunity", "label": "SPAM"},
        {"id": 10, "text": "Thanks for the great presentation today.", "label": "HAM"},
        {"id": 11, "text": "Lose 30 pounds in 30 days! Guaranteed results!", "label": "SPAM"},
        {"id": 12, "text": "Attached is the updated project timeline.", "label": "HAM"},
        {"id": 13, "text": "ALERT: Unusual login detected. Verify your identity here.", "label": "SPAM"},
        {"id": 14, "text": "Happy birthday! Hope you have a wonderful day.", "label": "HAM"},
        {"id": 15, "text": "Claim your FREE gift card before midnight tonight!", "label": "SPAM"},
    ]


def get_intent_eval_set() -> List[Dict]:
    """15 intent classification items with ground truth labels."""
    return [
        {"id": 1, "text": "I want to return this item", "label": "return_request"},
        {"id": 2, "text": "What are your business hours?", "label": "information_query"},
        {"id": 3, "text": "My package hasn't arrived yet", "label": "delivery_issue"},
        {"id": 4, "text": "Can I speak to a manager?", "label": "escalation"},
        {"id": 5, "text": "How do I reset my password?", "label": "account_help"},
        {"id": 6, "text": "I'd like to place a new order", "label": "new_order"},
        {"id": 7, "text": "The product I received is defective", "label": "complaint"},
        {"id": 8, "text": "Do you ship internationally?", "label": "information_query"},
        {"id": 9, "text": "I want to cancel my subscription", "label": "cancellation"},
        {"id": 10, "text": "Thank you for your help!", "label": "gratitude"},
        {"id": 11, "text": "Where is my refund?", "label": "return_request"},
        {"id": 12, "text": "Can I change my delivery address?", "label": "delivery_issue"},
        {"id": 13, "text": "I need a receipt for my purchase", "label": "information_query"},
        {"id": 14, "text": "This is unacceptable service", "label": "complaint"},
        {"id": 15, "text": "What payment methods do you accept?", "label": "information_query"},
    ]


def get_all_eval_sets() -> Dict[str, List[Dict]]:
    """Get all evaluation datasets."""
    return {
        "sentiment": get_sentiment_eval_set(),
        "spam": get_spam_eval_set(),
        "intent": get_intent_eval_set(),
    }
