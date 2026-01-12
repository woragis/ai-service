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

from app.agents import get_agent_names, get_agent, build_agent_with_model, build_system_message
from app.providers import make_model, CipherClient
from app.config import settings
from app.logger import configure_logging, get_logger
from app.middleware import RequestIDMiddleware, RequestLoggerMiddleware
from app.tracing import init_tracing, get_trace_id, set_trace_id
from prometheus_fastapi_instrumentator import Instrumentator


load_dotenv()

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

app = FastAPI(title="Woragis AI Service", version="0.1.0")

# Add middleware for request ID and logging
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggerMiddleware)

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
    agent: Literal["economist", "strategist", "entrepreneur", "startup", "auto"] = Field(..., description="Agent persona or 'auto'")
    input: str = Field(..., description="User input or question")
    system: Optional[str] = Field(None, description="Optional additional system instruction")
    temperature: Optional[float] = Field(None, description="Optional temperature override")
    model: Optional[str] = Field(None, description="Optional model override")
    provider: Optional[Literal["openai", "anthropic", "xai", "manus", "cipher"]] = Field("openai", description="LLM provider")


class ChatResponse(BaseModel):
    agent: str
    output: str


class ChatStreamRequest(ChatRequest):
    pass

class ImageRequest(BaseModel):
    provider: Literal["cipher"] = Field("cipher", description="Image provider")
    prompt: str = Field(..., description="Image generation prompt")
    n: Optional[int] = Field(None, description="Number of images to generate")
    size: Optional[str] = Field(None, description="Image size, e.g., 1024x1024")


class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None


class ImageResponse(BaseModel):
    data: list[ImageData]

class ContentGenerationRequest(BaseModel):
    type: Literal["profile", "experience", "skills", "summary"] = Field(..., description="Type of content to generate")
    jobDescription: str = Field(..., description="Job description for context")
    userContext: Optional[dict] = Field(None, description="Additional user context")

class ContentGenerationResponse(BaseModel):
    content: str
    tokens_used: int
    model: str

@app.get("/v1/agents", response_model=list[str])
def list_agents():
    return get_agent_names()


def _apply_overrides(chain: Runnable, model_name: Optional[str], temperature: Optional[float]) -> Runnable:
    # For simple chains, we rebuild only if overrides provided
    if model_name or temperature is not None:
        from langchain_openai import ChatOpenAI
        new_model = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature if temperature is not None else float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
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
    provider = (req.provider or "openai").lower()

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

    agent_name = req.agent if req.agent != "auto" else pick_agent_auto(req.input)

    # Cipher provider: call external API directly (query string API key, OpenAI-like JSON)
    if provider == "cipher":
        system_text = build_system_message(agent_name)
        if not system_text:
            raise HTTPException(status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

        messages = [{"role": "system", "content": system_text}]
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.input})

        client = CipherClient.from_env()
        text = await client.chat(
            messages=messages,
            temperature=req.temperature if req.temperature is not None else settings.DEFAULT_TEMPERATURE,
            max_tokens=settings.CIPHER_MAX_TOKENS,
            top_p=settings.CIPHER_TOP_P,
        )
        return ChatResponse(agent=agent_name, output=text)

    # Default: build model via LangChain
    try:
        model = make_model(provider, req.model, req.temperature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    chain = build_agent_with_model(agent_name, model)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

    # Optionally augment with extra system instruction by prepending a SystemMessage
    inputs = req.input
    if req.system:
        # Simple concatenation to include system guidance
        inputs = f"{req.system}\n\nUser: {req.input}"

    logger.info("invoking chat chain", agent=agent_name, provider=provider)
    # The prompt template expects both 'agent_name' and 'input' variables
    result = await chain.ainvoke({
        "agent_name": agent_name.title() + " Agent",
        "input": inputs
    })
    if hasattr(result, "content"):
        output_text = result.content  # AIMessage
    else:
        output_text = str(result)

    logger.info("chat completed", agent=agent_name, output_len=len(output_text))
    return ChatResponse(agent=agent_name, output=output_text)


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


@app.post("/api/v1/content/generate", response_model=ContentGenerationResponse)
async def generate_content(req: ContentGenerationRequest):
    """
    Generate resume content based on job description and type.
    This endpoint is used by the resume-worker service.
    """
    logger.info(
        "content generation request",
        type=req.type,
        job_description_length=len(req.jobDescription),
    )
    
    # Build the prompt based on content type
    prompts = {
        "profile": "Generate a professional summary/profile section for a resume. "
                  "Make it compelling, concise (3-4 lines), and tailored to the job description. "
                  "Focus on relevant skills and experience. Format as plain text.",
        "experience": "Generate professional experience descriptions for a resume. "
                     "Make them achievement-oriented with metrics where possible. "
                     "Tailor to the job description requirements. Format as bullet points.",
        "skills": "Generate a technical skills section for a resume. "
                 "Organize by category (e.g., Languages, Frameworks, Tools). "
                 "Prioritize skills relevant to the job description. Format as categorized list.",
        "summary": "Generate an executive summary for a resume. "
                  "Make it impactful, highlighting key qualifications and career achievements. "
                  "Tailor to the job description. Keep it 2-3 sentences."
    }
    
    system_prompt = prompts.get(req.type, prompts["profile"])
    
    # Build user input with job description and context
    user_input_parts = [f"Job Description:\n{req.jobDescription}"]
    
    if req.userContext:
        if req.userContext.get("experience"):
            user_input_parts.append(f"\nCurrent Experience:\n{req.userContext['experience']}")
        if req.userContext.get("skills"):
            skills_list = ", ".join(req.userContext["skills"])
            user_input_parts.append(f"\nCurrent Skills: {skills_list}")
        if req.userContext.get("projects"):
            user_input_parts.append(f"\nProjects:\n{req.userContext['projects']}")
    
    user_input = "\n".join(user_input_parts)
    
    # Use the "auto" agent or a generic approach with OpenAI
    try:
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.7,  # Slightly higher for creative content
            timeout=60,
        )
        
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_input),
        ])
        
        chain = prompt | model
        result = await chain.ainvoke({})
        
        content = result.content if hasattr(result, "content") else str(result)
        
        # Extract token usage if available
        tokens_used = 0
        if hasattr(result, "response_metadata"):
            usage = result.response_metadata.get("token_usage", {})
            tokens_used = usage.get("total_tokens", 0)
        
        logger.info(
            "content generation completed",
            type=req.type,
            content_length=len(content),
            tokens_used=tokens_used,
        )
        
        return ContentGenerationResponse(
            content=content,
            tokens_used=tokens_used,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    except Exception as e:
        logger.error("content generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@app.post("/v1/images", response_model=ImageResponse)
async def generate_images(req: ImageRequest):
    provider = (req.provider or "cipher").lower()
    if provider != "cipher":
        raise HTTPException(status_code=400, detail="Only provider 'cipher' is supported for images currently")

    prompt = req.prompt
    n = req.n if req.n is not None else settings.CIPHER_IMAGE_N
    size = req.size if req.size else settings.CIPHER_IMAGE_SIZE

    client = CipherClient.from_env()
    items = await client.generate_images(prompt=prompt, n=n, size=size)
    # Normalize to ImageData
    normalized = []
    for item in items:
        normalized.append(ImageData(url=item.get("url"), b64_json=item.get("b64_json")))
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
    provider = (req.provider or "openai").lower()

    def pick_agent_auto(text: str) -> str:
        lowered = (text or "").lower()
        if any(k in lowered for k in ["market", "inflation", "macro", "econom", "unit economics", "pricing"]):
            return "economist"
        if any(k in lowered for k in ["strategy", "positioning", "go-to-market", "gtm", "competitor", "moat"]):
            return "strategist"
        if any(k in lowered for k in ["mvp", "launch", "prototype", "hack", "validate", "scrappy"]):
            return "entrepreneur"
        return "startup"

    agent_name = req.agent if req.agent != "auto" else pick_agent_auto(req.input)

    # Prepare input
    inputs = req.input
    if req.system:
        inputs = f"{req.system}\n\nUser: {req.input}"

    # Cipher has no documented streaming: return one full chunk then done
    if provider == "cipher":
        system_text = build_system_message(agent_name) or ""
        messages = [{"role": "system", "content": system_text}]
        if req.system:
            messages.append({"role": "system", "content": req.system})
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

    # LangChain-supported streaming
    try:
        model = make_model(provider, req.model, req.temperature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    chain = build_agent_with_model(agent_name, model)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Unknown agent '{agent_name}'. Available: {', '.join(get_agent_names())}")

    async def event_gen():
        logger.info("stream started", agent=agent_name, provider=provider)
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
        logger.info("stream completed", agent=agent_name, output_len=len(final_text))
        yield json.dumps({"done": True, "output": final_text}) + "\n"

    return StreamingResponse(event_gen(), media_type="application/x-ndjson")
