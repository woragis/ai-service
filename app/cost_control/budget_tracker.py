"""
Budget tracking and enforcement.

Tracks spending against budget limits and enforces per-request limits.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from threading import Lock
from app.logger import get_logger
from app.cost_control.policy import get_cost_control_policy_loader

logger = get_logger()


class BudgetTracker:
    """
    Tracks budget usage and enforces limits.
    
    Note: This is an in-memory implementation. For production, consider
    using Redis or a database for distributed tracking.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self._lock = Lock()
        self._daily_spending: Dict[str, float] = {}  # date -> amount
        self._monthly_spending: Dict[str, float] = {}  # YYYY-MM -> amount
        self._last_reset: Optional[datetime] = None
    
    def _get_date_key(self) -> str:
        """Get current date key for daily tracking."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_month_key(self) -> str:
        """Get current month key for monthly tracking."""
        return datetime.now().strftime("%Y-%m")
    
    def _should_reset_daily(self) -> bool:
        """Check if daily budget should be reset."""
        policy = get_cost_control_policy_loader().get_policy()
        reset_hour = policy.budget.reset_hour
        
        now = datetime.now()
        if self._last_reset is None:
            return True
        
        # Reset if we've passed the reset hour today
        if now.hour >= reset_hour and self._last_reset.hour < reset_hour:
            return True
        
        # Reset if it's a new day
        if now.date() > self._last_reset.date():
            return True
        
        return False
    
    def _reset_if_needed(self):
        """Reset daily spending if needed."""
        if self._should_reset_daily():
            date_key = self._get_date_key()
            if date_key not in self._daily_spending:
                self._daily_spending[date_key] = 0.0
            self._last_reset = datetime.now()
            self.logger.debug("Daily budget reset", date=date_key)
    
    def record_spending(self, amount_usd: float) -> Tuple[bool, Optional[str]]:
        """
        Record spending and check if it exceeds limits.
        
        Args:
            amount_usd: Amount spent in USD
        
        Returns:
            Tuple of (allowed, error_message)
        """
        if amount_usd <= 0:
            return True, None
        
        policy = get_cost_control_policy_loader().get_policy()
        
        if not policy.budget.enabled:
            return True, None
        
        with self._lock:
            self._reset_if_needed()
            
            # Check per-request limit
            if amount_usd > policy.budget.per_request_limit_usd:
                error_msg = f"Request cost ${amount_usd:.4f} exceeds per-request limit ${policy.budget.per_request_limit_usd:.2f}"
                self.logger.warn("Request rejected due to per-request limit", 
                               cost=amount_usd, limit=policy.budget.per_request_limit_usd)
                return False, error_msg
            
            # Get current spending
            date_key = self._get_date_key()
            month_key = self._get_month_key()
            
            daily_spent = self._daily_spending.get(date_key, 0.0)
            monthly_spent = self._monthly_spending.get(month_key, 0.0)
            
            # Check daily limit
            if daily_spent + amount_usd > policy.budget.daily_limit_usd:
                error_msg = f"Daily budget limit exceeded. Spent: ${daily_spent:.2f}, Limit: ${policy.budget.daily_limit_usd:.2f}"
                self.logger.warn("Request rejected due to daily budget limit",
                               daily_spent=daily_spent, limit=policy.budget.daily_limit_usd)
                return False, error_msg
            
            # Check monthly limit
            if monthly_spent + amount_usd > policy.budget.monthly_limit_usd:
                error_msg = f"Monthly budget limit exceeded. Spent: ${monthly_spent:.2f}, Limit: ${policy.budget.monthly_limit_usd:.2f}"
                self.logger.warn("Request rejected due to monthly budget limit",
                               monthly_spent=monthly_spent, limit=policy.budget.monthly_limit_usd)
                return False, error_msg
            
            # Record spending
            self._daily_spending[date_key] = daily_spent + amount_usd
            self._monthly_spending[month_key] = monthly_spent + amount_usd
            
            self.logger.debug("Spending recorded", 
                            amount=amount_usd, 
                            daily_total=self._daily_spending[date_key],
                            monthly_total=self._monthly_spending[month_key])
            
            return True, None
    
    def get_current_spending(self) -> Dict[str, float]:
        """Get current spending statistics."""
        with self._lock:
            self._reset_if_needed()
            date_key = self._get_date_key()
            month_key = self._get_month_key()
            
            return {
                "daily": self._daily_spending.get(date_key, 0.0),
                "monthly": self._monthly_spending.get(month_key, 0.0),
            }
    
    def get_budget_limits(self) -> Dict[str, float]:
        """Get current budget limits."""
        policy = get_cost_control_policy_loader().get_policy()
        return {
            "daily_limit_usd": policy.budget.daily_limit_usd,
            "monthly_limit_usd": policy.budget.monthly_limit_usd,
            "per_request_limit_usd": policy.budget.per_request_limit_usd,
        }
    
    def reset_budget(self, reset_type: str = "daily"):
        """
        Manually reset budget (for testing/admin purposes).
        
        Args:
            reset_type: "daily" or "monthly"
        """
        with self._lock:
            if reset_type == "daily":
                date_key = self._get_date_key()
                self._daily_spending[date_key] = 0.0
                self.logger.info("Daily budget manually reset", date=date_key)
            elif reset_type == "monthly":
                month_key = self._get_month_key()
                self._monthly_spending[month_key] = 0.0
                self.logger.info("Monthly budget manually reset", month=month_key)
            else:
                raise ValueError(f"Invalid reset_type: {reset_type}")


# Global budget tracker instance
_budget_tracker: Optional[BudgetTracker] = None


def get_budget_tracker() -> BudgetTracker:
    """Get the global budget tracker instance."""
    global _budget_tracker
    if _budget_tracker is None:
        _budget_tracker = BudgetTracker()
    return _budget_tracker

