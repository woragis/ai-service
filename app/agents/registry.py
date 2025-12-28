"""
Agent registry with YAML policy support and RAG integration.

Loads agents from YAML policies and builds chains with knowledge base context.
"""

import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.policy import get_policy_loader, AgentPolicy
from app.knowledge_base.rag import RAGEngine
from app.logger import get_logger

logger = get_logger()


def _persona_prompt(persona_description: str, context: str = "") -> ChatPromptTemplate:
    """Build persona prompt with optional RAG context."""
    system = (
        "You are {agent_name}. "
        + persona_description
        + " Be concise, structured, and provide actionable insights. "
        "When assumptions are needed, state them explicitly."
    )
    
    if context:
        system += f"\n\nRelevant Context:\n{context}\n"
    
    return ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{input}"),
        ]
    )


def _build_chain(agent_name: str, persona_description: str, model: BaseChatModel, context: str = "") -> Runnable:
    """Build agent chain with persona and optional context."""
    prompt = _persona_prompt(persona_description, context)
    return prompt | model


def _model() -> BaseChatModel:
    """Get default model."""
    from langchain_openai import ChatOpenAI
    
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
        timeout=60,
    )


def get_agent_names() -> list[str]:
    """Get list of available agent names from policies."""
    policy_loader = get_policy_loader()
    return policy_loader.list_agents()


def get_agent(name: str) -> Runnable | None:
    """Get agent chain by name (uses default model)."""
    return build_agent_with_model(name, _model())


def build_agent_with_model(agent_name: str, model: BaseChatModel) -> Runnable | None:
    """
    Build agent chain using a provided model with RAG support.
    
    Args:
        agent_name: Agent name
        model: Language model to use
    
    Returns:
        Runnable chain or None if agent not found
    """
    policy_loader = get_policy_loader()
    policy = policy_loader.get_policy(agent_name.lower())
    
    if not policy:
        logger.warn("Agent policy not found", agent=agent_name)
        return None
    
    # Build persona description
    persona = policy.personality
    
    # Initialize RAG if enabled
    context = ""
    if policy.knowledge_base.enabled:
        try:
            rag_engine = RAGEngine()
            # Note: RAG context will be retrieved at request time, not here
            # This is a placeholder for future async RAG integration
            logger.info("RAG enabled for agent", agent=agent_name, collection=policy.knowledge_base.collection)
        except Exception as e:
            logger.warn("Failed to initialize RAG", error=str(e), agent=agent_name)
    
    # Use behavior settings from policy
    if hasattr(model, 'temperature'):
        model.temperature = policy.behavior.temperature
    
    return _build_chain(
        agent_name=policy.display_name,
        persona_description=persona,
        model=model,
        context=context
    )


def build_system_message(agent_name: str) -> str | None:
    """
    Build system message for an agent from policy.
    
    Args:
        agent_name: Agent name
    
    Returns:
        System message string or None if agent not found
    """
    policy_loader = get_policy_loader()
    policy = policy_loader.get_policy(agent_name.lower())
    
    if not policy:
        return None
    
    system_message = (
        f"You are {policy.display_name}. "
        + policy.personality
        + " Be concise, structured, and provide actionable insights. "
        "When assumptions are needed, state them explicitly."
    )
    
    # Add constraints if any
    if policy.constraints:
        system_message += "\n\nConstraints:\n" + "\n".join(f"- {c}" for c in policy.constraints)
    
    return system_message


async def get_rag_context(agent_name: str, query: str) -> str:
    """
    Get RAG context for an agent query.
    
    Args:
        agent_name: Agent name
        query: User query
    
    Returns:
        Context string from knowledge base
    """
    policy_loader = get_policy_loader()
    policy = policy_loader.get_policy(agent_name.lower())
    
    if not policy or not policy.knowledge_base.enabled:
        return ""
    
    try:
        rag_engine = RAGEngine()
        context = await rag_engine.retrieve_context(
            query=query,
            collection=policy.knowledge_base.collection,
            document_paths=policy.knowledge_base.document_paths,
            top_k=policy.knowledge_base.top_k,
            score_threshold=policy.knowledge_base.similarity_threshold
        )
        return rag_engine.format_context_for_prompt(context)
    except Exception as e:
        logger.error("Failed to retrieve RAG context", error=str(e), agent=agent_name)
        return ""
