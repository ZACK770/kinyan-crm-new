"""
Phone number normalization & validation.
Replaces the scattered phone handling in JS modules.
"""
import re


def normalize_phone(phone: str) -> str:
    """
    Normalize phone numbers - Israeli to 05XXXXXXXX format, foreign kept as-is.

    Israeli format: 10 digits starting with 0 (mobile 05X, landline 02-09)
    Foreign: Any other format (longer/shorter, different prefix)

    Examples:
        Israeli:
            +972-50-123-4567 → 0501234567
            972501234567     → 0501234567
            050-123-4567     → 0501234567
            501234567        → 0501234567 (missing 0)
            0501234567       → 0501234567
        
        Foreign (kept as-is):
            +1-289-262-1452  → 12892621452
            0044123456789    → 0044123456789
    """
    if not phone:
        return ""

    # Strip everything except digits and +
    clean = re.sub(r"[^\d+]", "", phone.strip())
    
    # Remove leading + if exists
    if clean.startswith("+"):
        clean = clean[1:]

    # Handle Israeli +972 prefix
    if clean.startswith("972"):
        # +972 50 1234567 → 0501234567
        if len(clean) >= 12:  # 972 + 9 digits
            clean = "0" + clean[3:]
        elif len(clean) == 12:  # 972501234567
            clean = "0" + clean[3:]

    # Israeli number without 0 at start (9 digits starting with 2-9)
    # Examples: 501234567, 21234567, 31234567
    if clean and not clean.startswith("0") and len(clean) == 9 and clean[0] in "23456789":
        clean = "0" + clean
    
    # If it's 10 digits starting with 0 and second digit is 2-9, it's Israeli - keep it
    # Otherwise (foreign number) - keep as-is
    
    return clean


def is_israeli_phone(phone: str) -> bool:
    """
    Check if a phone number matches Israeli format.
    Israeli: 10 digits, starts with 0, second digit 2-9.
    """
    clean = normalize_phone(phone)
    if not clean:
        return False
    
    # Israeli format: 0[2-9]XXXXXXXX (10 digits total)
    return bool(re.match(r"^0[2-9]\d{8}$", clean))


def is_valid_phone(phone: str) -> bool:
    """
    Check if a phone number is valid (Israeli or foreign).
    Israeli: Must be 10 digits starting with 0.
    Foreign: Any number with 7+ digits.
    """
    clean = normalize_phone(phone)
    if not clean:
        return False

    # Israeli mobile: 05X, landline: 02-09 (10 digits)
    if re.match(r"^0[2-9]\d{8}$", clean):
        return True
    
    # Foreign: at least 7 digits
    if len(clean) >= 7 and clean.isdigit():
        return True
    
    return False


def format_phone_display(phone: str) -> str:
    """Format phone for display: 050-123-4567."""
    clean = normalize_phone(phone)
    if len(clean) == 10:
        return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
    return clean
