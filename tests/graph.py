from src.docs_doctor import graph

async def test_react_agent_simple_passthrough() -> None:
    res = await graph.ainvoke(
        {"messages": [("user", "I want to add a session focused on strength and one on technique.")]},
        {"configurable": {"system_prompt": """You are a helpful AI assistant that has access to tools.
If the tools don't depend on each other call them in parallel.

System time: {system_time}"""}},
    )

    print(res)

test_react_agent_simple_passthrough()