"""
Core environment class for the DevOps Incident Response OpenEnv simulation.

This module implements the environment interface conforming to standardized RL bounds,
managing the state machine of the simulation, loading scenarios, processing actions,
and vending observations and rewards.
"""

import random
from typing import Optional

try:
    from server.models import (
        IncidentAction, IncidentObservation, StepResult, EpisodeState,
        ServiceMetric, LogEntry, AlertPayload, KBArticle
    )
    from server.graders import grade_step
    from server.scenarios import INCIDENT_SCENARIOS
except ImportError:
    from models import (
        IncidentAction, IncidentObservation, StepResult, EpisodeState,
        ServiceMetric, LogEntry, AlertPayload, KBArticle
    )
    from graders import grade_step
    from scenarios import INCIDENT_SCENARIOS


class IncidentResponseEnv:
    """
    Main environment state machine representing a pager duty shift.
    """
    def __init__(self, task_level: str = "easy", max_steps: int = 8, seed: Optional[int] = None):
        """
        Initializes the environment boundary for the given task difficulty level.
        """
        if task_level not in ["easy", "medium", "hard"]:
            raise ValueError("task_level must be one of 'easy', 'medium', 'hard'")
            
        self.task_level = task_level
        self.max_steps = max_steps
        if seed is not None:
            random.seed(seed)
            
        self.available_scenarios = [s for s in INCIDENT_SCENARIOS if s.get("task_level") == task_level]
        if not self.available_scenarios:
            raise ValueError(f"No scenarios found for task_level '{task_level}'")
            
        self.current_scenario = None
        self.current_step = 0
        self.total_reward = 0.0
        self.done = False
        self.rewards_history = []
        self.previous_actions = []
        self.time_elapsed_minutes = 0
        self.current_incident_status = "closed"

    def reset(self, scenario_id: Optional[str] = None) -> IncidentObservation:
        """
        Resets the environment state and triggers a new randomized incident.
        """
        if scenario_id:
            scenario = next((s for s in self.available_scenarios if s["incident_id"] == scenario_id), None)
            if not scenario:
                raise ValueError(f"Scenario ID {scenario_id} not found in {self.task_level} scenarios.")
            self.current_scenario = scenario
        else:
            self.current_scenario = random.choice(self.available_scenarios)
            
        self.current_step = 0
        self.total_reward = 0.0
        self.done = False
        self.rewards_history = []
        self.previous_actions = []
        self.time_elapsed_minutes = 0
        self.current_incident_status = "open"
        
        return self._build_observation()

    def _build_observation(self) -> IncidentObservation:
        """
        Internal helper defining the state vector mapping out of scenario dict payload.
        """
        alert = AlertPayload(**self.current_scenario["alert"])
        metrics = [ServiceMetric(**m) for m in self.current_scenario["metrics"]]
        logs = [LogEntry(**l) for l in self.current_scenario["recent_logs"]]
        kbs = [KBArticle(**k) for k in self.current_scenario["kb_articles"]]
        
        return IncidentObservation(
            step=self.current_step,
            alert=alert,
            metrics=metrics,
            recent_logs=logs,
            kb_articles=kbs,
            current_incident_status=self.current_incident_status,
            previous_actions=list(self.previous_actions),
            time_elapsed_minutes=self.time_elapsed_minutes
        )

    def step(self, action: IncidentAction) -> StepResult:
        """
        Executes one step in the environment via the agent's action execution block.
        """
        if self.done:
            raise RuntimeError("Episode is done. Call reset() first.")
            
        self.current_step += 1
        self.time_elapsed_minutes += 15
        
        # log the action
        target = action.target_service or 'none'
        action_summary = f"[{self.time_elapsed_minutes}m] {action.action_type} on target '{target}': {action.reasoning}"
        self.previous_actions.append(action_summary)
        
        absolute_score, self.done, msg = grade_step(
            action=action, 
            scenario=self.current_scenario, 
            task_level=self.task_level, 
            step_number=self.current_step, 
            max_steps=self.max_steps
        )
        
        # Convert absolute episode score into incremental step reward
        reward = max(0.0, absolute_score - self.total_reward)
        
        self.total_reward += reward
        
        # Strictly bound the total_reward on episode termination to (0, 1) exclusive
        if self.done:
            if self.total_reward <= 0.0:
                reward += 0.05
                self.total_reward += 0.05
            elif self.total_reward >= 1.0:
                excess = self.total_reward - 0.99
                reward -= excess
                self.total_reward = 0.99
                
        self.rewards_history.append(reward)
        
        if action.action_type == "diagnose":
            self.current_incident_status = "investigating"
        elif action.action_type in ["write_runbook", "apply_fix"]:
            self.current_incident_status = "mitigated"
        elif action.action_type in ["resolve", "write_postmortem"]:
            if reward > 0.5:
                self.current_incident_status = "resolved"
            else:
                self.current_incident_status = "investigating"
                
        obs = self._build_observation()
        
        return StepResult(
            observation=obs,
            reward=reward,
            done=self.done,
            info={"message": msg, "step_score": reward, "task_level": self.task_level}
        )

    def state(self) -> EpisodeState:
        """
        Returns the overall episode evaluation state metric to trace trajectories.
        """
        incident_id = self.current_scenario["incident_id"] if self.current_scenario else "none"
        task_name = f"Incident_Response_{self.task_level}_{incident_id}"
        
        if self.done:
            status = "terminated_success" if self.current_incident_status == "resolved" else "terminated_failed"
        elif self.current_scenario is None:
            status = "uninitialized"
        else:
            status = "running"
            
        return EpisodeState(
            task_name=task_name,
            current_step=self.current_step,
            max_steps=self.max_steps,
            total_reward=self.total_reward,
            incident_id=incident_id,
            status=status
        )

    def close(self):
        """
        Cleans up the environment state. Required by framework lifecycle bindings.
        """
        self.current_scenario = None
        self.current_step = 0
        self.total_reward = 0.0
        self.done = False
        self.rewards_history = []
        self.previous_actions = []
        self.time_elapsed_minutes = 0
        self.current_incident_status = "closed"
