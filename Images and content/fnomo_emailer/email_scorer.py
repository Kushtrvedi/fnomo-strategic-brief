"""
email_scorer.py
Scores each generated email on three dimensions before sending.

  Hook Strength  (1-5): How specific and relevant is the hook to this firm?
  Clarity Score  (1-5): Is the email well-structured, concise, readable?
  Spam Risk Flag (Low/Medium/High): Will this trigger spam filters?
"""

import re

# ── Spam trigger words (common filters) ───────────────────────────────────────
SPAM_HIGH = [
    "guaranteed", "100%", "free money", "make money", "earn money",
    "click here", "act now", "limited time", "urgent", "winner",
    "congratulations", "no risk", "risk-free", "investment opportunity",
    "double your", "triple your", "passive income", "get rich",
    "financial freedom", "exclusive offer", "special promotion",
]

SPAM_MEDIUM = [
    "free", "bonus", "profit", "cash", "income", "revenue", "wealth",
    "returns", "gains", "opportunity", "offer", "discount", "save",
    "cheap", "buy now", "sign up", "subscribe", "call now", "contact us",
    "dear friend", "as seen on", "satisfaction guaranteed",
]

# Words that reduce spam score (signal legitimacy)
LEGITIMACY_SIGNALS = [
    "audit", "compliance", "regulatory", "chartered", "advisory",
    "institutional", "research", "framework", "analysis", "strategy",
    "governance", "fiduciary", "diligence", "mandate", "protocol",
]


def score_hook_strength(hook: str, firm_name: str, email_body: str) -> tuple[int, str]:
    """
    Score how specific and compelling the context hook is.
    Returns (score, reason)
    """
    score = 1
    reasons = []

    hook_lower  = hook.lower()
    body_lower  = email_body.lower()
    firm_lower  = firm_name.lower().split()[0]  # first word of firm name

    # +1 if hook mentions the firm name or is specific to them
    if firm_lower in hook_lower or firm_lower in body_lower:
        score += 1
        reasons.append("Firm name referenced")

    # +1 if hook has a specific year, number, or milestone
    if re.search(r"\b(19|20)\d{2}\b", hook) or re.search(r"\d+\s*(partner|staff|year|decade)", hook_lower):
        score += 1
        reasons.append("Specific milestone/date found")

    # +1 if hook references a verifiable practice area or event
    specific_terms = [
        "audit", "nfra", "sebi", "gst", "ifrs", "fema", "mca", "ipo",
        "forensic", "valuation", "advisory", "compliance", "regulatory",
        "succession", "technology", "partner", "established", "founded",
        "diamond jubilee", "stanford", "institute",
    ]
    if any(t in hook_lower for t in specific_terms):
        score += 1
        reasons.append("Practice-specific context")

    # +1 if the body connects the hook to a clear pain point
    pain_terms = [
        "pressure", "challenge", "tension", "ceiling", "gap", "burden",
        "scrutiny", "attrition", "bandwidth", "lag", "debt", "trap",
    ]
    if any(t in body_lower for t in pain_terms):
        score += 1
        reasons.append("Pain point surfaced in body")

    score = min(score, 5)
    reason = ", ".join(reasons) if reasons else "Generic hook — consider more specific research"
    return score, reason


def score_clarity(subject: str, body: str) -> tuple[int, str]:
    """
    Score structural clarity and readability.
    Returns (score, reason)
    """
    score = 5
    issues = []

    word_count     = len(body.split())
    sentence_count = len(re.split(r'[.!?]+', body.strip()))
    avg_words_per_sentence = word_count / max(sentence_count, 1)

    # Word count check
    if word_count < 80:
        score -= 2
        issues.append(f"Too short ({word_count} words)")
    elif word_count < 110:
        score -= 1
        issues.append(f"Slightly short ({word_count} words)")
    elif word_count > 200:
        score -= 1
        issues.append(f"Too long ({word_count} words)")

    # Sentence length check
    if avg_words_per_sentence > 30:
        score -= 1
        issues.append("Sentences too long (avg {:.0f} words)".format(avg_words_per_sentence))

    # Subject length check
    subject_words = len(subject.split())
    if subject_words > 8:
        score -= 1
        issues.append(f"Subject too long ({subject_words} words)")

    # Check for formatting issues (bullets, markdown in plain text)
    if re.search(r"^\s*[-*•]\s", body, re.MULTILINE):
        score -= 1
        issues.append("Contains bullet points (should be plain prose)")

    # Check for CTA presence (soft ask at end)
    cta_signals = ["worth", "curious", "thoughts", "make sense", "open to", "explore", "brief"]
    if not any(s in body.lower() for s in cta_signals):
        score -= 1
        issues.append("Missing soft CTA")

    score = max(score, 1)
    reason = "; ".join(issues) if issues else "Well-structured"
    return score, reason


def score_spam_risk(subject: str, body: str) -> tuple[str, list[str]]:
    """
    Flag spam risk as Low / Medium / High.
    Returns (risk_level, triggered_words)
    """
    full_text    = (subject + " " + body).lower()
    triggered    = []
    high_count   = 0
    medium_count = 0

    for word in SPAM_HIGH:
        if word.lower() in full_text:
            triggered.append(f"HIGH: '{word}'")
            high_count += 1

    for word in SPAM_MEDIUM:
        if word.lower() in full_text:
            triggered.append(f"MED: '{word}'")
            medium_count += 1

    # Legitimacy signals reduce risk
    legitimacy_count = sum(1 for w in LEGITIMACY_SIGNALS if w in full_text)

    # ALL CAPS subject
    if subject.upper() == subject and len(subject) > 5:
        triggered.append("HIGH: ALL CAPS subject")
        high_count += 1

    # Excessive exclamation marks
    if body.count("!") > 2:
        triggered.append(f"MED: {body.count('!')} exclamation marks")
        medium_count += 1

    # Determine risk level
    if high_count >= 1:
        risk = "HIGH"
    elif medium_count >= 3 and legitimacy_count < 2:
        risk = "MEDIUM"
    elif medium_count >= 1:
        risk = "LOW-MEDIUM"
    else:
        risk = "LOW"

    return risk, triggered


def score_email(lead: dict, email_data: dict) -> dict:
    """
    Score a generated email. Returns a scores dict to attach to the lead.
    """
    subject    = email_data.get("subject", "")
    body       = email_data.get("body", "")
    hook       = lead.get("hook", lead.get("industry", ""))
    firm_name  = lead.get("name", lead.get("company", ""))

    hook_score, hook_reason         = score_hook_strength(hook, firm_name, body)
    clarity_score, clarity_reason   = score_clarity(subject, body)
    spam_risk, spam_triggers        = score_spam_risk(subject, body)

    # Overall send recommendation
    sendable = (
        hook_score >= 2
        and clarity_score >= 3
        and spam_risk in ("LOW", "LOW-MEDIUM")
    )

    return {
        "hook_strength":    hook_score,
        "hook_reason":      hook_reason,
        "clarity_score":    clarity_score,
        "clarity_reason":   clarity_reason,
        "spam_risk":        spam_risk,
        "spam_triggers":    spam_triggers,
        "send_recommended": sendable,
        "send_flag":        "✅ SEND" if sendable else "⚠️  REVIEW",
    }


def format_score_block(scores: dict) -> str:
    """Format scores for the AAR report."""
    lines = [
        f"  Hook Strength : {'★' * scores['hook_strength']}{'☆' * (5 - scores['hook_strength'])} ({scores['hook_strength']}/5) — {scores['hook_reason']}",
        f"  Clarity       : {'★' * scores['clarity_score']}{'☆' * (5 - scores['clarity_score'])} ({scores['clarity_score']}/5) — {scores['clarity_reason']}",
        f"  Spam Risk     : {scores['spam_risk']}",
    ]
    if scores["spam_triggers"]:
        lines.append(f"  Triggers      : {', '.join(scores['spam_triggers'][:3])}")
    lines.append(f"  Verdict       : {scores['send_flag']}")
    return "\n".join(lines)
