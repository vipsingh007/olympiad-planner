import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from datetime import datetime

# Database connection
@st.cache_resource
def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        st.secrets["database"]["url"],
        cursor_factory=RealDictCursor
    )

# Student operations
def get_or_create_student(name, grade):
    """Get student or create if doesn't exist"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if student exists
    cur.execute(
        "SELECT * FROM students WHERE student_name = %s AND grade = %s",
        (name, grade)
    )
    student = cur.fetchone()
    
    if not student:
        # Create new student
        cur.execute(
            "INSERT INTO students (student_name, grade) VALUES (%s, %s) RETURNING *",
            (name, grade)
        )
        student = cur.fetchone()
        conn.commit()
    
    cur.close()
    return dict(student) if student else None

def update_student_stats(name, grade, total_hours=None, streak_days=None):
    """Update student statistics"""
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

# Topic operations
def get_completed_topics(name, grade):
    """Get all completed topics for a student"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT topic, subject FROM completed_topics WHERE student_name = %s AND grade = %s",
        (name, grade)
    )
    topics = cur.fetchall()
    cur.close()
    
    return [dict(t) for t in topics]

def mark_topic_completed(name, grade, subject, topic):
    """Mark a topic as completed"""
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

def unmark_topic(name, grade, subject, topic):
    """Remove topic from completed list"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "DELETE FROM completed_topics WHERE student_name = %s AND grade = %s AND subject = %s AND topic = %s",
        (name, grade, subject, topic)
    )
    conn.commit()
    cur.close()

# Study session operations
def add_study_session(name, grade, subject, duration, topics=None):
    """Log a study session"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO study_sessions (student_name, grade, subject, duration_minutes, topics)
           VALUES (%s, %s, %s, %s, %s)""",
        (name, grade, subject, duration, topics)
    )
    conn.commit()
    cur.close()

def get_total_study_hours(name, grade):
    """Calculate total study hours from sessions"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM study_sessions WHERE student_name = %s AND grade = %s",
        (name, grade)
    )
    result = cur.fetchone()
    cur.close()
    
    return float(result['total']) / 60.0 if result else 0.0

# Weekly plan operations
def save_weekly_plan(name, grade, week_key, day, subject, topics, duration, completed):
    """Save or update weekly plan"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO weekly_plans (student_name, grade, week_key, day_of_week, subject, topics, duration, completed)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (student_name, grade, week_key, day_of_week)
           DO UPDATE SET subject = EXCLUDED.subject, topics = EXCLUDED.topics, 
                         duration = EXCLUDED.duration, completed = EXCLUDED.completed""",
        (name, grade, week_key, day, subject, topics, duration, completed)
    )
    conn.commit()
    cur.close()

def get_weekly_plan(name, grade, week_key):
    """Get weekly plan for a student"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT * FROM weekly_plans WHERE student_name = %s AND grade = %s AND week_key = %s",
        (name, grade, week_key)
    )
    plans = cur.fetchall()
    cur.close()
    
    return [dict(p) for p in plans]