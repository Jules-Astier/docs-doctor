import asyncio
import logging
from types import SimpleNamespace
from typing import Any, AsyncGenerator

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from streamlit.runtime.scriptrunner import get_script_run_ctx

from docs_doctor.core import settings
from docs_doctor.agent.graph import equip_docs_doctor
from docs_doctor.schema import ChatHistory, ChatMessage
from docs_doctor.utils.streamlit_utils import (
    convert_message_content_to_string,
    langchain_to_chat_message,
    remove_tool_calls,
)
from docs_doctor.utils.packages import get_available_packages, get_local_packages

APP_TITLE = "DocsDoctor"
APP_ICON = "🧰"
logger = logging.getLogger(__name__)

class DirectAgentClient:
    def __init__(self):
        self.info = self._get_service_info()
        self._current_packages = set(self.info.packages)
        self.agent = equip_docs_doctor(self.info.packages)
        
    def _get_service_info(self):
        available_packages = get_available_packages()
        local_packages = get_local_packages()
        preset_packages = [
            package['package_name']
            for package in available_packages
            if package['package_name'] in local_packages
        ]
        return SimpleNamespace(
            models=settings.AVAILABLE_MODELS,
            default_model=settings.DEFAULT_MODEL,
            default_packages=preset_packages,
            available_packages=[package['package_name'] for package in available_packages],
            packages=preset_packages
        )
    
    def _ensure_agent_current(self):
        if set(self._current_packages) != set(self.info.packages):
            self.agent = equip_docs_doctor(self.info.packages)
            self._current_packages = set(self.info.packages)
    
    def _create_config(self, message: str, model: str, thread_id: str) -> dict[str, Any]:
        history = self.get_history(thread_id)
        messages_to_send = []
        
        i = 0
        while i < len(history.messages):
            msg = history.messages[i]
            
            if msg.type == "human":
                messages_to_send.append(HumanMessage(content=msg.content))
            elif msg.type == "ai":
                ai_message = AIMessage(content=msg.content, tool_calls=msg.tool_calls)
                messages_to_send.append(ai_message)
                
                if msg.tool_calls:
                    tool_call_ids = [call["id"] for call in msg.tool_calls]
                    i += 1
                    while i < len(history.messages) and history.messages[i].type == "tool":
                        tool_msg = history.messages[i]
                        if tool_msg.tool_call_id in tool_call_ids:
                            messages_to_send.append(ToolMessage(
                                tool_call_id=tool_msg.tool_call_id,
                                content=tool_msg.content
                            ))
                        i += 1
                    i -= 1
            i += 1
        
        messages_to_send.append(HumanMessage(content=message))
        
        return {
            "input": {"messages": messages_to_send},
            "config": RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "model": model,
                },
            ),
        }
    
    async def ainvoke(self, message: str, model: str, thread_id: str) -> ChatMessage:
        self._ensure_agent_current()
        config = self._create_config(message, model, thread_id)
        response = await self.agent.ainvoke(**config)
        return langchain_to_chat_message(response["messages"][-1])
    
    async def astream(self, message: str, model: str, thread_id: str) -> AsyncGenerator[ChatMessage | str, None]:
        self._ensure_agent_current()
        config = self._create_config(message, model, thread_id)
        
        async for event in self.agent.astream_events(**config, version="v2"):
            if not event:
                continue
            
            new_messages = []
            if (event["event"] == "on_chain_end" and 
                any(t.startswith("graph:step:") for t in event.get("tags", [])) and 
                "messages" in event["data"]["output"]):
                new_messages = event["data"]["output"]["messages"]
            elif event["event"] == "on_custom_event" and "custom_data_dispatch" in event.get("tags", []):
                new_messages = [event["data"]]

            for message in new_messages:
                try:
                    chat_message = langchain_to_chat_message(message)
                    if not (chat_message.type == "human" and chat_message.content == message):
                        yield chat_message
                except Exception as e:
                    logger.error(f"Error parsing message: {e}")

            if (event["event"] == "on_chat_model_stream" and 
                "llama_guard" not in event.get("tags", [])):
                content = remove_tool_calls(event["data"]["chunk"].content)
                if content:
                    yield convert_message_content_to_string(content)

    def get_history(self, thread_id: str) -> ChatHistory:
        state = self.agent.get_state(
            config=RunnableConfig(
                configurable={"thread_id": thread_id},
                callbacks=None,
            )
        )
        messages = state.values.get('messages', []) if state else []
        return ChatHistory(messages=[langchain_to_chat_message(m) for m in messages])

class MessageRenderer:
    @staticmethod
    def render_message(msg: ChatMessage):
        if msg.type == "human":
            st.chat_message("human").write(msg.content)
        elif msg.type == "ai":
            with st.chat_message("ai") as container:
                if msg.content:
                    st.write(msg.content)
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        status = st.status(
                            f"Tool Call: {tool_call['name']}",
                            state="complete"
                        )
                        status.write("Input:")
                        status.write(tool_call["args"])
                        return status  # Return status for tool result updates

    @staticmethod
    async def render_stream(messages_agen: AsyncGenerator[ChatMessage | str, None],
                          existing_messages: bool = False):
        streaming_content = ""
        streaming_placeholder = None
        current_ai_message = None
        message_container = st.chat_message("ai") if not existing_messages else None
        
        async for msg in messages_agen:
            print("STREAMING MSG: ", msg)
            if isinstance(msg, str):
                if not existing_messages:
                    if not streaming_placeholder:
                        with message_container:
                            streaming_placeholder = st.empty()
                    streaming_content += msg
                    streaming_placeholder.write(streaming_content)
                continue
            
            if msg.type == "ai":
                current_ai_message = msg
        
        if not existing_messages and current_ai_message:
            st.session_state.messages.append(current_ai_message)

def setup_page():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        menu_items={},
    )
    
    st.html("""
        <style>
        [data-testid="stStatusWidget"] {
            visibility: hidden;
            height: 0%;
            position: fixed;
        }
        </style>
    """)
    
    if st.get_option("client.toolbarMode") != "minimal":
        st.set_option("client.toolbarMode", "minimal")
        st.rerun()

def setup_sidebar(agent_client: DirectAgentClient):
    with st.sidebar:
        st.header(f"{APP_ICON} {APP_TITLE}")
        st.write("")
        st.write("Full toolkit for running an AI agent service built with LangGraph, FastAPI and Streamlit")
        
        agent_client.info.packages = st.multiselect(
            "Enabled packages",
            options=agent_client.info.available_packages,
            default=agent_client.info.default_packages,
            help="Select packages to enable"
        )
        use_streaming = st.toggle("Stream results", value=settings.DEFAULT_STREAMING)
        
        st.write("[View the source code](https://github.com/Jules-Astier/docs-doctor)")
        st.caption("Made with :material/favorite: by [Jules] in London")
        
        return use_streaming

def setup_model_selection(agent_client: DirectAgentClient):
    # Initialize session state
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = agent_client.info.models[0]
    if "model_settings_expanded" not in st.session_state:
        st.session_state.model_settings_expanded = False
    
    sort_keys = {
        "Name": ("name", False),
        "Prompt Price ↑": ("pricing.prompt", False),
        "Prompt Price ↓": ("pricing.prompt", True),
        "Completion Price ↑": ("pricing.completion", False),
        "Completion Price ↓": ("pricing.completion", True)
    }
    
    # Get sorted models before creating the expander
    models = agent_client.info.models.copy()
    sort_option = st.session_state.get("model_sort", "Prompt Price ↑")
    key, reverse = sort_keys[sort_option]
    
    def get_nested_value(d, key_path):
        current = d
        for k in key_path.split('.'):
            current = current[k]
        return current
    
    models.sort(key=lambda x: get_nested_value(x, key), reverse=reverse)
    model_options = {m['name']: m for m in models}
    
    # Create expander using the current selected model
    current_model_id = st.session_state.selected_model['id']
    model_select = st.expander(
        f"Selected Model: {current_model_id}", 
        expanded=st.session_state.model_settings_expanded
    )
    
    if model_select:
        with model_select:
            st.session_state.model_settings_expanded = True
            col1, col2 = st.columns([2, 1])
            
            with col2:
                # Sort options
                sort_option = st.selectbox(
                    "Sort by",
                    options=list(sort_keys.keys()),
                    index=1,
                    key="model_sort"
                )
            
            with col1:
                # Model selection
                selected_model_name = st.selectbox(
                    "Select Model",
                    options=list(model_options.keys()),
                    index=list(model_options.keys()).index(st.session_state.selected_model['name']),
                    key="model_selection"
                )
                
                # Update session state with new selection
                st.session_state.selected_model = model_options[selected_model_name]
                
                # Force a rerun to update the expander label using the current method
                if current_model_id != st.session_state.selected_model['id']:
                    st.rerun()
            
            # Display model info
            st.info(f"""
                ##### {st.session_state.selected_model['name']}
                **Context Length:** {st.session_state.selected_model['context_length']:,} tokens\n
                **Pricing:** ${round(float(st.session_state.selected_model['pricing']['prompt']) * 1000000, 3)}/
                            ${round(float(st.session_state.selected_model['pricing']['completion']) * 1000000, 3)} per M token\n
                **Architecture:**
                - Modality: {st.session_state.selected_model['architecture']['modality']}
                - Type: {st.session_state.selected_model['architecture']['instruct_type']}
                
                {st.session_state.selected_model['description']}
            """)
    else:
        st.session_state.model_settings_expanded = False
    
    return st.session_state.selected_model['id']

async def handle_user_input(agent_client: DirectAgentClient, 
							user_input: str, 
							model: str,
							use_streaming: bool):
	user_message = ChatMessage(type="human", content=user_input)
	st.session_state.messages.append(user_message)
	MessageRenderer.render_message(user_message)

	if use_streaming:
		stream = agent_client.astream(
			message=user_input,
			model=model,
			thread_id=st.session_state.thread_id,
		)
		await MessageRenderer.render_stream(stream)
	else:
		response = await agent_client.ainvoke(
			message=user_input,
			model=model,
			thread_id=st.session_state.thread_id,
		)
		st.session_state.messages.append(response)
		MessageRenderer.render_message(response)

	st.rerun()

async def main():
	setup_page()

	if "agent_client" not in st.session_state:
		load_dotenv()
		try:
			with st.spinner("Initializing agent..."):
				st.session_state.agent_client = DirectAgentClient()
		except Exception as e:
			st.error(f"Error initializing agent: {e}")
			st.stop()

	agent_client: DirectAgentClient = st.session_state.agent_client

	if "thread_id" not in st.session_state:
		thread_id = st.query_params.get("thread_id") or get_script_run_ctx().session_id
		try:
			messages = agent_client.get_history(thread_id=thread_id).messages if thread_id else []
		except Exception as e:
			logger.error(f"Error loading message history: {e}")
			messages = []
		st.session_state.messages = messages
		st.session_state.thread_id = thread_id

	use_streaming = setup_sidebar(agent_client)
	model = setup_model_selection(agent_client)

	if len(st.session_state.messages) == 0:
		WELCOME = "Hello! I'm an AI-powered coding assistant dedicated to your project. Ask me anything!"
		with st.chat_message("ai"):
			st.write(WELCOME)
	else:
		# print("MESSAGES: ", st.session_state.messages)
		for msg in st.session_state.messages:
			MessageRenderer.render_message(msg)

	if user_input := st.chat_input():
		await handle_user_input(agent_client, user_input, model, use_streaming)

if __name__ == "__main__":
    asyncio.run(main())