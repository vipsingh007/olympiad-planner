import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from datetime import datetime
import time
import bcrypt
import re

# Database connection with retry logic
def get_db_connection():
    """Create database connection with optimized settings (Olympic Planner)"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                st.secrets["database"]["url"],
                cursor_factory=RealDictCursor,
                connect_timeout=5
            )
            return conn
        except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                raise Exception(f"Database connection failed: {str(e)}")

def get_gyaan_db_connection():
    """Create database connection for Online Gyaan platform (uses same database as Olympic Planner)"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            # Use the same database connection as Olympic Planner
            conn = psycopg2.connect(
                st.secrets["database"]["url"],
                cursor_factory=RealDictCursor,
                connect_timeout=5
            )
            return conn
        except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                raise Exception(f"Online Gyaan database connection failed: {str(e)}")

def initialize_database():
    """Initialize all database tables including multi-tenant support"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create families table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS families (
                family_id SERIAL PRIMARY KEY,
                family_name VARCHAR(100),
                parent_email VARCHAR(255) UNIQUE NOT NULL,
                parent_password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create students table (if not exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100) NOT NULL,
                grade VARCHAR(20) NOT NULL,
                total_hours DECIMAL DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Add family_id to students table if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='students' AND column_name='family_id'
                ) THEN
                    ALTER TABLE students ADD COLUMN family_id INTEGER REFERENCES families(family_id);
                END IF;
            END $$;
        """)
        
        # Drop old unique constraint if it exists (for multi-tenant support)
        cur.execute("""
            DO $$ 
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'students_student_name_grade_key'
                ) THEN
                    ALTER TABLE students DROP CONSTRAINT students_student_name_grade_key;
                END IF;
            END $$;
        """)
        
        # Add new unique constraint for multi-tenant (student_name + grade + family_id)
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'students_name_grade_family_unique'
                ) THEN
                    ALTER TABLE students ADD CONSTRAINT students_name_grade_family_unique 
                    UNIQUE (student_name, grade, family_id);
                END IF;
            END $$;
        """)
        
        # Create completed_topics table (if not exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS completed_topics (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                topic TEXT,
                subject VARCHAR(50),
                completed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create study_sessions table (if not exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                topics TEXT,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create weekly_plans table (if not exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weekly_plans (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                week_start DATE,
                day_of_week VARCHAR(20),
                subjects TEXT[],
                topics TEXT[],
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(student_name, grade, week_start, day_of_week)
            )
        """)
        
        # Create quiz_results table (if not exists)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                score INTEGER,
                num_questions INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create preset_topics table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS preset_topics (
                id SERIAL PRIMARY KEY,
                grade VARCHAR(20),
                subject VARCHAR(50),
                topic TEXT,
                difficulty VARCHAR(20),
                estimated_hours DECIMAL,
                description TEXT
            )
        """)
        
        # Create mock_tests table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mock_tests (
                id SERIAL PRIMARY KEY,
                grade VARCHAR(20),
                subject VARCHAR(50),
                test_name TEXT,
                questions JSONB,
                difficulty VARCHAR(20)
            )
        """)
        
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database initialization failed: {str(e)}")
    finally:
        if conn:
            conn.close()

# Authentication operations
def create_family(email, password, family_name):
    """Create a new family account"""
    conn = None
    try:
        # Validate email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        # Validate password
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO families (parent_email, parent_password_hash, family_name) VALUES (%s, %s, %s) RETURNING family_id",
            (email.lower(), password_hash, family_name)
        )
        family_id = cur.fetchone()['family_id']
        conn.commit()
        cur.close()
        
        return family_id
    except psycopg2.errors.UniqueViolation:
        raise ValueError("Email already registered")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Failed to create family: {str(e)}")
    finally:
        if conn:
            conn.close()

def authenticate_family(email, password):
    """Authenticate family login"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT family_id, parent_password_hash, family_name FROM families WHERE parent_email = %s",
            (email.lower(),)
        )
        result = cur.fetchone()
        cur.close()
        
        if not result:
            return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), result['parent_password_hash'].encode('utf-8')):
            return {
                'family_id': result['family_id'],
                'family_name': result['family_name'],
                'email': email
            }
        return None
    finally:
        if conn:
            conn.close()

def get_family_students(family_id):
    """Get all students for a family"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT DISTINCT student_name, grade FROM students WHERE family_id = %s ORDER BY grade, student_name",
            (family_id,)
        )
        students = cur.fetchall()
        cur.close()
        
        return [dict(s) for s in students]
    finally:
        if conn:
            conn.close()

def add_student_to_family(family_id, student_name, grade):
    """Add a student to a family"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if student already exists for this family
        cur.execute(
            "SELECT id FROM students WHERE student_name = %s AND grade = %s AND family_id = %s",
            (student_name, grade, family_id)
        )
        existing = cur.fetchone()
        
        if existing:
            cur.close()
            return existing['id']
        
        # Add new student
        cur.execute(
            "INSERT INTO students (student_name, grade, family_id) VALUES (%s, %s, %s) RETURNING id",
            (student_name, grade, family_id)
        )
        student_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        
        return student_id
    finally:
        if conn:
            conn.close()

# Student operations
def get_or_create_student(name, grade, family_id=None):
    """Get student or create if doesn't exist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if family_id:
            cur.execute(
                "SELECT * FROM students WHERE student_name = %s AND grade = %s AND family_id = %s",
                (name, grade, family_id)
            )
        else:
            # Backward compatibility for existing users without family_id
            cur.execute(
                "SELECT * FROM students WHERE student_name = %s AND grade = %s AND family_id IS NULL",
                (name, grade)
            )
        student = cur.fetchone()
        
        if not student:
            cur.execute(
                "INSERT INTO students (student_name, grade, family_id) VALUES (%s, %s, %s) RETURNING *",
                (name, grade, family_id)
            )
            student = cur.fetchone()
            conn.commit()
        
        cur.close()
        return dict(student) if student else None
    finally:
        if conn:
            conn.close()

def update_student_stats(name, grade, total_hours=None, streak_days=None):
    """Update student statistics"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if total_hours is not None:
            cur.execute(
                "UPDATE students SET total_hours = %s WHERE student_name = %s AND grade = %s",
                (total_hours, name, grade)
            )
        
        if streak_days is not None:
            cur.execute(
                "UPDATE students SET streak_days = %s WHERE student_name = %s AND grade = %s",
                (streak_days, name, grade)
            )
        
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

# Topic operations
def get_completed_topics(name, grade):
    """Get all completed topics for a student"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT topic, subject FROM completed_topics WHERE student_name = %s AND grade = %s",
            (name, grade)
        )
        topics = cur.fetchall()
        cur.close()
        
        return [dict(t) for t in topics]
    finally:
        if conn:
            conn.close()

def mark_topic_completed(name, grade, subject, topic):
    """Mark a topic as completed"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO completed_topics (student_name, grade, subject, topic)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (student_name, grade, subject, topic) DO NOTHING""",
            (name, grade, subject, topic)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

def unmark_topic(name, grade, subject, topic):
    """Remove topic from completed list"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "DELETE FROM completed_topics WHERE student_name = %s AND grade = %s AND subject = %s AND topic = %s",
            (name, grade, subject, topic)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

# Study session operations
def add_study_session(name, grade, subject, duration, topics=None):
    """Log a study session"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO study_sessions (student_name, grade, subject, duration_minutes, topics)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, grade, subject, duration, topics)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

def get_recent_study_sessions(name, grade, limit=10):
    """Get recent study sessions for a student"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """SELECT created_at, subject, duration_minutes, topics 
               FROM study_sessions 
               WHERE student_name = %s AND grade = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (name, grade, limit)
        )
        sessions = cur.fetchall()
        cur.close()
        
        return [dict(s) for s in sessions]
    finally:
        if conn:
            conn.close()

def get_student_insights(name, grade):
    """
    Generate insights about student's study patterns
    Returns analysis of sessions, quiz performance, and subject balance
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        insights = {}
        
        # Get all sessions for last 30 days
        cur.execute("""
            SELECT subject, duration_minutes, created_at
            FROM study_sessions 
            WHERE student_name = %s AND grade = %s 
            AND created_at >= NOW() - INTERVAL '30 days'
            ORDER BY created_at DESC
        """, (name, grade))
        all_sessions = cur.fetchall()
        
        # Get sessions by subject for last 14 days
        cur.execute("""
            SELECT subject, COUNT(*) as session_count, SUM(duration_minutes) as total_minutes
            FROM study_sessions 
            WHERE student_name = %s AND grade = %s 
            AND created_at >= NOW() - INTERVAL '14 days'
            GROUP BY subject
        """, (name, grade))
        recent_by_subject = cur.fetchall()
        
        # Get quiz performance trend (last 10 quizzes)
        cur.execute("""
            SELECT score, num_questions, subject, created_at
            FROM quiz_results 
            WHERE student_name = %s AND grade = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (name, grade))
        quiz_results = cur.fetchall()
        
        # Get last session date
        cur.execute("""
            SELECT MAX(created_at) as last_session
            FROM study_sessions 
            WHERE student_name = %s AND grade = %s
        """, (name, grade))
        last_session_result = cur.fetchone()
        
        cur.close()
        
        insights['all_sessions'] = [dict(s) for s in all_sessions]
        insights['recent_by_subject'] = {s['subject']: dict(s) for s in recent_by_subject}
        insights['quiz_results'] = [dict(q) for q in quiz_results] if quiz_results else []
        insights['last_session_date'] = last_session_result['last_session'] if last_session_result else None
        
        return insights
        
    finally:
        if conn:
            conn.close()

def get_total_study_hours(name, grade):
    """Calculate total study hours from sessions"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM study_sessions WHERE student_name = %s AND grade = %s",
            (name, grade)
        )
        result = cur.fetchone()
        cur.close()
        
        return float(result['total']) / 60.0 if result else 0.0
    finally:
        if conn:
            conn.close()

# Weekly plan operations
def save_weekly_plan(name, grade, week_key, day, subject, topics, duration, completed):
    """Save weekly plan - allows multiple sessions per day"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO weekly_plans (student_name, grade, week_key, day_of_week, subject, topics, duration, completed)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, grade, week_key, day, subject, topics, duration, completed)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

def get_weekly_plan(name, grade, week_key):
    """Get weekly plan for a student"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT * FROM weekly_plans WHERE student_name = %s AND grade = %s AND week_key = %s",
            (name, grade, week_key)
        )
        plans = cur.fetchall()
        cur.close()
        
        return [dict(p) for p in plans]
    finally:
        if conn:
            conn.close()

# Quiz operations
def save_quiz_result(name, grade, subject, num_questions, score, topics):
    """Save quiz result to database"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                num_questions INTEGER,
                score INTEGER,
                topics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert quiz result
        cur.execute(
            """INSERT INTO quiz_results (student_name, grade, subject, num_questions, score, topics)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (name, grade, subject, num_questions, score, topics)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

def get_quiz_results(name, grade, limit=10):
    """Get recent quiz results for a student"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                num_questions INTEGER,
                score INTEGER,
                topics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cur.execute(
            """SELECT subject, num_questions, score, topics, created_at 
               FROM quiz_results 
               WHERE student_name = %s AND grade = %s 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (name, grade, limit)
        )
        results = cur.fetchall()
        cur.close()
        
        return [dict(r) for r in results]
    finally:
        if conn:
            conn.close()

def get_quiz_stats(name, grade):
    """Get quiz statistics for a student"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                num_questions INTEGER,
                score INTEGER,
                topics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cur.execute(
            """SELECT 
                COUNT(*) as total_quizzes,
                AVG(CAST(score AS FLOAT) / CAST(num_questions AS FLOAT) * 100) as avg_percentage
               FROM quiz_results 
               WHERE student_name = %s AND grade = %s""",
            (name, grade)
        )
        stats = cur.fetchone()
        cur.close()
        
        return dict(stats) if stats else {"total_quizzes": 0, "avg_percentage": 0}
    finally:
        if conn:
            conn.close()

# Bulk loading for parent dashboard (optimized)
def get_student_dashboard_data(student_list):
    """
    Load all dashboard data for multiple students in one connection.
    Much faster than calling individual functions.
    
    Args:
        student_list: List of tuples [(name, grade), ...]
    
    Returns:
        Dictionary with all data for each student
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Ensure quiz_results table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id SERIAL PRIMARY KEY,
                student_name VARCHAR(100),
                grade VARCHAR(20),
                subject VARCHAR(50),
                num_questions INTEGER,
                score INTEGER,
                topics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        result = {}
        
        for name, grade in student_list:
            # Get/create student
            cur.execute(
                "SELECT * FROM students WHERE student_name = %s AND grade = %s",
                (name, grade)
            )
            student_data = cur.fetchone()
            
            if not student_data:
                cur.execute(
                    "INSERT INTO students (student_name, grade) VALUES (%s, %s) RETURNING *",
                    (name, grade)
                )
                student_data = cur.fetchone()
                conn.commit()
            
            # Get completed topics
            cur.execute(
                "SELECT topic, subject FROM completed_topics WHERE student_name = %s AND grade = %s",
                (name, grade)
            )
            completed_topics = cur.fetchall()
            
            # Get total study hours (convert minutes to hours)
            cur.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM study_sessions WHERE student_name = %s AND grade = %s",
                (name, grade)
            )
            hours_result = cur.fetchone()
            total_hours = (hours_result['total'] / 60.0) if hours_result else 0
            
            # Get quiz stats
            cur.execute(
                """SELECT 
                    COUNT(*) as total_quizzes,
                    AVG(CAST(score AS FLOAT) / CAST(num_questions AS FLOAT) * 100) as avg_percentage
                   FROM quiz_results 
                   WHERE student_name = %s AND grade = %s""",
                (name, grade)
            )
            quiz_stats_result = cur.fetchone()
            quiz_stats = dict(quiz_stats_result) if quiz_stats_result else {"total_quizzes": 0, "avg_percentage": 0}
            
            # Store all data for this student
            result[f"{name}_{grade}"] = {
                'student_data': dict(student_data) if student_data else None,
                'completed_topics': [dict(t) for t in completed_topics],
                'total_hours': total_hours,
                'quiz_stats': quiz_stats
            }
        
        cur.close()
        return result
        
    finally:
        if conn:
            conn.close()

# Preset content operations
def populate_preset_content(syllabus_data):
    """Populate preset topics from syllabus data (one-time operation)"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if already populated
        cur.execute("SELECT COUNT(*) as count FROM preset_topics")
        result = cur.fetchone()
        if result['count'] > 0:
            cur.close()
            return False  # Already populated
        
        # Define difficulty and estimated hours for topics
        hours_mapping = {
            "Easy": 1.0,
            "Medium": 1.5,
            "Hard": 2.0
        }
        
        # Auto-assign difficulty based on grade level
        def auto_assign_difficulty(grade_str, num_topics):
            """Assign difficulty mix based on grade level"""
            grade_num = int(grade_str.replace("Grade ", ""))
            
            if grade_num <= 2:
                # Grades 1-2: Mostly Easy
                return ["Easy"] * num_topics
            elif grade_num <= 4:
                # Grades 3-4: Mix of Easy and Medium
                pattern = ["Easy", "Medium"] * (num_topics // 2)
                if num_topics % 2:
                    pattern.append("Easy")
                return pattern[:num_topics]
            elif grade_num <= 6:
                # Grades 5-6: Mostly Medium with some Hard
                pattern = ["Medium", "Medium", "Hard"] * (num_topics // 3)
                pattern.extend(["Medium"] * (num_topics % 3))
                return pattern[:num_topics]
            elif grade_num <= 8:
                # Grades 7-8: Medium and Hard
                pattern = ["Medium", "Hard"] * (num_topics // 2)
                if num_topics % 2:
                    pattern.append("Medium")
                return pattern[:num_topics]
            else:
                # Grades 9-12: Mostly Hard with some Medium
                pattern = ["Hard", "Hard", "Medium"] * (num_topics // 3)
                pattern.extend(["Hard"] * (num_topics % 3))
                return pattern[:num_topics]
        
        # Insert topics
        for grade, subjects in syllabus_data.items():
            for subject, topics in subjects.items():
                difficulties = auto_assign_difficulty(grade, len(topics))
                for i, topic in enumerate(topics):
                    difficulty = difficulties[i]
                    estimated_hours = hours_mapping.get(difficulty, 1.5)
                    
                    cur.execute(
                        """INSERT INTO preset_topics (grade, subject, topic, difficulty, estimated_hours)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (grade, subject, topic, difficulty, estimated_hours)
                    )
        
        conn.commit()
        cur.close()
        return True  # Successfully populated
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Failed to populate preset content: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_preset_topics(grade, subject=None, difficulty=None):
    """Get preset topics filtered by grade, subject, and/or difficulty"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = "SELECT * FROM preset_topics WHERE grade = %s"
        params = [grade]
        
        if subject:
            query += " AND subject = %s"
            params.append(subject)
        
        if difficulty:
            query += " AND difficulty = %s"
            params.append(difficulty)
        
        query += " ORDER BY subject, topic"
        
        cur.execute(query, params)
        topics = cur.fetchall()
        cur.close()
        
        return [dict(t) for t in topics]
    finally:
        if conn:
            conn.close()

def get_preset_topics_count():
    """Get count of preset topics to check if populated"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) as count FROM preset_topics")
        result = cur.fetchone()
        cur.close()
        
        return result['count'] if result else 0
    finally:
        if conn:
            conn.close()


# ============================================
# ONLINE GYAAN - Learning Platform Functions
# ============================================

def initialize_online_gyaan_db():
    """Initialize database tables for Online Gyaan platform"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        # Users table (for all user types)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name VARCHAR(200) NOT NULL,
                user_type VARCHAR(20) NOT NULL,
                phone VARCHAR(20),
                grade VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Teachers table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_teachers (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES gyaan_users(id),
                subjects TEXT[],
                bio TEXT,
                rating DECIMAL DEFAULT 0,
                total_classes INTEGER DEFAULT 0,
                total_students INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Classes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_classes (
                id SERIAL PRIMARY KEY,
                title VARCHAR(300) NOT NULL,
                description TEXT,
                subject VARCHAR(100),
                grade VARCHAR(50),
                teacher_id INTEGER REFERENCES gyaan_teachers(id),
                class_date DATE NOT NULL,
                class_time TIME NOT NULL,
                duration_minutes INTEGER NOT NULL,
                max_students INTEGER DEFAULT 30,
                price DECIMAL DEFAULT 0,
                meeting_link TEXT,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Subscriptions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_subscriptions (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES gyaan_users(id),
                class_id INTEGER REFERENCES gyaan_classes(id),
                subscription_date TIMESTAMP DEFAULT NOW(),
                payment_status VARCHAR(20) DEFAULT 'pending',
                payment_id TEXT,
                UNIQUE(student_id, class_id)
            )
        """)
        
        # Attendance table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES gyaan_users(id),
                class_id INTEGER REFERENCES gyaan_classes(id),
                attended BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Certificates table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gyaan_certificates (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES gyaan_users(id),
                class_id INTEGER REFERENCES gyaan_classes(id),
                certificate_title TEXT,
                issued_date DATE DEFAULT CURRENT_DATE,
                certificate_url TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Database initialization failed: {str(e)}")
    finally:
        if conn:
            conn.close()

# User authentication
def create_gyaan_user(email, password, name, user_type, phone=None, grade=None):
    """Create a new user for Online Gyaan"""
    conn = None
    try:
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO gyaan_users (email, password_hash, name, user_type, phone, grade)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (email.lower(), password_hash, name, user_type, phone, grade)
        )
        user_id = cur.fetchone()['id']
        
        # If user is a teacher, also create teacher profile
        if user_type == 'teacher':
            cur.execute(
                """INSERT INTO gyaan_teachers (user_id, subjects, bio)
                   VALUES (%s, %s, %s) RETURNING id""",
                (user_id, ['General'], 'New teacher on Online Gyaan')
            )
        
        conn.commit()
        cur.close()
        
        return user_id
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Failed to create user: {str(e)}")
    finally:
        if conn:
            conn.close()

def authenticate_gyaan_user(email, password):
    """Authenticate user login"""
    conn = None
    try:
        import bcrypt
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT id, email, password_hash, name, user_type, phone, grade FROM gyaan_users WHERE email = %s AND is_active = TRUE",
            (email.lower(),)
        )
        result = cur.fetchone()
        cur.close()
        
        if not result:
            return None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), result['password_hash'].encode('utf-8')):
            return {
                'id': result['id'],
                'email': result['email'],
                'name': result['name'],
                'user_type': result['user_type'],
                'phone': result['phone'],
                'grade': result['grade']
            }
        return None
    finally:
        if conn:
            conn.close()

# Class management
def schedule_class(title, description, subject, grade, teacher_id, class_date, class_time, duration_minutes, max_students, price):
    """Schedule a new class"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO gyaan_classes (title, description, subject, grade, teacher_id, class_date, class_time, duration_minutes, max_students, price)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (title, description, subject, grade, teacher_id, class_date, class_time, duration_minutes, max_students, price)
        )
        class_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        
        return class_id
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Failed to schedule class: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_all_classes(status=None, teacher_id=None):
    """Get all classes with optional filters"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT c.*, t.user_id, u.name as teacher_name
            FROM gyaan_classes c
            JOIN gyaan_teachers t ON c.teacher_id = t.id
            JOIN gyaan_users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND c.status = %s"
            params.append(status)
        
        if teacher_id:
            query += " AND c.teacher_id = %s"
            params.append(teacher_id)
        
        query += " ORDER BY c.class_date DESC, c.class_time DESC"
        
        cur.execute(query, params)
        classes = cur.fetchall()
        cur.close()
        
        return [dict(c) for c in classes]
    finally:
        if conn:
            conn.close()

def subscribe_to_class(student_id, class_id, payment_id=None):
    """Subscribe student to a class"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO gyaan_subscriptions (student_id, class_id, payment_id, payment_status)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (student_id, class_id, payment_id, 'completed' if payment_id else 'pending')
        )
        subscription_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        
        return subscription_id
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Failed to subscribe: {str(e)}")
    finally:
        if conn:
            conn.close()

def get_student_classes(student_id):
    """Get all classes a student is subscribed to"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT c.*, u.name as teacher_name, s.subscription_date
            FROM gyaan_classes c
            JOIN gyaan_subscriptions s ON c.id = s.class_id
            JOIN gyaan_teachers t ON c.teacher_id = t.id
            JOIN gyaan_users u ON t.user_id = u.id
            WHERE s.student_id = %s AND s.payment_status = 'completed'
            ORDER BY c.class_date, c.class_time
        """, (student_id,))
        
        classes = cur.fetchall()
        cur.close()
        
        return [dict(c) for c in classes]
    finally:
        if conn:
            conn.close()

def mark_attendance(student_id, class_id, attended=True, duration_minutes=0):
    """Mark student attendance for a class"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            """INSERT INTO gyaan_attendance (student_id, class_id, attended, joined_at, duration_minutes)
               VALUES (%s, %s, %s, NOW(), %s)
               ON CONFLICT (student_id, class_id) 
               DO UPDATE SET attended = %s, duration_minutes = %s""",
            (student_id, class_id, attended, duration_minutes, attended, duration_minutes)
        )
        conn.commit()
        cur.close()
    finally:
        if conn:
            conn.close()

def get_class_students(class_id):
    """Get all students enrolled in a class"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT u.id, u.name, u.email, s.subscription_date, 
                   a.attended, a.duration_minutes
            FROM gyaan_users u
            JOIN gyaan_subscriptions s ON u.id = s.student_id
            LEFT JOIN gyaan_attendance a ON u.id = a.student_id AND a.class_id = %s
            WHERE s.class_id = %s AND s.payment_status = 'completed'
            ORDER BY u.name
        """, (class_id, class_id))
        
        students = cur.fetchall()
        cur.close()
        
        return [dict(s) for s in students]
    finally:
        if conn:
            conn.close()

def get_all_teachers():
    """Get all registered teachers"""
    conn = None
    try:
        conn = get_gyaan_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT t.id, t.user_id, u.name, u.email, t.subjects, t.bio, 
                   t.rating, t.total_classes, t.total_students
            FROM gyaan_teachers t
            JOIN gyaan_users u ON t.user_id = u.id
            WHERE u.is_active = TRUE
            ORDER BY u.name
        """)
        
        teachers = cur.fetchall()
        cur.close()
        
        return [dict(t) for t in teachers]
    finally:
        if conn:
            conn.close()
