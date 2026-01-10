import os
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.runnables import Runnable
from fastapi.responses import StreamingResponse
import json

from app.agents import get_agent_names, get_agent, build_agent_with_model, build_system_message, get_rag_context
from app.providers import make_model, CipherClient
from app.routing import select_provider_and_model, execute_with_fallback
from app.config import settings, validate_required_env_vars
from app.cost_tracking import cost_tracker, estimate_request_cost
from app.cost_control import (
    validate_token_limits,
    estimate_and_check_cost,
    get_budget_tracker,
    get_token_limits,
    get_cost_routing_config,
)
from app.caching import get_cache_manager
from app.security import (
    check_content_filter,
    check_pii,
    mask_pii,
    check_prompt_injection,
    sanitize_response,
)
from app.quality import (
    validate_length,
    validate_format,
    validate_quality,
    check_toxicity,
    sanitize_toxicity,
)
from app.features import is_rag_enabled, is_provider_enabled
from app.logger import configure_logging, get_logger
from app.middleware import RequestIDMiddleware, RequestLoggerMiddleware
from app.middleware_slo import SLOTrackingMiddleware
from app.middleware_timeout import TimeoutMiddleware
from app.tracing import init_tracing, get_trace_id, set_trace_id
from app.graceful_shutdown import lifespan
from prometheus_fastapi_instrumentator import Instrumentator


load_dotenv()

# Validate required environment variables first
validate_required_env_vars()

# Configure structured logging
env = os.getenv("ENV", "development")
log_to_file = os.getenv("LOG_TO_FILE", "false").lower() == "true"
log_dir = os.getenv("LOG_DIR", "logs")
configure_logging(env=env, log_to_file=log_to_file, log_dir=log_dir)

logger = get_logger()
logger.info("AI service initialized", env=env)

# Initialize OpenTelemetry tracing
try:
    init_tracing(
        service_name="ai-service",
        service_version="0.1.0",
        environment=env,
    )
    logger.info("Tracing initialized")
except Exception as e:
    logger.warn("Failed to initialize tracing", error=str(e))

app = FastAPI(
    title="Woragis AI Service",
    version="0.1.0",
    lifespan=lifespan
)

# Add middleware for request ID, logging, SLO tracking, and timeouts
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(SLOTrackingMiddleware)
app.add_middleware(TimeoutMiddleware)

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

if settings.CORS_ENABLED:
    origins = settings.CORS_ALLOWED_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class ChatRequest(BaseModel):
    agent: str = Field(..., description="Agent persona name or 'auto'")
    input: str = Field(..., description="User input or question")
    system: Optional[str] = Field(
        None, description="Optional additional system instruction")
    temperature: Optional[float] = Field(
        None, description="Optional temperature override")
    model: Optional[str] = Field(None, description="Optional model override")
    provider: Optional[Literal["openai", "anthropic", "xai", "manus", "cipher"]] = Field(
        "openai", description="LLM provider")


class ChatResponse(BaseModel):
    agent: str
    output: str


class ChatStreamRequest(ChatRequest):
    pass


class ImageRequest(BaseModel):
    provider: Literal["cipher"] = Field("cipher", description="Image provider")
    prompt: str = Field(..., description="Image generation prompt")
    n: Optional[int] = Field(None, description="Number of images to generate")
    size: Optional[str] = Field(
        None, description="Image size, e.g., 1024x1024")


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None


class ImageResponse(BaseModel):
    data: list[ImageData]


@app.get("/v1/agents", response_model=list[str])
def list_agents():
    return get_agent_names()


@app.post("/v1/agents/reload")
def reload_agents():
    """Reload agent policies (hot reload)."""
    from app.agents.policy import get_policy_loader
    policy_loader = get_policy_loader()
    policy_loader.reload()
    logger.info("Agent policies reloaded")
    return {"status": "success", "message": "Agent policies reloaded", "agents": get_agent_names()}


@app.get("/v1/cost/budget")
def get_budget_status():
    """Get current budget spending and limits."""
    budget_tracker = get_budget_tracker()
    spending = budget_tracker.get_current_spending()
    limits = budget_tracker.get_budget_limits()

    return {
        "spending": spending,
        "limits": limits,
        "remaining": {
            "daily": max(0, limits["daily_limit_usd"] - spending["daily"]),
            "monthly": max(0, limits["monthly_limit_usd"] - spending["monthly"]),
        }
    }


@app.get("/v1/cost/token-limits")
def get_token_limits_endpoint():
    """Get current token limits configuration."""
    return get_token_limits()


@app.get("/v1/cost/routing-config")
def get_cost_routing_config_endpoint():
    """Get current cost routing configuration."""
    return get_cost_routing_config()


@app.post("/v1/cost/reload")
def reload_cost_control():
    """Reload cost control policies (hot reload)."""
    from app.cost_control.policy import get_cost_control_policy_loader
    policy_loader = get_cost_control_policy_loader()
    policy_loader.reload()
    logger.info("Cost control policies reloaded")
    return {"status": "success", "message": "Cost control policies reloaded"}


@app.get("/v1/cache/stats")
def get_cache_stats():
    """Get cache statistics."""
    cache_manager = get_cache_manager()
    return cache_manager.get_stats()


@app.post("/v1/cache/clear")
def clear_cache():
    """Clear all caches."""
    cache_manager = get_cache_manager()
    cache_manager.clear()
    logger.info("Cache cleared")
    return {"status": "success", "message": "Cache cleared"}


@app.post("/v1/cache/reload")
def reload_cache_policies():
    """Reload caching policies (hot reload)."""
    from app.caching.policy import get_caching_policy_loader
    from app.caching.cache_manager import reset_cache_manager
    policy_loader = get_caching_policy_loader()
    policy_loader.reload()
    # Reinitialize cache manager with new policies
    reset_cache_manager()
    logger.info("Caching policies reloaded")
    return {"status": "success", "message": "Caching policies reloaded"}


@app.post("/v1/security/reload")
def reload_security_policies():
    """Reload security policies (hot reload)."""
    from app.security.policy import get_security_policy_loader
    policy_loader = get_security_policy_loader()
    policy_loader.reload()
    logger.info("Security policies reloaded")
    return {"status": "success", "message": "Security policies reloaded"}


@app.get("/v1/quality/length-limits")
def get_quality_length_limits(agent: str = ""):
    """Get length limits configuration."""
    from app.quality import get_length_limits
    return get_length_limits(agent_name=agent)


@app.get("/v1/quality/format-config")
def get_quality_format_config():
    """Get format validation configuration."""
    from app.quality import get_format_config
    return get_format_config()


@app.get("/v1/quality/quality-config")
def get_quality_checks_config():
    """Get quality checks configuration."""
    from app.quality import get_quality_config
    return get_quality_config()


@app.get("/v1/quality/toxicity-config")
def get_quality_toxicity_config():
    """Get toxicity detection configuration."""
    from app.quality import get_toxicity_config
    return get_toxicity_config()


@app.post("/v1/quality/reload")
def reload_quality_policies():
    """Reload quality policies (hot reload)."""
    from app.quality.policy import get_quality_policy_loader
    policy_loader = get_quality_policy_loader()
    policy_loader.reload()
    logger.info("Quality policies reloaded")
    return {"status": "success", "message": "Quality policies reloaded"}


@app.get("/v1/features/config")
def get_features_config():
    """Get feature flags configuration."""
    from app.features import get_feature_config
    return get_feature_config()


@app.post("/v1/features/reload")
def reload_feature_policies():
    """Reload feature flag policies (hot reload)."""
    from app.features.policy import get_feature_policy_loader
    policy_loader = get_feature_policy_loader()
    policy_loader.reload()
    logger.info("Feature policies reloaded")
    return {"status": "success", "message": "Feature policies reloaded"}


@app.post("/v1/routing/reload")
def reload_routing():
    """Reload routing policies (hot reload)."""
    from app.routing.policy import get_routing_policy_loader
    policy_loader = get_routing_policy_loader()
    policy_loader.reload()
    logger.info("Routing policies reloaded")
    return {"status": "success", "message": "Routing policies reloaded"}


@app.post("/v1/resilience/reload")
def reload_resilience():
    """Reload resilience policies (hot reload)."""
    from app.resilience.policy import get_resilience_policy_loader
    policy_loader = get_resilience_policy_loader()
    policy_loader.reload()
    logger.info("Resilience policies reloaded")
    return {"status": "success", "message": "Resilience policies reloaded"}


def _apply_overrides(chain: Runnable, model_name: Optional[str], temperature: Optional[float]) -> Runnable:
    # For simple chains, we rebuild only if overrides provided
    if model_name or temperature is not None:
        from langchain_openai import ChatOpenAI
        new_model = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature if temperature is not None else float(
                os.getenv("OPENAI_TEMPERATURE", "0.3")),
            timeout=60,
        )
        # We cannot introspect the prompt here reliably; rebuild via agents registry is clearer
        # For now, just return a simple prompt rebuild using the same agent name via query param usage.
        # In practice, callers should set env vars if they need global overrides.
        return new_model
    return chain


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info(
        "chat request",
        agent=req.agent,
        provider=(req.provider or "openai").lower(),
        model=req.model or "",
        has_system=bool(req.system),
        temperature=req.temperature,
    )

    # Validate agent name early (before processing)
    try:
        agent_names = get_agent_names()
        # Ensure it's a list (handle case where mock returns Mock object)
        if not isinstance(agent_names, list):
            agent_names = []
        valid_agents = agent_names + ["auto"]
        if req.agent not in valid_agents:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid agent '{req.agent}'. Valid agents: {', '.join(valid_agents)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        # If get_agent_names fails, still try to process but will fail later with 404
        logger.warn("Failed to validate agent name",
                    error=str(e), agent=req.agent)

    # Simple heuristic for auto agent selection
    def pick_agent_auto(text: str) -> str:
        lowered = (text or "").lower()
        if any(k in lowered for k in ["market", "inflation", "macro", "econom", "unit economics", "pricing"]):
            return "economist"
        if any(k in lowered for k in ["strategy", "positioning", "go-to-market", "gtm", "competitor", "moat"]):
            return "strategist"
        if any(k in lowered for k in ["mvp", "launch", "prototype", "hack", "validate", "scrappy"]):
            return "entrepreneur"
        return "startup"

    agent_name = req.agent if req.agent != "auto" else pick_agent_auto(
        req.input)

    # Security checks on input
    # Check prompt injection
    injection_allowed, injection_error = check_prompt_injection(req.input)
    if not injection_allowed:
        raise HTTPException(status_code=400, detail=injection_error)

    # Check content filter
    content_allowed, content_error = check_content_filter(req.input)
    if not content_allowed:
        raise HTTPException(status_code=400, detail=content_error)

    # Check and mask PII in input if needed
    pii_allowed, pii_error, pii_counts = check_pii(req.input)
    if not pii_allowed:
        raise HTTPException(status_code=400, detail=pii_error)

    # Mask PII in input if policy requires it
    input_text = req.input
    if pii_counts:
        input_text, _ = mask_pii(input_text)
        if input_text != req.input:
            logger.info("PII masked in input", pii_counts=pii_counts)

    # Get RAG context if enabled for this agent
    rag_context = None
    if is_rag_enabled(agent_name):
        rag_context = await get_rag_context(agent_name, input_text)

    # Estimate input tokens (simple approximation: ~4 chars per token)
    if req.system:
        input_text = f"{req.system}\n\n{input_text}"
    if rag_context:
        input_text = f"{rag_context}\n\n{input_text}"

    estimated_input_tokens = len(input_text) // 4  # Rough estimate

    # Validate token limits before processing
    token_valid, token_error = validate_token_limits(estimated_input_tokens)
    if not token_valid:
        raise HTTPException(status_code=400, detail=token_error)

    # Select provider and model using routing policies
    # Can be overridden per request in future
    cost_mode = os.getenv("COST_MODE", "balanced")
    selected_provider, selected_model, fallback_chain = select_provider_and_model(
        requested_provider=req.provider,
        requested_model=req.model,
        query=req.input,
        agent_name=agent_name,
        cost_mode=cost_mode,
        enable_fallback=True,
    )

    provider = selected_provider
    model = selected_model or req.model

    # Check if provider is enabled
    if not is_provider_enabled(provider):
        raise HTTPException(
            status_code=400, detail=f"Provider '{provider}' is disabled")

    # Check cache before processing
    cache_manager = get_cache_manager()
    cached_response = cache_manager.get(
        query=req.input,
        agent_name=agent_name,
        provider=provider,
        model=model,
        endpoint="/v1/chat"
    )

    if cached_response is not None:
        logger.info("Cache hit", agent=agent_name,
                    provider=provider, model=model)
        return ChatResponse(agent=agent_name, output=cached_response)

    # Estimate cost and check budget before processing
    estimated_cost, budget_allowed, budget_error = estimate_and_check_cost(
        provider=provider,
        model=model or "default",
        input_tokens=estimated_input_tokens,
        output_tokens=0  # Will be updated after response
    )

    if not budget_allowed:
        raise HTTPException(status_code=429, detail=budget_error)

    # Cipher provider: call external API directly (query string API key, OpenAI-like JSON)
    if provider == "cipher":
        system_text = build_system_message(agent_name)
        if not system_text:
            raise HTTPException(
                status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

        messages = [{"role": "system", "content": system_text}]
        if req.system:
            messages.append({"role": "system", "content": req.system})
        # Add RAG context if available
        if rag_context:
            messages.append({"role": "system", "content": rag_context})
        messages.append({"role": "user", "content": req.input})

        client = CipherClient.from_env()
        text = await client.chat(
            messages=messages,
            temperature=req.temperature if req.temperature is not None else settings.DEFAULT_TEMPERATURE,
            max_tokens=settings.CIPHER_MAX_TOKENS,
            top_p=settings.CIPHER_TOP_P,
        )
        return ChatResponse(agent=agent_name, output=text)

    # Default: build model via LangChain with fallback support
    async def _execute_chat(attempt_provider: str, attempt_model: Optional[str]):
        """Execute chat with a specific provider/model."""
        try:
            model_obj = make_model(
                attempt_provider, attempt_model, req.temperature)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        chain = build_agent_with_model(agent_name, model_obj)
        if not chain:
            raise HTTPException(
                status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

        # Optionally augment with extra system instruction by prepending a SystemMessage
        # Use masked input_text if PII was masked
        inputs = input_text
        if req.system:
            # Simple concatenation to include system guidance
            inputs = f"{req.system}\n\nUser: {input_text}"

        # Add RAG context to input if available
        if rag_context:
            inputs = rag_context + "\n\nUser Query: " + inputs

        logger.info("invoking chat chain", agent=agent_name, provider=attempt_provider,
                    model=attempt_model, has_rag_context=bool(rag_context))
        # The prompt template expects both 'agent_name' and 'input' variables
        result = await chain.ainvoke({
            "agent_name": agent_name.title() + " Agent",
            "input": inputs
        })
        if hasattr(result, "content"):
            return result.content  # AIMessage
        else:
            return str(result)

    # Execute with fallback chain and resilience
    try:
        output_text = await execute_with_fallback(
            provider,
            model,
            fallback_chain,
            _execute_chat,
            endpoint="/v1/chat"
        )
    except Exception as e:
        logger.error("Chat execution failed", error=str(
            e), provider=provider, fallback_chain=fallback_chain)
        raise HTTPException(
            status_code=500, detail=f"Chat execution failed: {str(e)}")

    logger.info("chat completed", agent=agent_name,
                output_len=len(output_text))

    # Quality checks
    # Validate length
    length_valid, length_error = validate_length(output_text, agent_name)
    if not length_valid:
        raise HTTPException(status_code=500, detail=length_error)

    # Validate format
    format_valid, format_error, detected_format = validate_format(output_text)
    if not format_valid:
        raise HTTPException(status_code=500, detail=format_error)

    # Validate quality (coherence and relevance)
    quality_valid, quality_error, quality_scores = validate_quality(
        req.input, output_text, agent_name)
    if not quality_valid:
        logger.warn("Quality check failed",
                    scores=quality_scores, error=quality_error)
        # Don't block, just log warning for now (can be made configurable)

    # Check toxicity
    toxicity_allowed, toxicity_error, toxicity_score = check_toxicity(
        output_text)
    if not toxicity_allowed:
        raise HTTPException(status_code=500, detail=toxicity_error)

    # Sanitize response
    sanitized_output = sanitize_response(output_text)

    # Sanitize toxicity if needed
    if toxicity_score > 0:
        sanitized_output = sanitize_toxicity(sanitized_output)

    # Check and mask PII in response if needed
    response_pii_allowed, response_pii_error, response_pii_counts = check_pii(
        sanitized_output)
    if not response_pii_allowed:
        # If blocking is enabled, return error; otherwise mask
        raise HTTPException(status_code=500, detail=response_pii_error)

    # Mask PII in response if policy requires it
    final_output = sanitized_output
    if response_pii_counts:
        final_output, _ = mask_pii(sanitized_output)
        if final_output != sanitized_output:
            logger.info("PII masked in response",
                        pii_counts=response_pii_counts)

    # Store in cache (use original input for cache key, but sanitized output for value)
    try:
        cache_manager.set(
            query=req.input,  # Use original input for cache key
            agent_name=agent_name,
            provider=provider,
            model=model,
            value=final_output,  # Store sanitized output
            endpoint="/v1/chat"
        )
    except Exception as e:
        logger.warn("Failed to store in cache", error=str(e))

    # Estimate output tokens and final cost
    estimated_output_tokens = len(final_output) // 4  # Rough estimate
    final_cost = estimate_request_cost(
        provider, model or "default", estimated_input_tokens, estimated_output_tokens)

    # Track cost and tokens
    try:
        cost_tracker.record_request(
            endpoint="/v1/chat",
            provider=provider,
            cost_usd=final_cost
        )
        cost_tracker.record_api_call(
            provider=provider, model=model or "default")
        cost_tracker.record_tokens(
            provider=provider,
            model=model or "default",
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens
        )
    except Exception as e:
        logger.warn("Failed to record cost metrics", error=str(e))

    return ChatResponse(agent=agent_name, output=final_output)


@app.get("/healthz")
def healthz():
    """
    Health check endpoint.
    Returns service availability and dependency status.
    """
    from app.health import check_health
    result = check_health()

    # Determine HTTP status code
    status_code = 200
    if result["status"] == "unhealthy":
        status_code = 503

    return JSONResponse(content=result, status_code=status_code)


@app.post("/v1/images", response_model=ImageResponse)
async def generate_images(req: ImageRequest):
    provider = (req.provider or "cipher").lower()
    if provider != "cipher":
        raise HTTPException(
            status_code=400, detail="Only provider 'cipher' is supported for images currently")

    prompt = req.prompt
    n = req.n if req.n is not None else settings.CIPHER_IMAGE_N
    size = req.size if req.size else settings.CIPHER_IMAGE_SIZE

    client = CipherClient.from_env()
    items = await client.generate_images(prompt=prompt, n=n, size=size)
    # Normalize to ImageData
    normalized = []
    for item in items:
        normalized.append(ImageData(url=item.get("url"),
                          b64_json=item.get("b64_json")))
    return ImageResponse(data=normalized)


@app.post("/v1/chat/stream")
async def chat_stream(req: ChatStreamRequest):
    logger.info(
        "chat stream request",
        agent=req.agent,
        provider=(req.provider or "openai").lower(),
        model=req.model or "",
        has_system=bool(req.system),
        temperature=req.temperature,
    )

    # Validate agent name early (before processing)
    try:
        agent_names = get_agent_names()
        # Ensure it's a list (handle case where mock returns Mock object)
        if not isinstance(agent_names, list):
            agent_names = []
        valid_agents = agent_names + ["auto"]
        if req.agent not in valid_agents:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid agent '{req.agent}'. Valid agents: {', '.join(valid_agents)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        # If get_agent_names fails, still try to process but will fail later with 404
        logger.warn("Failed to validate agent name",
                    error=str(e), agent=req.agent)

    # Select provider and model using routing policies
    cost_mode = os.getenv("COST_MODE", "balanced")
    selected_provider, selected_model, fallback_chain = select_provider_and_model(
        requested_provider=req.provider,
        requested_model=req.model,
        query=req.input,
        agent_name=req.agent,
        cost_mode=cost_mode,
        enable_fallback=True,
    )

    provider = selected_provider
    model = selected_model or req.model

    # Check if provider is enabled
    if not is_provider_enabled(provider):
        raise HTTPException(
            status_code=400, detail=f"Provider '{provider}' is disabled")

    def pick_agent_auto(text: str) -> str:
        lowered = (text or "").lower()
        if any(k in lowered for k in ["market", "inflation", "macro", "econom", "unit economics", "pricing"]):
            return "economist"
        if any(k in lowered for k in ["strategy", "positioning", "go-to-market", "gtm", "competitor", "moat"]):
            return "strategist"
        if any(k in lowered for k in ["mvp", "launch", "prototype", "hack", "validate", "scrappy"]):
            return "entrepreneur"
        return "startup"

    agent_name = req.agent if req.agent != "auto" else pick_agent_auto(
        req.input)

    # Check if streaming is enabled
    from app.features import is_streaming_enabled
    if not is_streaming_enabled("/v1/chat/stream"):
        raise HTTPException(
            status_code=400, detail="Streaming is disabled for this endpoint")

    # Get RAG context if enabled for this agent
    rag_context = None
    if is_rag_enabled(agent_name):
        rag_context = await get_rag_context(agent_name, req.input)

    # Prepare input
    inputs = req.input
    if req.system:
        inputs = f"{req.system}\n\nUser: {req.input}"

    # Add RAG context to input if available
    if rag_context:
        inputs = rag_context + "\n\nUser Query: " + inputs

    # Cipher has no documented streaming: return one full chunk then done
    if provider == "cipher":
        system_text = build_system_message(agent_name) or ""
        messages = [{"role": "system", "content": system_text}]
        if req.system:
            messages.append({"role": "system", "content": req.system})
        # Add RAG context if available
        if rag_context:
            messages.append({"role": "system", "content": rag_context})
        messages.append({"role": "user", "content": req.input})

        client = CipherClient.from_env()
        text = await client.chat(
            messages=messages,
            temperature=req.temperature if req.temperature is not None else settings.DEFAULT_TEMPERATURE,
            max_tokens=settings.CIPHER_MAX_TOKENS,
            top_p=settings.CIPHER_TOP_P,
        )

        async def _gen_once():
            yield json.dumps({"delta": text}) + "\n"
            yield json.dumps({"done": True}) + "\n"

        return StreamingResponse(_gen_once(), media_type="application/x-ndjson")

    # LangChain-supported streaming with fallback
    async def _execute_stream(attempt_provider: str, attempt_model: Optional[str]):
        """Execute streaming chat with a specific provider/model."""
        try:
            model_obj = make_model(
                attempt_provider, attempt_model, req.temperature)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        chain = build_agent_with_model(agent_name, model_obj)
        if not chain:
            raise HTTPException(
                status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

        async def event_gen():
            logger.info("stream started", agent=agent_name, provider=attempt_provider,
                        model=attempt_model, has_rag_context=bool(rag_context))
            full_parts = []
            try:
                # The prompt template expects both 'agent_name' and 'input' variables
                async for event in chain.astream_events({
                    "agent_name": agent_name.title() + " Agent",
                    "input": inputs
                }, version="v1"):
                    if event.get("event") in ("on_chat_model_stream", "on_llm_new_token"):
                        data = event.get("data", {})
                        chunk = None
                        if "chunk" in data and hasattr(data["chunk"], "content"):
                            chunk = data["chunk"].content
                        elif "token" in data:
                            chunk = data["token"]
                        if chunk:
                            full_parts.append(chunk)
                            yield json.dumps({"delta": chunk}) + "\n"
            except Exception as e:
                logger.exception("stream error", exc_info=True)
                yield json.dumps({"error": str(e)}) + "\n"
            final_text = "".join(full_parts)
            logger.info("stream completed", agent=agent_name,
                        output_len=len(final_text))
            yield json.dumps({"done": True, "output": final_text}) + "\n"

        return event_gen()

    # For streaming, we can't easily use fallback (streaming is stateful)
    # So we'll just try the primary provider
    try:
        event_gen = await _execute_stream(provider, model)
        return StreamingResponse(event_gen, media_type="application/x-ndjson")
    except Exception as e:
        logger.error("Stream execution failed, trying fallback",
                     error=str(e), provider=provider)
        # Try first fallback if available
        if fallback_chain:
            try:
                event_gen = await _execute_stream(fallback_chain[0], model)
                return StreamingResponse(event_gen, media_type="application/x-ndjson")
            except Exception as fallback_error:
                logger.error("Fallback stream also failed",
                             error=str(fallback_error))
                raise HTTPException(
                    status_code=500, detail=f"Stream execution failed: {str(fallback_error)}")
        raise HTTPException(
            status_code=500, detail=f"Stream execution failed: {str(e)}")
