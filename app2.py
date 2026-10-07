import streamlit as st
from google import genai
from google.genai import types


from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE
)


# -----------------------------
# App settings
# -----------------------------

MODEL_NAME = "gemini-3.8-flash"

st.set_page_config(
    page_title="MacroSnap",
    page_icon="🥗"
)


# -----------------------------
# Get API keys
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]



# -----------------------------
# Gemini client
# -----------------------------

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# -----------------------------
# Twilio client
# -----------------------------



# -----------------------------
# Onboarding
# -----------------------------

if "onboarded" not in st.session_state:

    st.title("🥗 MacroSnap")
    st.write("Your instant calorie & macro decoder!")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input("WhatsApp number")

        submitted = st.form_submit_button("Start MacroSnap")

        if submitted:
            if not name.strip():
                st.error("Please enter your name.")

            elif not whatsapp_number.strip():
                st.error("Please enter your WhatsApp number.")

            else:
                st.session_state.name = name.strip()
                st.session_state.whatsapp_number = whatsapp_number.strip()

                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )

                st.session_state.messages = []
                st.session_state.onboarded = True

                st.rerun()

    st.stop()

# -----------------------------
# Chat functions
# -----------------------------

def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )


def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":

            st.write(message["content"])

        elif message["kind"] == "image":

            st.image(message["content"])


def ask_gemini(parts):

    import time

    for attempt in range(3):

        try:

            response = st.session_state.chat.send_message(
                parts
            )

            return response.text

        except Exception as e:

            if "503" in str(e):

                time.sleep(3)

            else:

                return f"Sorry, something went wrong: {e}"

    return "Gemini is temporarily busy. Please try again in a few seconds."


# -----------------------------
# Welcome message
# -----------------------------

if not st.session_state.messages:

    welcome = WELCOME_MESSAGE_TEMPLATE.format(
        name=st.session_state.name
    )

    add_message(
        "assistant",
        "text",
        welcome
    )


# -----------------------------
# Display previous messages
# -----------------------------

for message in st.session_state.messages:

    render_message(message)


# -----------------------------
# Chat input
# -----------------------------

user_input = st.chat_input(
    "Tell me what you ate...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


if user_input:

    photo = None
    text = ""

    if hasattr(user_input, "text"):

        text = user_input.text

    if hasattr(user_input, "files"):

        if user_input.files:

            photo = user_input.files[0]


    parts = []


    # Text input

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # Photo input

    if photo:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes
        )

        image_part = types.Part.from_bytes(
            data=photo_bytes,
            mime_type=photo.type
        )

        parts.append(image_part)


        if not text:

            parts.append(
                "What is this meal? Give me the calories and macros."
            )


    # Send to Gemini

    if parts:

        answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer
        )

        st.rerun()


