import json
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

from langchain_core.runnables import RunnableConfig

from src.app.graph.state import AgentState
from src.app.prompts.renderer import render_prompt
from src.app.schemas import PlanSchema
from src.domain.entities.sphere import Sphere, SphereStatus
from src.infra.llm.client import get_llm_client

llm_client = get_llm_client()


def _user_id_to_uuid(user_id: str) -> UUID:
    """Convert user_id string to UUID consistently."""
    try:
        return UUID(user_id)
    except ValueError:
        # If not a valid UUID, create a deterministic UUID from the string
        return uuid5(NAMESPACE_DNS, user_id)


async def _extract_sphere_name(
    user_request: str, existing_spheres: list[Sphere], llm_client: Any
) -> str | None:
    """Extract sphere name from user request, or return None if unclear."""
    if not user_request.strip():
        return None

    # Simple heuristics first
    request_lower = user_request.lower()

    # Check for direct mentions like "about my career", "my childhood", etc.
    common_topics = [
        "career",
        "childhood",
        "education",
        "family",
        "relationships",
        "hobbies",
        "travel",
        "achievements",
    ]
    for topic in common_topics:
        if topic in request_lower:
            return topic.capitalize()

    # Check if user is selecting existing sphere by number or name
    existing_names = [s.name.lower() for s in existing_spheres]
    for i, name in enumerate(existing_names):
        if f"sphere {i + 1}" in request_lower or name in request_lower:
            return existing_spheres[i].name

    # Use LLM to extract if heuristics fail
    try:
        prompt = (
            "Extract the biography topic/sphere name from this user request. "
            "Return only the topic name in 1-3 words, or 'NONE' if unclear.\n\n"
            f"User request: {user_request}\n\nTopic:"
        )

        topic = await llm_client.generate_text(
            system_prompt=(
                "You are a helper that extracts biography topics from user requests."
            ),
            messages=[{"role": "user", "content": prompt}],
        )

        if isinstance(topic, str):
            topic = topic.strip()
            if topic and topic.upper() != "NONE":
                return topic
    except Exception:
        pass

    return None


async def architect_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Manages sphere selection and plan generation.
    """
    configurable = config.get("configurable", {})
    db_session = configurable.get("db_session")
    memory_service = configurable.get("memory_service")
    sphere_repo = configurable.get("sphere_repo")

    messages = state["messages"]
    user_id = state["user_id"]
    current_sphere_id = state.get("current_sphere_id")

    user_profile = state.get("user_profile")
    up_data: dict[str, Any]
    if user_profile is not None and hasattr(user_profile, "model_dump"):
        up_data = user_profile.model_dump()
    elif isinstance(user_profile, dict):
        up_data = user_profile
    else:
        up_data = {}

    # Get available spheres
    spheres = []
    current_sphere_name = ""
    if sphere_repo and db_session:
        spheres = await sphere_repo.get_by_user_id(_user_id_to_uuid(user_id))
        if current_sphere_id:
            current_sphere = await sphere_repo.get_by_id(UUID(current_sphere_id))
            current_sphere_name = current_sphere.name if current_sphere else ""

    spheres_data = [
        {"id": s.id, "name": s.name, "status": s.status.value} for s in spheres
    ]

    # Query memory for context
    memory_context = ""
    if memory_service and current_sphere_id:
        try:
            memories = await memory_service.search(
                "", user_id, limit=5
            )  # Recent memories
            memory_context = "\n".join([f"- {m.content}" for m in memories])
        except Exception:
            memory_context = "No existing memories found."

    # Extract user request from last message
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, "content"):
            user_request = last_msg.content
        elif isinstance(last_msg, dict):
            user_request = last_msg.get("content", str(last_msg))
        else:
            user_request = str(last_msg)
    else:
        user_request = ""

    system_prompt = render_prompt(
        "architect.j2",
        user_profile_json=json.dumps(up_data),
        spheres_json=json.dumps(spheres_data),
        current_sphere_name=current_sphere_name,
        memory_context=memory_context,
        user_request=user_request,
    )

    # If no sphere selected, handle sphere creation/selection
    if not current_sphere_id and sphere_repo:
        # Try to extract sphere name from user input
        sphere_name = await _extract_sphere_name(user_request, spheres, llm_client)

        if sphere_name:
            # Create new sphere
            new_sphere = Sphere(
                user_id=_user_id_to_uuid(user_id),
                name=sphere_name,
                status=SphereStatus.NOT_STARTED,
            )
            await sphere_repo.save(new_sphere)

            response = (
                f"Great! I've created a new sphere called '{sphere_name}' "
                "for you. Let's start collecting your biography in this area."
            )
            return {
                "messages": [{"role": "assistant", "content": response}],
                "current_sphere_id": str(new_sphere.id),
                "last_agent": "architect",
                "step_count": state["step_count"] + 1,
            }

        # No sphere name extracted, respond conversationally
        response = await llm_client.generate_text(
            system_prompt=system_prompt,
            messages=messages,
        )
        return {
            "messages": [{"role": "assistant", "content": response}],
            "last_agent": "architect",
            "step_count": state["step_count"] + 1,
        }

    # Sphere selected, generate plan
    plan = await llm_client.generate(
        system_prompt=system_prompt,
        messages=messages,
        schema=PlanSchema,
    )

    # Check if plan approval is required
    plan_approved = state.get("plan_approved")
    if plan_approved is None:
        # Plan generated but not approved yet - ask for approval
        approval_message = (
            "I've generated a plan for your biography collection. "
            "Would you like to proceed with this plan?\n\n"
            f"**Goal:** {plan.goal_analysis}\n\n"
            f"**Steps:** {len(plan.steps)} questions planned"
        )

        return {
            "plan": plan,  # Store the plan but don't proceed yet
            "messages": [{"role": "assistant", "content": approval_message}],
            "last_agent": "architect",
            "step_count": state["step_count"] + 1,
            # Don't set plan_approved - wait for user input
        }

    # Plan already approved/rejected
    if plan_approved:
        # Proceed to critic
        return {
            "plan": plan,
            "last_agent": "architect",
            "step_count": state["step_count"] + 1,
        }
    else:
        # Plan rejected - regenerate or ask for clarification
        rejection_message = (
            "Plan rejected. Let me create a different approach "
            "for your biography collection."
        )
        return {
            "plan": None,  # Clear the plan
            "plan_approved": None,  # Reset approval state
            "messages": [{"role": "assistant", "content": rejection_message}],
            "last_agent": "architect",
            "step_count": state["step_count"] + 1,
        }
