import streamlit as st
from datetime import datetime, timedelta
import database as db
import json
import hashlib

st.set_page_config(page_title="🎓 Online Gyaan", layout="wide", page_icon="🎓")

# Initialize database on first run
if 'db_initialized_gyaan' not in st.session_state:
    try:
        db.initialize_online_gyaan_db()
        st.session_state.db_initialized_gyaan = True
    except Exception as e:
        st.error(f"Database initialization error: {e}")

# Add custom CSS for better UI
st.markdown("""
    <style>
    .class-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .live-badge {
        background-color: #ff4444;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .upcoming-badge {
        background-color: #4CAF50;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# Authentication page
if not st.session_state.authenticated:
    st.title("🎓 Online Gyaan - Learn Anywhere")
    st.markdown("### Welcome to the Future of Learning")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2, tab3 = st.tabs(["👨‍🎓 Student Login", "👨‍🏫 Teacher Login", "👤 Admin Login"])
        
        # STUDENT LOGIN
        with tab1:
            st.markdown("#### Student Portal")
            student_email = st.text_input("Email", key="student_email", placeholder="student@example.com")
            student_password = st.text_input("Password", type="password", key="student_pass")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("🎓 Login as Student", type="primary", use_container_width=True):
                    # TODO: Replace with actual authentication
                    if student_email and student_password:
                        st.session_state.authenticated = True
                        st.session_state.user_type = "student"
                        st.session_state.user_data = {
                            "email": student_email,
                            "name": student_email.split('@')[0].title(),
                            "id": 1
                        }
                        st.success("✅ Welcome!")
                        st.rerun()
                    else:
                        st.error("Please enter credentials")
            
            with col_s2:
                if st.button("📝 Sign Up", use_container_width=True):
                    st.info("Signup feature coming soon!")
        
        # TEACHER LOGIN
        with tab2:
            st.markdown("#### Teacher Portal")
            teacher_email = st.text_input("Email", key="teacher_email", placeholder="teacher@example.com")
            teacher_password = st.text_input("Password", type="password", key="teacher_pass")
            
            if st.button("👨‍🏫 Login as Teacher", type="primary", use_container_width=True):
                # TODO: Replace with actual authentication
                if teacher_email and teacher_password:
                    st.session_state.authenticated = True
                    st.session_state.user_type = "teacher"
                    st.session_state.user_data = {
                        "email": teacher_email,
                        "name": teacher_email.split('@')[0].title(),
                        "id": 1
                    }
                    st.success("✅ Welcome Teacher!")
                    st.rerun()
                else:
                    st.error("Please enter credentials")
        
        # ADMIN LOGIN
        with tab3:
            st.markdown("#### Admin Portal")
            admin_email = st.text_input("Email", key="admin_email", placeholder="admin@example.com")
            admin_password = st.text_input("Password", type="password", key="admin_pass")
            
            if st.button("👤 Login as Admin", type="primary", use_container_width=True):
                # TODO: Replace with actual authentication
                if admin_email and admin_password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.user_type = "admin"
                    st.session_state.user_data = {
                        "email": admin_email,
                        "name": "Administrator",
                        "id": 1
                    }
                    st.success("✅ Welcome Admin!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    st.markdown("---")
    st.info("🎯 **Demo Credentials:** Use any email. Teacher/Student: any password. Admin: 'admin123'")
    st.stop()

# User is authenticated - show appropriate dashboard
user_type = st.session_state.user_type
user_data = st.session_state.user_data

# Sidebar with user info and logout
with st.sidebar:
    st.markdown(f"### 👋 {user_data['name']}")
    st.caption(f"Role: {user_type.title()}")
    st.caption(f"📧 {user_data['email']}")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_type = None
        st.session_state.user_data = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    if user_type == "student":
        st.metric("Subscribed Classes", "3")
        st.metric("Attended", "12")
        st.metric("Hours Learned", "18")
    elif user_type == "teacher":
        st.metric("Your Classes", "5")
        st.metric("Total Students", "45")
        st.metric("Classes This Week", "8")
    else:  # admin
        st.metric("Total Classes", "15")
        st.metric("Total Teachers", "8")
        st.metric("Total Students", "120")


# ADMIN DASHBOARD
if user_type == "admin":
    st.title("👤 Admin Dashboard")
    st.markdown("**Manage teachers, students, and schedule classes**")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "📅 Schedule Classes", 
        "👨‍🏫 Manage Teachers", 
        "👨‍🎓 Manage Students",
        "📊 Analytics"
    ])
    
    with admin_tab1:
        st.header("📅 Schedule New Class")
        
        col1, col2 = st.columns(2)
        
        with col1:
            class_title = st.text_input("Class Title", placeholder="e.g., Python Programming for Beginners")
            class_subject = st.selectbox("Subject", ["Mathematics", "Science", "English", "Coding", "Art", "Music"])
            class_teacher = st.selectbox("Assign Teacher", ["Dr. Amit Kumar", "Prof. Priya Sharma", "Mr. Rahul Verma"])
            class_grade = st.multiselect("Target Grades", ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10"])
        
        with col2:
            class_date = st.date_input("Class Date", min_value=datetime.now())
            class_time = st.time_input("Class Time", value=datetime.now().time())
            class_duration = st.number_input("Duration (minutes)", min_value=30, max_value=180, value=60, step=15)
            max_students = st.number_input("Max Students", min_value=1, max_value=100, value=30)
        
        class_description = st.text_area("Class Description", placeholder="What will students learn in this class?")
        
        if st.button("📅 Schedule Class", type="primary"):
            if class_title and class_description:
                st.success(f"✅ Class '{class_title}' scheduled successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields")
        
        st.markdown("---")
        st.subheader("📋 Upcoming Scheduled Classes")
        
        # Sample scheduled classes
        scheduled_classes = [
            {"title": "Python Basics", "teacher": "Dr. Amit Kumar", "date": "2024-12-01", "time": "10:00 AM", "students": 25},
            {"title": "Math Olympiad Prep", "teacher": "Prof. Priya Sharma", "date": "2024-12-02", "time": "2:00 PM", "students": 30},
            {"title": "Creative Writing", "teacher": "Mr. Rahul Verma", "date": "2024-12-03", "time": "4:00 PM", "students": 15},
        ]
        
        for idx, cls in enumerate(scheduled_classes):
            with st.expander(f"📚 {cls['title']} - {cls['date']} at {cls['time']}"):
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    st.write(f"**Teacher:** {cls['teacher']}")
                with col_c2:
                    st.write(f"**Students:** {cls['students']}/30")
                with col_c3:
                    if st.button("🗑️ Cancel", key=f"cancel_{idx}"):
                        st.warning("Class cancelled")
    
    with admin_tab2:
        st.header("👨‍🏫 Teacher Management")
        
        col_t1, col_t2 = st.columns([2, 1])
        
        with col_t1:
            st.subheader("Add New Teacher")
            new_teacher_name = st.text_input("Teacher Name")
            new_teacher_email = st.text_input("Email")
            new_teacher_subject = st.multiselect("Subjects", ["Math", "Science", "English", "Coding", "Art"])
            
            if st.button("➕ Add Teacher"):
                if new_teacher_name and new_teacher_email:
                    st.success(f"✅ Teacher {new_teacher_name} added!")
        
        with col_t2:
            st.metric("Total Teachers", "8")
            st.metric("Active Today", "5")
        
        st.markdown("---")
        st.subheader("👥 All Teachers")
        
        teachers = [
            {"name": "Dr. Amit Kumar", "subject": "Mathematics", "classes": 12, "students": 45, "rating": 4.8},
            {"name": "Prof. Priya Sharma", "subject": "Science", "classes": 15, "students": 52, "rating": 4.9},
            {"name": "Mr. Rahul Verma", "subject": "English", "classes": 10, "students": 38, "rating": 4.7},
        ]
        
        for teacher in teachers:
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
            with col1:
                st.write(f"**{teacher['name']}**")
            with col2:
                st.write(teacher['subject'])
            with col3:
                st.write(f"📚 {teacher['classes']}")
            with col4:
                st.write(f"👥 {teacher['students']}")
            with col5:
                st.write(f"⭐ {teacher['rating']}")
    
    with admin_tab3:
        st.header("👨‍🎓 Student Management")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Total Students", "120")
        with col_s2:
            st.metric("Active Today", "85")
        with col_s3:
            st.metric("New This Week", "12")
        
        st.markdown("---")
        
        search_student = st.text_input("🔍 Search Students", placeholder="Search by name or email")
        
        st.subheader("📋 All Students")
        
        students = [
            {"name": "Anaya Singh", "grade": "Grade 5", "classes": 8, "hours": 12, "joined": "2024-01-15"},
            {"name": "Rohan Kumar", "grade": "Grade 7", "classes": 12, "hours": 18, "joined": "2024-02-20"},
            {"name": "Priya Patel", "grade": "Grade 6", "classes": 10, "hours": 15, "joined": "2024-03-10"},
        ]
        
        for student in students:
            with st.expander(f"👤 {student['name']} - {student['grade']}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Classes:** {student['classes']}")
                with col2:
                    st.write(f"**Hours:** {student['hours']}")
                with col3:
                    st.write(f"**Joined:** {student['joined']}")
                with col4:
                    if st.button("View Details", key=f"view_{student['name']}"):
                        st.info("Student details...")
    
    with admin_tab4:
        st.header("📊 Platform Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Classes This Month", "45", "+12")
        with col2:
            st.metric("Total Students", "120", "+18")
        with col3:
            st.metric("Active Teachers", "8", "+2")
        with col4:
            st.metric("Avg Rating", "4.7", "+0.2")
        
        st.markdown("---")
        
        st.subheader("📈 Monthly Trends")
        st.line_chart({"Classes": [20, 25, 30, 35, 45], "Students": [80, 90, 100, 110, 120]})


# TEACHER DASHBOARD
elif user_type == "teacher":
    st.title("👨‍🏫 Teacher Dashboard")
    st.markdown(f"**Welcome back, {user_data['name']}!**")
    
    teacher_tab1, teacher_tab2, teacher_tab3, teacher_tab4 = st.tabs([
        "🎥 My Classes",
        "📅 Schedule",
        "👥 Students",
        "📊 Performance"
    ])
    
    with teacher_tab1:
        st.header("🎥 My Classes")
        
        # Live class indicator
        st.markdown('<span class="live-badge">🔴 LIVE NOW</span>', unsafe_allow_html=True)
        st.markdown("### Python Programming - Basics")
        
        col_live1, col_live2 = st.columns([3, 1])
        
        with col_live1:
            st.markdown("""
            **Current Class:** Python Programming Fundamentals  
            **Time:** 10:00 AM - 11:00 AM  
            **Students Joined:** 28/30  
            **Duration:** 35 minutes elapsed
            """)
            
            # Jitsi Video Streaming Integration
            st.markdown("### 🎥 Live Video Stream")
            
            # Generate unique meeting room ID
            class_room_id = hashlib.md5(f"python_basics_teacher".encode()).hexdigest()[:12]
            jitsi_url = f"https://meet.jit.si/{class_room_id}"
            
            # Embed Jitsi meeting
            jitsi_html = f"""
            <iframe
                allow="camera; microphone; fullscreen; display-capture; autoplay"
                src="{jitsi_url}#userInfo.displayName='{user_data['name']}'&config.prejoinPageEnabled=false"
                style="height: 500px; width: 100%; border: 2px solid #4CAF50; border-radius: 8px;"
            ></iframe>
            """
            st.components.v1.html(jitsi_html, height=520)
            
            st.caption(f"🔗 **Meeting Link:** {jitsi_url}")
            st.caption("💡 Students can join using this link")
        
        with col_live2:
            st.markdown("**Live Chat**")
            st.text_area("Messages", value="Student1: Great explanation!\nStudent2: Can you repeat?", height=200, disabled=True)
            chat_msg = st.text_input("Type message...")
            if st.button("Send"):
                st.success("Message sent!")
        
        st.markdown("---")
        
        st.subheader("📚 Upcoming Classes")
        
        upcoming = [
            {"title": "Python - Functions", "date": "Tomorrow", "time": "10:00 AM", "students": 25},
            {"title": "Python - OOP Concepts", "date": "Dec 3", "time": "10:00 AM", "students": 22},
        ]
        
        for cls in upcoming:
            with st.expander(f"📖 {cls['title']} - {cls['date']} at {cls['time']}"):
                st.write(f"**Enrolled Students:** {cls['students']}")
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if st.button("✏️ Edit Class", key=f"edit_{cls['title']}"):
                        st.info("Edit class details...")
                with col_a2:
                    if st.button("🎥 Start Class", key=f"start_{cls['title']}", type="primary"):
                        st.success("Starting class...")
    
    with teacher_tab2:
        st.header("📅 My Schedule")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("This Week")
            
            schedule = [
                {"day": "Monday", "class": "Python Basics", "time": "10:00 AM", "duration": "60 min"},
                {"day": "Tuesday", "class": "Python Functions", "time": "10:00 AM", "duration": "60 min"},
                {"day": "Wednesday", "class": "Python OOP", "time": "10:00 AM", "duration": "60 min"},
                {"day": "Friday", "class": "Python Projects", "time": "10:00 AM", "duration": "90 min"},
            ]
            
            for item in schedule:
                st.markdown(f"""
                **{item['day']}** - {item['class']}  
                ⏰ {item['time']} ({item['duration']})
                """)
                st.markdown("---")
        
        with col2:
            st.subheader("Quick Stats")
            st.metric("Classes This Week", "4")
            st.metric("Next Class", "Tomorrow 10 AM")
            st.metric("Total Hours", "5.5")
    
    with teacher_tab3:
        st.header("👥 My Students")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Students", "45")
        with col2:
            st.metric("Avg Attendance", "92%")
        with col3:
            st.metric("Active Students", "38")
        
        st.markdown("---")
        
        st.subheader("📋 Student List")
        
        students = [
            {"name": "Anaya Singh", "attendance": "95%", "assignments": "8/10", "performance": "Excellent"},
            {"name": "Rohan Kumar", "attendance": "88%", "assignments": "9/10", "performance": "Very Good"},
            {"name": "Priya Patel", "attendance": "92%", "assignments": "7/10", "performance": "Good"},
        ]
        
        for student in students:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1.5])
            with col1:
                st.write(f"**{student['name']}**")
            with col2:
                st.write(f"📊 {student['attendance']}")
            with col3:
                st.write(f"📝 {student['assignments']}")
            with col4:
                st.write(student['performance'])
    
    with teacher_tab4:
        st.header("📊 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Rating", "4.8 ⭐", "+0.2")
        with col2:
            st.metric("Classes Completed", "45", "+5")
        with col3:
            st.metric("Student Satisfaction", "96%", "+3%")
        
        st.markdown("---")
        
        st.subheader("📈 Class Attendance Trend")
        st.line_chart([25, 28, 26, 30, 28, 29, 27])
        
        st.subheader("💬 Recent Feedback")
        st.success("⭐⭐⭐⭐⭐ 'Excellent teacher! Very clear explanations.' - Anaya")
        st.success("⭐⭐⭐⭐⭐ 'Best coding class ever!' - Rohan")


# STUDENT DASHBOARD
else:  # student
    st.title("🎓 Student Dashboard")
    st.markdown(f"**Welcome back, {user_data['name']}!**")
    
    student_tab1, student_tab2, student_tab3, student_tab4 = st.tabs([
        "🎥 My Classes",
        "📚 Browse Classes",
        "📊 Progress",
        "⚙️ Settings"
    ])
    
    with student_tab1:
        st.header("🎥 My Subscribed Classes")
        
        # Live class
        st.markdown('<span class="live-badge">🔴 LIVE NOW</span>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown("### Python Programming - Basics")
            st.markdown("**Teacher:** Dr. Amit Kumar | **Time:** 10:00 AM - 11:00 AM")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Jitsi Video for Students
                if st.button("🎥 Join Live Class", type="primary", use_container_width=True, key="join_live"):
                    st.session_state.show_video = True
                
                if st.session_state.get('show_video', False):
                    # Generate same meeting room ID as teacher
                    class_room_id = hashlib.md5(f"python_basics_teacher".encode()).hexdigest()[:12]
                    jitsi_url = f"https://meet.jit.si/{class_room_id}"
                    
                    # Embed Jitsi meeting for student
                    jitsi_html = f"""
                    <iframe
                        allow="camera; microphone; fullscreen; display-capture; autoplay"
                        src="{jitsi_url}#userInfo.displayName='{user_data['name']}'&config.prejoinPageEnabled=false"
                        style="height: 450px; width: 100%; border: 2px solid #4CAF50; border-radius: 8px;"
                    ></iframe>
                    """
                    st.components.v1.html(jitsi_html, height=470)
                    
                    if st.button("❌ Leave Class", key="leave_class"):
                        st.session_state.show_video = False
                        st.rerun()
                else:
                    st.info("📹 **Live Class Video Stream**\n\nClick 'Join Live Class' to start learning!")
                    st.balloons()
            
            with col2:
                st.markdown("**Class Info**")
                st.write("👥 28 students")
                st.write("⏱️ 35 min elapsed")
                st.write("📝 Materials available")
        
        st.markdown("---")
        
        st.subheader("📅 Upcoming Classes")
        
        upcoming = [
            {"title": "Math Olympiad Prep", "teacher": "Prof. Priya Sharma", "date": "Tomorrow", "time": "2:00 PM"},
            {"title": "Creative Writing", "teacher": "Mr. Rahul Verma", "date": "Dec 3", "time": "4:00 PM"},
            {"title": "Science Experiments", "teacher": "Dr. Meera Reddy", "date": "Dec 4", "time": "3:00 PM"},
        ]
        
        for cls in upcoming:
            with st.expander(f"📖 {cls['title']} - {cls['date']} at {cls['time']}"):
                st.write(f"**Teacher:** {cls['teacher']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📅 Add to Calendar", key=f"cal_{cls['title']}"):
                        st.info("Added to calendar")
                with col2:
                    if st.button("🔔 Set Reminder", key=f"rem_{cls['title']}"):
                        st.info("Reminder set")
    
    with student_tab2:
        st.header("📚 Browse & Subscribe to Classes")
        
        # Search and filter
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 Search classes", placeholder="Search by name or subject")
        with col2:
            filter_subject = st.selectbox("Subject", ["All", "Math", "Science", "English", "Coding", "Art"])
        with col3:
            filter_grade = st.selectbox("Grade", ["All", "Grade 1-5", "Grade 6-8", "Grade 9-10"])
        
        st.markdown("---")
        
        # Available classes
        available_classes = [
            {"title": "Advanced Python", "teacher": "Dr. Amit Kumar", "subject": "Coding", "grade": "Grade 8-10", "students": 15, "rating": 4.8, "price": "₹499/month"},
            {"title": "Math Olympiad Advanced", "teacher": "Prof. Priya Sharma", "subject": "Mathematics", "grade": "Grade 9-10", "students": 20, "rating": 4.9, "price": "₹599/month"},
            {"title": "English Literature", "teacher": "Ms. Sarah Thomas", "subject": "English", "grade": "Grade 6-8", "students": 25, "rating": 4.7, "price": "₹399/month"},
        ]
        
        for cls in available_classes:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(cls['title'])
                    st.write(f"👨‍🏫 **Teacher:** {cls['teacher']}")
                    st.write(f"📚 **Subject:** {cls['subject']} | **Grade:** {cls['grade']}")
                    st.write(f"👥 {cls['students']} students enrolled | ⭐ {cls['rating']}/5.0")
                
                with col2:
                    st.write("")
                    st.write("")
                    st.markdown(f"**{cls['price']}**")
                
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("💳 Subscribe", key=f"sub_{cls['title']}", type="primary"):
                        # Razorpay Payment Integration
                        st.session_state.payment_class = cls['title']
                        st.session_state.payment_amount = int(cls['price'].replace('₹','').replace('/month','').replace(',',''))
                        
                        # Generate Razorpay payment link
                        payment_amount = st.session_state.payment_amount * 100  # Convert to paise
                        
                        # Razorpay payment button HTML
                        razorpay_html = f"""
                        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                        <script>
                        var options = {{
                            "key": "rzp_test_YOUR_KEY_HERE", // Replace with your Razorpay key
                            "amount": "{payment_amount}", 
                            "currency": "INR",
                            "name": "Online Gyaan",
                            "description": "{cls['title']} Subscription",
                            "image": "https://example.com/logo.png",
                            "handler": function (response){{
                                alert('Payment successful! Payment ID: ' + response.razorpay_payment_id);
                                // Save payment ID to database
                            }},
                            "prefill": {{
                                "name": "{user_data['name']}",
                                "email": "{user_data['email']}",
                            }},
                            "theme": {{
                                "color": "#4CAF50"
                            }}
                        }};
                        var rzp1 = new Razorpay(options);
                        rzp1.open();
                        </script>
                        """
                        
                        # Show payment UI
                        st.info(f"💳 **Processing Payment for {cls['title']}**")
                        st.markdown(f"**Amount:** {cls['price']}")
                        st.markdown("---")
                        
                        # Payment method selection
                        payment_method = st.radio("Choose Payment Method:", 
                                                  ["Razorpay (Card/UPI/Netbanking)", "Demo Payment"], 
                                                  key=f"payment_{cls['title']}")
                        
                        if payment_method == "Demo Payment":
                            if st.button("✅ Complete Demo Payment", key=f"demo_pay_{cls['title']}"):
                                st.success(f"✅ Payment successful! Subscribed to {cls['title']}!")
                                st.balloons()
                                st.info("📧 Confirmation email sent!")
                        else:
                            st.markdown("**Razorpay Integration**")
                            st.code("""
# Add to requirements.txt:
# razorpay

# Razorpay Setup:
import razorpay
client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))

# Create Order:
order = client.order.create({
    "amount": 49900,  # Amount in paise
    "currency": "INR",
    "payment_capture": 1
})
                            """)
                            st.caption("💡 Replace YOUR_KEY with actual Razorpay keys")
                            
                            if st.button("🚀 Launch Razorpay Payment", key=f"rzp_{cls['title']}"):
                                st.components.v1.html(razorpay_html, height=0)
                                st.info("Payment window will open...")
                
                st.markdown("---")
    
    with student_tab3:
        st.header("📊 My Learning Progress")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Classes Attended", "12")
        with col2:
            st.metric("Total Hours", "18")
        with col3:
            st.metric("Avg Attendance", "95%")
        with col4:
            st.metric("Certificates", "3")
        
        st.markdown("---")
        
        st.subheader("📈 Attendance by Subject")
        st.bar_chart({"Math": 10, "Science": 8, "English": 7, "Coding": 12})
        
        st.markdown("---")
        
        st.subheader("🏆 Certificates Earned")
        
        certificates = [
            {"title": "Python Basics Completion", "date": "2024-10-15", "teacher": "Dr. Amit Kumar"},
            {"title": "Math Olympiad Participation", "date": "2024-09-20", "teacher": "Prof. Priya Sharma"},
        ]
        
        for cert in certificates:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🏅 **{cert['title']}**")
                st.caption(f"Issued by {cert['teacher']} on {cert['date']}")
            with col2:
                if st.button("📥 Download", key=f"cert_{cert['title']}"):
                    st.info("Downloading certificate...")
    
    with student_tab4:
        st.header("⚙️ Settings")
        
        st.subheader("👤 Profile")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Name", value=user_data['name'])
            st.text_input("Email", value=user_data['email'], disabled=True)
        with col2:
            st.selectbox("Grade", ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10"])
            st.text_input("Phone", placeholder="+91 98765 43210")
        
        if st.button("💾 Save Profile"):
            st.success("Profile updated!")
        
        st.markdown("---")
        
        st.subheader("🔔 Notification Preferences")
        st.checkbox("Email notifications for new classes", value=True)
        st.checkbox("Reminder before class starts (15 min)", value=True)
        st.checkbox("Weekly progress report", value=True)
        
        if st.button("💾 Save Preferences"):
            st.success("Preferences saved!")

st.markdown("---")
st.caption("© 2024 Online Gyaan - Empowering Education 🎓")

