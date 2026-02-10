"""
Phone number normalization & validation.
Replaces the scattered phone handling in JS modules.
"""
import re


def normalize_phone(phone: str) -> str:
    """
    Normalize an Israeli phone number to 05XXXXXXXX format.

    Examples:
        +972-50-123-4567 → 0501234567
        972501234567     → 0501234567
        050-123-4567     → 0501234567
        0501234567       → 0501234567
    """
    if not phone:
        return ""

    # Strip everything except digits and +
    clean = re.sub(r"[^\d+]", "", phone.strip())

    # Remove +972 prefix
    if clean.startswith("+972"):
        clean = "0" + clean[4:]
    elif clean.startswith("972") and len(clean) > 9:
        clean = "0" + clean[3:]

    # Ensure starts with 0
    if clean and not clean.startswith("0") and len(clean) == 9:
        clean = "0" + clean

    return clean


def is_valid_phone(phone: str) -> bool:
    """
    Check if an Israeli phone number is valid.
    Must be 10 digits starting with 0.
    """
    clean = normalize_phone(phone)
    if not clean:
        return False

    # Israeli mobile: 05X, landline: 02-09
    return bool(re.match(r"^0[2-9]\d{7,8}$", clean))


def format_phone_display(phone: str) -> str:
    """Format phone for display: 050-123-4567."""
    clean = normalize_phone(phone)
    if len(clean) == 10:
        return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
    return clean
