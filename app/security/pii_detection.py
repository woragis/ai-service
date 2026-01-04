"""
PII (Personally Identifiable Information) detection and masking.

Detects and masks sensitive information like emails, phone numbers, SSNs, etc.
"""

import re
from typing import Tuple, List, Dict, Optional
from app.logger import get_logger
from app.security.policy import get_security_policy_loader

logger = get_logger()


# PII detection patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b')
IP_ADDRESS_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect PII in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary mapping PII types to lists of detected values
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.pii_detection.enabled:
        return {}
    
    detected = {}
    
    if policy.pii_detection.detect_email:
        emails = EMAIL_PATTERN.findall(text)
        if emails:
            detected["email"] = emails
    
    if policy.pii_detection.detect_phone:
        phones = PHONE_PATTERN.findall(text)
        if phones:
            detected["phone"] = phones
    
    if policy.pii_detection.detect_ssn:
        ssns = SSN_PATTERN.findall(text)
        if ssns:
            detected["ssn"] = ssns
    
    if policy.pii_detection.detect_credit_card:
        cards = CREDIT_CARD_PATTERN.findall(text)
        if cards:
            detected["credit_card"] = cards
    
    if policy.pii_detection.detect_ip_address:
        ips = IP_ADDRESS_PATTERN.findall(text)
        if ips:
            detected["ip_address"] = ips
    
    return detected


def mask_pii(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Mask PII in text.
    
    Args:
        text: Text to mask
    
    Returns:
        Tuple of (masked_text, pii_counts)
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.pii_detection.enabled or policy.pii_detection.action != "mask":
        return text, {}
    
    masked = text
    pii_counts = {}
    mask_char = policy.pii_detection.mask_char
    
    if policy.pii_detection.detect_email:
        emails = EMAIL_PATTERN.findall(text)
        if emails:
            pii_counts["email"] = len(emails)
            for email in emails:
                # Mask email: keep first char and domain, mask the rest
                parts = email.split("@")
                if len(parts) == 2:
                    local = parts[0]
                    domain = parts[1]
                    masked_local = local[0] + mask_char * (len(local) - 1) if len(local) > 1 else mask_char
                    masked_email = f"{masked_local}@{domain}"
                    masked = masked.replace(email, masked_email)
    
    if policy.pii_detection.detect_phone:
        phones = PHONE_PATTERN.findall(text)
        if phones:
            pii_counts["phone"] = len(phones)
            for phone in phones:
                # Mask phone: keep last 4 digits
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 4:
                    masked_phone = mask_char * (len(digits) - 4) + digits[-4:]
                    masked = masked.replace(phone, masked_phone)
    
    if policy.pii_detection.detect_ssn:
        ssns = SSN_PATTERN.findall(text)
        if ssns:
            pii_counts["ssn"] = len(ssns)
            for ssn in ssns:
                # Mask SSN: show only last 4 digits
                masked_ssn = "XXX-XX-" + ssn[-4:]
                masked = masked.replace(ssn, masked_ssn)
    
    if policy.pii_detection.detect_credit_card:
        cards = CREDIT_CARD_PATTERN.findall(text)
        if cards:
            pii_counts["credit_card"] = len(cards)
            for card in cards:
                # Mask credit card: show only last 4 digits
                digits = re.sub(r'\D', '', card)
                if len(digits) >= 4:
                    masked_card = mask_char * (len(digits) - 4) + digits[-4:]
                    masked = masked.replace(card, masked_card)
    
    if policy.pii_detection.detect_ip_address:
        ips = IP_ADDRESS_PATTERN.findall(text)
        if ips:
            pii_counts["ip_address"] = len(ips)
            for ip in ips:
                # Mask IP: show only last octet
                parts = ip.split(".")
                if len(parts) == 4:
                    masked_ip = "XXX.XXX.XXX." + parts[-1]
                    masked = masked.replace(ip, masked_ip)
    
    if pii_counts:
        logger.info("PII masked in text", counts=pii_counts)
    
    return masked, pii_counts


def check_pii(text: str) -> Tuple[bool, Optional[str], Dict[str, int]]:
    """
    Check for PII and determine if content should be blocked.
    
    Args:
        text: Text to check
    
    Returns:
        Tuple of (allowed, error_message, pii_counts)
    """
    policy_loader = get_security_policy_loader()
    policy = policy_loader.get_policy()
    
    if not policy.pii_detection.enabled:
        return True, None, {}
    
    detected = detect_pii(text)
    
    if detected and policy.pii_detection.action == "block":
        pii_types = ", ".join(detected.keys())
        error_msg = f"Content blocked: contains PII ({pii_types})"
        logger.warn("Content blocked due to PII", pii_types=list(detected.keys()))
        pii_counts = {pii_type: len(values) for pii_type, values in detected.items()}
        return False, error_msg, pii_counts
    
    # Count PII for logging
    pii_counts = {pii_type: len(values) for pii_type, values in detected.items()}
    
    return True, None, pii_counts

