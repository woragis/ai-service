"""
Cost tracking and optimization metrics.

This module tracks resource usage and cost-related metrics to help optimize
deployment costs.
"""

from prometheus_client import Gauge, Counter, Histogram
from app.logger import get_logger

logger = get_logger()

# Cost-related metrics
cost_cpu_usage = Gauge(
    'cost_cpu_usage_cores',
    'Current CPU usage in cores',
    ['pod', 'node']
)

cost_memory_usage = Gauge(
    'cost_memory_usage_bytes',
    'Current memory usage in bytes',
    ['pod', 'node']
)

cost_request_cost = Histogram(
    'cost_request_cost_usd',
    'Estimated cost per request in USD',
    ['endpoint', 'provider'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

cost_total_requests = Counter(
    'cost_total_requests',
    'Total number of requests (for cost calculation)',
    ['endpoint']
)

cost_provider_api_calls = Counter(
    'cost_provider_api_calls_total',
    'Total API calls to external providers',
    ['provider', 'model']
)

cost_provider_tokens = Counter(
    'cost_provider_tokens_total',
    'Total tokens processed by providers',
    ['provider', 'model', 'type']  # type: input/output
)

# Resource utilization metrics
resource_utilization = Gauge(
    'resource_utilization_percent',
    'Resource utilization percentage',
    ['resource_type']  # cpu, memory
)


class CostTracker:
    """Tracks cost and resource usage metrics."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def record_request(self, endpoint: str, provider: str = None, cost_usd: float = 0.0):
        """
        Record a request for cost tracking.
        
        Args:
            endpoint: The endpoint path
            provider: Provider used (e.g., 'openai', 'anthropic')
            cost_usd: Estimated cost in USD
        """
        cost_total_requests.labels(endpoint=endpoint).inc()
        
        if provider and cost_usd > 0:
            cost_request_cost.labels(
                endpoint=endpoint,
                provider=provider
            ).observe(cost_usd)
    
    def record_api_call(self, provider: str, model: str):
        """Record an API call to external provider."""
        cost_provider_api_calls.labels(
            provider=provider,
            model=model
        ).inc()
    
    def record_tokens(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        """Record token usage for cost calculation."""
        if input_tokens > 0:
            cost_provider_tokens.labels(
                provider=provider,
                model=model,
                type="input"
            ).inc(input_tokens)
        
        if output_tokens > 0:
            cost_provider_tokens.labels(
                provider=provider,
                model=model,
                type="output"
            ).inc(output_tokens)
    
    def update_resource_usage(self, cpu_cores: float, memory_bytes: int, pod: str = "unknown", node: str = "unknown"):
        """
        Update resource usage metrics.
        
        Note: In Kubernetes, this would typically be scraped by cAdvisor.
        This is for manual tracking if needed.
        """
        cost_cpu_usage.labels(pod=pod, node=node).set(cpu_cores)
        cost_memory_usage.labels(pod=pod, node=node).set(memory_bytes)


# Global cost tracker instance
cost_tracker = CostTracker()


def estimate_request_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate cost per request based on provider and token usage.
    
    Note: These are example pricing. Update with actual provider pricing.
    """
    # Example pricing (update with actual pricing)
    pricing = {
        "openai": {
            "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
            "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        },
        "anthropic": {
            "claude-3-5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
        },
    }
    
    provider_pricing = pricing.get(provider, {})
    model_pricing = provider_pricing.get(model, {"input": 0.0, "output": 0.0})
    
    input_cost = input_tokens * model_pricing.get("input", 0.0)
    output_cost = output_tokens * model_pricing.get("output", 0.0)
    
    return input_cost + output_cost

