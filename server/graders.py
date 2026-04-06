"""
Deterministic graders for the DevOps Incident Response OpenEnv environment.

This module implements grading strategies for different task difficulties.
Each grader evaluates an IncidentAction against a ground truth scenario
to provide a consistent score from 0.0 to 1.0.
"""

from typing import Tuple

try:
    from server.models import IncidentAction
except ImportError:
    from models import IncidentAction


def grade_easy(action: IncidentAction, scenario: dict) -> float:
    """
    Grades easy tasks: isolating the failing service.
    Returns:
      - 1.0 for exact target_service match
      - 0.6 for partial match
      - 0.2 if wrong service but action_type == 'diagnose'
      - 0.0 otherwise
    """
    true_svc = scenario.get("true_affected_service", "")
    if not true_svc:
        return 0.0
        
    true_svc_lower = true_svc.lower()
    target_svc = action.target_service.lower() if action.target_service else ""
    
    if target_svc == true_svc_lower:
        return 1.0
        
    if target_svc and (target_svc in true_svc_lower or true_svc_lower in target_svc):
        return 0.6
        
    if action.action_type == "diagnose":
        return 0.2
        
    return 0.0


def grade_medium(action: IncidentAction, scenario: dict) -> float:
    """
    Grades medium tasks: writing runbooks.
    Checks presence of required semantic keywords in the runbook steps array.
    """
    required_kws = scenario.get("required_runbook_keywords", [])
    if not required_kws:
        return 0.0
        
    steps = action.runbook_steps
    if not steps:
        return 0.0
        
    all_text = " ".join(steps).lower()
    found_count = sum(1 for kw in required_kws if kw.lower() in all_text)
    
    base_score = float(found_count) / len(required_kws)
    
    if len(steps) >= 4:
        base_score += 0.1
        
    target_svc = action.target_service.lower() if action.target_service else ""
    true_svc = scenario.get("true_affected_service", "").lower()
    
    if target_svc and true_svc and target_svc == true_svc:
        base_score += 0.1
        
    return min(1.0, base_score)


def grade_hard(action: IncidentAction, scenario: dict) -> float:
    """
    Grades hard tasks: root cause analysis and postmortem generation.
    Validates independent required keywords across defined dictionary sections.
    """
    req_sections = scenario.get("required_postmortem_sections", {})
    if not req_sections:
        return 0.0
        
    sections = action.postmortem_sections
    if not sections:
        return 0.0
        
    section_scores = []
    for sec_name, keywords in req_sections.items():
        if not keywords:
            section_scores.append(1.0)
            continue
            
        sec_text = sections.get(sec_name, "").lower()
        found_count = sum(1 for kw in keywords if kw.lower() in sec_text)
        section_scores.append(float(found_count) / len(keywords))
        
    base_score = sum(section_scores) / len(section_scores) if section_scores else 0.0
    
    scenario_severity = scenario.get("alert", {}).get("severity", "").lower()
    action_severity = action.severity_assessment.lower() if action.severity_assessment else ""
    
    if scenario_severity and action_severity == scenario_severity:
        base_score += 0.1
        
    target_svc = action.target_service.lower() if action.target_service else ""
    true_svc = scenario.get("true_affected_service", "").lower()
    
    if target_svc and true_svc and target_svc == true_svc:
        base_score += 0.1
        
    return min(1.0, base_score)


def grade_step(action: IncidentAction, scenario: dict, task_level: str, step_number: int, max_steps: int) -> tuple[float, bool, str]:
    """
    Evaluates the step transition, maps to the required grader method and adjusts
    time penalty. Returns the standard reward, done boolean, and diagnostic metrics.
    """
    task_level = task_level.lower()
    
    if task_level == "easy":
        base_reward = grade_easy(action, scenario)
    elif task_level == "medium":
        base_reward = grade_medium(action, scenario)
    elif task_level == "hard":
        base_reward = grade_hard(action, scenario)
    else:
        base_reward = 0.0
        
    msg = f"Base score: {base_reward:.2f}."
    
    done = False
    if base_reward >= 0.7 or step_number >= max_steps:
        done = True
        if base_reward >= 0.7:
            msg += " Resolution threshold met."
        else:
            msg += " Maximum step limit reached."
            
    # Apply a time-pressure discount: reward *= (1.0 - 0.05 * max(0, step_number - 3))
    discount = 1.0 - 0.05 * max(0, step_number - 3)
    
    # Floor at 0.0 effectively bounding it safely 
    final_reward = max(0.0, base_reward * discount)
    
    if discount < 1.0:
        msg += f" Time discount applied (factor: {discount:.2f})."
        
    return final_reward, done, msg
