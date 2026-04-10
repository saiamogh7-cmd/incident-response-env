import os
import json
import time
import requests
from openai import OpenAI

# ── Environment variables ─────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN is required")

ENV_URL    = os.getenv("ENV_URL",    "http://localhost:7860")
TASK_LEVEL = os.getenv("TASK_LEVEL", "all")   # "easy", "medium", "hard", or "all"

MAX_STEPS = 8

# ── Agent system prompt (exact, per spec) ─────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a senior SRE diagnosing a live incident. Analyze the alert, metrics, and logs. \n"
    "Respond ONLY with valid JSON matching this exact schema — no markdown, no explanation:\n"
    "{\n"
    '  "action_type": "diagnose"|"write_runbook"|"write_postmortem"|"resolve"|"escalate"|"apply_fix",\n'
    '  "reasoning": "<your analysis>",\n'
    '  "target_service": "<service name or null>",\n'
    '  "runbook_steps": ["step1","step2",...] or null,\n'
    '  "severity_assessment": "P1"|"P2"|"P3"|"P4" or null,\n'
    '  "postmortem_sections": {"summary":"...","timeline":"...","root_cause":"...","impact":"...","action_items":"..."} or null\n'
    "}"
)

VALID_ACTION_TYPES = {
    "diagnose", "write_runbook", "write_postmortem",
    "resolve",  "escalate",      "apply_fix",
}

FALLBACK_ACTION = {
    "action_type":         "diagnose",
    "reasoning":           "fallback",
    "target_service":      None,
    "runbook_steps":       None,
    "severity_assessment": None,
    "postmortem_sections": None,
}


# ── Prompt builder ────────────────────────────────────────────────────────────
def build_user_prompt(step: int, obs: dict) -> str:
    alert   = obs.get("alert", {})
    metrics = obs.get("metrics", [])
    logs    = obs.get("recent_logs", [])
    kb      = obs.get("kb_articles", [])
    prev    = obs.get("previous_actions", [])
    elapsed = obs.get("time_elapsed_minutes", 0)

    # Format metrics — mark anomalous
    metric_lines = []
    for m in metrics:
        name  = m.get("metric_name") or m.get("name", "unknown")
        value = m.get("value", "N/A")
        unit  = m.get("unit", "")
        tag   = " [ANOMALOUS]" if m.get("is_anomalous") else ""
        metric_lines.append(f"  {name}: {value}{unit}{tag}")
    metrics_block = "\n".join(metric_lines) if metric_lines else "  (none)"

    # Last 8 log lines
    last_logs = logs[-8:] if len(logs) > 8 else logs
    log_block = "\n".join(
        f"  {ln}" if isinstance(ln, str) else f"  {json.dumps(ln)}"
        for ln in last_logs
    ) or "  (none)"

    # KB articles
    kb_block = "\n".join(
        f"  [{a.get('title','?')}]: {a.get('content','')}"
        if isinstance(a, dict) else f"  {a}"
        for a in kb
    ) or "  (none)"

    # Previous actions
    prev_block = json.dumps(prev, indent=2) if prev else "[]"

    prompt = (
        f"Step: {step}\n"
        f"Time elapsed: {elapsed} minutes\n"
        "\n"
        "=== ALERT ===\n"
        f"  Title:       {alert.get('title', 'N/A')}\n"
        f"  Severity:    {alert.get('severity', 'N/A')}\n"
        f"  Description: {alert.get('description', 'N/A')}\n"
        "\n"
        "=== METRICS ===\n"
        f"{metrics_block}\n"
        "\n"
        "=== RECENT LOGS (last 8) ===\n"
        f"{log_block}\n"
        "\n"
        "=== KNOWLEDGE BASE ARTICLES ===\n"
        f"{kb_block}\n"
        "\n"
        "=== PREVIOUS ACTIONS ===\n"
        f"{prev_block}\n"
        "\n"
        "Return ONLY the JSON action."
    )
    return prompt


# ── JSON fence stripper ───────────────────────────────────────────────────────
def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # remove opening fence line
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# ── Single task runner ────────────────────────────────────────────────────────
def run_task(client: OpenAI, task_name: str) -> None:
    print(f"[START] task={task_name} env=incident-response-env model={MODEL_NAME}")

    rewards: list[float] = []
    step     = 0
    done     = False
    success  = False
    obs: dict = {}

    try:
        # Reset environment
        resp = requests.post(
            f"{ENV_URL}/reset",
            json={"task_level": task_name},
            timeout=30,
        )
        resp.raise_for_status()
        obs = resp.json()

        # Episode loop
        while not done and step < MAX_STEPS:
            step += 1
            error_msg = "null"
            action    = None

            # ── Call LLM ──────────────────────────────────────────────────────
            try:
                user_prompt = build_user_prompt(step, obs)
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_prompt},
                    ],
                    max_tokens=1000,
                    temperature=0.0,
                )
                raw_text = response.choices[0].message.content
                json_text = strip_fences(raw_text)
                action = json.loads(json_text)

                # Sanitise action_type
                if not isinstance(action, dict):
                    raise ValueError("LLM response is not a JSON object")
                if action.get("action_type") not in VALID_ACTION_TYPES:
                    action["action_type"] = "diagnose"

            except Exception as exc:
                error_msg = str(exc)
                action    = dict(FALLBACK_ACTION)

            # ── Send action to environment ─────────────────────────────────
            action_type = action.get("action_type", "diagnose")
            reward      = 0.0
            try:
                step_resp = requests.post(
                    f"{ENV_URL}/step",
                    json=action,
                    timeout=30,
                )
                step_resp.raise_for_status()
                result  = step_resp.json()
                reward  = float(result.get("reward", 0.0))
                done    = bool(result.get("done",   False))
                obs     = result.get("observation", obs)
            except Exception as exc:
                if error_msg == "null":
                    error_msg = str(exc)
                else:
                    error_msg = f"{error_msg}; env error: {exc}"
                done = True

            rewards.append(reward)

            # success if any reward >= 0.7
            if reward >= 0.7:
                success = True

            print(
                f"[STEP] step={step} action={action_type} "
                f"reward={reward:.2f} done={str(done).lower()} error={error_msg}"
            )

    except Exception as outer_exc:
        # Unrecoverable error before loop finished; still need [END]
        if step == 0:
            # No steps were recorded; add a zero reward so rewards list is non-empty
            rewards.append(0.0)
            step = 1
        print(f"[STEP] step={step} action=diagnose reward=0.00 done=true error={outer_exc}")

    finally:
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(
            f"[END] success={str(success).lower()} "
            f"steps={step} rewards={rewards_str}"
        )


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

    if TASK_LEVEL == "all":
        tasks = ["easy", "medium", "hard"]
    else:
        tasks = [TASK_LEVEL]

    for task in tasks:
        run_task(client, task)


if __name__ == "__main__":
    main()
