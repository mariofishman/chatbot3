import json
import os
import sys
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from openai import APIConnectionError

from src.graphv3 import config, graph


def print_existing(existing: dict) -> None:
    if not existing:
        print("Existing profiles: none")
        return

    print(f"Existing profiles: {len(existing)}")
    for user_id, profile in existing.items():
        name = profile.name or "Unknown"
        role = profile.role or "-"
        location = profile.location or "-"
        company = profile.company or "-"
        interests = ", ".join(profile.interests) if profile.interests else "-"
        print(f"- {user_id}")
        print(f"  name={name} | role={role} | company={company} | location={location}")
        print(f"  interests={interests}")


def print_plan(plan) -> None:
    if not plan:
        print("Plan: none")
        return

    print("Plan:")
    print(f"- create summary: {plan.reasoning_summary_for_create or '-'}")
    print(f"- update summary: {plan.reasoning_summary_for_update or '-'}")

    if plan.relevant_for_create_links:
        print("- create links:")
        for link in plan.relevant_for_create_links:
            print(f"  - message_id={link.message_id} | new_person_count={link.new_person_count}")
    else:
        print("- create links: none")

    if plan.relevant_for_update_links:
        print("- update links:")
        for link in plan.relevant_for_update_links:
            ids = ", ".join(link.user_profile_ids) if link.user_profile_ids else "-"
            print(f"  - message_id={link.message_id} | user_profile_ids=[{ids}]")
    else:
        print("- update links: none")


def print_snapshot_summary() -> None:
    snapshot = graph.get_state(config)
    values = snapshot.values

    print("\nThread state summary:\n")
    print_plan(values.get("plan"))
    print()
    print_existing(values.get("existing", {}))

    if snapshot.next:
        print(f"\nNext node(s): {list(snapshot.next)}")
    else:
        print("\nNext node(s): none")

    if snapshot.interrupts:
        print("\nPending interrupt(s):")
        for interrupt in snapshot.interrupts:
            print(f"- {interrupt}")
    else:
        print("\nPending interrupt(s): none")


def run_user_turn(user_text: str) -> None:
    state = {
        "messages": [
            HumanMessage(
                id=f"hm_{uuid4().hex[:8]}",
                content=user_text,
            )
        ]
    }

    result = graph.invoke(state, config=config)

    print("\nTurn result:\n")
    print_plan(result.get("plan"))
    print()
    print_existing(result.get("existing", {}))
    print_snapshot_summary()


def resume_interrupt() -> None:
    print("\nPaste JSON to resume the pending interrupt.")
    payload_text = input("resume> ").strip()

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        print(f"\nInvalid JSON: {exc}")
        return

    result = graph.invoke(Command(resume=payload), config=config)

    print("\nTurn result after resume:\n")
    print_plan(result.get("plan"))
    print()
    print_existing(result.get("existing", {}))
    print_snapshot_summary()


def main() -> None:
    print("Graph terminal runner")
    print("Commands:")
    print("  /exit    quit")
    print("  /state   show checkpointed state")
    print("  /resume  resume a pending interrupt with JSON\n")

    while True:
        try:
            user_text = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

        if not user_text:
            continue
        if user_text == "/exit":
            return
        if user_text == "/state":
            print_snapshot_summary()
            continue
        if user_text == "/resume":
            try:
                resume_interrupt()
            except APIConnectionError as exc:
                print(f"\nModel API connection failed during resume: {exc}")
            continue

        try:
            run_user_turn(user_text)
        except APIConnectionError as exc:
            print("\nGraph run failed because the model API could not be reached.\n")
            print("Check that:")
            print("- your network connection is working")
            print("- your OpenAI API credentials are configured")
            print("- the selected model endpoint is reachable from this machine\n")
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
