import streamlit as st
import json
from datetime import datetime, timedelta
import database as db

st.set_page_config(page_title="🏆 Olympiad Prep Planner", layout="wide", page_icon="🏆")

# Olympiad syllabus by grade and subject
SYLLABUS = {
    "Grade 3": {
        "Math": [
            "Number System (1-4 digits)", "Addition & Subtraction", "Multiplication Tables (1-12)",
            "Division Basics", "Fractions (Halves, Quarters)", "Shapes & Patterns",
            "Measurement (Length, Weight, Time)", "Money Problems", "Mental Math",
            "Word Problems", "Geometry Basics", "Data Handling (Pictographs)"
        ],
        "Science": [
            "Living & Non-Living Things", "Plants & Their Parts", "Animals & Their Habitats",
            "Human Body Parts", "Food & Nutrition", "Air & Water", "Weather & Seasons",
            "Light & Shadows", "Magnets", "Simple Machines", "Environmental Awareness",
            "Safety & First Aid"
        ],
        "English": [
            "Reading Comprehension", "Vocabulary Building", "Grammar (Nouns, Verbs, Adjectives)",
            "Sentence Formation", "Tenses (Simple)", "Punctuation", "Spellings",
            "Story Writing", "Poem Reading", "Synonyms & Antonyms", "Articles (a, an, the)",
            "Singular & Plural"
        ]
    },
    "Grade 5": {
        "Math": [
            "Large Numbers (up to 10 digits)", "Roman Numerals", "Factors & Multiples",
            "LCM & HCF", "Fractions & Decimals", "Percentages", "Ratio & Proportion",
            "Algebraic Expressions", "Geometry (Angles, Triangles)", "Perimeter & Area",
            "Volume & Capacity", "Data Handling (Bar Graphs, Pie Charts)", "Time & Speed",
            "Profit & Loss", "Simple Interest", "Logical Reasoning"
        ],
        "Science": [
            "Cell Structure", "Plant & Animal Systems", "Food & Digestion",
            "Respiration & Circulation", "Reproduction in Plants", "Force, Work & Energy",
            "Simple Machines", "Light & Reflection", "Sound", "Heat & Temperature",
            "Electricity & Circuits", "Magnets & Magnetism", "Earth & Solar System",
            "Water Cycle", "Air & Atmosphere", "Environmental Science"
        ],
        "English": [
            "Advanced Reading Comprehension", "Vocabulary (Prefixes, Suffixes)",
            "Parts of Speech (All)", "Tenses (All)", "Active & Passive Voice",
            "Direct & Indirect Speech", "Clauses & Phrases", "Essay Writing",
            "Letter Writing", "Idioms & Proverbs", "Homophones & Homonyms",
            "Figures of Speech", "Poetry Analysis", "Grammar Application"
        ]
    }
}

# Study time recommendations
STUDY_PLAN = {
    "Grade 3": {"Math": 45, "Science": 30, "English": 30},
    "Grade 5": {"Math": 60, "Science": 45, "English": 45}
}

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# Simple authentication
if not st.session_state.authenticated:
    st.title("🏆 Welcome to Olympiad Prep!")
    st.markdown("### Login to track your progress")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🎓")
        
        name = st.text_input("Enter your name:")
        grade = st.selectbox("Select your grade:", ["Grade 3", "Grade 5"])
        password = st.text_input("Secret Password:", type="password")
        
        # Simple password
        PASSWORDS = {
            "Grade 3": "champ3",
            "Grade 5": "champ5"
        }
        
        if st.button("🚀 Start Learning!", type="primary"):
            if name and password == PASSWORDS[grade]:
                st.session_state.authenticated = True
                st.session_state.current_user = {"name": name, "grade": grade}
                
                # Create/load student from database
                db.get_or_create_student(name, grade)
                st.success("✅ Welcome!")
                st.rerun()
            elif name and password:
                st.error("❌ Wrong password! Ask Mom or Dad for help.")
            else:
                st.warning("⚠️ Please enter your name and password")
        
        st.markdown("---")
        st.info("**Passwords:**\n- Grade 3: `champ3`\n- Grade 5: `champ5`")
    
    st.stop()

# User is authenticated - load their data
name = st.session_state.current_user['name']
grade = st.session_state.current_user['grade']

# Load student data from database
try:
    student = db.get_or_create_student(name, grade)
    completed_topics_db = db.get_completed_topics(name, grade)
    completed_topics_list = [t['topic'] for t in completed_topics_db]
    total_hours = db.get_total_study_hours(name, grade)
    streak_days = student.get('streak_days', 0) if student else 0
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Running in offline mode. Data won't be saved.")
    completed_topics_list = []
    total_hours = 0
    streak_days = 0

# Title and header
st.title("🏆 Kids Olympiad Prep Planner")
st.markdown("**Systematic preparation for Math, Science & English Olympiads**")

# Sidebar
with st.sidebar:
    st.markdown(f"### 👋 Hi, {name}!")
    st.markdown(f"**Grade:** {grade}")
    
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()
    
    st.markdown("---")
    st.header("📊 Quick Stats")
    st.metric("Total Study Hours", f"{total_hours:.1f}")
    st.metric("Topics Completed", len(completed_topics_list))
    st.metric("Current Streak", f"{streak_days} days")
    
    st.markdown("---")
    st.header("🎯 Target Olympiads")
    st.markdown("""
    - **IMO** (International Math Olympiad)
    - **NSO** (National Science Olympiad)
    - **IEO** (International English Olympiad)
    - **SOF Olympiads**
    """)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📅 Weekly Planner", "📈 Progress Tracker", "📚 Study Resources", "🏅 Achievements"])

with tab1:
    st.header(f"📅 Weekly Study Planner - {name}")
    
    # Week selector
    week_date = st.date_input("Select week starting:", datetime.now())
    week_key = week_date.strftime("%Y-W%U")
    
    # Load existing weekly plan from database
    try:
        weekly_plan = db.get_weekly_plan(name, grade, week_key)
        plan_dict = {p['day_of_week']: p for p in weekly_plan}
    except:
        plan_dict = {}
    
    # Daily schedule
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    st.subheader("📝 Create Weekly Schedule")
    
    for day in days:
        existing = plan_dict.get(day, {})
        
        with st.expander(f"**{day}**", expanded=False):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                subject = st.selectbox(
                    "Subject:",
                    ["Math", "Science", "English", "Rest Day"],
                    index=["Math", "Science", "English", "Rest Day"].index(existing.get('subject', 'Rest Day')) if existing.get('subject') in ["Math", "Science", "English", "Rest Day"] else 3,
                    key=f"{grade}_{week_key}_{day}_subject"
                )
            
            with col2:
                if subject != "Rest Day":
                    topics = SYLLABUS[grade][subject]
                    topic = st.multiselect(
                        "Topics:",
                        topics,
                        key=f"{grade}_{week_key}_{day}_topic"
                    )
                else:
                    topic = ["Rest"]
            
            with col3:
                if subject != "Rest Day":
                    duration = st.number_input(
                        "Duration (min):",
                        min_value=15,
                        max_value=120,
                        value=existing.get('duration', STUDY_PLAN[grade].get(subject, 45)),
                        step=15,
                        key=f"{grade}_{week_key}_{day}_duration"
                    )
                else:
                    duration = 0
            
            with col4:
                completed = st.checkbox(
                    "✅ Done",
                    value=existing.get('completed', False),
                    key=f"{grade}_{week_key}_{day}_completed"
                )
                
                # Save to database when marked complete
                if completed and not existing.get('completed', False):
                    try:
                        # Save weekly plan
                        db.save_weekly_plan(name, grade, week_key, day, subject, 
                                          ','.join(topic) if topic else '', duration, completed)
                        
                        # Add study session
                        if duration > 0:
                            db.add_study_session(name, grade, subject, duration, 
                                               ','.join(topic) if topic else None)
                        
                        # Mark topics as completed
                        if topic and subject != "Rest Day":
                            for t in topic:
                                db.mark_topic_completed(name, grade, subject, t)
                        
                        st.success(f"✅ {day} session logged!")
                    except Exception as e:
                        st.error(f"Error saving: {e}")
    
    # Save plan button
    if st.button("💾 Save This Week's Plan", type="primary"):
        st.success(f"✅ Weekly plan saved for {name}!")
        st.rerun()

with tab2:
    st.header(f"📈 Progress Tracker - {name}")
    
    # Overall progress by subject
    st.subheader("📊 Subject-wise Topic Completion")
    
    for subject in ["Math", "Science", "English"]:
        total_topics = len(SYLLABUS[grade][subject])
        completed = [t for t in completed_topics_list if t in SYLLABUS[grade][subject]]
        completed_count = len(completed)
        progress_pct = (completed_count / total_topics * 100) if total_topics > 0 else 0
        
        col_subj1, col_subj2 = st.columns([3, 1])
        with col_subj1:
            st.write(f"**{subject}**")
            st.progress(progress_pct / 100)
        with col_subj2:
            st.metric("", f"{completed_count}/{total_topics}")
    
    st.markdown("---")
    
    # Detailed topic checklist
    st.subheader("✅ Topic Checklist")
    
    subject_tab = st.selectbox("Select subject to track:", ["Math", "Science", "English"], key="progress_subject")
    
    topics = SYLLABUS[grade][subject_tab]
    
    for i, topic in enumerate(topics):
        col_topic1, col_topic2 = st.columns([4, 1])
        with col_topic1:
            is_completed = topic in completed_topics_list
            new_state = st.checkbox(
                topic,
                value=is_completed,
                key=f"topic_check_{grade}_{subject_tab}_{i}"
            )
            
            # Update database if state changed
            if new_state != is_completed:
                try:
                    if new_state:
                        db.mark_topic_completed(name, grade, subject_tab, topic)
                        st.rerun()
                    else:
                        db.unmark_topic(name, grade, subject_tab, topic)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error updating: {e}")
        
        with col_topic2:
            if topic in completed_topics_list:
                st.success("✅")
    
    # Study time log
    st.markdown("---")
    st.subheader("⏱️ Log Study Session")
    
    log_col1, log_col2, log_col3, log_col4 = st.columns(4)
    with log_col1:
        log_subject = st.selectbox("Subject:", ["Math", "Science", "English"], key="log_subject")
    with log_col2:
        log_duration = st.number_input("Duration (min):", min_value=15, max_value=180, value=45, step=15)
    with log_col3:
        log_date = st.date_input("Date:", datetime.now())
    with log_col4:
        st.write("")
        st.write("")
        if st.button("➕ Add Session"):
            try:
                db.add_study_session(name, grade, log_subject, log_duration)
                st.success(f"Added {log_duration} minutes of {log_subject}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Weekly summary
    st.markdown("---")
    st.subheader("📅 This Week's Summary")
    
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    with sum_col1:
        st.metric("Study Hours", f"{total_hours:.1f} hrs")
    with sum_col2:
        st.metric("Topics Mastered", len(completed_topics_list))
    with sum_col3:
        total_topics_all = sum(len(SYLLABUS[grade][s]) for s in ["Math", "Science", "English"])
        overall_pct = (len(completed_topics_list) / total_topics_all * 100) if total_topics_all > 0 else 0
        st.metric("Overall Progress", f"{overall_pct:.1f}%")

with tab3:
    st.header("📚 Study Resources & Tips")
    
    resource_subject = st.selectbox("Choose subject:", ["Math", "Science", "English"], key="resource_subject")
    
    # Study tips by subject
    if resource_subject == "Math":
        st.subheader("🔢 Math Olympiad Tips")
        st.markdown("""
        **Daily Practice:**
        - Solve 10 problems daily (mix of easy, medium, hard)
        - Time yourself - aim for 2-3 minutes per problem
        - Focus on mental math for speed
        
        **Key Areas to Master:**
        - Number patterns and sequences
        - Logical reasoning puzzles
        - Word problems (age, time-distance, etc.)
        - Geometry and spatial reasoning
        
        **Recommended Resources:**
        - Olympiad Exam preparation books (MTG, Arihant)
        - Practice papers from previous years
        - Online: Khan Academy, BYJU'S
        """)
    
    elif resource_subject == "Science":
        st.subheader("🔬 Science Olympiad Tips")
        st.markdown("""
        **Learning Strategy:**
        - Understand concepts through experiments
        - Create mind maps for each chapter
        - Use diagrams and flowcharts
        
        **Key Focus Areas:**
        - Life Science (plants, animals, human body)
        - Physical Science (force, energy, light, sound)
        - Environmental awareness
        - Scientific reasoning
        
        **Recommended Resources:**
        - NCERT textbooks (foundation)
        - NSO workbooks
        - YouTube: ChuChu TV (Grade 3), Byju's Learning (Grade 5)
        - Science experiments at home
        """)
    
    else:  # English
        st.subheader("📖 English Olympiad Tips")
        st.markdown("""
        **Daily Practice:**
        - Read for 20 minutes daily (stories, articles)
        - Learn 5 new words with meanings
        - Write one paragraph on any topic
        
        **Key Areas:**
        - Reading comprehension (practice answering questions)
        - Vocabulary building (synonyms, antonyms)
        - Grammar rules with examples
        - Sentence formation and correction
        
        **Recommended Resources:**
        - English Olympiad workbooks (Macmillan, Oswaal)
        - Story books appropriate for age
        - Online: British Council Kids, Reading Eggs
        - English newspapers (simple articles)
        """)
    
    st.markdown("---")
    st.subheader("🎯 Mock Test Schedule")
    st.markdown("""
    **Monthly Mock Tests:**
    - Week 1: Math Olympiad (1 hour)
    - Week 2: Science Olympiad (1 hour)
    - Week 3: English Olympiad (1 hour)
    - Week 4: Mixed revision & weak areas
    
    **Important:** Take tests in exam-like conditions!
    """)

with tab4:
    st.header(f"🏅 Achievements - {name}")
    
    # Achievement badges
    st.subheader("🎖️ Badges Earned")
    
    badge_col1, badge_col2, badge_col3, badge_col4 = st.columns(4)
    
    # Define badges based on progress
    badges = []
    
    if total_hours >= 10:
        badges.append(("🕐", "10 Hour Club"))
    if total_hours >= 25:
        badges.append(("⏰", "25 Hour Champion"))
    if total_hours >= 50:
        badges.append(("🏆", "50 Hour Master"))
    
    if len(completed_topics_list) >= 10:
        badges.append(("📚", "10 Topics Done"))
    if len(completed_topics_list) >= 25:
        badges.append(("📖", "25 Topics Expert"))
    
    if streak_days >= 7:
        badges.append(("🔥", "Week Streak"))
    if streak_days >= 30:
        badges.append(("⚡", "Month Streak"))
    
    # Display badges
    if badges:
        for i, (emoji, badge_name) in enumerate(badges):
            with [badge_col1, badge_col2, badge_col3, badge_col4][i % 4]:
                st.markdown(f"### {emoji}")
                st.caption(badge_name)
    else:
        st.info("Keep studying to earn badges! 🌟")
    
    st.markdown("---")
    
    # Progress milestones
    st.subheader("🎯 Milestones")
    
    milestones = [
        (10, "🥉 Bronze Scholar"),
        (20, "🥈 Silver Scholar"),
        (30, "🥇 Gold Scholar"),
        (40, "💎 Diamond Scholar"),
        (50, "👑 Olympiad Ready!")
    ]
    
    completed_count = len(completed_topics_list)
    
    for target, title in milestones:
        progress = min(completed_count / target, 1.0)
        status = "✅" if completed_count >= target else f"{completed_count}/{target}"
        st.write(f"**{title}** - {status}")
        st.progress(progress)
    
    st.markdown("---")
    
    # Motivational message
    st.subheader("💪 Keep Going!")
    
    total_topics_all = sum(len(SYLLABUS[grade][s]) for s in ["Math", "Science", "English"])
    remaining = total_topics_all - len(completed_topics_list)
    
    if remaining > 30:
        st.info(f"🌱 Great start! You have {remaining} topics to go. One day at a time!")
    elif remaining > 15:
        st.success(f"🚀 You're halfway there! Keep the momentum going. {remaining} topics remaining.")
    elif remaining > 5:
        st.success(f"🎯 Almost there! Just {remaining} more topics. You've got this!")
    else:
        st.balloons()
        st.success(f"🏆 Wow! Only {remaining} topics left. You're ready for the Olympiad!")

# Footer with tips
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
<h4>💡 Study Tips</h4>
<p><b>Consistency > Intensity</b> | Study daily for 1-2 hours rather than cramming<br>
<b>Take Breaks</b> | 10 min break after every 45 min study session<br>
<b>Sleep Well</b> | 9-10 hours for kids is crucial for learning<br>
<b>Stay Healthy</b> | Exercise, healthy food, and water boost brain power!</p>
</div>
""", unsafe_allow_html=True)