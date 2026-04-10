"""
Deterministic graders for the DevOps Incident Response OpenEnv environment.

Each grader evaluates an IncidentAction against a ground-truth scenario dict
and returns a scalar reward in [0.0, 1.0].  All logic is entirely rule-based
and side-effect-free, guaranteeing reproducibility across runs.

Public API
----------
grade_easy(action, scenario)   -> float
grade_medium(action, scenario) -> float
grade_hard(action, scenario)   -> float
grade_step(action, scenario, task_level, step_number, max_steps)
    -> tuple[float, bool, str]
"""

from __future__ import annotations

from typing import Tuple

try:
    from server.models import IncidentAction
except ImportError:
    from models import IncidentAction


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise(text: str | None) -> str:
    """Return a lower-cased, stripped string, or '' for None/empty."""
    return (text or "").strip().lower()


def _partial_match(a: str, b: str) -> bool:
    """True if either normalised string is a substring of the other."""
    a, b = _normalise(a), _normalise(b)
    return bool(a and b and (a in b or b in a))


def _exact_match(a: str | None, b: str | None) -> bool:
    """True if both strings normalise to the same non-empty value."""
    a, b = _normalise(a), _normalise(b)
    return bool(a and b and a == b)


def _keyword_hits(keywords: list[str], corpus: str) -> int:
    """Count how many *unique* keywords appear (case-insensitive) in corpus."""
    corpus_lower = corpus.lower()
    return sum(1 for kw in keywords if kw.lower() in corpus_lower)


# ---------------------------------------------------------------------------
# grade_easy
# ---------------------------------------------------------------------------

def grade_easy(action: IncidentAction, scenario: dict) -> float:
    """
    Grade an easy task: identify the single failing service.

    Scoring rubric (highest matching rule wins):

    1.0  — target_service exactly matches scenario's true_affected_service
           (case-insensitive).
    0.8  — target_service *partially* matches true_affected_service AND
           action_type == "diagnose".  Correct approach, close answer.
    0.6  — target_service partially matches true_affected_service (any
           action_type).  Right service vicinity, wrong action framing.
    0.3  — action_type == "diagnose" AND target_service is set to *something*
           (non-null, non-empty).  Shows the correct investigative approach
           but hasn't pinned the service.
    0.1  — action_type == "diagnose" but target_service is null/empty.
           Tried but produced no service identification.
    0.0  — anything else (wrong action_type, no useful output).

    Parameters
    ----------
    action   : IncidentAction — the agent's decision for this step.
    scenario : dict           — the ground-truth scenario record.

    Returns
    -------
    float in [0.0, 1.0]
    """
    true_svc: str = scenario.get("true_affected_service", "")
    target_svc: str | None = action.target_service

    # Rule 1 — exact service match
    if _exact_match(target_svc, true_svc):
        return 1.0

    # Rule 2 — partial match + correct action type
    if _partial_match(target_svc, true_svc) and action.action_type == "diagnose":
        return 0.8

    # Rule 3 — partial match alone
    if _partial_match(target_svc, true_svc):
        return 0.6

    # Rule 4 — correct action type with *any* service named
    if action.action_type == "diagnose" and _normalise(target_svc):
        return 0.3

    # Rule 5 — correct action type but no service named
    if action.action_type == "diagnose":
        return 0.1

    # Rule 6 — no credit
    return 0.0


# ---------------------------------------------------------------------------
# grade_medium
# ---------------------------------------------------------------------------

def grade_medium(action: IncidentAction, scenario: dict) -> float:
    """
    Grade a medium task: write a remediation runbook.

    Scoring components (all additive, capped at 1.0):

    keyword_score
        ``matched_keywords / total_required_keywords`` where each keyword is
        searched case-insensitively across the *entire joined runbook text*.

    step_bonus
        +0.15 if len(runbook_steps) >= 5  (comprehensive procedure)
        +0.08 if len(runbook_steps) >= 3  (minimal viable procedure)
        +0.00 otherwise

    service_bonus
        +0.10 if target_service exactly matches true_affected_service.

    reasoning_bonus
        +0.05 if len(action.reasoning) > 100 chars (genuine analysis present).

    If runbook_steps is absent or empty → returns 0.0 immediately.

    Parameters
    ----------
    action   : IncidentAction — the agent's decision for this step.
    scenario : dict           — the ground-truth scenario record.

    Returns
    -------
    float in [0.0, 1.0]
    """
    steps = action.runbook_steps
    if not steps:
        return 0.0

    required_kws: list[str] = scenario.get("required_runbook_keywords", [])

    # keyword_score — search the full joined text once
    if required_kws:
        joined_text = " ".join(steps)
        hits = _keyword_hits(required_kws, joined_text)
        keyword_score = hits / len(required_kws)
    else:
        # No rubric keywords defined: give full credit for having steps at all
        keyword_score = 1.0

    # step_bonus
    n_steps = len(steps)
    if n_steps >= 5:
        step_bonus = 0.15
    elif n_steps >= 3:
        step_bonus = 0.08
    else:
        step_bonus = 0.0

    # service_bonus
    true_svc: str = scenario.get("true_affected_service", "")
    service_bonus = 0.10 if _exact_match(action.target_service, true_svc) else 0.0

    # reasoning_bonus
    reasoning_bonus = 0.05 if len(action.reasoning) > 100 else 0.0

    total = keyword_score + step_bonus + service_bonus + reasoning_bonus
    return min(1.0, total)


# ---------------------------------------------------------------------------
# grade_hard
# ---------------------------------------------------------------------------

def grade_hard(action: IncidentAction, scenario: dict) -> float:
    """
    Grade a hard task: write a complete, accurate postmortem.

    Scoring components (all additive, capped at 1.0):

    base (per-section average)
        ``required_postmortem_sections`` maps section names to keyword lists.
        For each section: ``section_score = found_keywords / total_keywords``.
        ``base = mean(section_scores)``.
        Missing sections score 0.0 for that slot.

    severity_bonus
        +0.08 if action.severity_assessment matches the alert's severity field
        (case-insensitive).

    service_bonus
        +0.08 if action.target_service exactly matches true_affected_service.

    completeness_bonus
        +0.05 if ALL 5 canonical sections (summary, timeline, root_cause,
        impact, action_items) are present AND each contains > 50 characters.

    If postmortem_sections is absent → returns 0.0 immediately.

    Parameters
    ----------
    action   : IncidentAction — the agent's decision for this step.
    scenario : dict           — the ground-truth scenario record.

    Returns
    -------
    float in [0.0, 1.0]
    """
    sections: dict[str, str] | None = action.postmortem_sections
    if not sections:
        return 0.0

    req_sections: dict[str, list[str]] = scenario.get("required_postmortem_sections", {})

    # Per-section keyword scores
    section_scores: list[float] = []
    for sec_name, keywords in req_sections.items():
        if not keywords:
            section_scores.append(1.0)
            continue
        sec_text = sections.get(sec_name, "")
        hits = _keyword_hits(keywords, sec_text)
        section_scores.append(hits / len(keywords))

    base = sum(section_scores) / len(section_scores) if section_scores else 0.0

    # severity_bonus
    alert_severity: str = scenario.get("alert", {}).get("severity", "")
    severity_bonus = (
        0.08
        if _exact_match(action.severity_assessment, alert_severity)
        else 0.0
    )

    # service_bonus
    true_svc: str = scenario.get("true_affected_service", "")
    service_bonus = 0.08 if _exact_match(action.target_service, true_svc) else 0.0

    # completeness_bonus — all 5 canonical sections present and non-trivial
    canonical = ("summary", "timeline", "root_cause", "impact", "action_items")
    complete = all(
        sec in sections and len(sections[sec].strip()) > 50
        for sec in canonical
    )
    completeness_bonus = 0.05 if complete else 0.0

    total = base + severity_bonus + service_bonus + completeness_bonus
    return min(1.0, total)


# ---------------------------------------------------------------------------
# grade_step  (dispatcher + time discount)
# ---------------------------------------------------------------------------

def grade_step(
    action: IncidentAction,
    scenario: dict,
    task_level: str,
    step_number: int,
    max_steps: int,
) -> Tuple[float, bool, str]:
    """
    Evaluate a single environment step and return the transition tuple.

    This function:
    1. Dispatches to the appropriate difficulty grader.
    2. Decides the ``done`` flag.
    3. Applies a time-pressure discount for steps beyond step 2.
    4. Floors the final reward at 0.0.

    Parameters
    ----------
    action      : IncidentAction — the agent's decision for this step.
    scenario    : dict           — the ground-truth scenario record.
    task_level  : str            — "easy", "medium", or "hard".
    step_number : int            — 1-indexed current step (1 … max_steps).
    max_steps   : int            — hard cap on episode length.

    Returns
    -------
    (final_reward, done, message) where:
        final_reward : float — discounted reward, floored at 0.0.
        done         : bool  — True if reward >= 0.7 OR step limit reached.
        message      : str   — human-readable diagnostic summary.

    Time discount formula
    ---------------------
    discount = 1.0 - 0.04 * max(0, step_number - 2)

    Applied *after* the ``done`` decision so that a correct answer on step 1
    will still flag success even though discount would be 1.0 there too.
    """
    level = task_level.lower()

    if level == "easy":
        base_reward = grade_easy(action, scenario)
        grader_name = "grade_easy"
    elif level == "medium":
        base_reward = grade_medium(action, scenario)
        grader_name = "grade_medium"
    elif level == "hard":
        base_reward = grade_hard(action, scenario)
        grader_name = "grade_hard"
    else:
        base_reward = 0.0
        grader_name = "unknown"

    # -- done decision (before time discount, against base reward) -----------
    resolved = base_reward >= 0.7
    exhausted = step_number >= max_steps
    done = resolved or exhausted

    # -- descriptive message -------------------------------------------------
    parts: list[str] = [
        f"Grader={grader_name}",
        f"base_reward={base_reward:.3f}",
        f"action_type={action.action_type}",
    ]
    if action.target_service:
        parts.append(f"target_service={action.target_service}")
    if resolved:
        parts.append("resolution_threshold_met")
    elif exhausted:
        parts.append("max_steps_reached")

    # -- time discount --------------------------------------------------------
    discount = 1.0 - 0.04 * max(0, step_number - 2)
    final_reward = max(0.0, base_reward * discount)

    if discount < 1.0:
        parts.append(f"time_discount={discount:.3f}")

    parts.append(f"final_reward={final_reward:.3f}")

    message = " | ".join(parts)
    return final_reward, done, message
