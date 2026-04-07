import os
import json
import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
TASK_LEVEL_VAR = os.getenv("TASK_LEVEL")
MAX_STEPS = 8

def run_task(client, task_level):
    print(f"[START] task={task_level} env=incident-response-env model={MODEL_NAME}")
    
    try:
        resp = requests.post(f"{ENV_URL}/reset", json={"task_level": task_level}, timeout=30)
        resp.raise_for_status()
        obs = resp.json()
    except Exception as e:
        print(f"Failed to reset environment: {e}")
        return

    rewards = []
    done = False
    step = 0
    score = 0.0
    
    while not done and step < MAX_STEPS:
        step += 1
        
        system_prompt = "You are an expert Site Reliability Engineer responding to a system incident. You will receive alert details, service metrics, recent logs, and knowledge base articles. Based on this information, decide on the best action to take. Always respond with a valid JSON object matching the IncidentAction schema: {action_type, reasoning, target_service, runbook_steps, severity_assessment, postmortem_sections}. The 'action_type' MUST be one of exactly: ['diagnose', 'escalate', 'write_runbook', 'apply_fix', 'write_postmortem', 'resolve']. Be specific and technical."
        
        prompt = f"""Current Step: {step}
Time Elapsed: {obs.get('time_elapsed_minutes', 0)} mins
Incident Status: {obs.get('current_incident_status', 'N/A')}
Previous Actions: {json.dumps(obs.get('previous_actions', []))}

Alert:
{json.dumps(obs.get('alert', {}), indent=2)}

Metrics:
{json.dumps([m for m in obs.get('metrics', []) if m.get('is_anomalous')], indent=2)}
(Only showing anomalous metrics for brevity, but consider them all)

Recent Logs (last 10):
{json.dumps(obs.get('recent_logs', [])[-10:], indent=2)}

Knowledge Base Articles:
{json.dumps(obs.get('kb_articles', []), indent=2)}

Return ONLY valid JSON.
"""

        action_json = None
        action = None
        error_msg = "null"
        
        if client:
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.0
                )
                action_text = response.choices[0].message.content.strip()
                if action_text.startswith("```json"):
                    action_text = action_text[7:]
                if action_text.endswith("```"):
                    action_text = action_text[:-3]
                action = json.loads(action_text.strip())
            except Exception as e:
                error_msg = f"LLM error or parse error: {str(e)}"
        
        if not action or not isinstance(action, dict):
            if not error_msg or error_msg == "null":
                error_msg = "Parse error: default fallback used"
            action = {
                "action_type": "diagnose",
                "reasoning": "parse error fallback",
                "target_service": None,
                "runbook_steps": None,
                "severity_assessment": None,
                "postmortem_sections": None
            }
        else:
            valid_actions = ['diagnose', 'escalate', 'write_runbook', 'apply_fix', 'write_postmortem', 'resolve']
            if action.get("action_type") not in valid_actions:
                action["action_type"] = "diagnose"
            
        action_str = action.get("action_type", "unknown")
            
        try:
            step_resp = requests.post(f"{ENV_URL}/step", json=action, timeout=30)
            step_resp.raise_for_status()
            result = step_resp.json()
            
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            obs = result.get("observation", {})
        except Exception as e:
            reward = 0.01
            done = True
            error_msg = f"Env API error: {str(e)}"
            
        rewards.append(reward)
        print(f"[STEP] step={step} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_msg}")
        
    raw_score = sum(rewards) / MAX_STEPS
    score = min(max(raw_score, 0.01), 0.99)
    success = score >= 0.1
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    
    print(f"[END] success={str(success).lower()} steps={step} score={score:.3f} rewards={rewards_str}")

def main():
    client = None
    if HF_TOKEN:
        client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
        
    tasks = ["easy", "medium", "hard"]
    if TASK_LEVEL_VAR:
        tasks = [TASK_LEVEL_VAR]
        
    for task in tasks:
        run_task(client, task)

if __name__ == "__main__":
    main()
