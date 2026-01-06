import json
import sys
import time
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
        # Send Request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )

        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            body = response.read().decode("utf-8")
            print(f"Response Received in {time.time() - start_time:.2f}s")
            print(f"Body: {body}")

        # Verify State
        state = get_state(thread_id)
        if not state:
            print("FAILURE: Could not retrieve state.")
            return 1

        print("\n--- State Verification ---")

        # 1. Check Plan
        plan = state.get("plan")
        if plan:
            print("[PASS] Plan created.")
            print(f"       Goal Analysis: {plan.get('goal_analysis')}")
            print(f"       Steps: {len(plan.get('steps', []))}")
        else:
            print("[FAIL] No plan found in state.")

        # 2. Check Critique
        critique = state.get("critique")
        if critique:
            print("[PASS] Critique generated.")
            print(f"       Score: {critique.get('score')}")
            print(f"       Improved: {critique.get('feedback')}")
        else:
            print("[FAIL] No critique found in state.")

        # 3. Check Flow
        last_agent = state.get("last_agent")
        step_count = state.get("step_count", 0)

        print(f"Last Agent: {last_agent}")
        print(f"Total Steps: {step_count}")

        if last_agent == "interviewer" and step_count >= 3:
            print("[PASS] Full cycle completed (Architect -> Critic -> Interviewer).")
            return 0
        else:
            print("[FAIL] Cycle did not complete as expected.")
            return 1

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_full_cycle_test())
