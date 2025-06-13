
import streamlit as st
import os
import json
from dotenv import load_dotenv, set_key

from api_openai import ask_openai
from api_anthropic import ask_anthropic
from api_mistral import ask_mistral
from api_local import ask_local

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.json")
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

def require_api_keys():
    load_dotenv(ENV_PATH)
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    mistral_key = os.getenv("MISTRAL_API_KEY")
    missing = not openai_key
    if missing or st.session_state.get("api_form", False):
        st.session_state["api_form"] = True
        st.title("🔑 Enter your API Keys")
        st.write("You must enter your OpenAI API key to use the comparator. Anthropic and Mistral are optional.")
        with st.form("api_keys"):
            new_openai = st.text_input("OpenAI API Key (required)", type="password", value=openai_key or "")
            new_anthropic = st.text_input("Anthropic API Key (optional)", type="password", value=anthropic_key or "")
            new_mistral = st.text_input("Mistral API Key (optional)", type="password", value=mistral_key or "")
            submit = st.form_submit_button("Save and continue")
        if submit:
            set_key(ENV_PATH, "OPENAI_API_KEY", new_openai)
            set_key(ENV_PATH, "ANTHROPIC_API_KEY", new_anthropic)
            set_key(ENV_PATH, "MISTRAL_API_KEY", new_mistral)
            st.success("API keys saved! Please rerun the app if required.")
            st.session_state["api_form"] = False
            st.experimental_rerun()
        st.stop()

require_api_keys()
load_dotenv(ENV_PATH)

MODEL_APIS = {
    "GPT-3.5-turbo (OpenAI)": lambda prompt: ask_openai(prompt, "gpt-3.5-turbo"),
    "GPT-4o (OpenAI)": lambda prompt: ask_openai(prompt, "gpt-4o"),
    "Claude 3 Opus (Anthropic)": lambda prompt: ask_anthropic(prompt, "claude-3-opus-20240229"),
    "Mistral-small-latest (Mistral)": lambda prompt: ask_mistral(prompt, "mistral-small-latest"),
    "Local endpoint (example)": lambda prompt: ask_local(prompt),
}

st.set_page_config(page_title="AI Prompt Comparator", layout="wide")
st.title("🤖 AI Prompt Comparator")
st.write("Compare responses from different AI models/APIs side by side.")

prompt = st.text_area("Prompt:", height=120)
selected_models = st.multiselect(
    "Choose models to compare:",
    list(MODEL_APIS.keys()),
    default=["GPT-3.5-turbo (OpenAI)", "GPT-4o (OpenAI)"]
)

responses = {}
if st.button("Compare responses!", type="primary"):
    if not prompt.strip() or not selected_models:
        st.warning("Enter a prompt and select at least one model.")
    else:
        with st.spinner("Querying models..."):
            for model in selected_models:
                try:
                    response = MODEL_APIS[model](prompt)
                except Exception as e:
                    response = f"❌ Error: {e}"
                responses[model] = response
        st.session_state["last_prompt"] = prompt
        st.session_state["last_responses"] = responses

if "last_responses" in st.session_state:
    st.subheader("Results:")
    cols = st.columns(len(st.session_state["last_responses"]))
    for i, (model, resp) in enumerate(st.session_state["last_responses"].items()):
        with cols[i]:
            st.markdown(f"**{model}**")
            st.code(resp)

    if st.button("Save to history"):
        history = []
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.insert(0, {
            "prompt": st.session_state["last_prompt"],
            "responses": st.session_state["last_responses"]
        })
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        st.success("Saved to history!")

st.header("🕑 Comparison History")
if os.path.exists(HISTORY_PATH):
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

search = st.text_input("Search history:")
filtered = [
    h for h in history
    if search.lower() in h["prompt"].lower() or any(search.lower() in r.lower() for r in h["responses"].values())
] if search else history

for i, item in enumerate(filtered):
    with st.expander(f"{i+1}. {item['prompt'][:60]}..."):
        st.markdown(f"**Prompt:**

{item['prompt']}")
        cols = st.columns(len(item["responses"]))
        for j, (model, resp) in enumerate(item["responses"].items()):
            with cols[j]:
                st.markdown(f"**{model}**")
                st.code(resp)
if st.button("Clear history"):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        f.write("[]")
    st.success("History cleared.")
