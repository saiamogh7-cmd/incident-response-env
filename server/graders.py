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
    
    1.0 -> 0.99 (Max)
    0.0 -> 0.01 (Min)
    """
    true_svc: str = scenario.get("true_affected_service", "")
    target_svc: str | None = action.target_service

    # Rule 1 — exact service match
    if _exact_match(target_svc, true_svc):
        return 0.99

    # Rule 2 — partial match + correct action type
    if _partial_match(target_svc, true_svc) and action.action_type == "diagnose":
        return 0.8

    # Rule 3 — partial match alone
    if _partial_match(target_svc, true_svc):
        return 0.6

    # Rule 4 — correct action type with *any* service named
    if action.action_type == "diagnose" and _normalise(target_svc):
        return 0.3

    # Rule 5 — correct action type
    if action.action_type == "diagnose":
        return 0.1

    return 0.01


def grade_medium(action: IncidentAction, scenario: dict) -> float:
    steps = action.runbook_steps
    if not steps:
        return 0.01

    required_kws: list[str] = scenario.get("required_runbook_keywords", [])
    if required_kws:
        joined_text = " ".join(steps)
        hits = _keyword_hits(required_kws, joined_text)
        keyword_score = hits / len(required_kws)
    else:
        keyword_score = 0.99

    n_steps = len(steps)
    step_bonus = 0.15 if n_steps >= 5 else (0.08 if n_steps >= 3 else 0.0)
    
    true_svc: str = scenario.get("true_affected_service", "")
    service_bonus = 0.10 if _exact_match(action.target_service, true_svc) else 0.0
    reasoning_bonus = 0.05 if len(action.reasoning) > 100 else 0.0

    total = keyword_score + step_bonus + service_bonus + reasoning_bonus
    return max(0.01, min(0.99, total))


def grade_hard(action: IncidentAction, scenario: dict) -> float:
    sections: dict[str, str] | None = action.postmortem_sections
    if not sections:
        return 0.01

    req_sections: dict[str, list[str]] = scenario.get("required_postmortem_sections", {})
    section_scores: list[float] = []
    for sec_name, keywords in req_sections.items():
        if not keywords:
            section_scores.append(0.99)
            continue
        sec_text = sections.get(sec_name, "")
        hits = _keyword_hits(keywords, sec_text)
        section_scores.append(hits / len(keywords))

    base = sum(section_scores) / len(section_scores) if section_scores else 0.01

    alert_severity: str = scenario.get("alert", {}).get("severity", "")
    severity_bonus = 0.08 if _exact_match(action.severity_assessment, alert_severity) else 0.0
    
    true_svc: str = scenario.get("true_affected_service", "")
    service_bonus = 0.08 if _exact_match(action.target_service, true_svc) else 0.0

    canonical = ("summary", "timeline", "root_cause", "impact", "action_items")
    complete = all(sec in sections and len(sections[sec].strip()) > 50 for sec in canonical)
    completeness_bonus = 0.05 if complete else 0.0

    total = base + severity_bonus + service_bonus + completeness_bonus
    return max(0.01, min(0.99, total))


def grade_step(
    action: IncidentAction,
    scenario: dict,
    task_level: str,
    step_number: int,
    max_steps: int,
) -> Tuple[float, bool, str]:
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
        base_reward = 0.01
        grader_name = "unknown"

    resolved = base_reward >= 0.7
    exhausted = step_number >= max_steps
    done = resolved or exhausted

    discount = 1.0 - 0.04 * max(0, step_number - 2)
    final_reward = max(0.01, min(0.99, base_reward * discount))

    message = f"Grader={grader_name} | reward={final_reward:.3f} | done={str(done).lower()}"
    return final_reward, done, message
