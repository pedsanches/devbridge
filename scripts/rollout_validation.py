import httpx
import json
import time
import random

BASE_URL = "http://localhost:8001/api/v1"
USERS_COUNT = 5
RESPONSES_TARGET = 30
DISPLAYED_TARGET = 20
FEEDBACK_TARGET = 10  # 5 up, 5 down

QUESTIONS = [
    "O que o time fez essa semana?",
    "Quais os ultimos PRs do Pedro?",
    "Como esta o roadmap?",
    "Liste as atividades recentes",
    "Quem trabalhou no backend?",
    "Quais issues foram fechadas?",
    "Resuma o progresso do projeto",
    "Ha bloqueios identificados?",
    "Mostre commits recentes",
    "Qual o status da sprint?",
]


def main():
    print("Starting Rollout Validation...")

    # Check if endpoints are up
    try:
        httpx.get(f"{BASE_URL}/chat/health", timeout=5)
    except Exception as e:
        print(
            f"ERROR: Backend does not seem to be running at http://localhost:8001: {e}"
        )
        return

    # 1. Authenticate Users
    users = []
    print(f"1. Authenticating {USERS_COUNT} users...")

    for i in range(USERS_COUNT):
        email = f"user{i+1}@example.com"
        try:
            resp = httpx.post(
                f"{BASE_URL}/auth/dev-login", json={"email": email}, timeout=10
            )
            if resp.status_code >= 400:
                print(f"Status: {resp.status_code}, Body: {resp.text}")
                resp.raise_for_status()

            # httpx cookies
            users.append({"email": email, "cookies": resp.cookies})
        except Exception as e:
            print(f"Failed to login {email}: {e}")
            return

    print(f"Authenticated {len(users)} users.")

    # 2. Generate Responses
    responses = []

    print(f"\n2. Generating {RESPONSES_TARGET} responses...")

    user_idx = 0
    for i in range(RESPONSES_TARGET):
        user = users[user_idx % len(users)]
        user_idx += 1

        question = random.choice(QUESTIONS)

        try:
            # Send Chat
            chat_payload = {"message": question, "persona": "product", "days": 30}
            resp = httpx.post(
                f"{BASE_URL}/chat",
                json=chat_payload,
                cookies=user["cookies"],
                timeout=30,
            )
            resp.raise_for_status()
            chat_data = resp.json()

            conversation_id = chat_data["conversation_id"]
            metadata = chat_data.get("metadata", {})
            generation_id = metadata.get("generation_id")
            trace_id = metadata.get("trace_id")
            prompt_version_id = metadata.get("prompt_version_id")

            if not generation_id or not prompt_version_id:
                print(f"WARNING: Missing lineage in response {i}. Metadata: {metadata}")
                continue

            # Get Message ID (Assistant's response)
            # Fetch conversation details
            conv_resp = httpx.get(
                f"{BASE_URL}/conversations/{conversation_id}",
                cookies=user["cookies"],
                timeout=10,
            )
            conv_resp.raise_for_status()
            conv_data = conv_resp.json()
            messages = conv_data.get("messages", [])

            # Assuming the last message is the assistant's
            if not messages:
                print(f"WARNING: No messages found for conv {conversation_id}")
                continue

            last_message = messages[-1]
            if last_message["role"] != "assistant":
                # Find the last assistant message
                assistant_msgs = [m for m in messages if m["role"] == "assistant"]
                if assistant_msgs:
                    last_message = assistant_msgs[-1]
                else:
                    print(f"WARNING: No assistant message in conv {conversation_id}")
                    continue

            message_id = last_message["id"]

            responses.append(
                {
                    "user": user,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "generation_id": generation_id,
                    "trace_id": trace_id,
                    "prompt_version_id": prompt_version_id,
                }
            )

            # Progress dot
            print(".", end="", flush=True)

        except Exception as e:
            print(f"x ({e})", end="", flush=True)

    print(f"\nGenerated {len(responses)} valid responses.")
    if len(responses) < RESPONSES_TARGET:
        print("Warning: Did not reach target responses.")

    # 3. Log Displayed Events
    print(f"\n3. Logging {DISPLAYED_TARGET} displayed events...")
    displayed_count = 0
    for i in range(min(len(responses), DISPLAYED_TARGET)):
        r = responses[i]
        try:
            params = {
                "generation_id": r["generation_id"],
                "message_id": r["message_id"],
            }
            if r["trace_id"]:
                params["trace_id"] = r["trace_id"]

            resp = httpx.post(
                f"{BASE_URL}/feedback/events/displayed",
                params=params,
                cookies=r["user"]["cookies"],
                timeout=10,
            )
            resp.raise_for_status()
            displayed_count += 1
            r["displayed"] = True
            print(".", end="", flush=True)
        except Exception as e:
            print(f"x ({e})", end="", flush=True)

    print(f"\nLogged {displayed_count} displayed events.")

    # 4. Submit Feedback
    print(f"\n4. Submitting {FEEDBACK_TARGET} feedbacks...")
    feedback_count = 0
    feedbacks_sent = []

    # Use the responses that were displayed
    displayed_responses = [r for r in responses if r.get("displayed")]

    for i in range(min(len(displayed_responses), FEEDBACK_TARGET)):
        r = displayed_responses[i]

        # Split 50/50 up/down
        feedback_type = "thumbs_up" if i < 5 else "thumbs_down"

        payload = {
            "message_id": r["message_id"],
            "conversation_id": r["conversation_id"],
            "feedback_type": feedback_type,
            "generation_id": r["generation_id"],
            "prompt_version_id": r["prompt_version_id"],
            "trace_id": r["trace_id"],
        }

        try:
            resp = httpx.post(
                f"{BASE_URL}/feedback",
                json=payload,
                cookies=r["user"]["cookies"],
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            feedbacks_sent.append(
                {"payload": payload, "response": data, "user": r["user"]}
            )
            feedback_count += 1
            print(".", end="", flush=True)
        except Exception as e:
            print(f"x ({e})", end="", flush=True)

    print(f"\nSubmitted {feedback_count} feedbacks.")

    # 5. Idempotency Test
    print("\n5. Testing idempotency...")
    if feedbacks_sent:
        original = feedbacks_sent[0]
        try:
            resp = httpx.post(
                f"{BASE_URL}/feedback",
                json=original["payload"],
                cookies=original["user"]["cookies"],
                timeout=10,
            )
            resp.raise_for_status()
            dup_data = resp.json()

            if (
                dup_data["created"] is False
                and dup_data["feedback_id"] == original["response"]["feedback_id"]
            ):
                print(
                    "SUCCESS: Idempotency confirmed: 'created' is False and IDs match."
                )
            else:
                print(f"FAILURE: Idempotency check failed: {dup_data}")
        except Exception as e:
            print(f"Error testing idempotency: {e}")
    else:
        print("Skipped idempotency test (no feedback sent).")

    # 6. Fetch stats
    # Pick a user who has submitted feedback to see their org stats
    target_user = feedbacks_sent[0]["user"] if feedbacks_sent else users[0]

    print("\n\n--- REPORT METRICS ---")
    print(f"Fetching metrics for user: {target_user['email']} (Organization scope)")

    time.sleep(1)

    try:
        # Funnel
        resp = httpx.get(
            f"{BASE_URL}/feedback/funnel?period_days=1",
            cookies=target_user["cookies"],
            timeout=10,
        )
        if resp.status_code == 200:
            print("\n[Funnel]")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Failed to get funnel: {resp.status_code} {resp.text}")

        # Stats
        resp = httpx.get(
            f"{BASE_URL}/feedback/stats?period_days=1",
            cookies=target_user["cookies"],
            timeout=10,
        )
        if resp.status_code == 200:
            print("\n[Stats]")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Failed to get stats: {resp.status_code} {resp.text}")

        # Quality Score
        resp = httpx.get(
            f"{BASE_URL}/feedback/quality-score?period_days=1",
            cookies=target_user["cookies"],
            timeout=10,
        )
        if resp.status_code == 200:
            print("\n[Quality Score]")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Failed to get quality score: {resp.status_code} {resp.text}")

    except Exception as e:
        print(f"Error fetching stats: {e}")


if __name__ == "__main__":
    main()
