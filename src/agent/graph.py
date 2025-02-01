"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.configuration import Configuration
from src.agent.state import InputState, State
from src.agent.tools import TOOLS
from src.agent.utils import call_model

# Define the function that calls the model


async def package_supervisor(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = call_model(config).bind_tools(TOOLS)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt

    # Get the model's response
    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages], config
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ]
        }
    
    return {"messages": [response]}

# Define a new graph

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(package_supervisor)
builder.add_node("tools", ToolNode(TOOLS))
# builder.add_node(package_aggregator)

# Set the entrypoint as `package_supervisor`
# This means that this node is the first one called
builder.add_edge("__start__", "package_supervisor")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"


# Add a conditional edge to determine the next step after `package_supervisor`
builder.add_conditional_edges(
    "package_supervisor",
    # After package_supervisor finishes running, the next node(s) are scheduled
    # based on the output from route_model_output
    route_model_output,
)

# Add a normal edge from `tools` to `package_supervisor`
# This creates a cycle: after using tools, we always return to the model
builder.add_edge("tools", "package_supervisor")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
docs_doctor = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
docs_doctor.name = "Docs Doctor"  # This customizes the name in LangSmith

def invoke_docs_doctor(st_messages, callables):
    # Ensure the callables parameter is a list as you can have multiple callbacks
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")
    # Invoke the graph with the current messages and callback configuration
    return docs_doctor.invoke({"messages": st_messages}, config={"callbacks": callables})
