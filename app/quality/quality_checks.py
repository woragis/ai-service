"""
Quality checks for coherence and relevance.

Checks if responses are coherent and relevant to the query.
"""

from typing import Tuple, Optional
from app.logger import get_logger
from app.quality.policy import get_quality_policy_loader

logger = get_logger()


def check_coherence(text: str) -> float:
    """
    Check coherence of response.
    
    Simple heuristic-based coherence check.
    In production, this could use more sophisticated NLP models.
    
    Args:
        text: Response text to check
    
    Returns:
        Coherence score (0-1)
    """
    if not text or len(text.strip()) < 10:
        return 0.0
    
    # Simple heuristics for coherence
    sentences = text.split('.')
    if len(sentences) < 2:
        return 0.5  # Single sentence, moderate coherence
    
    # Check for repeated words/phrases (low coherence indicator)
    words = text.lower().split()
    if len(words) < 5:
        return 0.3
    
    # Check for sentence length variation (good coherence indicator)
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    if len(sentence_lengths) < 2:
        return 0.5
    
    avg_length = sum(sentence_lengths) / len(sentence_lengths)
    variance = sum((l - avg_length) ** 2 for l in sentence_lengths) / len(sentence_lengths)
    
    # Normalize variance (higher variance = more natural = better coherence)
    coherence_score = min(1.0, variance / 10.0)
    
    return max(0.3, coherence_score)  # Minimum score of 0.3


def check_relevance(query: str, response: str, use_semantic: bool = True) -> float:
    """
    Check relevance of response to query.
    
    Args:
        query: Original query
        response: Response text
        use_semantic: Whether to use semantic similarity (if available)
    
    Returns:
        Relevance score (0-1)
    """
    if not query or not response:
        return 0.0
    
    query_lower = query.lower()
    response_lower = response.lower()
    
    # Simple keyword overlap check
    query_words = set(query_lower.split())
    response_words = set(response_lower.split())
    
    if not query_words:
        return 0.5  # Can't determine relevance without query
    
    # Calculate overlap
    overlap = len(query_words & response_words)
    relevance_score = min(1.0, overlap / len(query_words))
    
    # Boost score if response contains query as substring
    if query_lower in response_lower:
        relevance_score = min(1.0, relevance_score + 0.3)
    
    # Use semantic similarity if available and enabled
    if use_semantic:
        try:
            from app.caching.semantic_cache import get_semantic_cache
            semantic_cache = get_semantic_cache()
            if semantic_cache and semantic_cache._embedding_model:
                query_embedding = semantic_cache._generate_embedding(query)
                response_embedding = semantic_cache._generate_embedding(response)
                if query_embedding is not None and response_embedding is not None:
                    # Cosine similarity
                    import numpy as np
                    similarity = float(np.dot(query_embedding, response_embedding))
                    # Combine with keyword overlap
                    relevance_score = (relevance_score * 0.3 + similarity * 0.7)
        except Exception as e:
            logger.debug("Semantic similarity check failed, using keyword overlap", error=str(e))
    
    return max(0.0, min(1.0, relevance_score))


def validate_quality(query: str, response: str, agent_name: str = "") -> Tuple[bool, Optional[str], dict]:
    """
    Validate response quality (coherence and relevance).
    
    Args:
        query: Original query
        response: Response text
        agent_name: Agent name
    
    Returns:
        Tuple of (is_valid, error_message, quality_scores)
    """
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.quality_checks.enabled:
        return True, None, {}
    
    quality_scores = {}
    errors = []
    
    # Check coherence
    if policy.quality_checks.check_coherence:
        coherence_score = check_coherence(response)
        quality_scores["coherence"] = coherence_score
        
        if coherence_score < policy.quality_checks.coherence_threshold:
            errors.append(f"Low coherence score: {coherence_score:.2f} (threshold: {policy.quality_checks.coherence_threshold})")
    
    # Check relevance
    if policy.quality_checks.check_relevance:
        relevance_score = check_relevance(query, response, policy.quality_checks.use_semantic_similarity)
        quality_scores["relevance"] = relevance_score
        
        if relevance_score < policy.quality_checks.relevance_threshold:
            errors.append(f"Low relevance score: {relevance_score:.2f} (threshold: {policy.quality_checks.relevance_threshold})")
    
    if errors:
        error_msg = "; ".join(errors)
        logger.warn("Quality check failed", scores=quality_scores, errors=errors)
        return False, error_msg, quality_scores
    
    return True, None, quality_scores


def get_quality_config() -> dict:
    """Get current quality checks configuration."""
    policy_loader = get_quality_policy_loader()
    policy = policy_loader.get_policy()
    return {
        "enabled": policy.quality_checks.enabled,
        "check_coherence": policy.quality_checks.check_coherence,
        "check_relevance": policy.quality_checks.check_relevance,
        "coherence_threshold": policy.quality_checks.coherence_threshold,
        "relevance_threshold": policy.quality_checks.relevance_threshold,
        "use_semantic_similarity": policy.quality_checks.use_semantic_similarity,
    }

