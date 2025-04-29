"""Stage for executing worker tasks."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for worker task"""
    # Create fetch-todo payload for stakingSignature and publicSignature
    payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "fetch-todo",
        "githubUsername": worker.env.get("GITHUB_USERNAME"),
        "stakingKey": worker.staking_public_key,
        "pubKey": worker.public_key,
    }

    return {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "stakingKey": worker.staking_public_key,
        "pubKey": worker.public_key,
        "stakingSignature": create_signature(worker.staking_signing_key, payload),
        "publicSignature": create_signature(worker.public_signing_key, payload),
    }


def execute(runner, worker, data):
    """Execute worker task step"""
    url = f"{runner.get('middle_server_url')}/summarizer/worker/fetch-todo"
    response = requests.post(
        url,
        json={"signature": data["stakingSignature"], "stakingKey": data["stakingKey"]},
    )
    result = response.json()

    # Handle 409 gracefully - no eligible todos is an expected case
    if response.status_code == 409:
        print(
            f"✓ {result.get('message', 'No eligible todos')} for {worker.name} - continuing"
        )
        return {"success": True, "message": result.get("message")}
    else:
        response.raise_for_status()

    if result.get("success"):
        repo_url = f"https://github.com/{result['data']['repo_owner']}/{result['data']['repo_name']}"
        runner.set("repo_url", repo_url, scope="round")

    return result
