"""
Structured error codes for AI Service
Error code format: SERVICE_CATEGORY_NUMBER
Each code should be used in exactly one place for easy tracking
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """Error code constants"""

    # VALIDATION - Input validation errors (4000-4099)
    VALIDATION_INVALID_INPUT = "AI_4001"
    VALIDATION_MISSING_FIELD = "AI_4002"
    VALIDATION_INVALID_MESSAGES = "AI_4003"
    VALIDATION_EMPTY_PROMPT = "AI_4004"
    VALIDATION_INVALID_MODEL = "AI_4005"
    VALIDATION_INVALID_TEMPERATURE = "AI_4006"
    VALIDATION_INVALID_MAX_TOKENS = "AI_4007"

    # PROVIDER - AI Provider errors (5000-5099)
    PROVIDER_NOT_FOUND = "AI_5001"
    PROVIDER_UNAVAILABLE = "AI_5002"
    PROVIDER_API_KEY_MISSING = "AI_5003"
    PROVIDER_API_KEY_INVALID = "AI_5004"
    PROVIDER_RATE_LIMITED = "AI_5005"
    PROVIDER_QUOTA_EXCEEDED = "AI_5006"
    PROVIDER_REQUEST_FAILED = "AI_5007"
    PROVIDER_INVALID_RESPONSE = "AI_5008"
    PROVIDER_TIMEOUT = "AI_5009"
    PROVIDER_MODEL_NOT_SUPPORTED = "AI_5010"

    # AGENT - Agent/Tool errors (6000-6099)
    AGENT_NOT_FOUND = "AI_6001"
    AGENT_EXECUTION_FAILED = "AI_6002"
    AGENT_INVALID_CONFIG = "AI_6003"
    AGENT_TOOL_NOT_FOUND = "AI_6004"
    AGENT_TOOL_EXECUTION_FAILED = "AI_6005"

    # CONTENT - Content moderation errors (7000-7099)
    CONTENT_POLICY_VIOLATION = "AI_7001"
    CONTENT_TOXIC_DETECTED = "AI_7002"
    CONTENT_PII_DETECTED = "AI_7003"
    CONTENT_PROMPT_INJECTION = "AI_7004"
    CONTENT_FILTER_ERROR = "AI_7005"

    # COST - Cost control errors (8000-8099)
    COST_BUDGET_EXCEEDED = "AI_8001"
    COST_TOKEN_LIMIT_EXCEEDED = "AI_8002"
    COST_TRACKING_FAILED = "AI_8003"

    # CACHE - Caching errors (8100-8199)
    CACHE_GET_FAILED = "AI_8101"
    CACHE_SET_FAILED = "AI_8102"
    CACHE_INVALID_KEY = "AI_8103"

    # SERVER - Server/System errors (9000-9099)
    SERVER_INTERNAL_ERROR = "AI_9001"
    SERVER_SERVICE_UNAVAILABLE = "AI_9002"
    SERVER_TIMEOUT = "AI_9003"
    SERVER_CONTEXT_CANCELLED = "AI_9004"
    SERVER_CONFIG_ERROR = "AI_9005"


# Error messages mapping
ERROR_MESSAGES = {
    # Validation
    ErrorCode.VALIDATION_INVALID_INPUT: "Invalid input provided",
    ErrorCode.VALIDATION_MISSING_FIELD: "Required field is missing",
    ErrorCode.VALIDATION_INVALID_MESSAGES: "Invalid messages format",
    ErrorCode.VALIDATION_EMPTY_PROMPT: "Prompt cannot be empty",
    ErrorCode.VALIDATION_INVALID_MODEL: "Invalid model specified",
    ErrorCode.VALIDATION_INVALID_TEMPERATURE: "Temperature must be between 0 and 2",
    ErrorCode.VALIDATION_INVALID_MAX_TOKENS: "Invalid max_tokens value",

    # Provider
    ErrorCode.PROVIDER_NOT_FOUND: "AI provider not found",
    ErrorCode.PROVIDER_UNAVAILABLE: "AI provider is temporarily unavailable",
    ErrorCode.PROVIDER_API_KEY_MISSING: "API key is not configured",
    ErrorCode.PROVIDER_API_KEY_INVALID: "API key is invalid",
    ErrorCode.PROVIDER_RATE_LIMITED: "Rate limit exceeded for AI provider",
    ErrorCode.PROVIDER_QUOTA_EXCEEDED: "API quota exceeded",
    ErrorCode.PROVIDER_REQUEST_FAILED: "AI provider request failed",
    ErrorCode.PROVIDER_INVALID_RESPONSE: "AI provider returned invalid response",
    ErrorCode.PROVIDER_TIMEOUT: "AI provider request timeout",
    ErrorCode.PROVIDER_MODEL_NOT_SUPPORTED: "Model is not supported by this provider",

    # Agent
    ErrorCode.AGENT_NOT_FOUND: "Agent not found",
    ErrorCode.AGENT_EXECUTION_FAILED: "Agent execution failed",
    ErrorCode.AGENT_INVALID_CONFIG: "Invalid agent configuration",
    ErrorCode.AGENT_TOOL_NOT_FOUND: "Agent tool not found",
    ErrorCode.AGENT_TOOL_EXECUTION_FAILED: "Agent tool execution failed",

    # Content
    ErrorCode.CONTENT_POLICY_VIOLATION: "Content violates usage policy",
    ErrorCode.CONTENT_TOXIC_DETECTED: "Toxic content detected",
    ErrorCode.CONTENT_PII_DETECTED: "Personal identifiable information detected",
    ErrorCode.CONTENT_PROMPT_INJECTION: "Potential prompt injection detected",
    ErrorCode.CONTENT_FILTER_ERROR: "Content filtering failed",

    # Cost
    ErrorCode.COST_BUDGET_EXCEEDED: "Cost budget exceeded",
    ErrorCode.COST_TOKEN_LIMIT_EXCEEDED: "Token limit exceeded",
    ErrorCode.COST_TRACKING_FAILED: "Failed to track costs",

    # Cache
    ErrorCode.CACHE_GET_FAILED: "Failed to retrieve from cache",
    ErrorCode.CACHE_SET_FAILED: "Failed to store in cache",
    ErrorCode.CACHE_INVALID_KEY: "Invalid cache key",

    # Server
    ErrorCode.SERVER_INTERNAL_ERROR: "Internal server error occurred",
    ErrorCode.SERVER_SERVICE_UNAVAILABLE: "Service is temporarily unavailable",
    ErrorCode.SERVER_TIMEOUT: "Request timeout",
    ErrorCode.SERVER_CONTEXT_CANCELLED: "Request was cancelled",
    ErrorCode.SERVER_CONFIG_ERROR: "Service configuration error",
}


def get_message(code: ErrorCode) -> str:
    """Get human-readable message for error code"""
    return ERROR_MESSAGES.get(code, "Unknown error occurred")


class AppError(Exception):
    """Structured application error"""

    def __init__(
        self,
        code: ErrorCode,
        details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.code = code
        self.message = get_message(code)
        self.details = details
        self.context = context or {}
        self.original_error = original_error

        # Build error message
        msg = f"[{code}] {self.message}"
        if details:
            msg += f": {details}"
        super().__init__(msg)

    def to_http_status(self) -> int:
        """Map error code to HTTP status code"""
        if self.code in [
            ErrorCode.VALIDATION_INVALID_INPUT,
            ErrorCode.VALIDATION_MISSING_FIELD,
            ErrorCode.VALIDATION_INVALID_MESSAGES,
            ErrorCode.VALIDATION_EMPTY_PROMPT,
            ErrorCode.VALIDATION_INVALID_MODEL,
            ErrorCode.VALIDATION_INVALID_TEMPERATURE,
            ErrorCode.VALIDATION_INVALID_MAX_TOKENS,
            ErrorCode.AGENT_INVALID_CONFIG,
        ]:
            return 400

        if self.code in [
            ErrorCode.PROVIDER_API_KEY_MISSING,
            ErrorCode.PROVIDER_API_KEY_INVALID,
        ]:
            return 401

        if self.code in [
            ErrorCode.CONTENT_POLICY_VIOLATION,
            ErrorCode.CONTENT_TOXIC_DETECTED,
            ErrorCode.CONTENT_PII_DETECTED,
            ErrorCode.CONTENT_PROMPT_INJECTION,
        ]:
            return 403

        if self.code in [
            ErrorCode.PROVIDER_NOT_FOUND,
            ErrorCode.AGENT_NOT_FOUND,
            ErrorCode.AGENT_TOOL_NOT_FOUND,
        ]:
            return 404

        if self.code in [
            ErrorCode.PROVIDER_RATE_LIMITED,
        ]:
            return 429

        if self.code in [
            ErrorCode.PROVIDER_UNAVAILABLE,
            ErrorCode.SERVER_SERVICE_UNAVAILABLE,
        ]:
            return 503

        if self.code in [
            ErrorCode.PROVIDER_TIMEOUT,
            ErrorCode.SERVER_TIMEOUT,
        ]:
            return 504

        # Default to 500
        return 500

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        result = {
            "code": self.code.value,
            "message": self.message,
        }

        if self.details:
            result["details"] = self.details

        if self.context:
            result["context"] = self.context

        return result


def error_response(error: AppError) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "success": False,
        "error": error.to_dict()
    }
