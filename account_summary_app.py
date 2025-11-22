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

st.set_page_config(page_title="📋 Account Summary", layout="wide")

st.title("📋 Account 360° Summary")
st.markdown("**Comprehensive Account Overview with No Hallucination**")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "account_data" not in st.session_state:
    st.session_state.account_data = None
if "summary_result" not in st.session_state:
    st.session_state.summary_result = None

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This tool creates a comprehensive account summary including:
    - **Account health snapshot**
    - **Key metrics & trends**
    - **Relationship status**
    - **Business context**
    - **Action items & next steps**
    """)
    
    st.header("📋 Use Cases")
    st.markdown("""
    - QBR preparation
    - Executive briefings
    - Account handoffs
    - Quarterly reviews
    - Strategic planning
    """)
    
    st.markdown("---")
    st.header("🎨 Summary Format")
    summary_format = st.selectbox(
        "Choose format:",
        ["Executive Summary", "Detailed Report", "Quick Brief", "QBR Format"]
    )

# Account Information Section
st.header("🏢 Account Information")
col1, col2, col3 = st.columns(3)

with col1:
    account_id = st.text_input("Account ID", "ACC-12345")
    account_name = st.text_input("Account Name", "Acme Corporation")
    industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Other"])

with col2:
    contract_start_date = st.date_input("Contract Start Date")
    contract_end_date = st.date_input("Contract Renewal Date")
    days_to_renewal = (contract_end_date - datetime.now().date()).days

with col3:
    current_arr = st.number_input("Current ARR ($)", min_value=0, value=100000, step=1000)
    account_tier = st.selectbox("Account Tier", ["Enterprise", "Mid-Market", "SMB", "Strategic"])
    customer_since_months = st.number_input("Customer Since (months)", min_value=0, value=12)

# Business Context
st.header("💼 Business Context")
col4, col5 = st.columns(2)

with col4:
    primary_use_case = st.text_input("Primary Use Case", "Team collaboration and project management")
    business_goals = st.text_area("Customer's Business Goals", placeholder="e.g., Increase team productivity by 30%, Reduce project delays")

with col5:
    competitive_products = st.text_input("Known Competitors They Use", "")
    decision_makers = st.text_area("Key Decision Makers", placeholder="e.g., CTO: John Smith, VP Ops: Jane Doe")

# Usage & Engagement Metrics
st.header("📊 Usage & Engagement")
col6, col7, col8 = st.columns(3)

with col6:
    active_users = st.number_input("Active Users (MAU)", min_value=0, value=85)
    licensed_seats = st.number_input("Licensed Seats", min_value=1, value=100)
    login_frequency = st.slider("Avg Logins per User/Week", 0, 50, 8)

with col7:
    feature_usage_breadth = st.slider("Feature Usage Breadth (%)", 0, 100, 65)
    api_calls_30d = st.number_input("API Calls (Last 30d)", min_value=0, value=5000)
    integrations_active = st.number_input("Active Integrations", min_value=0, value=3)

with col8:
    training_completed = st.slider("Training Completion (%)", 0, 100, 70)
    documentation_views_30d = st.number_input("Doc Views (Last 30d)", min_value=0, value=150)
    community_engagement = st.slider("Community Engagement (0-10)", 0, 10, 5)

# Health & Sentiment
st.header("❤️ Health & Sentiment")
col9, col10, col11 = st.columns(3)

with col9:
    nps_score = st.slider("Latest NPS Score", -100, 100, 45)
    csat_score = st.slider("Latest CSAT Score", 1, 5, 4)
    health_score = st.slider("Overall Health Score", 0, 100, 75)

with col10:
    support_tickets_30d = st.number_input("Support Tickets (Last 30d)", min_value=0, value=3)
    critical_issues_open = st.number_input("Critical Issues Open", min_value=0, value=0)
    avg_response_time_hours = st.number_input("Avg Response Time (hours)", min_value=0.0, value=2.5, step=0.5)

with col11:
    executive_engagement_score = st.slider("Executive Engagement (0-10)", 0, 10, 7)
    last_qbr_days_ago = st.number_input("Days Since Last QBR", min_value=0, value=60)
    champion_count = st.number_input("Active Champions", min_value=0, value=2)

# Financial & Growth
st.header("💰 Financial & Growth")
col12, col13, col14 = st.columns(3)

with col12:
    arr_growth_yoy = st.number_input("ARR Growth YoY (%)", min_value=-100.0, max_value=500.0, value=15.0, step=5.0)
    payment_status = st.selectbox("Payment Status", ["Current", "1-30 Days Overdue", "30+ Days Overdue"])
    lifetime_value = st.number_input("Lifetime Value ($)", min_value=0, value=250000, step=5000)

with col13:
    upsell_potential = st.selectbox("Upsell Potential", ["Very High", "High", "Medium", "Low"])
    churn_risk = st.selectbox("Churn Risk", ["Low", "Medium", "High", "Critical"])
    expansion_conversations = st.number_input("Active Expansion Conversations", min_value=0, value=1)

with col14:
    cross_sell_products = st.multiselect("Cross-sell Opportunities", 
        ["Premium Features", "Additional Modules", "Enterprise Support", "Training Services", "Professional Services"])
    budget_cycle = st.selectbox("Budget Cycle Status", ["Post-Budget (Locked)", "Mid-Cycle", "Pre-Budget (Planning)", "Unknown"])

# Relationship & Engagement History
st.header("🤝 Relationship & Recent Activity")
col15, col16 = st.columns(2)

with col15:
    recent_meetings = st.text_area("Recent Meetings/Calls", 
        placeholder="e.g., QBR on 2024-10-15 with CTO - discussed roadmap\nCheck-in call on 2024-11-01 - training questions")
    key_wins = st.text_area("Key Wins & Successes", 
        placeholder="e.g., Successfully launched to entire sales team\nReduced project delivery time by 25%")

with col16:
    concerns_risks = st.text_area("Known Concerns/Risks", 
        placeholder="e.g., Budget constraints for next year\nChange in leadership - new CTO coming in Q1")
    upcoming_milestones = st.text_area("Upcoming Milestones", 
        placeholder="e.g., Renewal conversation in 45 days\nExecutive sponsor quarterly meeting in 2 weeks")

# Additional Context
additional_notes = st.text_area(
    "Additional Context (Optional)", 
    placeholder="Any other relevant information about this account..."
)

if st.button("📝 Generate Account Summary", type="primary"):
    # Create structured data object
    account_data = {
        "account_info": {
            "account_id": account_id,
            "account_name": account_name,
            "industry": industry,
            "account_tier": account_tier,
            "customer_since_months": customer_since_months,
            "days_to_renewal": days_to_renewal,
            "current_arr": current_arr
        },
        "business_context": {
            "primary_use_case": primary_use_case,
            "business_goals": business_goals,
            "competitive_products": competitive_products,
            "decision_makers": decision_makers
        },
        "usage_engagement": {
            "active_users": active_users,
            "licensed_seats": licensed_seats,
            "utilization_rate": round((active_users / licensed_seats * 100), 1) if licensed_seats > 0 else 0,
            "login_frequency": login_frequency,
            "feature_usage_breadth_percent": feature_usage_breadth,
            "api_calls_30d": api_calls_30d,
            "integrations_active": integrations_active,
            "training_completed_percent": training_completed,
            "documentation_views_30d": documentation_views_30d,
            "community_engagement": community_engagement
        },
        "health_sentiment": {
            "nps_score": nps_score,
            "csat_score": csat_score,
            "health_score": health_score,
            "support_tickets_30d": support_tickets_30d,
            "critical_issues_open": critical_issues_open,
            "avg_response_time_hours": avg_response_time_hours,
            "executive_engagement_score": executive_engagement_score,
            "last_qbr_days_ago": last_qbr_days_ago,
            "champion_count": champion_count
        },
        "financial_growth": {
            "arr_growth_yoy_percent": arr_growth_yoy,
            "payment_status": payment_status,
            "lifetime_value": lifetime_value,
            "upsell_potential": upsell_potential,
            "churn_risk": churn_risk,
            "expansion_conversations": expansion_conversations,
            "cross_sell_products": cross_sell_products,
            "budget_cycle": budget_cycle
        },
        "relationship": {
            "recent_meetings": recent_meetings,
            "key_wins": key_wins,
            "concerns_risks": concerns_risks,
            "upcoming_milestones": upcoming_milestones
        },
        "additional_notes": additional_notes if additional_notes else None,
        "summary_format": summary_format
    }
    
    # Create summary prompt based on format
    if summary_format == "Executive Summary":
        format_instructions = "Create a concise executive summary (300-400 words) suitable for leadership review. Focus on high-level insights, key risks, and strategic recommendations."
    elif summary_format == "Detailed Report":
        format_instructions = "Create a comprehensive detailed report with sections for all major aspects of the account. Include specific metrics, trends, and detailed recommendations."
    elif summary_format == "Quick Brief":
        format_instructions = "Create a brief summary (150-200 words) highlighting the most critical information for a quick account review before a call."
    else:  # QBR Format
        format_instructions = "Create a QBR-style summary organized by: Business Review, Product Usage, Success Metrics, Challenges, and Next Steps. Suitable for quarterly business review meetings."

    context_prompt = f"""
You are an expert Account Manager assistant creating account summaries.

Your job:
- Synthesize the provided account data into a clear, actionable summary
- Highlight key insights, trends, and patterns
- Identify risks and opportunities
- Provide specific next steps and recommendations
- Use ONLY the data provided - never invent information
- Be clear about any data gaps

FORMAT REQUESTED: {summary_format}
{format_instructions}

REQUIRED SUMMARY STRUCTURE:

1. **Account Overview** (2-3 sentences about who they are and what they do with us)

2. **Current Status** (health, engagement, sentiment in bullet points)

3. **Key Metrics Snapshot**
   - ARR & Growth
   - Usage & Adoption  
   - Health & Sentiment

4. **Notable Highlights** (Positive signals and wins)

5. **Concerns & Risks** (Issues that need attention)

6. **Opportunities** (Upsell, expansion, or optimization opportunities)

7. **Recommended Actions** (Specific next steps with priorities)

8. **Upcoming Important Dates** (Renewal, QBRs, milestones)

CONSTRAINTS:
- Base everything on the provided data
- If data is missing, note it as "Data not available"
- Do NOT make assumptions or create fictional details
- Be specific and cite actual numbers from the data
- Keep language professional but conversational
"""

    prompt = f"""
Create an account summary for the following customer using the guidelines above.

Account Data:
{json.dumps(account_data, indent=2)}

Generate a {summary_format} that helps the account team understand this customer's current state and take appropriate action.
"""

    with st.spinner("📝 Generating comprehensive account summary..."):
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
                temperature=0.0
            )
            
            output = response.choices[0].message.content
            
            # Store in session state
            st.session_state.account_data = account_data
            st.session_state.summary_result = output
            st.session_state.messages = []
            
            # Display results
            st.success("✅ Account Summary Generated")
            
            # Quick metrics at the top
            st.markdown("---")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("Health Score", f"{health_score}/100", 
                         delta=None, delta_color="normal")
            with metric_col2:
                utilization = round((active_users / licensed_seats * 100), 1) if licensed_seats > 0 else 0
                st.metric("Utilization", f"{utilization}%")
            with metric_col3:
                st.metric("ARR", f"${current_arr:,}", 
                         delta=f"{arr_growth_yoy:+.1f}% YoY" if arr_growth_yoy != 0 else None)
            with metric_col4:
                st.metric("Days to Renewal", days_to_renewal,
                         delta="Urgent" if days_to_renewal < 30 else None,
                         delta_color="inverse")
            
            # Display the summary
            st.markdown("---")
            st.markdown("### 📋 Account Summary")
            st.markdown(output)
            
            # Show input data for transparency
            with st.expander("📊 View All Account Data"):
                st.json(account_data)
            
            # Timestamp
            st.markdown("---")
            st.caption(f"Summary generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Download options
            col_dl1, col_dl2 = st.columns(2)
            
            report = f"""ACCOUNT SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Format: {summary_format}
Account: {account_name} ({account_id})

=======================================================================

{output}

=======================================================================

COMPLETE ACCOUNT DATA:
{json.dumps(account_data, indent=2)}
"""
            
            with col_dl1:
                st.download_button(
                    label="📥 Download Summary (TXT)",
                    data=report,
                    file_name=f"account_summary_{account_id}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
            
            with col_dl2:
                st.download_button(
                    label="📥 Download Data (JSON)",
                    data=json.dumps(account_data, indent=2),
                    file_name=f"account_data_{account_id}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Chatbot for account questions
if st.session_state.summary_result is not None:
    st.markdown("---")
    st.markdown("## 💬 Ask Questions About This Account")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if user_question := st.chat_input("e.g., 'What should I prepare for the next QBR?', 'What are the biggest risks?'"):
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        with st.chat_message("user"):
            st.markdown(user_question)
        
        context = f"""You are an account management assistant helping with customer strategy.

**STRICT RULES:**
1. Answer ONLY based on the account data and summary provided
2. Do NOT make up information
3. Be specific and actionable
4. Focus on helping manage the account successfully

**ACCOUNT DATA:**
{json.dumps(st.session_state.account_data, indent=2)}

**ACCOUNT SUMMARY:**
{st.session_state.summary_result}

**QUESTION:**
{user_question}

Provide a helpful, data-driven answer.
"""
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chat_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a helpful account management assistant. You only use provided data and never hallucinate."},
                            {"role": "user", "content": context}
                        ],
                        temperature=0.0
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
📋 360° Account View | 📊 Data-Driven | 🚫 No Bias | ✅ No Hallucination
</small>
</div>
""", unsafe_allow_html=True)