import streamlit as st
import json
from datetime import datetime, timedelta
import database as db
import os

st.set_page_config(page_title="🏆 Olympiad Prep Planner", layout="wide", page_icon="🏆")

# Get OpenAI API key for quiz generation
def get_openai_key():
    """Get OpenAI API key from environment or secrets"""
    # Try environment variable first
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    
    # Try Streamlit secrets
    try:
        key = st.secrets["OPENAI_API_KEY"]
        return key
    except (KeyError, AttributeError):
        return None

api_key = get_openai_key()

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
        
        user_type = st.radio("👤 I am:", ["Student", "Parent"], horizontal=True)
        
        if user_type == "Student":
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
                    st.session_state.current_user = {"name": name, "grade": grade, "type": "student"}
                    st.session_state.student_data_loaded = False
                    st.success("✅ Welcome!")
                    st.rerun()
                elif name and password:
                    st.error("❌ Wrong password! Ask Mom or Dad for help.")
                else:
                    st.warning("⚠️ Please enter your name and password")
            
            st.markdown("---")
            st.info("**Passwords:**\n- Grade 3: `champ3`\n- Grade 5: `champ5`")
        
        else:  # Parent
            parent_password = st.text_input("🔐 Parent Password:", type="password", placeholder="Enter parent password")
            
            if st.button("📊 View Dashboard", type="primary"):
                if parent_password == "parent2024":
                    st.session_state.authenticated = True
                    st.session_state.current_user = {"name": "Parent", "grade": None, "type": "parent"}
                    st.session_state.student_data_loaded = False
                    st.success("✅ Welcome, Parent!")
                    st.rerun()
                elif parent_password:
                    st.error("❌ Incorrect password!")
                else:
                    st.warning("⚠️ Please enter password")
            
            st.markdown("---")
            st.info("**Parent Password:** `parent2024`")
    
    st.stop()

# User is authenticated - check if parent or student
user_type = st.session_state.current_user.get('type', 'student')

# PARENT DASHBOARD
if user_type == "parent":
    st.title("📊 Parent Dashboard")
    st.markdown("**Monitor your kids' Olympiad preparation progress**")
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown("### 👋 Hi, Parent!")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
        
        st.markdown("---")
        st.info("**Parent Dashboard**\n\nTrack both kids' progress, study hours, and achievements.")
    
    # Load data for both kids
    try:
        # Get all students from database
        conn = db.get_db_connection()
        cur = conn.cursor()
        
        # Get all unique students
        cur.execute("SELECT DISTINCT name, grade FROM students ORDER BY grade")
        students = cur.fetchall()
        
        if not students:
            st.info("👶 No student data yet. Kids need to log in and start studying first!")
            conn.close()
            st.stop()
        
        # Overview metrics
        st.header("📈 Overall Progress")
        cols = st.columns(len(students))
        
        for idx, (student_name, student_grade) in enumerate(students):
            with cols[idx]:
                st.subheader(f"{student_name}")
                st.caption(f"{student_grade}")
                
                # Get stats
                student_data = db.get_or_create_student(student_name, student_grade)
                completed_topics = db.get_completed_topics(student_name, student_grade)
                total_hours = db.get_total_study_hours(student_name, student_grade)
                
                st.metric("📚 Topics Completed", len(completed_topics))
                st.metric("⏱️ Total Hours", f"{total_hours:.1f}")
                st.metric("🔥 Streak", f"{student_data.get('streak_days', 0)} days")
        
        st.markdown("---")
        
        # Detailed view - select student
        st.header("🔍 Detailed View")
        selected_student = st.selectbox(
            "Select student to view details:",
            options=[f"{name} ({grade})" for name, grade in students]
        )
        
        # Parse selected student
        selected_name = selected_student.split(" (")[0]
        selected_grade = selected_student.split("(")[1].replace(")", "")
        
        # Get detailed data
        student_data = db.get_or_create_student(selected_name, selected_grade)
        completed_topics_db = db.get_completed_topics(selected_name, selected_grade)
        completed_topics_list = [t['topic'] for t in completed_topics_db]
        total_hours = db.get_total_study_hours(selected_name, selected_grade)
        
        # Create tabs for detailed view
        dtab1, dtab2, dtab3, dtab4 = st.tabs(["📊 Progress", "📅 Weekly Plan", "🏆 Achievements", "📝 Recent Activity"])
        
        with dtab1:
            st.subheader(f"📊 {selected_name}'s Progress")
            
            # Progress by subject
            col1, col2, col3 = st.columns(3)
            
            subjects = ["Math", "Science", "English"]
            subject_counts = {subj: 0 for subj in subjects}
            
            for topic_data in completed_topics_db:
                topic = topic_data['topic']
                for subj in subjects:
                    if subj in topic_data.get('subject', ''):
                        subject_counts[subj] += 1
            
            with col1:
                st.metric("🔢 Math Topics", subject_counts["Math"])
            with col2:
                st.metric("🔬 Science Topics", subject_counts["Science"])
            with col3:
                st.metric("📖 English Topics", subject_counts["English"])
            
            st.markdown("---")
            
            # Completed topics list
            st.subheader("✅ Completed Topics")
            if completed_topics_list:
                for i, topic_data in enumerate(completed_topics_db[:20], 1):
                    st.markdown(f"{i}. **{topic_data['topic']}** ({topic_data['subject']})")
                if len(completed_topics_db) > 20:
                    st.caption(f"... and {len(completed_topics_db) - 20} more")
            else:
                st.info("No topics completed yet.")
        
        with dtab2:
            st.subheader(f"📅 {selected_name}'s Weekly Plan")
            
            # Show this week's plan
            import datetime
            today = datetime.date.today()
            week_start = today - datetime.timedelta(days=today.weekday())
            
            for i in range(7):
                day = week_start + datetime.timedelta(days=i)
                day_name = day.strftime("%A")
                day_str = day.strftime("%Y-%m-%d")
                
                with st.expander(f"{'📍' if day == today else '📅'} {day_name} ({day.strftime('%b %d')})"):
                    plans = db.get_weekly_plan(selected_name, selected_grade, day_str)
                    if plans:
                        for plan in plans:
                            st.markdown(f"**{plan['subject']}:** {plan['topic']} - {plan['duration']} min")
                    else:
                        st.caption("No plan for this day")
        
        with dtab3:
            st.subheader(f"🏆 {selected_name}'s Achievements")
            
            # Calculate badges
            badges_earned = []
            
            if total_hours >= 1:
                badges_earned.append("🎯 First Hour - Logged 1 hour")
            if total_hours >= 10:
                badges_earned.append("💪 Dedicated Learner - 10+ hours")
            if total_hours >= 25:
                badges_earned.append("🔥 Study Master - 25+ hours")
            if total_hours >= 50:
                badges_earned.append("👑 Olympiad Champion - 50+ hours")
            
            if len(completed_topics_list) >= 5:
                badges_earned.append("📚 Topic Explorer - 5 topics")
            if len(completed_topics_list) >= 15:
                badges_earned.append("🌟 Knowledge Builder - 15 topics")
            if len(completed_topics_list) >= 30:
                badges_earned.append("🎓 Expert Student - 30 topics")
            
            if student_data.get('streak_days', 0) >= 3:
                badges_earned.append("🔥 3-Day Streak")
            if student_data.get('streak_days', 0) >= 7:
                badges_earned.append("⚡ Week Warrior - 7 days")
            if student_data.get('streak_days', 0) >= 14:
                badges_earned.append("💎 Two Week Champion")
            
            if badges_earned:
                for badge in badges_earned:
                    st.success(badge)
            else:
                st.info("No badges earned yet. Keep studying!")
        
        with dtab4:
            st.subheader(f"📝 {selected_name}'s Recent Activity")
            
            # Get recent study sessions
            cur.execute("""
                SELECT date, subject, duration_hours, notes 
                FROM study_sessions 
                WHERE student_name = %s AND grade = %s 
                ORDER BY date DESC 
                LIMIT 10
            """, (selected_name, selected_grade))
            sessions = cur.fetchall()
            
            if sessions:
                for session in sessions:
                    date, subject, duration, notes = session
                    st.markdown(f"**{date}** - {subject} ({duration:.1f}h)")
                    if notes:
                        st.caption(f"📝 {notes}")
                    st.markdown("---")
            else:
                st.info("No study sessions logged yet.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
    
    st.stop()

# STUDENT VIEW - load their data
name = st.session_state.current_user['name']
grade = st.session_state.current_user['grade']

# Cache data in session state to avoid repeated database calls
if 'student_data_loaded' not in st.session_state or not st.session_state.student_data_loaded:
    try:
        with st.spinner("Loading your data..."):
            student = db.get_or_create_student(name, grade)
            completed_topics_db = db.get_completed_topics(name, grade)
            completed_topics_list = [t['topic'] for t in completed_topics_db]
            total_hours = db.get_total_study_hours(name, grade)
            streak_days = student.get('streak_days', 0) if student else 0
            
            # Store in session state
            st.session_state.completed_topics_list = completed_topics_list
            st.session_state.total_hours = total_hours
            st.session_state.streak_days = streak_days
            st.session_state.student_data_loaded = True
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Running in offline mode. Data won't be saved.")
        st.session_state.completed_topics_list = []
        st.session_state.total_hours = 0
        st.session_state.streak_days = 0
        st.session_state.student_data_loaded = True
else:
    # Use cached data
    completed_topics_list = st.session_state.completed_topics_list
    total_hours = st.session_state.total_hours
    streak_days = st.session_state.streak_days

# Title and header
st.title("🏆 Kids Olympiad Prep Planner")
st.markdown("**Systematic preparation for Math, Science & English Olympiads**")

# Sidebar
with st.sidebar:
    st.markdown(f"### 👋 Hi, {name}!")
    st.markdown(f"**Grade:** {grade}")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.student_data_loaded = False
            st.rerun()
    with col_btn2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.student_data_loaded = False
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Weekly Planner", "📈 Progress Tracker", "📚 Study Resources", "🎯 Quiz", "🏅 Achievements"])

with tab1:
    st.header(f"📅 Weekly Study Planner - {name}")
    st.caption("Plan your week ahead. Track completion in the Progress Tracker tab.")
    
    # Week selector
    col_week1, col_week2 = st.columns([2, 1])
    with col_week1:
        week_date = st.date_input("📆 Select week starting:", datetime.now())
        week_key = week_date.strftime("%Y-W%U")
    with col_week2:
        st.metric("Week #", week_key.split('-W')[1])
    
    st.markdown("---")
    
    # Load ALL weekly plans once (not per day)
    cache_key = f"weekly_plan_{week_key}"
    if cache_key not in st.session_state:
        try:
            with st.spinner("Loading week..."):
                all_plans = db.get_weekly_plan(name, grade, week_key)
                st.session_state[cache_key] = all_plans
        except:
            st.session_state[cache_key] = []
    else:
        all_plans = st.session_state[cache_key]
    
    # Daily schedule
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_emojis = ["📘", "📗", "📙", "📕", "📔", "🌟", "🌈"]
    
    for day_idx, day in enumerate(days):
        # Get sessions for this day from cached data
        day_plans = [p for p in all_plans if p['day_of_week'] == day]
        
        # Calculate total time for the day
        total_day_minutes = sum([p.get('duration', 0) for p in day_plans])
        session_count = len(day_plans)
        
        # Day card
        st.markdown(f"### {day_emojis[day_idx]} {day}")
        
        if day_plans:
            # Show sessions in a clean format
            for session_idx, session in enumerate(day_plans):
                subject = session.get('subject', 'N/A')
                duration = session.get('duration', 0)
                topics = session.get('topics', '').split(',') if session.get('topics') else []
                
                # Subject emoji mapping
                subject_emoji = {"Math": "🔢", "Science": "🔬", "English": "📖", "Rest Day": "😴"}
                
                col_sess1, col_sess2 = st.columns([3, 4])
                
                with col_sess1:
                    st.markdown(f"**{subject_emoji.get(subject, '📚')} {subject}** · {duration} min")
                
                with col_sess2:
                    if topics and topics[0]:
                        topics_display = ", ".join([t.strip() for t in topics[:3] if t.strip()])
                        if len(topics) > 3:
                            topics_display += f" +{len(topics)-3} more"
                        st.caption(f"📝 {topics_display}")
            
            # Day summary
            st.caption(f"📊 Total: {session_count} session{'s' if session_count != 1 else ''} · {total_day_minutes} minutes ({total_day_minutes/60:.1f} hours)")
        else:
            st.info(f"No sessions planned for {day}")
        
        # Add session button (compact)
        with st.expander(f"➕ Add session", expanded=False):
            col1, col2, col3, col4 = st.columns([2, 3, 1.5, 1])
            
            with col1:
                new_subject = st.selectbox(
                    "Subject",
                    ["Math", "Science", "English", "Rest Day"],
                    key=f"subj_{day}_{week_key}",
                    label_visibility="collapsed"
                )
            
            with col2:
                if new_subject != "Rest Day":
                    new_topics = st.multiselect(
                        "Topics",
                        SYLLABUS[grade][new_subject],
                        key=f"topics_{day}_{week_key}",
                        placeholder="Select topics..."
                    )
                else:
                    new_topics = ["Rest"]
            
            with col3:
                if new_subject != "Rest Day":
                    new_duration = st.number_input(
                        "Minutes",
                        min_value=15,
                        max_value=180,
                        value=STUDY_PLAN[grade].get(new_subject, 45),
                        step=15,
                        key=f"dur_{day}_{week_key}",
                        label_visibility="collapsed"
                    )
                else:
                    new_duration = 0
                    st.caption("Rest day 😴")
            
            with col4:
                if st.button("Add", key=f"add_{day}_{week_key}", type="primary", use_container_width=True):
                    if new_subject != "Rest Day" and not new_topics:
                        st.error("Please select topics")
                    else:
                        try:
                            with st.spinner("Adding..."):
                                db.save_weekly_plan(
                                    name, grade, week_key, day, 
                                    new_subject, 
                                    ','.join(new_topics) if new_topics else '', 
                                    new_duration, 
                                    False
                                )
                                # Clear cache to force reload
                                if cache_key in st.session_state:
                                    del st.session_state[cache_key]
                            st.success("✅ Added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        st.markdown("---")
    
    # Weekly overview
    st.markdown("### 📊 Week Overview")
    
    if all_plans:
            total_sessions = len(all_plans)
            total_minutes = sum([p.get('duration', 0) for p in all_plans])
            
            # Count by subject
            subject_breakdown = {}
            for plan in all_plans:
                subj = plan.get('subject', 'Unknown')
                subject_breakdown[subj] = subject_breakdown.get(subj, 0) + plan.get('duration', 0)
            
            col_ov1, col_ov2, col_ov3 = st.columns(3)
            
            with col_ov1:
                st.metric("📅 Total Sessions", total_sessions)
            
            with col_ov2:
                st.metric("⏱️ Total Time", f"{total_minutes} min", f"{total_minutes/60:.1f} hrs")
            
            with col_ov3:
                avg_per_day = total_minutes / 7
                st.metric("📈 Avg/Day", f"{avg_per_day:.0f} min")
            
            # Subject breakdown
            if subject_breakdown:
                st.markdown("**Time by Subject:**")
                cols = st.columns(len(subject_breakdown))
                for idx, (subj, mins) in enumerate(subject_breakdown.items()):
                    with cols[idx]:
                        emoji = {"Math": "🔢", "Science": "🔬", "English": "📖", "Rest Day": "😴"}.get(subj, "📚")
                        st.metric(f"{emoji} {subj}", f"{mins} min")
    else:
        st.info("👆 Start planning your week by adding study sessions above!")

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
    
    # Study session logger
    st.markdown("---")
    st.subheader("⏱️ Log Today's Study Session")
    st.caption("After completing a study session, log it here to track your progress")
    
    col_log1, col_log2, col_log3, col_log4 = st.columns([2, 2, 1.5, 1.5])
    
    with col_log1:
        log_subject = st.selectbox("Subject", ["Math", "Science", "English"], key="log_subject")
    
    with col_log2:
        log_topics = st.multiselect(
            "Topics covered",
            SYLLABUS[grade][log_subject],
            key="log_topics_multi",
            placeholder="What did you study?"
        )
    
    with col_log3:
        log_duration = st.number_input("Duration (min)", min_value=5, max_value=240, value=45, step=5)
    
    with col_log4:
        st.write("")
        st.write("")
        if st.button("📝 Log Session", type="primary", use_container_width=True):
            if not log_topics:
                st.warning("Please select topics you studied")
            else:
                try:
                    with st.spinner("Saving..."):
                        # Add study session
                        db.add_study_session(name, grade, log_subject, log_duration, ','.join(log_topics))
                        
                        # Mark topics as completed
                        for topic in log_topics:
                            db.mark_topic_completed(name, grade, log_subject, topic)
                        
                        # Update cache immediately
                        st.session_state.total_hours += log_duration / 60.0
                        for topic in log_topics:
                            if topic not in st.session_state.completed_topics_list:
                                st.session_state.completed_topics_list.append(topic)
                    
                    st.success(f"✅ Logged {log_duration} min of {log_subject}!")
                    st.balloons()
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
    st.header(f"🎯 Knowledge Quiz - {name}")
    st.caption("Test your understanding of completed topics!")
    
    # Initialize quiz state
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = None
    
    # Show completed topics by subject
    st.subheader("📚 Select Topics to Test")
    
    # Filter completed topics by subject
    completed_by_subject = {}
    for subject in ["Math", "Science", "English"]:
        completed = [t for t in completed_topics_list if t in SYLLABUS[grade][subject]]
        if completed:
            completed_by_subject[subject] = completed
    
    if not completed_by_subject:
        st.info("👆 Complete some topics first in the Progress Tracker tab, then come back here to test your knowledge!")
    else:
        # Subject selection
        quiz_subject = st.selectbox("Choose subject to test:", list(completed_by_subject.keys()), key="quiz_subject")
        
        # Topic selection
        quiz_topics = st.multiselect(
            f"Select {quiz_subject} topics to test (1-5 topics recommended):",
            completed_by_subject[quiz_subject],
            key="quiz_topics_select"
        )
        
        # Check if API key is available
        if not api_key:
            st.error("❌ OpenAI API key not found! Quiz feature requires an API key.")
            st.info("""
            **To fix this:**
            1. Go to Streamlit Cloud → Your app → Settings → Secrets
            2. Add this line:
            ```
            OPENAI_API_KEY = "your-openai-api-key-here"
            ```
            3. Save and wait for app to restart
            """)
            st.stop()
        
        # Number of questions
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            num_questions = st.slider("Number of questions:", 5, 10, 5)
        with col_q2:
            difficulty = st.select_slider("Difficulty:", ["Easy", "Medium", "Hard"], value="Medium")
        
        # Generate quiz button
        if st.button("🎲 Generate Quiz", type="primary", disabled=len(quiz_topics) == 0):
            if not quiz_topics:
                st.warning("Please select at least one topic!")
            else:
                with st.spinner(f"🤖 Generating {num_questions} {difficulty.lower()} questions..."):
                    try:
                        # Create prompt for OpenAI
                        topics_str = ", ".join(quiz_topics)
                        prompt = f"""Create {num_questions} multiple choice questions for a {grade} student about these {quiz_subject} topics: {topics_str}.

Difficulty level: {difficulty}
Grade level: {grade}

Requirements:
1. Questions should be age-appropriate for {grade}
2. Each question should have 4 options (A, B, C, D)
3. Only ONE correct answer per question
4. Cover different topics from the list
5. Make questions practical and engaging

Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation why this is correct",
      "topic": "Specific topic from the list"
    }}
  ]
}}"""
                        
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)
                        
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "You are an educational quiz generator. Always return valid JSON only."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7
                        )
                        
                        quiz_data = json.loads(response.choices[0].message.content)
                        st.session_state.quiz_questions = quiz_data['questions']
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_score = None
                        st.success(f"✅ Generated {len(quiz_data['questions'])} questions!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating quiz: {e}")
                        st.info("Try again or select different topics.")
        
        # Display quiz if generated
        if st.session_state.quiz_questions:
            st.markdown("---")
            st.subheader("📝 Answer the Questions")
            
            if not st.session_state.quiz_submitted:
                # Show questions
                for idx, q in enumerate(st.session_state.quiz_questions, 1):
                    with st.container():
                        st.markdown(f"### Question {idx}")
                        st.markdown(f"**Topic:** {q.get('topic', 'N/A')}")
                        st.markdown(f"**{q['question']}**")
                        
                        # Radio buttons for options
                        answer = st.radio(
                            f"Select your answer:",
                            options=list(q['options'].keys()),
                            format_func=lambda x: f"{x}) {q['options'][x]}",
                            key=f"q_{idx}",
                            index=None
                        )
                        
                        if answer:
                            st.session_state.quiz_answers[idx] = answer
                        
                        st.markdown("---")
                
                # Submit button
                if len(st.session_state.quiz_answers) == len(st.session_state.quiz_questions):
                    if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                        # Calculate score
                        correct = 0
                        for idx, q in enumerate(st.session_state.quiz_questions, 1):
                            if st.session_state.quiz_answers.get(idx) == q['correct_answer']:
                                correct += 1
                        
                        st.session_state.quiz_score = correct
                        st.session_state.quiz_submitted = True
                        st.rerun()
                else:
                    st.warning(f"⚠️ Please answer all {len(st.session_state.quiz_questions)} questions before submitting.")
            
            else:
                # Show results
                score = st.session_state.quiz_score
                total = len(st.session_state.quiz_questions)
                percentage = (score / total * 100)
                
                st.markdown("### 📊 Quiz Results")
                
                # Score display
                col_score1, col_score2, col_score3 = st.columns(3)
                with col_score1:
                    st.metric("Score", f"{score}/{total}")
                with col_score2:
                    st.metric("Percentage", f"{percentage:.0f}%")
                with col_score3:
                    if percentage >= 80:
                        st.metric("Grade", "⭐ Excellent!", delta="Great job!")
                    elif percentage >= 60:
                        st.metric("Grade", "👍 Good!", delta="Keep practicing")
                    else:
                        st.metric("Grade", "📚 Needs work", delta="Review topics")
                
                # Show answers
                st.markdown("---")
                st.subheader("📋 Answer Review")
                
                for idx, q in enumerate(st.session_state.quiz_questions, 1):
                    user_answer = st.session_state.quiz_answers.get(idx)
                    correct_answer = q['correct_answer']
                    is_correct = user_answer == correct_answer
                    
                    with st.expander(
                        f"{'✅' if is_correct else '❌'} Question {idx}: {q['question'][:50]}...",
                        expanded=not is_correct
                    ):
                        st.markdown(f"**{q['question']}**")
                        st.markdown(f"**Your answer:** {user_answer}) {q['options'][user_answer] if user_answer else 'Not answered'}")
                        
                        if is_correct:
                            st.success(f"✅ Correct!")
                        else:
                            st.error(f"❌ Wrong. Correct answer: {correct_answer}) {q['options'][correct_answer]}")
                        
                        st.info(f"💡 **Explanation:** {q.get('explanation', 'N/A')}")
                
                # Action buttons
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔄 Take New Quiz", type="primary", use_container_width=True):
                        st.session_state.quiz_questions = None
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_score = None
                        st.rerun()
                with col_btn2:
                    if st.button("📚 Review Topics", use_container_width=True):
                        st.info("Go to Study Resources tab to review!")

with tab5:
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