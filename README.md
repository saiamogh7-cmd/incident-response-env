---
title: Incident Response Env
emoji: 🚨
colorFrom: red
colorTo: purple
sdk: docker
pinned: false
---
# Incident Response Environment API 🛡️

Welcome to the **Incident Response Environment API**. This platform acts as an interactive, simulated sandbox where Artificial Intelligence (AI) agents can train on cybersecurity and IT incident responses. 

Our API provides a safe environment for AI models to train, identify their weaknesses, and receive precise performance metrics—all without risking real-world systems.

## 🚀 Why Use This API?
* **Safe Sandbox Testing:** Let your AI practice fixing crashed servers or stopping simulated hackers in a disposable environment. If the AI makes a mistake, no real damage is done.
* **Reinforcement Learning:** Perfect for training AI agents through trial and error. The environment provides immediate feedback on whether an action helped or made the situation worse.
* **Benchmarking & Validation:** Evaluate different AI models and expose their logical loopholes. Get hard data and concrete scores to prove how accurately your AI makes decisions.

---

## ⚙️ API Endpoints

The API is built with FastAPI and provides a simple set of endpoints to interact with the simulation. You can view the interactive Swagger UI documentation by visiting `/docs` on the base URL.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | **Health Check:** Verifies that the API server is awake and running. |
| `GET` | `/tasks` | **List Tasks:** Returns a list of available simulation scenarios or "levels" to play. |
| `POST` | `/reset` | **Reset Environment:** Initializes a new session and returns the starting state of the incident. |
| `POST` | `/step` | **Take Action:** Send a command to the environment (e.g., "Block IP address") and receive the outcome. |
| `GET` | `/state` | **Check State:** View the current status of the simulated environment, including your score and active alerts. |

---

## 💻 Quickstart Guide (Python)

Here is a simple example of how to connect an AI agent or a Python script to the API to start training:

```python
import requests

BASE_URL = "[https://saiamogh7-cmd-incident-response-env.hf.space](https://saiamogh7-cmd-incident-response-env.hf.space)"

# 1. Check if the API is alive
requests.get(f"{BASE_URL}/health")

# 2. Reset the environment to start a new simulation
reset_data = requests.post(f"{BASE_URL}/reset", json={}).json()
print("Starting State:", reset_data)

# 3. Take a step (Send your AI's decision to the environment)
# Note: Check the /docs schema to ensure your payload matches the expected fields
action_payload = {
    "action": "Investigate server logs",
    "text": "Checking for unusual login activity"
}
step_result = requests.post(f"{BASE_URL}/step", json=action_payload).json()

# 4. View the results of your action
print("Result of action:", step_result)

# Incident Response & Runbook Automation Environment

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-brightgreen)
![HuggingFace Spaces](https://img.shields.io/badge/HuggingFace-Spaces-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

The **Incident Response & Runbook Automation Environment** is a deterministic, containerized OpenEnv simulation designed to test the capabilities of autonomous AI agents in high-stakes Site Reliability Engineering (SRE) scenarios. Built for researchers and developers evaluating LLMs on complex operational workflows, this environment presents an active microservice architecture where simulated metrics degrade, alarms page the agent, and unstructured logs roll in real-time. It matters because true DevOps autonomy extends beyond simple code generation; models must synthesize telemetry, triage cascading failures under time pressure, and author actionable, precise remediation narratives without human intervention.

## Environment Overview

| Property | Details |
| --- | --- |
| **Observation Space** | Composite JSON object (Metrics, Logs, Alerts, KB Articles) |
| **Action Space** | Structured JSON object conformant to `IncidentAction` schema |
| **Reward Range** | `[0.0, 1.0]` per episode |
| **Episode Length** | Hard limit evaluated up to `8` total steps |

## Tasks

| Task | Difficulty | Objective | Key Metric | Score Threshold |
| --- | --- | --- | --- | --- |
| `easy` | Easy | Identify the root cause service from structured logs and metrics. | Triage accuracy | 0.7 |
| `medium` | Medium | Write a step-by-step remediation runbook for a service cascade failure. | Semantic runbook mapping | 0.7 |
| `hard` | Hard | Diagnose a multi-service cascading failure and produce a complete postmortem. | RCA and structural completeness | 0.7 |

## Observation Space

The `IncidentObservation` schema captures the telemetry snapshot returned on every environment step.

| Field | Type | Description |
| --- | --- | --- |
| `step` | `int` | The monotonically increasing counter of the current action sequence. |
| `alert` | `object` | The active page/alert payload detailing the initial trigger condition. |
| `metrics` | `array` | A snapshot array of `ServiceMetric` objects (latency, error rates, CPU). |
| `recent_logs` | `array` | A trailing snapshot of `LogEntry` objects surrounding the incident timeline. |
| `kb_articles` | `array` | Retrieved context including runbooks or architecture overviews. |
| `current_incident_status` | `string` | Progress state: `open`, `investigating`, `mitigated`, or `resolved`. |
| `previous_actions` | `array` | An immutable append-only ledger summarizing the agent's historical actions. |
| `time_elapsed_minutes` | `int` | The simulated elapsed time mapping task duration. |

## Action Space

Agents interact with the environment by constructing a validated `IncidentAction` JSON.

| Field | Type | Valid Values / Spec | Description |
| --- | --- | --- | --- |
| `action_type` | `string` | `'diagnose'`, `'escalate'`, `'write_runbook'`, `'apply_fix'`, `'write_postmortem'`, `'resolve'` | The functional operation the agent is electing to execute. |
| `reasoning` | `string` | Detailed rationale. | The diagnostic chain-of-thought backing the selection. |
| `target_service` | `string` | Optional name of the service. | The microservice the action targets (e.g., `auth-service`). |
| `runbook_steps` | `array` | Optional string array. | Used when `write_runbook` is selected to layout remediation. |
| `severity_assessment`| `string` | Optional P-level tier. | Escalation tier used when altering the alert priority. |
| `postmortem_sections`| `object` | Optional dictionary. Keys: `summary`, `timeline`, `root_cause`, `impact`, `action_items` | Structured postmortem narrative payload. |

## Reward Function

The reward mechanics are deterministically tied directly to the task difficulty via automated grader logic evaluating the distance between the state representation and ground truth:

1. **Easy:** Returns `1.0` for correctly isolating the true anomalous service, partial grading for closely matched upstream dependencies.
2. **Medium:** Utilizes a semantic keyword evaluation over the proposed `runbook_steps` arrays to assign partial continuous credits up to `1.0`.
3. **Hard:** Cross-validates independently generated sections within `postmortem_sections` against required systemic themes along with priority matching.

**Time-Pressure Discount**: The environment imposes a time penalty. For any task spanning beyond `3` steps, the raw score incurs a compounding `-0.05` deduction to incentivize efficiency natively simulating service downtime cost.

## Quick Start

### a. Docker Run Locally
```bash
docker build -t incident-response-env .
docker run -p 7860:7860 incident-response-env
```

### b. Test with cURL
```bash
curl -X POST http://localhost:7860/reset \
     -H "Content-Type: application/json" \
     -d '{"task_level": "easy"}'
```

### c. Run Baseline
```bash
export HF_TOKEN="your_huggingface_token_here"
export ENV_URL="http://localhost:7860"
python inference.py
```

## Baseline Scores

| Task | Model | Avg Score | Steps |
| --- | --- | --- | --- |
| easy | Qwen2.5-72B | 0.85 | 3 |
| medium | Qwen2.5-72B | 0.45 | 8 |
| hard | Qwen2.5-72B | 0.20 | 8 |

## Project Structure
```text
.
├── Dockerfile                  # Container orchestration script
├── inference.py                # Native python baseline validation agent script
├── openenv.yaml                # Standard OpenEnv metadata schema
├── README.md                   # Environment documentation (this file)
└── server/
    ├── environment.py          # State-transition and core simulation mechanics
    ├── graders.py              # Task difficulty logic and deterministic scoring  
    ├── main.py                 # FastAPI container entrypoint and HTTP wrappers
    ├── models.py               # Pydantic typing for observation/action spaces
    ├── scenarios.py            # Static pre-rendered incidence ground truth files
    └── requirements.txt        # Isolated Python container dependencies
```

## License
MIT License.
