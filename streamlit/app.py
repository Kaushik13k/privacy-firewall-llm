import json
import time
import requests
import streamlit as st

st.set_page_config(page_title="AI Privacy Firewall Dashboard", layout="wide")

st.title("🌐 AI Privacy Firewall Dashboard")

st.markdown("""
This dashboard demonstrates a basic implementation of Personally Identifiable Information (PII) protection.  
It processes input text, detects PII, scores the associated risk, and returns a sanitized version.
""")

input_text = st.text_area(
    "Enter text for analysis:",
    height=200,
    max_chars=1000,
    key="input_text",
    help="Enter any text for analysis here.",
    placeholder="Type or paste text here..."
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(time.time())

with st.container():
    submit_button = st.button('Submit', use_container_width=True)

if submit_button:
    url = "http://0.0.0.0:8000/v1/ask"
    payload = json.dumps({"message": input_text})
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        result = response.json()

        with st.expander("🔍 Original Input", expanded=True):
            st.write(input_text)


        with st.expander("🔍 Output after PII format", expanded=True):
            st.write(result.get("redacted_prompt",
                     "No redacted prompt available."))

        with st.expander("📊 Step-by-Step Processing", expanded=True):
            pii_status = "No PII Detected"
            if "pii" in result:
                pii_status = f"🔴 **PII Detected**: {result['pii']}"

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            st.write(f"**PII Detection**: {pii_status}")

            risk_score = result.get("risk_score", 0)
            st.write(f"**Risk Score**: {risk_score}/100")

        with st.expander("🧹 Sanitized Output", expanded=True):
            st.write(result.get("response", "No sanitized response available."))

        st.write(f"**Session ID**: {st.session_state.session_id}")

    else:
        st.error("❌ Error processing the input. Please try again.")

st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; font-size: 16px; color: #555;">
        <p>Built with ❤️. Privacy First.</p>
    </div>
""", unsafe_allow_html=True)
