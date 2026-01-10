import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def get_state(thread_id: str) -> dict[str, Any]:
    url = f"http://localhost:8000/v1/chat/debug/state/{thread_id}"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        pass
    return {}


def _send_request(url: str, payload: dict[str, Any]) -> None:
    """Send the initial request."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    start_time = time.time()
    with urllib.request.urlopen(req) as response:
        body = response.read().decode("utf-8")
        print(f"Response Received in {time.time() - start_time:.2f}s")
        print(f"Body: {body}")


def _verify_plan(state: dict[str, Any]) -> None:
    """Verify plan existence."""
    plan = state.get("plan")
    if plan:
        print("[PASS] Plan created.")
        print(f"       Goal Analysis: {plan.get('goal_analysis')}")
        print(f"       Steps: {len(plan.get('steps', []))}")
    else:
        print("[FAIL] No plan found in state.")


def _verify_critique(state: dict[str, Any]) -> None:
    """Verify critique existence."""
    critique = state.get("critique")
    if critique:
        print("[PASS] Critique generated.")
        print(f"       Score: {critique.get('score')}")
        print(f"       Improved: {critique.get('feedback')}")
    else:
        print("[FAIL] No critique found in state.")


def _verify_flow(state: dict[str, Any]) -> bool:
    """Verify the agent flow and step count."""
    last_agent = state.get("last_agent")
    step_count = state.get("step_count", 0)

    print(f"Last Agent: {last_agent}")
    print(f"Total Steps: {step_count}")

    if last_agent == "interviewer" and step_count >= 3:
        print("[PASS] Full cycle completed (Architect -> Critic -> Interviewer).")
        return True

    print("[FAIL] Cycle did not complete as expected.")
    return False


def run_full_cycle_test():
    thread_id = f"test_cycle_{int(time.time())}"
    url = "http://localhost:8000/v1/chat/message"
    payload = {
        "user_id": "e2e_user",
        "message": "Create a 3-step plan to learn Python.",
        "thread_id": thread_id,
    }

    print(f"Starting Full Cycle Test (Thread: {thread_id})...")

    try:
        _send_request(url, payload)

        # Verify State
        state = get_state(thread_id)
        if not state:
            print("FAILURE: Could not retrieve state.")
            return 1

        print("\n--- State Verification ---")
        _verify_plan(state)
        _verify_critique(state)

        if _verify_flow(state):
            return 0
        return 1

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_full_cycle_test())
