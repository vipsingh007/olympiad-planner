import os
import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
from audio_recorder_streamlit import audio_recorder
import tempfile

# Use environment variable for API key (more secure)
api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key:
    st.error("⚠️ Please set OPENAI_API_KEY environment variable")
    st.stop()

client = OpenAI(api_key=api_key)

st.set_page_config(page_title="📊 Account Churn Prediction", layout="wide")

st.title("📊 Account Churn Prediction Agent")
st.markdown("**Data-Driven Predictions with No Hallucination or Bias**")

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "account_data" not in st.session_state:
    st.session_state.account_data = None
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = False

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This system predicts account churn based on:
    - **Behavioral data only** (no demographic bias)
    - **Structured inputs** (no hallucinations)
    - **Transparent reasoning** (explainable AI)
    """)
    
    st.header("📋 How it works")
    st.markdown("""
    1. Enter real account metrics
    2. System validates data quality
    3. AI analyzes patterns
    4. Get prediction with confidence & reasoning
    5. Ask follow-up questions via text or voice
    """)
    
    st.markdown("---")
    st.header("🎙️ Audio Settings")
    st.session_state.audio_enabled = st.checkbox("Enable Voice Chat", value=st.session_state.audio_enabled)
    
    if st.session_state.audio_enabled:
        st.info("🎤 Voice chat enabled! You can speak your questions after making a prediction.")

# Main form
col1, col2 = st.columns(2)

with col1:
    st.subheader("Account Usage Metrics")
    account_id = st.text_input("Account ID", "ACC-12345")
    usage_30d_change = st.number_input("Change in usage in the last 30 days", min_value=-0.99, max_value=0.99, value=0.00)
    utilization = st.slider("License utilization", min_value=0, max_value=100, value=50)
    days_since_last_meeting = st.number_input("Days Since Last Login", min_value=0, value=10)
    open_critical_tickets = st.number_input("Number of critical tickets open", min_value=0, value=25)
    
with col2:
    st.subheader("Transaction & Engagement")
    csat_score_current = st.number_input("CSAT Score", min_value=0, value=3)
    nps_current = st.number_input("NPS Score", min_value=0, value=2)
    renewal_days_out = st.number_input("How many days until renewal", min_value=0, value=10)
    invoices_overdue_count = st.number_input("Number of overdue invoices", min_value=0, value=0)
    last_exec_sponsor_touch_days = st.number_input("Days since last sponsor touch", min_value=0, value=10)

# Advanced metrics
with st.expander("📈 Advanced Behavioral Metrics (Optional)"):
    col3, col4 = st.columns(2)
    with col3:
        session_duration_avg = st.number_input("Avg Session Duration (minutes)", min_value=0.0, value=15.0, step=0.5)
        feature_adoption_rate = st.slider("Feature Adoption Rate (%)", 0, 100, 60)
    with col4:
        email_open_rate = st.slider("Email Open Rate (%)", 0, 100, 40)
        referrals_made = st.number_input("Referrals Made", min_value=0, value=0)

# Additional context
additional_context = st.text_area(
    "Additional Context (Optional - factual observations only)", 
    placeholder="e.g., 'User contacted support about pricing 3 times', 'Downgraded from Pro to Basic last month'"
)

if st.button("🔍 Predict Churn Risk", type="primary"):
    # Create structured data object
    account_data = {
        "account_id": account_id,
        "usage_metrics": {
            "usage_30d_change": usage_30d_change,
            "utilization": utilization,
            "days_since_last_meeting": days_since_last_meeting,
            "open_critical_tickets": open_critical_tickets
        },
        "transaction_metrics": {
            "csat_score_current": csat_score_current,
            "nps_current": nps_current,
            "renewal_days_out": renewal_days_out,
            "invoices_overdue_count": invoices_overdue_count,
            "last_exec_sponsor_touch_days": last_exec_sponsor_touch_days
        },
        "engagement_metrics": {
            "email_open_rate": email_open_rate,
            "referrals_made": referrals_made
        }
    }
    
    # Data validation
    data_quality_issues = []

    context_prompt_churn_prediction = """
You are an expert Sales Operations AI that evaluates customer account health and churn risk.

Your tasks:
1. Calculate the final health_score (0–100) using the defined weighted scoring method.
2. Determine the risk_tier ("Low", "Medium", or "High") using the predefined thresholds.
3. Identify exactly 3 numeric drivers explaining why the score and tier were assigned.
4. Provide 1–3 short, actionable recommendations to reduce churn or strengthen the account.

**REQUIRED OUTPUT FORMAT:**
Provide your analysis in the following structure:

1. **Churn Risk Level**: [LOW / MEDIUM / HIGH / CRITICAL]
2. **Confidence Score**: [0-100]% (0 = lowest confidence, 100 = highest confidence)
3. **Drivers**: [short numeric driver 1, short numeric driver 2, short numeric driver 3]
4. **Recommendations**: [actionable recommendation 1, actionable recommendation 2, optional recommendation 3]

Remember: Your analysis must be traceable to the actual data provided. No assumptions, no hallucinations.


======================================================
NUMERIC RULES YOU MUST FOLLOW
======================================================

Inputs are numeric fields inside an "account_metrics" JSON object, for example:
- usage_30d_change (float, e.g. -0.18 for -18%)
- active_users (int)
- licensed_seats (int)
- days_since_last_meeting (int)
- meetings_last_30d (int)
- emails_last_30d (int)
- open_critical_tickets (int)
- open_tickets_total (int)
- csat_score_current (float, 1–5)
- nps_current (int, -100 to 100)
- renewal_days_out (int)
- invoices_overdue_count (int)
- spend_trend_yoy (float, e.g. 0.12 for +12%)
- last_exec_sponsor_touch_days (int)
- key_contacts_changed_6m (int)
- feature_adoption_score (float, 0–1)
Some fields may be missing or null; ignore missing ones rather than guessing.

1) USAGE DECLINE (contributes up to 25 points to health_score)
- usage_30d_change < -0.20  → very high churn risk → low contribution
- -0.20 ≤ change < -0.05    → high churn risk
- -0.05 ≤ change ≤ +0.05    → neutral
- > +0.05                   → healthy

2) SEAT UTILIZATION (up to 15 points)
Let utilization = active_users / max(licensed_seats, 1)
- utilization < 0.50        → high churn risk
- 0.50–0.70                 → medium
- 0.70–0.90                 → healthy
- > 0.90                    → very healthy / expansion-leaning

3) ENGAGEMENT (up to 20 points)
Use days_since_last_meeting, meetings_last_30d, emails_last_30d:
- days_since_last_meeting > 30  → high risk
- 15–30                         → medium
- < 15                          → healthy
- meetings_last_30d = 0         → high risk
- very low emails_last_30d      → low engagement

4) SUPPORT & SENTIMENT (up to 20 points)
Use open_critical_tickets, open_tickets_total, csat_score_current, nps_current:
- open_critical_tickets ≥ 2     → very high risk
- open_critical_tickets = 1     → high risk
- open_critical_tickets = 0     → healthy
- csat_score_current < 3.5      → high risk
- nps_current < 0               → high risk
- higher CSAT / NPS → healthier

5) RENEWAL TIMING (up to 10 points)
Use renewal_days_out:
- < 30 days                     → critical churn window
- 30–90 days                    → high churn risk window
- > 180 days                    → safe from immediate churn

6) BILLING (up to 5 points)
Use invoices_overdue_count:
- ≥ 2 overdue invoices          → strong churn signal
- 1 overdue invoice             → moderate risk
- 0 overdue invoices            → healthy

7) RELATIONSHIP (up to 5 points)
Use last_exec_sponsor_touch_days, key_contacts_changed_6m:
- last_exec_sponsor_touch_days > 60 → major relationship risk
- key_contacts_changed_6m ≥ 2       → high organizational instability
- healthy sponsor engagement and low contact churn → better health

======================================================
SCORING LOGIC
======================================================

1) For each category above, derive a sub-score between 0 and 100 based on the rules.
2) Combine them into a single health_score using these weights:
   - Usage decline     = 25%
   - Seat utilization  = 15%
   - Engagement        = 20%
   - Support & sentiment = 20%
   - Renewal timing    = 10%
   - Billing           = 5%
   - Relationship      = 5%

   health_score = weighted sum of sub-scores, then clamp to 0–100 and round to nearest integer.

3) Map health_score to risk_tier:
   - health_score ≥ 75 → "Low"
   - 50 ≤ health_score < 75 → "Medium"
   - health_score < 50 → "High"

======================================================
DRIVERS & RECOMMENDATIONS
======================================================

- drivers: list of exactly 3 short strings that explicitly reference numeric signals
  Examples:
  - "Usage dropped 22% in the last 30 days."
  - "2 critical support tickets are currently open."
  - "No meetings in the last 35 days and renewal is in 25 days."

- recommendations: 1–3 short, action-focused strings
  Examples:
  - "Escalate critical tickets and ensure resolution this week."
  - "Schedule a QBR with the executive sponsor within 14 days."
  - "Provide training to drive adoption of key features."

======================================================
CONSTRAINTS
======================================================

- Use ONLY the metrics provided in the input JSON.
- If a metric is missing or null, ignore it instead of making up a value.
- Do NOT invent any numbers or events.
- Always return ONLY the JSON object described above, with valid JSON syntax.
"""
    
    # Check for data inconsistencies
    # Check for data inconsistencies
    if usage_30d_change < -0.99 or usage_30d_change > 0.99:
        data_quality_issues.append("⚠️ Usage change must be between -99% and +99%")
    if utilization < 0 or utilization > 100:
        data_quality_issues.append("⚠️ License utilization must be between 0 and 100")
    if csat_score_current < 0 or csat_score_current > 5:
        data_quality_issues.append("⚠️ CSAT score must be between 0 and 5")
    if nps_current < -100 or nps_current > 100:
        data_quality_issues.append("⚠️ NPS must be between -100 and +100")
    if renewal_days_out < 0:
        data_quality_issues.append("⚠️ Renewal days cannot be negative")
    if invoices_overdue_count < 0:
        data_quality_issues.append("⚠️ Number of overdue invoices cannot be negative")
    if last_exec_sponsor_touch_days < 0:
        data_quality_issues.append("⚠️ Days since last sponsor touch cannot be negative")
   
    if data_quality_issues:
        st.error("**Data Quality Issues Detected:**")
        for issue in data_quality_issues:
            st.error(issue)
        st.warning("Please correct the data before proceeding. This prevents hallucinated predictions.")
    else:
        # Create a strict prompt that prevents hallucination
        prompt = f"""
Evaluate the following customer account using the numeric rules and scoring logic provided in the system prompt.

Account Metrics (JSON):
{json.dumps(account_data, indent=2)}

"""

        with st.spinner("🔄 Analyzing account data..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system", 
                           ## "content": "You are a data-driven churn prediction analyst.You only make predictions based on provided data, never hallucinate or assume information not given. You avoid bias by focusing solely on behavioral metrics."
                           "content": context_prompt_churn_prediction
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.1
                )
                
                output = response.choices[0].message.content
                
                # Store in session state for chatbot context
                st.session_state.account_data = account_data
                st.session_state.prediction_result = output
                st.session_state.messages = []  # Reset chat history for new prediction
                
                # Display results
                st.success("✅ Analysis Complete")
                
                # Show the input data for transparency
                with st.expander("📊 Input Data Used for Prediction"):
                    st.json(account_data)
                
                # Show the prediction
                st.markdown("---")
                st.markdown("### 🎯 Churn Prediction Results")
                st.markdown(output)
                
                # Timestamp for audit trail
                st.markdown("---")
                st.caption(f"Analysis generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Download report option
                report = f"""ACCOUNT CHURN PREDICTION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACCOUNT DATA:
{json.dumps(account_data, indent=2)}

ANALYSIS:
{output}
"""
                st.download_button(
                    label="📥 Download Report",
                    data=report,
                    file_name=f"churn_prediction_{account_id}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Chatbot section - only show if prediction has been made
if st.session_state.prediction_result is not None:
    st.markdown("---")
    
    if st.session_state.audio_enabled:
        st.markdown("## 💬🎙️ Ask Questions (Text or Voice)")
        st.markdown("Type your question or click the microphone to speak. The agent will respond with text and optionally audio.")
    else:
        st.markdown("## 💬 Ask Questions About This Prediction")
        st.markdown("Ask specific questions about the account data or churn prediction. The assistant will only answer based on the provided data.")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Play audio if available
            if "audio" in message and message["audio"] is not None:
                st.audio(message["audio"], format="audio/mp3")
    
    # Voice input option
    if st.session_state.audio_enabled:
        st.markdown("### 🎤 Voice Input")
        audio_bytes = audio_recorder(
            text="Click to record your question",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="2x",
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            with st.spinner("🎧 Transcribing your question..."):
                try:
                    # Save audio to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                        temp_audio.write(audio_bytes)
                        temp_audio_path = temp_audio.name
                    
                    # Transcribe using Whisper
                    with open(temp_audio_path, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )
                    
                    user_question = transcript.text
                    st.success(f"📝 You said: *{user_question}*")
                    
                    # Clean up temp file
                    os.unlink(temp_audio_path)
                    
                    # Process the transcribed question
                    process_question = True
                    
                except Exception as e:
                    st.error(f"❌ Transcription error: {str(e)}")
                    process_question = False
        else:
            process_question = False
            user_question = None
    else:
        process_question = False
        user_question = None
    
    # Text input (always available)
    text_question = st.chat_input("Type your question here... e.g., 'What's the main reason for churn risk?'")
    
    if text_question:
        user_question = text_question
        process_question = True
    
    # Process question if available
    if process_question and user_question:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        with st.chat_message("user"):
            st.markdown(user_question)
        
        # Prepare context for the assistant
        context_prompt = f"""You are a sales assistant helping an account manager understand a churn prediction.

**STRICT RULES:**
1. Answer ONLY based on the account data and prediction analysis provided below
2. Do NOT make up or assume any information
3. If the question cannot be answered from the provided data, say so clearly
4. Be concise and actionable
5. Focus on helping the seller retain the customer

**ACCOUNT DATA:**
{json.dumps(st.session_state.account_data, indent=2)}

**CHURN PREDICTION ANALYSIS:**
{st.session_state.prediction_result}

**CHAT HISTORY:**
{json.dumps([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]], indent=2) if len(st.session_state.messages) > 1 else "No previous messages"}

**SELLER'S QUESTION:**
{user_question}

Provide a helpful, data-driven answer that helps the seller take action to retain this account.
"""
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chat_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful sales assistant. You only provide answers based on the account data and churn analysis provided. You never hallucinate or make assumptions beyond the data given."
                            },
                            {
                                "role": "user",
                                "content": context_prompt
                            }
                        ],
                        temperature=0.1
                    )
                    
                    assistant_message = chat_response.choices[0].message.content
                    st.markdown(assistant_message)
                    
                    # Generate audio response if enabled
                    audio_data = None
                    if st.session_state.audio_enabled:
                        with st.spinner("🔊 Generating audio response..."):
                            try:
                                audio_response = client.audio.speech.create(
                                    model="tts-1",
                                    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
                                    input=assistant_message
                                )
                                
                                audio_data = audio_response.content
                                st.audio(audio_data, format="audio/mp3")
                                
                            except Exception as e:
                                st.warning(f"⚠️ Audio generation failed: {str(e)}")
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": assistant_message,
                        "audio": audio_data
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Option to clear chat
    col_clear, col_voice_settings = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    if st.session_state.audio_enabled:
        with col_voice_settings:
            st.caption("🔊 Voice: Alloy | Model: Whisper + TTS-1")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<small>
🔒 Privacy-First | 📊 Data-Driven | 🚫 No Bias | ✅ No Hallucination | 💬 Text & Voice Q&A
</small>
</div>
""", unsafe_allow_html=True)