from pydantic import ValidationError

from app.agents.exceptions import SafetyAgentError
from app.llm.provider import get_llm
from app.schemas.safety import SafetyDecision

import re


SAFETY_SYSTEM_PROMPT = """
You are the Safety and Escalation Agent for AgentCare.

AgentCare is a healthcare ADMINISTRATION and care-coordination
application. It is NOT a diagnosis or treatment system.

Your only responsibility is to determine whether the patient's
request may safely continue through administrative automation.

You MUST NOT:
- diagnose a medical condition;
- determine what disease a patient has;
- prescribe medication;
- recommend medication;
- recommend or change medication dosage;
- recommend clinical treatment;
- interpret medical test findings clinically;
- claim to replace a healthcare professional.

Classify the request into exactly one category:

1. administrative_allowed

The user is asking for an administrative action such as:
- registering or updating patient information;
- booking, rescheduling, or cancelling an appointment;
- checking administrative appointment availability;
- routing to a department;
- uploading or organizing documents;
- reminders or follow-up coordination.

A patient may mention an existing condition, department,
document, or follow-up context and still be administrative.
Do not diagnose anything from that information.

2. medical_advice

The user asks AgentCare to:
- diagnose;
- recommend treatment;
- choose medication;
- change medication;
- recommend dosage;
- clinically interpret findings.

3. emergency

The request contains information suggesting a potentially urgent
or emergency situation that should not continue through normal
automated administrative processing.

Do not diagnose the situation. Only mark it for human escalation.

4. sensitive

The request involves a sensitive situation for which automated
administrative action should pause for human review.

5. uncertain

You cannot safely determine whether administrative automation
should continue.

Rules:

- medical_advice, emergency, sensitive, and uncertain MUST have
  allow_automation=false and requires_human_review=true.
- administrative_allowed MUST have
  allow_automation=true and requires_human_review=false.
- Do not provide health advice in "reason".
- Keep "reason" administrative and concise.
- confidence must be between 0 and 1.

Return ONLY a JSON object with this exact shape:

{
  "classification": "administrative_allowed",
  "allow_automation": true,
  "requires_human_review": false,
  "confidence": 0.95,
  "reason": "Administrative appointment scheduling request.",
  "flags": []
}

Do not include Markdown.
Do not include additional text outside the JSON object.
"""


EMERGENCY_PATTERNS = (
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "trouble breathing",
    "shortness of breath",
    "severe bleeding",
    "unconscious",
    "passed out",
    "overdose",
)


MEDICAL_ADVICE_PATTERNS = (
    "what medication should",
    "which medication should",
    "what medicine should",

    "what dosage",
    "what dose",

    "should i take",
    "can i take",

    "increase my dose",
    "decrease my dose",
    "double my dose",

    "increase my medication dose",
    "decrease my medication dose",
    "double my medication dose",
    "change my medication dose",
    "adjust my medication dose",

    "change my medication",

    "prescribe",
    "diagnose me",

    "do i have",

    "what treatment should",
)

MEDICATION_ACTION_PATTERNS = (
    r"\b(double|increase|decrease|change|adjust)\b"
    r".{0,40}"
    r"\b(dose|dosage|medication|medicine)\b",

    r"\b(should|can)\s+i\s+"
    r"(take|stop|change|increase|decrease)\b"
    r".{0,40}"
    r"\b(medication|medicine|dose|dosage)\b",
)


def deterministic_safety_check(
    request_text: str,
) -> SafetyDecision | None:
    """
    Catch high-confidence prohibited situations before
    relying on an LLM classification.
    """

    normalized = request_text.lower().strip()

    emergency_matches = [
        pattern
        for pattern in EMERGENCY_PATTERNS
        if pattern in normalized
    ]

    if emergency_matches:
        return SafetyDecision(
            classification="emergency",
            allow_automation=False,
            requires_human_review=True,
            confidence=1.0,
            reason=(
                "Request contains potentially urgent language "
                "requiring human review."
            ),
            flags=emergency_matches,
            source="deterministic",
        )

    medical_matches = [
        pattern
        for pattern in MEDICAL_ADVICE_PATTERNS
        if pattern in normalized
    ]

    regex_medical_matches = [
    pattern
    for pattern in MEDICATION_ACTION_PATTERNS
    if re.search(
        pattern,
        normalized,
    )
]

    if medical_matches or regex_medical_matches:
        return SafetyDecision(
            classification="medical_advice",
            allow_automation=False,
            requires_human_review=True,
            confidence=1.0,
            reason=(
                "Request asks for clinical or medication guidance "
                "outside AgentCare's administrative scope."
            ),
            #flags=medical_matches,
            flags=(
    medical_matches
    + [
        "medication_dosage_action"
        for _ in regex_medical_matches
    ]
),
            source="deterministic",
        )

    return None


def classify_with_llm(
    request_text: str,
) -> SafetyDecision:
    llm = get_llm()

    json_llm = llm.bind(
        response_format={
            "type": "json_object",
        },
    )

    messages = [
        (
            "system",
            SAFETY_SYSTEM_PROMPT,
        ),
        (
            "human",
            f"""
Patient administrative request:

{request_text}

Classify this request according to your safety rules.
Return JSON only.
""".strip(),
        ),
    ]

    last_error: Exception | None = None

    for attempt in range(2):
        try:
            response = json_llm.invoke(
                messages
            )

            if not isinstance(
                response.content,
                str,
            ):
                raise SafetyAgentError(
                    "Safety Agent returned "
                    "non-text JSON content."
                )

            decision = SafetyDecision.model_validate_json(
                response.content
            )

            # Never trust contradictory LLM output.
            if (
                decision.classification
                == "administrative_allowed"
            ):
                decision.allow_automation = True
                decision.requires_human_review = False
            else:
                decision.allow_automation = False
                decision.requires_human_review = True

            decision.source = "llm"

            return decision

        except (
            ValidationError,
            SafetyAgentError,
        ) as exc:
            last_error = exc

            messages.append(
                (
                    "human",
                    """
Your previous output did not match the required schema.

Return ONLY one valid JSON object containing:
classification
allow_automation
requires_human_review
confidence
reason
flags
source

Use source="llm".
""".strip(),
                )
            )

    raise SafetyAgentError(
        "Safety Agent failed to produce "
        "a valid decision after retries."
    ) from last_error


def evaluate_safety(
    request_text: str,
) -> SafetyDecision:
    deterministic_result = (
        deterministic_safety_check(
            request_text
        )
    )

    if deterministic_result is not None:
        return deterministic_result

    return classify_with_llm(
        request_text
    )