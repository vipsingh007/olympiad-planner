import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from datetime import datetime
import time

# Database connection with retry logic
def get_db_connection():
    """Create database connection with optimized settings"""
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

# Student operations
def get_or_create_student(name, grade):
    """Get student or create if doesn't exist"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT * FROM students WHERE student_name = %s AND grade = %s",
            (name, grade)
        )
        student = cur.fetchone()
        
        if not student:
            cur.execute(
                "INSERT INTO students (student_name, grade) VALUES (%s, %s) RETURNING *",
                (name, grade)
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
