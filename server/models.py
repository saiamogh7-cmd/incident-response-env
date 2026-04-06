"""
DevOps Incident Response Environment Models.

This module provides the Pydantic v2 data models that structure the
observations, actions, and evaluation metrics for the OpenEnv simulation.
It encapsulates telemetry (metrics and logs), alerts, knowledge base lookups,
and the state tracked across the lifecycle of an incident.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceMetric(BaseModel):
    """
    Represents a single telemetry metric reading for an active service.
    
    Used by the agent to detect anomalies such as spikes in p99 latency or
    elevated 5xx error rates across infrastructure nodes.
    """
    service_name: str = Field(
        ...,
        description="The identifier of the service, e.g., 'auth-service', 'payment-gateway'."
    )
    metric_name: str = Field(
        ...,
        description="The specific metric measurement, e.g., 'error_rate', 'latency_p99', 'cpu_usage'."
    )
    value: float = Field(
        ...,
        description="The real-time measurable value of the metric."
    )
    unit: str = Field(
        ...,
        description="The unit of measurement (e.g., 'ms', 'req/sec', '%')."
    )
    threshold: float = Field(
        ...,
        description="The predefined safe operational limit for this metric."
    )
    is_anomalous: bool = Field(
        ...,
        description="Flag indicating whether the current value severely deviates from the threshold."
    )

    model_config = ConfigDict(extra="forbid", frozen=True)


class LogEntry(BaseModel):
    """
    Represents a single timestamped log event from a service.
    
    Provides unstructured context necessary for root-cause analysis.
    """
    timestamp: str = Field(
        ...,
        description="The UTC timestamp of the log event in ISO 8601 format."
    )
    level: str = Field(
        ...,
        description="Severity level of the log, typically 'INFO', 'WARN', 'ERROR', or 'CRITICAL'."
    )
    service: str = Field(
        ...,
        description="The name of the service that generated this log entry."
    )
    message: str = Field(
        ...,
        description="The text payload of the log entry containing system output."
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="A distributed correlation ID used to track a request across microservices."
    )

    model_config = ConfigDict(extra="forbid", frozen=True)


class AlertPayload(BaseModel):
    """
    Represents an incoming Page/Alert indicating an active system degradation.
    
    This forms the initial stimulus prompting the incident response agent
    to commence an investigation.
    """
    alert_id: str = Field(
        ...,
        description="A unique alphanumeric identifier for the active alert."
    )
    title: str = Field(
        ...,
        description="A concise, human-readable summary of the alert."
    )
    severity: str = Field(
        ...,
        description="The alert priority scale, typically ranging between 'P1' (Critical) to 'P4' (Low)."
    )
    triggered_at: str = Field(
        ...,
        description="The UTC timestamp when monitoring detected the incident, ISO 8601 formatted."
    )
    affected_services: List[str] = Field(
        default_factory=list,
        description="An array of backend services or dependencies directly implicated by the alert."
    )
    description: str = Field(
        ...,
        description="Expanded details specifying the alert trigger conditions and expected impact."
    )

    model_config = ConfigDict(extra="forbid", frozen=True)


class KBArticle(BaseModel):
    """
    Represents a Knowledge Base (KB) document or existing Incident Response Runbook.
    
    Agents parse these artifacts to understand architecture topologies and prior
    mitigation efforts.
    """
    article_id: str = Field(
        ...,
        description="The unique identifier for this document."
    )
    title: str = Field(
        ...,
        description="The title of the knowledge base article or runbook."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Metadata tags used for categorical search (e.g., 'database', 'networking', 'api')."
    )
    content: str = Field(
        ...,
        description="The complete textual content detailing standard operating procedures or architecture details."
    )

    model_config = ConfigDict(extra="forbid", frozen=True)


class IncidentObservation(BaseModel):
    """
    The composite environment observation space presented to the agent per step.
    
    Contains all situational context required for the agent to deduce the next
    ideal action.
    """
    step: int = Field(
        ...,
        description="The monotonically increasing counter representing the current interaction sequence."
    )
    alert: AlertPayload = Field(
        ...,
        description="The initial and potentially updated alert describing the current incident context."
    )
    metrics: List[ServiceMetric] = Field(
        default_factory=list,
        description="The latest snapshots of critical telemetry data points across affected clusters."
    )
    recent_logs: List[LogEntry] = Field(
        default_factory=list,
        description="A tailing slice of application logs closely preceding or succeeding the incident start."
    )
    kb_articles: List[KBArticle] = Field(
        default_factory=list,
        description="Runbooks or architectural diagrams retrieved based on the active alert's context."
    )
    current_incident_status: str = Field(
        ...,
        description="Progress state of the incident lifecycle: 'open', 'investigating', 'mitigated', or 'resolved'."
    )
    previous_actions: List[str] = Field(
        default_factory=list,
        description="An immutable append-only ledger summarizing the agent's historical actions."
    )
    time_elapsed_minutes: int = Field(
        default=0,
        description="The simulated passage of time since the alert was acknowledged."
    )

    model_config = ConfigDict(extra="ignore")


class IncidentAction(BaseModel):
    """
    Represents the agent's deterministically structured decision.
    
    Defines the specific operation the SRE agent executes within the simulation step.
    """
    action_type: str = Field(
        ...,
        description="The designated action to execute. Allowed: 'diagnose', 'escalate', 'write_runbook', 'apply_fix', 'write_postmortem', 'resolve'."
    )
    reasoning: str = Field(
        ...,
        description="The agent's chain of thought, explaining the diagnostic rationale backing the action selection."
    )
    target_service: Optional[str] = Field(
        default=None,
        description="The specific namespace or service to focus the action toward."
    )
    runbook_steps: Optional[List[str]] = Field(
        default=None,
        description="If action_type is 'write_runbook', details the ordered procedures for future mitigation."
    )
    severity_assessment: Optional[str] = Field(
        default=None,
        description="If escalating or downgrading an alert, declares the updated priority tier."
    )
    postmortem_sections: Optional[Dict[str, str]] = Field(
        default=None,
        description="Completed sections for a postmortem, keys: summary, timeline, root_cause, impact, action_items. Used if action_type is 'write_postmortem'."
    )

    model_config = ConfigDict(extra="ignore")


class StepResult(BaseModel):
    """
    The resulting transition tuple returned by the OpenEnv interface.
    
    Contains the updated world state, the scalar reward assignment, the termination
    flag, and custom environment metadata.
    """
    observation: IncidentObservation = Field(
        ...,
        description="The resultant state of the environment post-action application."
    )
    reward: float = Field(
        ...,
        description="The environment's evaluation of the taken action, guiding optimization objectives."
    )
    done: bool = Field(
        ...,
        description="Indicates whether the task episode has reached terminal state successfully or failed."
    )
    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional environment metadata or debugging information required by standard specifications."
    )

    model_config = ConfigDict(extra="ignore")


class EpisodeState(BaseModel):
    """
    Holistic aggregate tracker mapping the overall trajectory of a scenario.
    
    Utilized for telemetry emission, dashboard tracking, and replay generation.
    """
    task_name: str = Field(
        ...,
        description="The explicit name of the active OpenEnv incident scenario."
    )
    current_step: int = Field(
        ...,
        description="The current iteration depth of the step loop."
    )
    max_steps: int = Field(
        ...,
        description="The predefined hard-limit threshold for the agent to resolve the task."
    )
    total_reward: float = Field(
        default=0.0,
        description="The cumulative reward metric over the lifetime of the active episode."
    )
    incident_id: str = Field(
        ...,
        description="A globally unique identifier mapping to this specific incident rehearsal."
    )
    status: str = Field(
        ...,
        description="Current health flag of the episode itself (e.g., 'running', 'terminated_success', 'failed')."
    )

    model_config = ConfigDict(extra="ignore")
