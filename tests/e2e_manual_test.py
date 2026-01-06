import json
import sys
import time
import urllib.request


def run_test():
    url = "http://localhost:8000/v1/chat/message"
    payload = {
        "user_id": "e2e_test_user",
        "message": "Hello, verify you are working.",
        "thread_id": "e2e_test_thread",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )

    print(f"Sending request to {url}...")
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            body = response.read().decode("utf-8")

            print(f"Status: {status}")
            print(f"Response: {body}")

            if status == 200:
                print("SUCCESS: Endpoint returned 200")

                # Check state
                state_url = (
                    f"http://localhost:8000/v1/chat/debug/state/{payload['thread_id']}"
                )
                print(f"Checking state at {state_url}...")
                with urllib.request.urlopen(state_url) as r:
                    print(f"State: {r.read().decode('utf-8')}")

                return 0
            else:
                print("FAILURE: Endpoint returned non-200")
                return 1
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code}: {e.reason}")
        print(f"Error Body: {e.read().decode('utf-8')}")
        return 1
    except Exception as e:
        print(f"ERROR: Failed to connect or receive response: {e}")
        return 1


if __name__ == "__main__":
    # Wait for server to start
    for _ in range(10):
        try:
            with urllib.request.urlopen("http://localhost:8000/docs") as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(1)
            print("Waiting for server...")

    sys.exit(run_test())
