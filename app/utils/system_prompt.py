def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        "Use pdf_agent first to search for information."
        "If information are not found using pdf_agent, use web_agent to search information on website instead."
        "If you or any of the other assistants have the final answer or deliverable,"
        "prefix your response with FINAL ANSWER so the team knows to stop."
        f"\n{suffix}"
    )