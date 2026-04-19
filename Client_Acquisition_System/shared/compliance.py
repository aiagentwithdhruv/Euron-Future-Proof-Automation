"""CAN-SPAM + DPDP compliance helpers for outbound email.

Every email goes through `build_compliant_email()` before send.
If the returned dict's `compliant` is False, the caller MUST abort.
"""

from __future__ import annotations

import re

from shared import env


REQUIRED_FOOTER_KEYS = ("unsubscribe_url", "postal_address", "from_name")


def build_footer() -> str:
    """Canonical CAN-SPAM-compliant footer. Prepended with a separator line."""
    unsub = env.get("EMAIL_UNSUBSCRIBE_URL", "").strip()
    postal = env.get("EMAIL_POSTAL_ADDRESS", "").strip()
    from_name = env.get("EMAIL_FROM_NAME", "").strip()

    lines = ["", "---"]
    if from_name:
        lines.append(f"Sent by {from_name}.")
    if postal:
        lines.append(postal)
    if unsub:
        lines.append(f"Don't want these emails? Unsubscribe: {unsub}")
    lines.append(
        "We process this email under legitimate-interest basis for B2B outreach (DPDP / GDPR). "
        "Reply STOP or click unsubscribe to opt out instantly."
    )
    return "\n".join(lines)


def check_subject_honest(subject: str) -> tuple[bool, str]:
    s = subject.strip().lower()
    if s.startswith("re:") or s.startswith("fwd:"):
        return False, "Subject fakes a reply/forward — CAN-SPAM violation."
    if len(subject) < 3:
        return False, "Subject too short."
    if len(subject) > 120:
        return False, "Subject too long (>120 chars)."
    return True, ""


def check_body_has_hook(body: str, company: str, prospect_name: str = "") -> tuple[bool, str]:
    """Spray-and-pray detection: body must mention the prospect's company."""
    if not body or len(body.strip()) < 40:
        return False, "Body too short — missing personalization."
    if company and company.lower() not in body.lower():
        return False, f"Body missing company-specific hook (expected '{company}')."
    if prospect_name and prospect_name.split()[0].lower() not in body.lower():
        # Not a hard fail — some copy styles don't lead with the first name.
        pass
    # Detect generic openers
    generic_patterns = [
        r"^hope this email finds you well",
        r"^i hope this message finds you",
        r"^my name is .* and i",
    ]
    for pat in generic_patterns:
        if re.search(pat, body.strip().lower()):
            return False, f"Body starts with generic opener: /{pat}/"
    return True, ""


def build_compliant_email(
    *,
    subject: str,
    body: str,
    company: str,
    prospect_name: str = "",
    prospect_email: str = "",
) -> dict:
    """Validate + attach footer. Returns {compliant, reason, subject, body}."""
    missing_env = [k for k in REQUIRED_FOOTER_KEYS if not _lookup(k)]
    if missing_env:
        return {
            "compliant": False,
            "reason": f"Missing env for footer: {missing_env}. Set EMAIL_UNSUBSCRIBE_URL, "
                      "EMAIL_POSTAL_ADDRESS, EMAIL_FROM_NAME.",
            "subject": subject,
            "body": body,
        }

    ok, why = check_subject_honest(subject)
    if not ok:
        return {"compliant": False, "reason": why, "subject": subject, "body": body}

    ok, why = check_body_has_hook(body, company, prospect_name)
    if not ok:
        return {"compliant": False, "reason": why, "subject": subject, "body": body}

    if not prospect_email or "@" not in prospect_email:
        return {"compliant": False, "reason": "Invalid recipient email.", "subject": subject, "body": body}

    # Append footer if not already present
    footer = build_footer()
    if "unsubscribe" not in body.lower():
        body = body.rstrip() + "\n\n" + footer

    return {"compliant": True, "reason": "", "subject": subject, "body": body}


def _lookup(short_key: str) -> str | None:
    return {
        "unsubscribe_url": env.get("EMAIL_UNSUBSCRIBE_URL"),
        "postal_address": env.get("EMAIL_POSTAL_ADDRESS"),
        "from_name": env.get("EMAIL_FROM_NAME"),
    }.get(short_key)
