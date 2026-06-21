from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
# For production, consider using Redis or similar
class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: defaultdict[int, list[float]] = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        # Remove old requests outside the window
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if now - timestamp < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        
        return False
    
    def get_remaining_time(self, user_id: int) -> float:
        if not self.requests[user_id]:
            return 0.0
        
        oldest = min(self.requests[user_id])
        return max(0.0, self.window_seconds - (time.time() - oldest))


# Global rate limiter instance
_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)


def rate_limit_middleware(handler: Callable) -> Callable:
    """Middleware to rate limit handlers."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_user is None:
            return
        
        user_id = update.effective_user.id
        
        if not _rate_limiter.is_allowed(user_id):
            remaining = _rate_limiter.get_remaining_time(user_id)
            logger.warning("Rate limit exceeded for user %d", user_id)
            
            if update.message:
                await update.message.reply_text(
                    f"⚠️ Слишком много запросов. Попробуйте через {int(remaining)} сек."
                )
            return
        
        await handler(update, context)
    
    return wrapper
