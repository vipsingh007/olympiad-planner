import os
import streamlit as st
from openai import OpenAI
import json
from datetime import datetime

# Use environment variable for API key (more secure)
api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key:
    st.error("⚠️ Please set OPENAI_API_KEY environment variable")
    st.stop()

client = OpenAI(api_key=api_key)

st.set_page_config(page_title="📈 Upsell Opportunity Analyzer", layout="wide")

st.title("📈 Upsell Opportunity Analyzer")
st.markdown("**Data-Driven Expansion Signals with No Hallucination or Bias**")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "account_data" not in st.session_state:
    st.session_state.account_data = None
if "upsell_result" not in st.session_state:
    st.session_state.upsell_result = None

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This system identifies upsell opportunities based on:
    - **Behavioral signals** (usage, engagement, growth)
    - **Structured inputs** (no hallucinations)
    - **Transparent reasoning** (explainable AI)
    - **Data-driven recommendations** (no bias)
    """)
    
    st.header("📋 Upsell Signals")
    st.markdown("""
    **Expansion indicators:**
    - High product utilization
    - Growing usage trends
    - Feature adoption patterns
    - Team growth signals
    - Success metrics
    """)

# Main form
col1, col2 = st.columns(2)

with col1:
    st.subheader("Usage & Growth Metrics")
    account_id = st.text_input("Account ID", "ACC-12345")
    current_arr = st.number_input("Current ARR ($)", min_value=0, value=50000, step=1000)
    usage_30d_change = st.number_input("Usage Change (Last 30 days %)", min_value=-99.0, max_value=300.0, value=15.0, step=1.0)
    utilization_rate = st.slider("License Utilization Rate (%)", 0, 100, 85)
    active_users = st.number_input("Active Users", min_value=0, value=45)
    licensed_seats = st.number_input("Licensed Seats", min_value=1, value=50)
    
with col2:
    st.subheader("Engagement & Success")
    feature_adoption_score = st.slider("Feature Adoption Score (%)", 0, 100, 70)
    nps_score = st.slider("NPS Score", -100, 100, 40)
    csat_score = st.slider("CSAT Score", 1, 5, 4)
    active_champions = st.number_input("Number of Active Champions", min_value=0, value=2)
    success_milestone_hits = st.number_input("Success Milestones Hit (Last 90d)", min_value=0, value=3)

# Advanced metrics
with st.expander("📊 Advanced Expansion Signals (Optional)"):
    col3, col4 = st.columns(2)
    with col3:
        team_size_growth = st.number_input("Team Size Growth (Last 6mo %)", min_value=-50.0, max_value=500.0, value=20.0, step=5.0)
        exec_engagement_score = st.slider("Executive Engagement Score", 0, 10, 7)
        budget_cycle_proximity = st.number_input("Days to Next Budget Cycle", min_value=0, value=45)
    with col4:
        recent_support_interactions = st.number_input("Support Interactions (Last 30d)", min_value=0, value=2)
        training_sessions_attended = st.number_input("Training Sessions Attended (Last 90d)", min_value=0, value=1)
        api_integration_depth = st.slider("API Integration Depth (0=none, 10=deep)", 0, 10, 5)

# Available upsell products
st.subheader("🎯 Available Upsell Options")
upsell_products = st.multiselect(
    "Select available products/tiers for recommendation:",
    ["Premium Tier Upgrade", "Additional Seats", "Advanced Features Package", "Enterprise Support", "API Access", "Training & Onboarding", "Custom Integration"],
    default=["Premium Tier Upgrade", "Additional Seats", "Advanced Features Package"]
)

# Additional context
additional_context = st.text_area(
    "Additional Context (Optional - factual observations only)", 
    placeholder="e.g., 'Customer asked about advanced analytics in last QBR', 'Hiring 10 new team members next quarter'"
)

if st.button("🔍 Analyze Upsell Opportunities", type="primary"):
    # Create structured data object
    account_data = {
        "account_id": account_id,
        "current_metrics": {
            "current_arr": current_arr,
            "usage_30d_change_percent": usage_30d_change,
            "utilization_rate_percent": utilization_rate,
            "active_users": active_users,
            "licensed_seats": licensed_seats
        },
        "engagement_metrics": {
            "feature_adoption_score_percent": feature_adoption_score,
            "nps_score": nps_score,
            "csat_score": csat_score,
            "active_champions": active_champions,
            "success_milestone_hits_90d": success_milestone_hits
        },
        "growth_signals": {
            "team_size_growth_6mo_percent": team_size_growth,
            "exec_engagement_score": exec_engagement_score,
            "budget_cycle_proximity_days": budget_cycle_proximity,
            "recent_support_interactions_30d": recent_support_interactions,
            "training_sessions_attended_90d": training_sessions_attended,
            "api_integration_depth": api_integration_depth
        },
        "available_upsell_products": upsell_products,
        "additional_context": additional_context if additional_context else None
    }
    
    # Data validation
    data_quality_issues = []
    
    if active_users > licensed_seats:
        data_quality_issues.append("⚠️ Active users exceed licensed seats - possible data error")
    if utilization_rate < 0 or utilization_rate > 100:
        data_quality_issues.append("⚠️ Utilization rate must be between 0-100%")
    if nps_score < -100 or nps_score > 100:
        data_quality_issues.append("⚠️ NPS must be between -100 and +100")
    if csat_score < 1 or csat_score > 5:
        data_quality_issues.append("⚠️ CSAT must be between 1 and 5")
    if current_arr < 0:
        data_quality_issues.append("⚠️ ARR cannot be negative")
    
    if data_quality_issues:
        st.error("**Data Quality Issues Detected:**")
        for issue in data_quality_issues:
            st.error(issue)
        st.warning("Please correct the data before proceeding.")
    else:
        # Create upsell analysis prompt
        context_prompt = """
You are an expert Sales Operations AI that identifies expansion and upsell opportunities.

Your job:
- Analyze account metrics to calculate an Expansion Score (0-100)
- Identify specific upsell products that match the account's usage patterns
- Provide data-driven reasoning for each recommendation
- Estimate potential expansion ARR
- Always return STRICT JSON only

REQUIRED JSON FORMAT:
{{
  "expansion_score": <int 0-100>,
  "expansion_potential": "Low" | "Medium" | "High" | "Very High",
  "recommended_products": [
    {{
      "product": "<product name>",
      "priority": "High" | "Medium" | "Low",
      "reasoning": "<data-based explanation>",
      "estimated_arr_impact": <int>
    }}
  ],
  "key_signals": ["<signal 1>", "<signal 2>", "<signal 3>"],
  "optimal_timing": "<when to approach>",
  "talk_track": "<suggested conversation starter based on data>"
}}

EXPANSION SCORE CALCULATION RULES:

1. UTILIZATION (0-30 points):
   - >90% utilization → 30 points (seats upsell opportunity)
   - 70-90% → 20 points
   - 50-70% → 10 points
   - <50% → 5 points

2. USAGE GROWTH (0-25 points):
   - >30% growth → 25 points
   - 15-30% → 20 points
   - 5-15% → 10 points
   - <5% → 5 points

3. ENGAGEMENT & SUCCESS (0-20 points):
   - High NPS (>40) + CSAT (>4) + milestones → 20 points
   - Multiple champions → additional signal
   - Feature adoption >60% → strong signal

4. GROWTH SIGNALS (0-15 points):
   - Team growth >15% → 15 points
   - High exec engagement → 10 points
   - API integration depth → technical stickiness

5. READINESS (0-10 points):
   - Budget cycle <90 days → 10 points
   - Recent training engagement → buying interest
   - Support interactions (exploratory, not issues) → positive signal

CONSTRAINTS:
- Only recommend products from the available_upsell_products list
- Base all reasoning on specific numeric metrics provided
- Do NOT make up data or assume information not given
- If data is insufficient, state that clearly
- Estimated ARR impact should be realistic based on current ARR
"""

        prompt = f"""
Analyze the following account for upsell and expansion opportunities using the rules above.

Account Data:
{json.dumps(account_data, indent=2)}

Provide your analysis as JSON following the required format. Base all recommendations strictly on the data provided.
"""

        with st.spinner("🔄 Analyzing upsell opportunities..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system", 
                            "content": context_prompt
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.2
                )
                
                output = response.choices[0].message.content
                
                # Store in session state
                st.session_state.account_data = account_data
                st.session_state.upsell_result = output
                st.session_state.messages = []
                
                # Try to parse JSON for better display
                try:
                    result_json = json.loads(output)
                    
                    st.success("✅ Analysis Complete")
                    
                    # Display key metrics
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Expansion Score", f"{result_json.get('expansion_score', 'N/A')}/100")
                    with col_b:
                        st.metric("Potential", result_json.get('expansion_potential', 'N/A'))
                    with col_c:
                        est_impact = sum([p.get('estimated_arr_impact', 0) for p in result_json.get('recommended_products', [])])
                        st.metric("Est. ARR Impact", f"${est_impact:,}")
                    
                    # Show recommendations
                    st.markdown("---")
                    st.markdown("### 🎯 Recommended Products")
                    for product in result_json.get('recommended_products', []):
                        with st.expander(f"**{product.get('product', 'Unknown')}** - Priority: {product.get('priority', 'N/A')}"):
                            st.markdown(f"**Reasoning:** {product.get('reasoning', 'N/A')}")
                            st.markdown(f"**Est. ARR Impact:** ${product.get('estimated_arr_impact', 0):,}")
                    
                    # Key signals
                    st.markdown("### 📊 Key Expansion Signals")
                    for signal in result_json.get('key_signals', []):
                        st.markdown(f"- {signal}")
                    
                    # Timing and talk track
                    st.markdown("### ⏰ Optimal Timing")
                    st.info(result_json.get('optimal_timing', 'N/A'))
                    
                    st.markdown("### 💬 Suggested Talk Track")
                    st.success(result_json.get('talk_track', 'N/A'))
                    
                except json.JSONDecodeError:
                    # Fallback to plain text
                    st.success("✅ Analysis Complete")
                    st.markdown(output)
                
                # Show input data for transparency
                with st.expander("📊 Input Data Used"):
                    st.json(account_data)
                
                # Timestamp
                st.caption(f"Analysis generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Download option
                report = f"""UPSELL OPPORTUNITY ANALYSIS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACCOUNT DATA:
{json.dumps(account_data, indent=2)}

ANALYSIS:
{output}
"""
                st.download_button(
                    label="📥 Download Report",
                    data=report,
                    file_name=f"upsell_analysis_{account_id}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Chatbot for upsell questions
if st.session_state.upsell_result is not None:
    st.markdown("---")
    st.markdown("## 💬 Ask Questions About Upsell Strategy")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if user_question := st.chat_input("e.g., 'What's the best way to approach this upsell?', 'Why this product recommendation?'"):
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        with st.chat_message("user"):
            st.markdown(user_question)
        
        context = f"""You are a sales assistant helping with upsell strategy.

**STRICT RULES:**
1. Answer ONLY based on the account data and upsell analysis provided
2. Do NOT make up information
3. Focus on helping close the expansion deal
4. Be specific and actionable

**ACCOUNT DATA:**
{json.dumps(st.session_state.account_data, indent=2)}

**UPSELL ANALYSIS:**
{st.session_state.upsell_result}

**QUESTION:**
{user_question}

Provide a helpful answer based strictly on the data.
"""
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chat_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a helpful sales assistant focused on expansion deals. You only use provided data."},
                            {"role": "user", "content": context}
                        ],
                        temperature=0.2
                    )
                    
                    assistant_message = chat_response.choices[0].message.content
                    st.markdown(assistant_message)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
<small>
📈 Expansion-Focused | 📊 Data-Driven | 🚫 No Bias | ✅ No Hallucination
</small>
</div>
""", unsafe_allow_html=True)