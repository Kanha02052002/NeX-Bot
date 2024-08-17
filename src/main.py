import os
import json
import time
import streamlit as st
from groq import Groq
import base64
from datetime import datetime

st.set_page_config(
    page_title="NeX-Bot",
    layout="centered"
)

working_dir = os.path.dirname(os.path.abspath(__file__))
config_path = f"{working_dir}/config.json"

# Initialize Groq client
client = None


# Function to convert chat history to a downloadable text file with current date and time
def get_chat_history_download_link(chat_history):
    # Format chat history into a string
    chat_history_str = "\n".join([f"{message['role'].capitalize()}: {message['content']}" for message in chat_history])

    # Encode the string to bytes
    chat_history_bytes = chat_history_str.encode()

    # Encode bytes to base64
    b64 = base64.b64encode(chat_history_bytes).decode()

    # Get current date and time for the filename
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"chat_history_{current_time}.txt"

    # Create a download link
    download_link = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Chat History</a>'

    return download_link


# Function to truncate text to 10 words
def truncate_text(text, word_limit=10):
    words = text.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return text


# Sidebar for settings
with st.sidebar:
    st.header("Set-up")
    models = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "llama3-groq-70b-8192-tool-use-preview",
        "llama3-groq-8b-8192-tool-use-preview",
        "llama-guard-3-8b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma-7b-it",
        "gemma2-9b-it",
        "whisper-large-v3"
    ]
    selected_model = st.selectbox("Select Model", options=models,
                                  index=models.index(st.session_state.get("selected_model", models[0])))
    st.session_state.selected_model = selected_model

    # Input for Username
    username = st.text_input("Enter Username")

    # Input for API Key
    api_key = st.text_input("Enter API Key", type="password")

    # Button to submit API key
    if st.button("Submit Details"):
        if not username:
            st.error("Username cannot be empty.")
        else:
            # Simulate loading with a spinner and delay
            with st.spinner("Saving details..."):
                time.sleep(2)  # Adding a 2-second delay before saving the details

                # Save the API key and username to the config file
                config_data = {
                    "GROQ_API_KEY": api_key,
                    "USERNAME": username
                }
                try:
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f)
                except Exception as e:
                    st.error(f"Failed to register API Key and Username: {e}")

    # Add a line separator
    st.markdown("---")

    # Display truncated API Key and Username in sidebar
    if "config_data" in st.session_state:
        truncated_username = truncate_text(st.session_state.config_data.get("USERNAME", ""))
        st.markdown(f"**Username:** {truncated_username}")

    # Button to start new chat
    if st.button("Start New Chat"):
        if "chat_history" in st.session_state:
            # Create and display download link for chat history
            download_link = get_chat_history_download_link(st.session_state.chat_history)
            st.markdown(download_link, unsafe_allow_html=True)

            # Save current chat history and clear current chat history
            st.session_state.previous_chat_history = st.session_state.chat_history.copy()
            st.session_state.chat_history = []

    # Display previous chat history
    if "previous_chat_history" in st.session_state and st.session_state.previous_chat_history:
        st.subheader("Previous Chat History")
        for message in st.session_state.previous_chat_history:
            role = message["role"]
            content = message["content"]
            st.markdown(f"**{role.capitalize()}:** {content}")

# Initialize Groq client with the API key
try:
    with open(config_path) as f:
        config_data = json.load(f)
except json.JSONDecodeError as e:
    st.error(f"JSON decode error: {e}")
    st.stop()
except FileNotFoundError:
    st.error("Config file not found.")
    st.stop()

GROQ_API_KEY = config_data.get("GROQ_API_KEY")
username = config_data.get("USERNAME")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in config file.")
    st.stop()

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Streamlit main content
st.title("NeX-Bot")

# Input field for user's message
user_prompt = st.chat_input("Ask NeX...")

if user_prompt and username:
    user_message = f"{username}: {user_prompt}"
    st.chat_message("user").markdown(user_message)
    st.session_state.chat_history.append({"role": "user", "content": user_message})

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        *st.session_state.chat_history
    ]

    try:
        response = client.chat.completions.create(
            model=st.session_state.selected_model,
            messages=messages
        )
        assistant_response = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": f"NeX: {assistant_response}"})

        # Display the LLM's response
        with st.chat_message("assistant"):
            st.markdown(f"NeX: {assistant_response}")
    except Exception as e:
        st.error(f"An error occurred while getting a response: {e}")
