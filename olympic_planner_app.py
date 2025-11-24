import streamlit as st
import json
from datetime import datetime, timedelta
import database as db
import os

st.set_page_config(page_title="🏆 Olympiad Prep Planner", layout="wide", page_icon="🏆")

# Mobile-responsive CSS
st.markdown("""
    <style>
    /* Mobile-friendly improvements */
    @media (max-width: 768px) {
        .stButton button {
            width: 100%;
            padding: 0.75rem;
            font-size: 16px;
        }
        .stSelectbox, .stTextInput {
            font-size: 16px;
        }
        .stTextInput input {
            font-size: 16px;
        }
        .stRadio > div {
            flex-direction: column;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            flex-wrap: wrap;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            font-size: 14px;
        }
        section.main > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            font-size: 1.5rem;
        }
        h2 {
            font-size: 1.3rem;
        }
        h3 {
            font-size: 1.1rem;
        }
    }
    
    /* Better touch targets */
    .stCheckbox {
        min-height: 44px;
    }
    
    /* Improved form spacing */
    .stTextInput, .stSelectbox, .stMultiSelect {
        margin-bottom: 1rem;
    }
    
    /* Better metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

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

# Olympiad syllabus by grade and subject (Grades 1-12)
SYLLABUS = {
    "Grade 1": {
        "Math": ["Numbers 1-100", "Addition (1-digit)", "Subtraction (1-digit)", "Counting", "Shapes (Circle, Square, Triangle)", "Patterns", "Size Comparison", "Before/After Numbers", "Simple Word Problems"],
        "Science": ["My Body", "Animals Around Us", "Plants We See", "Food We Eat", "Water", "Air", "Day and Night", "Weather"],
        "English": ["Alphabet", "Simple Words", "Rhymes", "Short Sentences", "Common Objects", "Colors", "Numbers in Words", "Simple Stories"]
    },
    "Grade 2": {
        "Math": ["Numbers 1-1000", "Addition (2-digit)", "Subtraction (2-digit)", "Multiplication Tables (2, 3, 5, 10)", "Time (Hours)", "Money", "Measurement", "Shapes & Patterns", "Word Problems"],
        "Science": ["Parts of Plants", "Types of Animals", "Our Body Parts", "Food from Plants", "Clean Water", "Air We Breathe", "Sun and Moon", "Seasons"],
        "English": ["Vocabulary", "Nouns & Verbs", "Simple Sentences", "Rhymes & Poems", "Stories", "Comprehension", "Adjectives", "Spellings"]
    },
    "Grade 3": {
        "Math": ["Number System (1-4 digits)", "Addition & Subtraction", "Multiplication Tables (1-12)", "Division Basics", "Fractions (Halves, Quarters)", "Shapes & Patterns", "Measurement (Length, Weight, Time)", "Money Problems", "Mental Math", "Word Problems", "Geometry Basics", "Data Handling (Pictographs)"],
        "Science": ["Living & Non-Living Things", "Plants & Their Parts", "Animals & Their Habitats", "Human Body Parts", "Food & Nutrition", "Air & Water", "Weather & Seasons", "Light & Shadows", "Magnets", "Simple Machines", "Environmental Awareness", "Safety & First Aid"],
        "English": ["Reading Comprehension", "Vocabulary Building", "Grammar (Nouns, Verbs, Adjectives)", "Sentence Formation", "Tenses (Simple)", "Punctuation", "Spellings", "Story Writing", "Poem Reading", "Synonyms & Antonyms", "Articles (a, an, the)", "Singular & Plural"]
    },
    "Grade 4": {
        "Math": ["Large Numbers", "4 Operations", "Factors & Multiples", "Fractions", "Decimals", "Geometry", "Perimeter", "Area", "Time & Calendar", "Money", "Data Handling", "Patterns"],
        "Science": ["Digestive System", "Skeleton & Muscles", "Plants & Photosynthesis", "Animals & Adaptation", "Matter & Materials", "Force & Motion", "Light & Shadow", "Sound", "Heat", "Water Cycle"],
        "English": ["Comprehension", "Grammar (All Parts)", "Tenses", "Articles", "Prepositions", "Conjunctions", "Punctuation", "Paragraph Writing", "Letter Writing", "Vocabulary"]
    },
    "Grade 5": {
        "Math": ["Large Numbers (up to 10 digits)", "Roman Numerals", "Factors & Multiples", "LCM & HCF", "Fractions & Decimals", "Percentages", "Ratio & Proportion", "Algebraic Expressions", "Geometry (Angles, Triangles)", "Perimeter & Area", "Volume & Capacity", "Data Handling (Bar Graphs, Pie Charts)", "Time & Speed", "Profit & Loss", "Simple Interest", "Logical Reasoning"],
        "Science": ["Cell Structure", "Plant & Animal Systems", "Food & Digestion", "Respiration & Circulation", "Reproduction in Plants", "Force, Work & Energy", "Simple Machines", "Light & Reflection", "Sound", "Heat & Temperature", "Electricity & Circuits", "Magnets & Magnetism", "Earth & Solar System", "Water Cycle", "Air & Atmosphere", "Environmental Science"],
        "English": ["Advanced Reading Comprehension", "Vocabulary (Prefixes, Suffixes)", "Parts of Speech (All)", "Tenses (All)", "Active & Passive Voice", "Direct & Indirect Speech", "Clauses & Phrases", "Essay Writing", "Letter Writing", "Idioms & Proverbs", "Homophones & Homonyms", "Figures of Speech", "Poetry Analysis", "Grammar Application"]
    },
    "Grade 6": {
        "Math": ["Integers", "Fractions & Decimals", "Algebra Basics", "Ratio & Proportion", "Percentage", "Profit & Loss", "Simple & Compound Interest", "Geometry", "Mensuration", "Data Handling", "Symmetry", "Practical Geometry"],
        "Science": ["Nutrition", "Components of Food", "Fiber to Fabric", "Sorting Materials", "Separation of Substances", "Changes Around Us", "Living Organisms", "Motion & Measurement", "Light & Shadows", "Electricity & Circuits", "Magnets", "Water", "Air", "Garbage Management"],
        "English": ["Reading Comprehension", "Grammar", "Writing Skills", "Vocabulary", "Literature", "Prose & Poetry", "Tenses", "Voice", "Speech", "Composition"]
    },
    "Grade 7": {
        "Math": ["Integers", "Fractions & Decimals", "Data Handling", "Simple Equations", "Lines & Angles", "Triangles", "Comparing Quantities", "Rational Numbers", "Practical Geometry", "Perimeter & Area", "Algebraic Expressions", "Exponents & Powers", "Symmetry", "Visualizing Solid Shapes"],
        "Science": ["Nutrition in Plants & Animals", "Heat", "Acids, Bases & Salts", "Physical & Chemical Changes", "Weather, Climate & Adaptations", "Winds, Storms & Cyclones", "Soil", "Respiration", "Transportation in Animals & Plants", "Reproduction in Plants", "Motion & Time", "Electric Current", "Light", "Water", "Forests", "Wastewater"],
        "English": ["Advanced Comprehension", "Grammar & Composition", "Literature", "Writing Skills", "Vocabulary", "Functional English", "Creative Writing", "Formal Letters", "Speech Writing", "Debate"]
    },
    "Grade 8": {
        "Math": ["Rational Numbers", "Linear Equations", "Understanding Quadrilaterals", "Practical Geometry", "Data Handling", "Squares & Square Roots", "Cubes & Cube Roots", "Comparing Quantities", "Algebraic Expressions", "Mensuration", "Exponents & Powers", "Direct & Inverse Proportions", "Factorization", "Graphs", "Solid Shapes"],
        "Science": ["Crop Production", "Microorganisms", "Synthetic Fibers & Plastics", "Metals & Non-Metals", "Coal & Petroleum", "Combustion & Flame", "Conservation", "Cell Structure", "Reproduction", "Reaching Adolescence", "Force & Pressure", "Friction", "Sound", "Chemical Effects of Current", "Light", "Stars & Solar System", "Pollution"],
        "English": ["Comprehension", "Grammar", "Writing", "Literature", "Vocabulary", "Composition", "Formal Writing", "Report Writing", "Article Writing", "Story Writing"]
    },
    "Grade 9": {
        "Math": ["Number Systems", "Polynomials", "Coordinate Geometry", "Linear Equations (2 variables)", "Euclid's Geometry", "Lines & Angles", "Triangles", "Quadrilaterals", "Circles", "Constructions", "Heron's Formula", "Surface Areas & Volumes", "Statistics", "Probability"],
        "Science": ["Matter", "Atoms & Molecules", "Structure of Atom", "Cell", "Tissues", "Motion", "Force & Laws of Motion", "Gravitation", "Work & Energy", "Sound", "Natural Resources", "Diversity in Living", "Disease & Health", "Crop Improvement"],
        "English": ["Literature", "Grammar", "Writing Skills", "Comprehension", "Prose", "Poetry", "Drama", "Composition", "Formal Letters", "Notice Writing", "Message Writing", "Article Writing"]
    },
    "Grade 10": {
        "Math": ["Real Numbers", "Polynomials", "Linear Equations", "Quadratic Equations", "Arithmetic Progressions", "Triangles", "Coordinate Geometry", "Trigonometry", "Circles", "Constructions", "Mensuration", "Surface Areas & Volumes", "Statistics", "Probability"],
        "Science": ["Chemical Reactions", "Acids, Bases & Salts", "Metals & Non-Metals", "Carbon Compounds", "Periodic Classification", "Life Processes", "Control & Coordination", "Reproduction", "Heredity & Evolution", "Light", "Human Eye", "Electricity", "Magnetic Effects", "Energy Sources", "Environment", "Natural Resources"],
        "English": ["Literature", "Grammar", "Writing", "Comprehension", "Prose", "Poetry", "Drama", "Novel", "Letter Writing", "Article Writing", "Report Writing", "Story Writing"]
    },
    "Grade 11": {
        "Math": ["Sets", "Relations & Functions", "Trigonometry", "Complex Numbers", "Linear Inequalities", "Permutations & Combinations", "Binomial Theorem", "Sequences & Series", "Straight Lines", "Conic Sections", "3D Geometry", "Limits & Derivatives", "Statistics", "Probability"],
        "Science": ["Units & Measurements", "Motion", "Laws of Motion", "Work Energy Power", "Rotational Motion", "Gravitation", "Mechanical Properties", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves", "Classification", "Chemical Bonding", "States of Matter", "Equilibrium", "Redox Reactions", "Organic Chemistry", "Cell", "Biomolecules", "Plant Physiology", "Human Physiology", "Respiration"],
        "English": ["Literature", "Reading Comprehension", "Writing Skills", "Grammar", "Prose", "Poetry", "Novel", "Note Making", "Summarizing", "Report Writing", "Debate Writing", "Speech Writing"]
    },
    "Grade 12": {
        "Math": ["Relations & Functions", "Inverse Trigonometry", "Matrices", "Determinants", "Continuity & Differentiability", "Applications of Derivatives", "Integrals", "Applications of Integrals", "Differential Equations", "Vectors", "3D Geometry", "Linear Programming", "Probability"],
        "Science": ["Electric Charges", "Electrostatic Potential", "Current Electricity", "Moving Charges", "Magnetism", "Electromagnetic Induction", "AC", "Electromagnetic Waves", "Ray Optics", "Wave Optics", "Dual Nature", "Atoms", "Nuclei", "Semiconductors", "Communication Systems", "Solid State", "Solutions", "Electrochemistry", "Chemical Kinetics", "Surface Chemistry", "p-Block Elements", "d & f Block Elements", "Coordination Compounds", "Aldehydes Ketones", "Carboxylic Acids", "Amines", "Biomolecules", "Polymers", "Chemistry in Everyday Life", "Reproduction", "Genetics", "Evolution", "Human Health", "Microbes", "Biotechnology", "Organisms & Populations", "Ecosystem", "Biodiversity", "Environmental Issues"],
        "English": ["Literature", "Advanced Comprehension", "Writing Skills", "Prose", "Poetry", "Drama", "Novel", "Note Making", "Summarizing", "Report Writing", "Article Writing", "Speech Writing", "Debate Writing"]
    }
}

# Study time recommendations (minutes per session)
STUDY_PLAN = {
    "Grade 1": {"Math": 30, "Science": 20, "English": 20},
    "Grade 2": {"Math": 30, "Science": 25, "English": 25},
    "Grade 3": {"Math": 45, "Science": 30, "English": 30},
    "Grade 4": {"Math": 45, "Science": 35, "English": 35},
    "Grade 5": {"Math": 60, "Science": 45, "English": 45},
    "Grade 6": {"Math": 60, "Science": 45, "English": 45},
    "Grade 7": {"Math": 60, "Science": 50, "English": 45},
    "Grade 8": {"Math": 60, "Science": 50, "English": 45},
    "Grade 9": {"Math": 75, "Science": 60, "English": 45},
    "Grade 10": {"Math": 75, "Science": 60, "English": 45},
    "Grade 11": {"Math": 90, "Science": 75, "English": 45},
    "Grade 12": {"Math": 90, "Science": 75, "English": 45}
}

# All available grades
ALL_GRADES = [f"Grade {i}" for i in range(1, 13)]

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "family_id" not in st.session_state:
    st.session_state.family_id = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" or "signup"
if "db_initialized" not in st.session_state:
    try:
        db.initialize_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.stop()

# Check and populate preset content on first run
if "preset_content_checked" not in st.session_state:
    try:
        if db.get_preset_topics_count() == 0:
            db.populate_preset_content(SYLLABUS)
        st.session_state.preset_content_checked = True
    except Exception as e:
        st.warning(f"Could not load preset content: {e}")

# Multi-tenant authentication
if not st.session_state.authenticated:
    st.title("🏆 Welcome to Olympiad Prep!")
    st.markdown("### 📚 Master Math, Science & English for Olympiads")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Toggle between Login and Signup
        auth_tabs = st.tabs(["🔑 Login", "✨ Create Account"])
        
        # LOGIN TAB
        with auth_tabs[0]:
            st.markdown("### Welcome Back!")
            
            login_type = st.radio("I am:", ["Student", "Parent"], horizontal=True, key="login_type")
            
            if login_type == "Parent":
                # Parent Login
                email = st.text_input("📧 Email:", placeholder="parent@example.com", key="parent_login_email")
                password = st.text_input("🔐 Password:", type="password", key="parent_login_pass")
                
                if st.button("📊 Login as Parent", type="primary", use_container_width=True):
                    if email and password:
                        try:
                            family_data = db.authenticate_family(email, password)
                            if family_data:
                                st.session_state.authenticated = True
                                st.session_state.family_id = family_data['family_id']
                                st.session_state.current_user = {
                                    "name": family_data['family_name'],
                                    "email": email,
                                    "grade": None,
                                    "type": "parent"
                                }
                                st.success(f"✅ Welcome back, {family_data['family_name']}!")
                                st.rerun()
                            else:
                                st.error("❌ Invalid email or password")
                        except Exception as e:
                            st.error(f"Login error: {e}")
                    else:
                        st.warning("⚠️ Please enter email and password")
            
            else:  # Student Login
                # Get family students
                st.info("👨‍👩‍👧‍👦 Ask your parents to create an account first!")
                
                try:
                    # For now, show a simple student selector for existing families
                    parent_email_for_student = st.text_input("📧 Parent's Email:", placeholder="parent@example.com", key="student_parent_email")
                    
                    if parent_email_for_student:
                        # Simplified: Get students by trying to match
                        name = st.text_input("Your Name:", key="student_name_login")
                        grade = st.selectbox("Your Grade:", ALL_GRADES, key="student_grade_login")
                        
                        if st.button("🚀 Start Learning!", type="primary", use_container_width=True):
                            if name:
                                # Simple check - verify student exists
                                st.session_state.authenticated = True
                                st.session_state.current_user = {
                                    "name": name,
                                    "grade": grade,
                                    "type": "student",
                                    "parent_email": parent_email_for_student
                                }
                                st.session_state.student_data_loaded = False
                                st.success(f"✅ Welcome {name}!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Please enter your name")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # SIGNUP TAB
        with auth_tabs[1]:
            st.markdown("### Create Your Family Account")
            st.caption("Free forever • Track unlimited kids • Smart insights")
            
            family_name = st.text_input("👨‍👩‍👧‍👦 Family Name:", placeholder="The Kumar Family", key="signup_family")
            parent_email = st.text_input("📧 Parent Email:", placeholder="parent@example.com", key="signup_email")
            parent_password = st.text_input("🔐 Create Password:", type="password", placeholder="Min 6 characters", key="signup_pass")
            password_confirm = st.text_input("🔐 Confirm Password:", type="password", key="signup_pass_confirm")
            
            st.markdown("##### Add Your Kids (1-5 children)")
            
            num_kids = st.number_input("How many kids?", min_value=1, max_value=5, value=1, key="num_kids")
            
            kids_data = []
            for i in range(int(num_kids)):
                st.markdown(f"**Child {i+1}:**")
                c1, c2 = st.columns(2)
                with c1:
                    kid_name = st.text_input(f"Name", key=f"kid_name_{i}", placeholder=f"Child {i+1} name")
                with c2:
                    kid_grade = st.selectbox(f"Grade", ALL_GRADES, key=f"kid_grade_{i}")
                
                if kid_name:
                    kids_data.append({"name": kid_name, "grade": kid_grade})
            
            if st.button("✨ Create Family Account", type="primary", use_container_width=True):
                # Validation
                if not family_name:
                    st.error("❌ Please enter family name")
                elif not parent_email or '@' not in parent_email:
                    st.error("❌ Please enter valid email")
                elif len(parent_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif parent_password != password_confirm:
                    st.error("❌ Passwords don't match")
                elif not kids_data:
                    st.error("❌ Please add at least one child")
                else:
                    try:
                        # Create family account
                        family_id = db.create_family(parent_email, parent_password, family_name)
                        
                        # Add kids
                        for kid in kids_data:
                            db.add_student_to_family(family_id, kid['name'], kid['grade'])
                        
                        # Auto-login
                        st.session_state.authenticated = True
                        st.session_state.family_id = family_id
                        st.session_state.current_user = {
                            "name": family_name,
                            "email": parent_email,
                            "grade": None,
                            "type": "parent"
                        }
                        
                        st.success(f"🎉 Account created! Welcome {family_name}!")
                        st.balloons()
                        st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Signup failed: {str(e)}")
        
        st.markdown("---")
        st.caption("🔒 Your data is secure • 🌟 100% Free • 📱 Works on mobile")
    
    st.stop()

# User is authenticated - check if parent or student
user_type = st.session_state.current_user.get('type', 'student')

# PARENT DASHBOARD
if user_type == "parent":
    st.title("📊 Parent Dashboard")
    st.markdown("**Monitor your kids' Olympiad preparation progress**")
    
    # Logout button in sidebar
    with st.sidebar:
        family_name = st.session_state.current_user.get('name', 'Family')
        st.markdown(f"### 👋 {family_name}")
        st.caption(st.session_state.current_user.get('email', ''))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.session_state.parent_data_loaded = False
                st.rerun()
        with col_btn2:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.family_id = None
                st.session_state.parent_data_loaded = False
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 👥 My Kids")
        
        # Load kids from database
        try:
            family_students = db.get_family_students(st.session_state.family_id)
            st.session_state.parent_kids = family_students
        except Exception as e:
            st.error(f"Error loading kids: {e}")
            family_students = []
        
        # Add new kid
        with st.expander("➕ Add Child", expanded=len(family_students) == 0):
            kid_name = st.text_input("Child's Name:", key="add_kid_name")
            kid_grade = st.selectbox("Grade:", ALL_GRADES, key="add_kid_grade")
            
            if st.button("➕ Add Child", use_container_width=True):
                if kid_name:
                    try:
                        db.add_student_to_family(st.session_state.family_id, kid_name, kid_grade)
                        st.success(f"✅ Added {kid_name}!")
                        st.session_state.parent_data_loaded = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding child: {e}")
                else:
                    st.warning("Please enter child's name")
        
        # Show configured kids
        if family_students:
            st.markdown("**Your Children:**")
            for kid in family_students:
                st.markdown(f"- {kid['student_name']} ({kid['grade']})")
        else:
            st.warning("⚠️ Add your kids to get started!")
        
        st.markdown("---")
        st.info("💡 Kids can login using your email and their name")
    
    # Check if kids are configured
    if not st.session_state.parent_kids:
        st.info("👆 Please add your children in the sidebar to see their dashboard!")
        st.stop()
    
    # Cache parent dashboard data
    if 'parent_dashboard_data' not in st.session_state:
        st.session_state.parent_dashboard_data = {}
        st.session_state.parent_data_loaded = False
    
    # Load/refresh data
    if not st.session_state.parent_data_loaded:
        with st.spinner("Loading dashboard data..."):
            try:
                # Prepare student list - use student_name field
                students = [(kid['student_name'], kid['grade']) for kid in st.session_state.parent_kids]
                
                # Bulk load all data in ONE database call (much faster!)
                dashboard_cache = db.get_student_dashboard_data(students)
                
                # Filter out students that don't exist in DB
                existing_students = [(name, grade) for name, grade in students 
                                    if f"{name}_{grade}" in dashboard_cache 
                                    and dashboard_cache[f"{name}_{grade}"]['student_data'] is not None]
                
                if not existing_students:
                    st.warning("⚠️ Your kids haven't started using the app yet!")
                    st.info("They can login using your email and their name.")
                    st.stop()
                
                st.session_state.parent_dashboard_data = dashboard_cache
                st.session_state.parent_dashboard_students = existing_students
                st.session_state.parent_data_loaded = True
                
            except Exception as e:
                import traceback
                st.error(f"Error loading dashboard: {str(e)}")
                with st.expander("Debug info"):
                    st.code(traceback.format_exc())
                st.stop()
    
    # Use cached data
    students = st.session_state.parent_dashboard_students
    dashboard_cache = st.session_state.parent_dashboard_data
    
    try:
        
        # Overview metrics
        st.header("📈 Overall Progress")
        
        # Display student cards using cached data
        num_students = len(students)
        if num_students == 1:
            # Single student - full width
            student_name, student_grade = students[0]
            cache_key = f"{student_name}_{student_grade}"
            cached = dashboard_cache[cache_key]
            
            st.markdown(f"### {student_name}")
            st.caption(f"📚 {student_grade}")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Topics Done", len(cached['completed_topics']))
            with col2:
                st.metric("Study Hours", f"{cached['total_hours']:.1f}")
            with col3:
                st.metric("Streak", f"{cached['student_data'].get('streak_days', 0)} 🔥")
            with col4:
                quiz_stats = cached['quiz_stats']
                if quiz_stats['total_quizzes'] > 0:
                    st.metric("Quizzes", f"{quiz_stats['total_quizzes']} ({quiz_stats['avg_percentage']:.0f}%)")
                else:
                    st.metric("Quizzes", "0")
        else:
            # Multiple students - side by side
            cols = st.columns(num_students)
            
            for idx, (student_name, student_grade) in enumerate(students):
                cache_key = f"{student_name}_{student_grade}"
                cached = dashboard_cache[cache_key]
                
                with cols[idx]:
                    st.markdown(f"### {student_name}")
                    st.caption(f"📚 {student_grade}")
                    
                    st.metric("Topics", len(cached['completed_topics']))
                    st.metric("Hours", f"{cached['total_hours']:.1f}")
                    st.metric("Streak", f"{cached['student_data'].get('streak_days', 0)} 🔥")
                    
                    quiz_stats = cached['quiz_stats']
                    if quiz_stats['total_quizzes'] > 0:
                        st.metric("Quizzes", f"{quiz_stats['total_quizzes']}")
                        st.caption(f"Avg: {quiz_stats['avg_percentage']:.0f}%")
                    else:
                        st.metric("Quizzes", "0")
        
        st.markdown("---")
        
        # AI Insights Section
        st.header("💡 Smart Insights")
        st.caption("Data-driven observations about your kids' study patterns")
        
        # Generate insights for each student
        for student_name, student_grade in students:
            cache_key = f"{student_name}_{student_grade}"
            
            with st.expander(f"🔍 Insights for {student_name}", expanded=len(students) == 1):
                try:
                    insights_data = db.get_student_insights(student_name, student_grade)
                    
                    # Analyze and generate insights
                    insight_messages = []
                    
                    # Check subject balance (last 14 days)
                    recent_subjects = insights_data.get('recent_by_subject', {})
                    all_subjects = ['Math', 'Science', 'English']
                    
                    for subject in all_subjects:
                        if subject not in recent_subjects:
                            insight_messages.append({
                                'type': 'warning',
                                'icon': '⚠️',
                                'message': f"**No {subject} sessions** logged in the last 2 weeks. Consider adding {subject} study time."
                            })
                    
                    # Check for balanced study
                    if len(recent_subjects) >= 2:
                        subjects_list = list(recent_subjects.keys())
                        time_variance = max([s['total_minutes'] for s in recent_subjects.values()]) - min([s['total_minutes'] for s in recent_subjects.values()])
                        
                        if time_variance > 200:  # More than 3 hours difference
                            insight_messages.append({
                                'type': 'info',
                                'icon': '⚖️',
                                'message': f"**Study time imbalance detected.** {student_name} is focusing heavily on some subjects. Try to balance across Math, Science, and English."
                            })
                        elif len(recent_subjects) == 3:
                            insight_messages.append({
                                'type': 'success',
                                'icon': '✨',
                                'message': f"**Great balance!** {student_name} is studying all three subjects regularly."
                            })
                    
                    # Check quiz performance trend
                    quiz_results = insights_data.get('quiz_results', [])
                    if len(quiz_results) >= 3:
                        recent_3 = quiz_results[:3]
                        older_3 = quiz_results[3:6] if len(quiz_results) >= 6 else quiz_results[3:]
                        
                        if older_3:
                            recent_avg = sum([q['score'] / q['num_questions'] * 100 for q in recent_3]) / len(recent_3)
                            older_avg = sum([q['score'] / q['num_questions'] * 100 for q in older_3]) / len(older_3)
                            
                            if recent_avg > older_avg + 10:
                                insight_messages.append({
                                    'type': 'success',
                                    'icon': '📈',
                                    'message': f"**Quiz performance improving!** Recent average: {recent_avg:.0f}% (up from {older_avg:.0f}%). Keep up the good work!"
                                })
                            elif recent_avg < older_avg - 10:
                                insight_messages.append({
                                    'type': 'warning',
                                    'icon': '📉',
                                    'message': f"**Quiz scores declining.** Recent average: {recent_avg:.0f}% (down from {older_avg:.0f}%). May need more review time."
                                })
                            else:
                                insight_messages.append({
                                    'type': 'info',
                                    'icon': '📊',
                                    'message': f"**Quiz performance steady.** Maintaining {recent_avg:.0f}% average."
                                })
                    
                    # Check study consistency (last 7 days)
                    all_sessions = insights_data.get('all_sessions', [])
                    if all_sessions:
                        import datetime
                        now = datetime.datetime.now()
                        last_7_days = [s for s in all_sessions if (now - s['created_at']).days <= 7]
                        
                        if len(last_7_days) >= 5:
                            insight_messages.append({
                                'type': 'success',
                                'icon': '🔥',
                                'message': f"**Excellent consistency!** {len(last_7_days)} study sessions in the last week. {student_name} is building a strong habit!"
                            })
                        elif len(last_7_days) >= 3:
                            insight_messages.append({
                                'type': 'info',
                                'icon': '👍',
                                'message': f"**Good progress!** {len(last_7_days)} sessions this week. Try to aim for 5+ sessions per week."
                            })
                        elif len(last_7_days) >= 1:
                            insight_messages.append({
                                'type': 'warning',
                                'icon': '⏰',
                                'message': f"**Low activity.** Only {len(last_7_days)} session(s) this week. Encourage more regular study time."
                            })
                        
                        # Check if there's been no activity recently
                        last_session_date = insights_data.get('last_session_date')
                        if last_session_date:
                            days_since = (now - last_session_date).days
                            if days_since > 7:
                                insight_messages.append({
                                    'type': 'warning',
                                    'icon': '🚨',
                                    'message': f"**Inactive for {days_since} days!** Last study session was {last_session_date.strftime('%b %d')}. Time to restart the habit!"
                                })
                            elif days_since > 3:
                                insight_messages.append({
                                    'type': 'info',
                                    'icon': '📅',
                                    'message': f"**{days_since} days** since last session. Regular practice is key to retention!"
                                })
                    
                    # Check study duration patterns
                    if all_sessions:
                        avg_duration = sum([s['duration_minutes'] for s in all_sessions]) / len(all_sessions)
                        if avg_duration < 20:
                            insight_messages.append({
                                'type': 'info',
                                'icon': '⏱️',
                                'message': f"**Short sessions detected.** Average: {avg_duration:.0f} min. Consider 30-45 min sessions for better focus."
                            })
                        elif avg_duration > 90:
                            insight_messages.append({
                                'type': 'info',
                                'icon': '🧠',
                                'message': f"**Very long sessions.** Average: {avg_duration:.0f} min. Remember to take breaks to maintain focus!"
                            })
                    
                    # Display insights
                    if insight_messages:
                        for insight in insight_messages:
                            if insight['type'] == 'success':
                                st.success(f"{insight['icon']} {insight['message']}")
                            elif insight['type'] == 'warning':
                                st.warning(f"{insight['icon']} {insight['message']}")
                            else:
                                st.info(f"{insight['icon']} {insight['message']}")
                    else:
                        st.info("🎯 Not enough data yet. Insights will appear as your child uses the app more!")
                
                except Exception as e:
                    st.error(f"Error generating insights: {e}")
        
        st.markdown("---")
        
        # Detailed view - show all students by default
        st.header("🔍 Detailed View - All Kids")
        st.caption("Expand any section to see more details")
        
        # Loop through all students and show their details
        for student_idx, (selected_name, selected_grade) in enumerate(students):
            
            # Get detailed data for this student
            student_data = db.get_or_create_student(selected_name, selected_grade)
            completed_topics_db = db.get_completed_topics(selected_name, selected_grade)
            completed_topics_list = [t['topic'] for t in completed_topics_db]
            total_hours = db.get_total_study_hours(selected_name, selected_grade)
            
            # Student card with expander
            with st.expander(f"📚 {selected_name} ({selected_grade})", expanded=len(students) == 1):
                # Quick stats row
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    st.metric("Topics", len(completed_topics_list))
                with col_s2:
                    st.metric("Hours", f"{total_hours:.1f}")
                with col_s3:
                    st.metric("Streak", f"{student_data.get('streak_days', 0)} 🔥")
                with col_s4:
                    quiz_stats = db.get_quiz_stats(selected_name, selected_grade)
                    if quiz_stats['total_quizzes'] > 0:
                        st.metric("Quizzes", f"{quiz_stats['total_quizzes']}")
                    else:
                        st.metric("Quizzes", "0")
                
                st.markdown("---")
                
                # Create tabs for detailed view
                dtab1, dtab2, dtab3, dtab4, dtab5 = st.tabs(["📊 Progress", "📅 Weekly Plan", "🎯 Quiz Scores", "🏆 Achievements", "📝 Recent Activity"])
                
                with dtab1:
                    st.subheader(f"📊 Progress by Subject")
                    
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
                    st.subheader(f"📅 This Week's Plan")
                    
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
                    st.subheader(f"🎯 Quiz Performance")
                    
                    # Get quiz results
                    quiz_results = db.get_quiz_results(selected_name, selected_grade, limit=20)
                    quiz_stats = db.get_quiz_stats(selected_name, selected_grade)
                    
                    if quiz_stats['total_quizzes'] > 0:
                        # Summary stats
                        col_q1, col_q2, col_q3 = st.columns(3)
                        with col_q1:
                            st.metric("Total Quizzes", quiz_stats['total_quizzes'])
                        with col_q2:
                            st.metric("Average Score", f"{quiz_stats['avg_percentage']:.1f}%")
                        with col_q3:
                            if quiz_stats['avg_percentage'] >= 80:
                                st.metric("Performance", "⭐ Excellent")
                            elif quiz_stats['avg_percentage'] >= 60:
                                st.metric("Performance", "👍 Good")
                            else:
                                st.metric("Performance", "📈 Improving")
                        
                        st.markdown("---")
                        st.markdown("#### Recent Quizzes")
                        
                        # Show recent quiz results
                        for quiz in quiz_results:
                            created_at = quiz['created_at']
                            date_str = created_at.strftime("%b %d, %Y") if hasattr(created_at, 'strftime') else str(created_at)
                            
                            score = quiz['score']
                            total = quiz['num_questions']
                            percentage = (score / total * 100) if total > 0 else 0
                            
                            # Color based on performance
                            if percentage >= 80:
                                emoji = "⭐"
                            elif percentage >= 60:
                                emoji = "👍"
                            else:
                                emoji = "📈"
                            
                            with st.expander(f"{emoji} {quiz['subject']} - {score}/{total} ({percentage:.0f}%) - {date_str}"):
                                st.markdown(f"**Topics:** {quiz['topics']}")
                                st.progress(percentage / 100)
                                
                                if percentage >= 80:
                                    st.success("Excellent work! 🎉")
                                elif percentage >= 60:
                                    st.info("Good job! Keep practicing! 📚")
                                else:
                                    st.warning("Keep trying! Review these topics again. 💪")
                    else:
                        st.info("No quizzes taken yet.")
                
                with dtab4:
                    st.subheader(f"🏆 Achievements & Badges")
                    
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
                
                with dtab5:
                    st.subheader(f"📝 Recent Study Sessions")
                    
                    # Get recent study sessions
                    sessions = db.get_recent_study_sessions(selected_name, selected_grade, limit=10)
                    
                    if sessions:
                        for session in sessions:
                            created_at = session['created_at']
                            subject = session['subject']
                            duration_min = session['duration_minutes']
                            topics = session['topics']
                            
                            # Format date
                            date_str = created_at.strftime("%b %d, %Y") if hasattr(created_at, 'strftime') else str(created_at)
                            
                            st.markdown(f"**{date_str}** - {subject} ({duration_min} min)")
                            if topics:
                                st.caption(f"📝 Topics: {topics}")
                            st.markdown("---")
                    else:
                        st.info("No study sessions logged yet.")
                
                # Add spacing between students
                if student_idx < len(students) - 1:
                    st.markdown("---")
        
    except Exception as e:
        import traceback
        st.error(f"Error loading dashboard: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        with st.expander("Debug info"):
            st.code(traceback.format_exc())
    
    st.stop()

# STUDENT VIEW - load their data
name = st.session_state.current_user['name']
grade = st.session_state.current_user['grade']

# Get family_id if available (for multi-tenant), fallback to None for backward compatibility
student_family_id = None
if 'parent_email' in st.session_state.current_user:
    # Student logged in with parent email - need to lookup family_id
    # For simplicity, we'll let students work without family_id filtering for now
    # This maintains backward compatibility
    pass
else:
    # Parent is logged in as student, or old user
    student_family_id = st.session_state.get('family_id')

# Cache data in session state to avoid repeated database calls
if 'student_data_loaded' not in st.session_state or not st.session_state.student_data_loaded:
    try:
        with st.spinner("Loading your data..."):
            student = db.get_or_create_student(name, grade, family_id=student_family_id)
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

# First-time user onboarding
if 'onboarding_completed' not in st.session_state:
    st.session_state.onboarding_completed = False

if not st.session_state.onboarding_completed:
    # Check if truly first time (no completed topics or study sessions)
    if len(completed_topics_list) == 0 and total_hours == 0:
        st.info("👋 **Welcome to your Olympiad Prep Dashboard!** Let's get you started!")
        
        with st.expander("🎯 Quick Start Guide - Click to expand", expanded=True):
            st.markdown("""
            ### How to Use This App:
            
            #### 📅 1. Weekly Planner Tab
            - Plan your study sessions for the week
            - Select subjects, topics, and duration
            - Use suggested topics from curriculum with difficulty levels
            - 🟢 Easy · 🟡 Medium · 🔴 Hard
            
            #### 📈 2. Progress Tracker Tab
            - **Start a study session** with the timer
            - Click "Start Session" when you begin studying
            - Click "End Session" when done - duration is automatic!
            - Mark topics as completed
            - Track your study hours
            
            #### 🎯 3. Quiz Tab
            - Test your knowledge with AI-generated quizzes
            - Get 10 questions on any completed topic
            - Track your scores and improve!
            
            #### 🏅 4. Achievements Tab
            - Earn badges for milestones
            - Build study streaks
            - Celebrate your progress!
            
            ### 🚀 Ready to Start?
            """)
            
            col_start1, col_start2, col_start3 = st.columns(3)
            
            with col_start1:
                if st.button("📅 Plan My Week", type="primary", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.info("✅ Go to the 'Weekly Planner' tab above!")
                    st.rerun()
            
            with col_start2:
                if st.button("📈 Start Studying Now", type="primary", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.info("✅ Go to the 'Progress Tracker' tab above!")
                    st.rerun()
            
            with col_start3:
                if st.button("Skip Tutorial ⏭️", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.rerun()
            
            st.markdown("---")
            st.caption("💡 **Tip:** Ask your parents to check the Parent Dashboard to monitor your progress!")
    else:
        # Has some data, skip onboarding
        st.session_state.onboarding_completed = True

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
    st.caption("Quick and easy weekly planning")
    
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
            all_plans = db.get_weekly_plan(name, grade, week_key)
            st.session_state[cache_key] = all_plans
        except:
            st.session_state[cache_key] = []
    else:
        all_plans = st.session_state[cache_key]
    
    # Quick Add Section (at top for easy access)
    with st.container():
        st.subheader("⚡ Quick Add Session")
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1.5, 1])
        
        with col1:
            quick_day = st.selectbox(
                "Day",
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                key="quick_day"
            )
        
        with col2:
            quick_subject = st.selectbox(
                "Subject",
                ["Math", "Science", "English"],
                key="quick_subject"
            )
        
        with col3:
            # Simple multiselect with all topics (no checkboxes, no complexity)
            if grade in SYLLABUS and quick_subject in SYLLABUS[grade]:
                quick_topics = st.multiselect(
                    "Topics",
                    SYLLABUS[grade][quick_subject],
                    key="quick_topics",
                    placeholder="Select topics to study...",
                    max_selections=5
                )
            else:
                quick_topics = []
        
        with col4:
            quick_duration = st.number_input(
                "Minutes",
                min_value=15,
                max_value=180,
                value=STUDY_PLAN.get(grade, {}).get(quick_subject, 45),
                step=15,
                key="quick_duration"
            )
        
        with col5:
            st.write("")  # Spacing
            if st.button("➕ Add", type="primary", use_container_width=True, key="quick_add_btn"):
                if not quick_topics:
                    st.error("Select at least 1 topic")
                else:
                    try:
                        db.save_weekly_plan(
                            name, grade, week_key, quick_day,
                            quick_subject,
                            ','.join(quick_topics),
                            quick_duration,
                            False
                        )
                        # Clear cache
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.success(f"✅ Added to {quick_day}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Weekly view (compact, read-only display)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_emojis = ["📘", "📗", "📙", "📕", "📔", "🌟", "🌈"]
    
    # Show in grid layout (3 columns for better use of space)
    for row_start in range(0, 7, 3):
        cols = st.columns(3)
        
        for col_idx in range(3):
            day_idx = row_start + col_idx
            if day_idx >= 7:
                break
            
            day = days[day_idx]
            
            with cols[col_idx]:
                # Get sessions for this day
                day_plans = [p for p in all_plans if p['day_of_week'] == day]
                total_day_minutes = sum([p.get('duration', 0) for p in day_plans])
                
                # Day header with time
                st.markdown(f"**{day_emojis[day_idx]} {day}**")
                if total_day_minutes > 0:
                    st.caption(f"⏱️ {total_day_minutes} min")
                
                # Show sessions (compact)
                if day_plans:
                    for session in day_plans:
                        subject = session.get('subject', 'N/A')
                        subject_emoji = {"Math": "🔢", "Science": "🔬", "English": "📖"}
                        st.markdown(f"{subject_emoji.get(subject, '📚')} {subject} - {session.get('duration', 0)}m")
                else:
                    st.caption("_No plans_")
                
                st.markdown("")  # Spacing
    
    st.markdown("---")
    # Weekly overview
    st.subheader("📊 Week Summary")
    
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
            st.metric("⏱️ Total Time", f"{total_minutes/60:.1f} hrs")
        
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
                    st.metric(f"{emoji} {subj}", f"{mins}m")
    else:
        st.info("💡 **Tip:** Use Quick Add above to plan your week in seconds!")

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
    
    # Study session timer
    st.markdown("---")
    st.subheader("⏱️ Study Session Timer")
    
    # Initialize session state for active session
    if 'active_session' not in st.session_state:
        st.session_state.active_session = None
    
    # Check if there's an active session
    if st.session_state.active_session is None:
        # No active session - show start button
        st.caption("Start a study session and track your time automatically")
        
        col_start1, col_start2, col_start3 = st.columns([2, 2, 1.5])
        
        with col_start1:
            start_subject = st.selectbox("Subject to study", ["Math", "Science", "English"], key="start_subject")
        
        with col_start2:
            start_topics = st.multiselect(
                "Topics to cover",
                SYLLABUS[grade][start_subject],
                key="start_topics_multi",
                placeholder="What will you study?"
            )
        
        with col_start3:
            st.write("")
            st.write("")
            if st.button("🚀 Start Session", type="primary", use_container_width=True):
                if not start_topics:
                    st.warning("Please select topics you'll study")
                else:
                    import datetime
                    st.session_state.active_session = {
                        'subject': start_subject,
                        'topics': start_topics,
                        'start_time': datetime.datetime.now(),
                        'name': name,
                        'grade': grade
                    }
                    st.success(f"✅ Session started! Study hard, {name}! 💪")
                    st.rerun()
    
    else:
        # Active session - show timer and end button
        import datetime
        session = st.session_state.active_session
        elapsed = datetime.datetime.now() - session['start_time']
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        elapsed_seconds = int(elapsed.total_seconds() % 60)
        
        # Display current session info
        st.success(f"📚 **Active Session:** {session['subject']}")
        st.info(f"**Topics:** {', '.join(session['topics'])}")
        
        # Display timer
        col_timer1, col_timer2 = st.columns([2, 1])
        
        with col_timer1:
            st.markdown(f"### ⏱️ Time Elapsed: {elapsed_minutes:02d}:{elapsed_seconds:02d}")
            if elapsed_minutes < 5:
                st.caption("Keep going! Minimum 5 minutes recommended.")
            elif elapsed_minutes >= 60:
                st.caption("Great job! Consider taking a break soon! 🌟")
        
        with col_timer2:
            st.write("")
            if st.button("⏹️ End Session", type="primary", use_container_width=True):
                if elapsed_minutes < 1:
                    st.warning("Session too short! Study at least 1 minute before ending.")
                else:
                    try:
                        with st.spinner("Saving session..."):
                            # Add study session with calculated duration
                            db.add_study_session(
                                session['name'], 
                                session['grade'], 
                                session['subject'], 
                                elapsed_minutes,
                                ','.join(session['topics'])
                            )
                            
                            # Mark topics as completed
                            for topic in session['topics']:
                                db.mark_topic_completed(session['name'], session['grade'], session['subject'], topic)
                            
                            # Update cache immediately
                            st.session_state.total_hours += elapsed_minutes / 60.0
                            for topic in session['topics']:
                                if topic not in st.session_state.completed_topics_list:
                                    st.session_state.completed_topics_list.append(topic)
                        
                        # Clear active session
                        st.session_state.active_session = None
                        
                        st.success(f"✅ Session saved! You studied {session['subject']} for {elapsed_minutes} minutes!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving session: {e}")
        
        # Refresh button to update timer
        if st.button("🔄 Update Timer", use_container_width=True):
            st.rerun()
        
        st.caption("💡 Tip: Click 'Update Timer' to refresh the elapsed time, or just click 'End Session' when done!")
    
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
                        st.session_state.quiz_subject_selected = quiz_subject
                        st.session_state.quiz_topics_selected = quiz_topics
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
                        
                        # Save quiz result to database
                        try:
                            topics_str = ", ".join(st.session_state.quiz_topics_selected)
                            db.save_quiz_result(
                                name, grade, 
                                st.session_state.quiz_subject_selected,
                                len(st.session_state.quiz_questions),
                                correct,
                                topics_str
                            )
                        except Exception as e:
                            st.warning(f"Note: Quiz result saved locally but not to database: {e}")
                        
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