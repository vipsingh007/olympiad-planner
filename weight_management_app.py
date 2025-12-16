import streamlit as st
from datetime import datetime, timedelta
import json
from openai import OpenAI

st.set_page_config(page_title="💪 FitLife - Weight Management", layout="wide", page_icon="💪")

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        if api_key:
            return OpenAI(api_key=api_key)
        return None
    except:
        return None

client = get_openai_client()

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
if 'progress_logs' not in st.session_state:
    st.session_state.progress_logs = []
if 'ai_meal_plan' not in st.session_state:
    st.session_state.ai_meal_plan = None
if 'ai_tips' not in st.session_state:
    st.session_state.ai_tips = None

# AI-powered meal plan generation
def generate_ai_meal_plan(profile):
    """Generate personalized meal plan using OpenAI"""
    if not client:
        return None
    
    try:
        prompt = f"""
        Create a personalized weekly meal plan for a person with the following profile:
        
        Goal: {profile['goal']}
        Current Weight: {profile['current_weight']} kg
        Target Weight: {profile['target_weight']} kg
        Diet Type: {profile['diet_type']}
        Activity Level: {profile['activity_level']}
        Age: {profile['age']}
        Gender: {profile['gender']}
        Duration: {profile['duration']}
        
        Please provide:
        1. A 7-day meal plan with breakfast, lunch, snack, and dinner for each day
        2. Make meals specific to {profile['diet_type']} preference
        3. Include portion sizes and approximate calories
        4. Make meals realistic and easy to prepare
        5. Include variety throughout the week
        6. Consider Indian/Asian cuisine preferences
        
        Format the response as a structured weekly plan.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional nutritionist and dietitian specializing in personalized meal planning for weight management."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating AI meal plan: {str(e)}")
        return None

# AI-powered personalized tips
def generate_ai_tips(profile, progress_logs):
    """Generate personalized tips based on user's progress"""
    if not client:
        return None
    
    try:
        progress_summary = ""
        if progress_logs:
            recent_logs = progress_logs[-5:]  # Last 5 entries
            progress_summary = f"Recent progress: {len(recent_logs)} logs, "
            progress_summary += f"Weight range: {min([l['weight'] for l in recent_logs])}-{max([l['weight'] for l in recent_logs])} kg"
        else:
            progress_summary = "Just started, no logs yet"
        
        prompt = f"""
        Provide 5 personalized, actionable tips for a person with this profile:
        
        Goal: {profile['goal']}
        Current Weight: {profile['current_weight']} kg
        Target Weight: {profile['target_weight']} kg
        Diet Type: {profile['diet_type']}
        Activity Level: {profile['activity_level']}
        Progress: {progress_summary}
        
        Tips should be:
        1. Specific and actionable
        2. Motivating and encouraging
        3. Tailored to their goal
        4. Practical and easy to follow
        5. Based on their current progress
        
        Format as a numbered list with clear, concise advice.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a motivating fitness coach and nutritionist who provides personalized, practical advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating AI tips: {str(e)}")
        return None

# AI-powered progress analysis
def analyze_progress_with_ai(profile, progress_logs):
    """Analyze user's progress and provide insights"""
    if not client or not progress_logs or len(progress_logs) < 2:
        return None
    
    try:
        weights = [log['weight'] for log in progress_logs]
        dates = [log['date'] for log in progress_logs]
        
        prompt = f"""
        Analyze this person's weight management progress:
        
        Goal: {profile['goal']}
        Starting Weight: {profile['current_weight']} kg
        Target Weight: {profile['target_weight']} kg
        Target Duration: {profile['duration']}
        
        Progress Data:
        {chr(10).join([f"Date: {log['date']}, Weight: {log['weight']} kg, Calories: {log.get('calories', 'N/A')}" for log in progress_logs])}
        
        Provide:
        1. Brief assessment of progress (2-3 sentences)
        2. Are they on track to meet their goal?
        3. One specific recommendation to improve
        4. One thing they're doing well
        5. Motivation message
        
        Keep it encouraging and constructive!
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an encouraging fitness coach analyzing progress data to provide constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error analyzing progress: {str(e)}")
        return None

# AI-powered recipe suggestions
def get_ai_recipe(meal_type, diet_type, calories):
    """Get a specific recipe suggestion"""
    if not client:
        return None
    
    try:
        prompt = f"""
        Provide a detailed {meal_type} recipe that is:
        - {diet_type}
        - Approximately {calories} calories
        - Healthy and nutritious
        - Easy to prepare (20-30 minutes)
        - Uses commonly available ingredients
        
        Format:
        1. Recipe Name
        2. Ingredients (with quantities)
        3. Instructions (step by step)
        4. Nutritional Info (calories, protein, carbs, fats)
        5. Prep time and cooking time
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional chef and nutritionist who creates healthy, delicious recipes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting recipe: {str(e)}")
        return None

# Helper function to calculate BMI
def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 1)

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight", "🔵"
    elif bmi < 25:
        return "Normal", "🟢"
    elif bmi < 30:
        return "Overweight", "🟡"
    else:
        return "Obese", "🔴"

# Calculate daily calorie needs
def calculate_calories(weight, height, age, gender, activity_level, goal):
    # Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation
    if gender == "Male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # Activity multipliers
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extremely Active": 1.9
    }
    
    tdee = bmr * activity_multipliers[activity_level]
    
    # Adjust for goal
    if goal == "Lose Weight":
        target_calories = tdee - 500  # 500 calorie deficit
    elif goal == "Gain Weight":
        target_calories = tdee + 500  # 500 calorie surplus
    else:
        target_calories = tdee
    
    return int(tdee), int(target_calories)

# Generate meal plan
def generate_meal_plan(calories, diet_type, goal):
    # Macro distribution
    if goal == "Gain Weight":
        protein_ratio = 0.30
        carb_ratio = 0.45
        fat_ratio = 0.25
    else:  # Lose Weight
        protein_ratio = 0.35
        carb_ratio = 0.35
        fat_ratio = 0.30
    
    protein_cals = calories * protein_ratio
    carb_cals = calories * carb_ratio
    fat_cals = calories * fat_ratio
    
    protein_g = int(protein_cals / 4)
    carb_g = int(carb_cals / 4)
    fat_g = int(fat_cals / 9)
    
    # Sample meals based on diet type
    if diet_type == "Vegetarian":
        meals = {
            "Breakfast": [
                "Oatmeal with nuts and fruits",
                "Paneer sandwich with vegetables",
                "Smoothie bowl with chia seeds",
                "Poha with peanuts and vegetables"
            ],
            "Lunch": [
                "Brown rice with dal and mixed vegetables",
                "Chickpea curry with whole wheat roti",
                "Vegetable pulao with raita",
                "Quinoa salad with tofu"
            ],
            "Snack": [
                "Greek yogurt with berries",
                "Roasted chickpeas",
                "Fruit with almond butter",
                "Sprouts salad"
            ],
            "Dinner": [
                "Grilled paneer with vegetables",
                "Lentil soup with whole grain bread",
                "Vegetable stir-fry with brown rice",
                "Mushroom curry with roti"
            ]
        }
    elif diet_type == "Non-Vegetarian":
        meals = {
            "Breakfast": [
                "Scrambled eggs with whole wheat toast",
                "Chicken sausage with vegetables",
                "Omelette with cheese and vegetables",
                "Boiled eggs with avocado toast"
            ],
            "Lunch": [
                "Grilled chicken with brown rice and vegetables",
                "Fish curry with roti",
                "Chicken breast salad",
                "Mutton keema with brown rice"
            ],
            "Snack": [
                "Boiled eggs",
                "Chicken tikka",
                "Protein shake",
                "Tuna salad"
            ],
            "Dinner": [
                "Grilled fish with vegetables",
                "Chicken soup with vegetables",
                "Egg curry with roti",
                "Grilled chicken with salad"
            ]
        }
    else:  # Both
        meals = {
            "Breakfast": [
                "Oatmeal with nuts / Scrambled eggs",
                "Paneer sandwich / Chicken sandwich",
                "Smoothie bowl / Protein shake with banana",
                "Poha / Egg paratha"
            ],
            "Lunch": [
                "Dal rice / Chicken rice",
                "Chickpea curry / Fish curry with roti",
                "Vegetable pulao / Chicken biryani",
                "Quinoa salad / Grilled chicken salad"
            ],
            "Snack": [
                "Yogurt with fruits / Boiled eggs",
                "Roasted chickpeas / Chicken tikka",
                "Nuts and seeds / Protein bar",
                "Sprouts salad / Tuna wrap"
            ],
            "Dinner": [
                "Grilled paneer / Grilled chicken with vegetables",
                "Lentil soup / Chicken soup",
                "Vegetable stir-fry / Fish with vegetables",
                "Mushroom curry / Egg curry with roti"
            ]
        }
    
    return meals, protein_g, carb_g, fat_g

# Main app
st.title("💪 FitLife - Your Weight Management Partner")
st.markdown("### Achieve Your Weight Goals with Personalized Diet Plans")

# Sidebar navigation
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=FitLife", use_container_width=True)
    st.markdown("---")
    
    if st.session_state.user_profile:
        st.success(f"👤 {st.session_state.user_profile['name']}")
        st.info(f"🎯 Goal: {st.session_state.user_profile['goal']}")
        if st.button("🔄 Reset Profile"):
            st.session_state.user_profile = None
            st.session_state.progress_logs = []
            st.rerun()
    
    page = st.radio("Navigation", ["🏠 Setup Profile", "📊 My Plan", "🤖 AI Coach", "📈 Track Progress", "📚 Tips & Resources"])

# Setup Profile Page
if page == "🏠 Setup Profile" or not st.session_state.user_profile:
    st.header("🏠 Setup Your Profile")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        name = st.text_input("Name", placeholder="Enter your name")
        age = st.number_input("Age", min_value=10, max_value=100, value=25)
        gender = st.selectbox("Gender", ["Male", "Female"])
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
        current_weight = st.number_input("Current Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.5)
        
        # Calculate and show BMI
        if height and current_weight:
            bmi = calculate_bmi(current_weight, height)
            bmi_cat, icon = get_bmi_category(bmi)
            st.metric("Your BMI", f"{bmi}", help=f"{icon} {bmi_cat}")
    
    with col2:
        st.subheader("Your Goals")
        goal = st.selectbox("What's your goal?", ["Lose Weight", "Gain Weight", "Maintain Weight"])
        
        if goal != "Maintain Weight":
            target_weight = st.number_input(
                f"Target Weight (kg)", 
                min_value=30.0, 
                max_value=200.0, 
                value=current_weight - 5 if goal == "Lose Weight" else current_weight + 5,
                step=0.5
            )
            weight_diff = abs(target_weight - current_weight)
            st.info(f"📊 Target: {weight_diff:.1f} kg to {goal.split()[0].lower()}")
        else:
            target_weight = current_weight
        
        duration = st.selectbox(
            "Time Period to Achieve Goal",
            ["1 month", "2 months", "3 months", "6 months", "12 months"]
        )
        
        activity_level = st.selectbox(
            "Activity Level",
            ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"],
            help="Sedentary: Little/no exercise\nLightly Active: 1-3 days/week\nModerately: 3-5 days/week\nVery: 6-7 days/week\nExtremely: Very intense daily"
        )
        
        diet_type = st.selectbox("Diet Preference", ["Vegetarian", "Non-Vegetarian", "Both"])
    
    st.markdown("---")
    
    if st.button("🚀 Generate My Plan", type="primary", use_container_width=True):
        if name:
            st.session_state.user_profile = {
                "name": name,
                "age": age,
                "gender": gender,
                "height": height,
                "current_weight": current_weight,
                "target_weight": target_weight,
                "goal": goal,
                "duration": duration,
                "activity_level": activity_level,
                "diet_type": diet_type,
                "bmi": bmi,
                "start_date": datetime.now().strftime("%Y-%m-%d")
            }
            st.success("✅ Profile created! Navigate to 'My Plan' to see your personalized diet plan.")
            st.balloons()
        else:
            st.error("Please enter your name")

# My Plan Page
elif page == "📊 My Plan":
    if not st.session_state.user_profile:
        st.warning("⚠️ Please setup your profile first!")
        st.stop()
    
    profile = st.session_state.user_profile
    
    st.header("📊 Your Personalized Plan")
    
    # Overview cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Weight", f"{profile['current_weight']} kg")
    with col2:
        st.metric("Target Weight", f"{profile['target_weight']} kg")
    with col3:
        weight_diff = abs(profile['target_weight'] - profile['current_weight'])
        st.metric("To Go", f"{weight_diff:.1f} kg")
    with col4:
        st.metric("Duration", profile['duration'])
    
    st.markdown("---")
    
    # Calculate calories
    tdee, target_calories = calculate_calories(
        profile['current_weight'],
        profile['height'],
        profile['age'],
        profile['gender'],
        profile['activity_level'],
        profile['goal']
    )
    
    # Calorie information
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔥 Calorie Plan")
        st.info(f"**Maintenance Calories:** {tdee} kcal/day")
        st.success(f"**Target Calories:** {target_calories} kcal/day")
        
        if profile['goal'] == "Lose Weight":
            st.caption("📉 Calorie deficit of 500 kcal/day = ~0.5 kg loss/week")
        elif profile['goal'] == "Gain Weight":
            st.caption("📈 Calorie surplus of 500 kcal/day = ~0.5 kg gain/week")
    
    with col2:
        st.subheader("🥗 Macro Distribution")
        meals, protein_g, carb_g, fat_g = generate_meal_plan(target_calories, profile['diet_type'], profile['goal'])
        
        st.write(f"**Protein:** {protein_g}g ({int(protein_g*4)} kcal)")
        st.write(f"**Carbs:** {carb_g}g ({int(carb_g*4)} kcal)")
        st.write(f"**Fats:** {fat_g}g ({int(fat_g*9)} kcal)")
    
    st.markdown("---")
    
    # Weekly meal plan
    st.subheader("📅 Weekly Meal Plan")
    st.caption(f"Diet Type: {profile['diet_type']}")
    
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day in days:
        with st.expander(f"📆 {day}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("**🌅 Breakfast**")
                st.write(meals["Breakfast"][days.index(day) % len(meals["Breakfast"])])
            
            with col2:
                st.markdown("**🍽️ Lunch**")
                st.write(meals["Lunch"][days.index(day) % len(meals["Lunch"])])
            
            with col3:
                st.markdown("**🍎 Snack**")
                st.write(meals["Snack"][days.index(day) % len(meals["Snack"])])
            
            with col4:
                st.markdown("**🌙 Dinner**")
                st.write(meals["Dinner"][days.index(day) % len(meals["Dinner"])])
    
    st.markdown("---")
    
    # Additional tips
    st.subheader("💡 Important Tips")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **Hydration 💧**
        - Drink 8-10 glasses of water daily
        - Have water before meals
        - Carry a water bottle
        """)
        
        st.success("""
        **Exercise 🏃**
        - 30 minutes cardio 5x/week
        - Strength training 3x/week
        - Stay consistent
        """)
    
    with col2:
        st.warning("""
        **Sleep 😴**
        - Get 7-8 hours sleep
        - Sleep affects metabolism
        - Maintain regular schedule
        """)
        
        st.info("""
        **Consistency 📈**
        - Track your meals
        - Log your weight weekly
        - Don't skip meals
        """)
    
    # AI-Generated Content Section
    if client:
        st.markdown("---")
        st.subheader("🤖 AI-Powered Enhancements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✨ Generate AI Meal Plan", type="primary"):
                with st.spinner("🤖 AI is creating your personalized meal plan..."):
                    ai_plan = generate_ai_meal_plan(profile)
                    if ai_plan:
                        st.session_state.ai_meal_plan = ai_plan
                        st.success("✅ AI meal plan generated!")
        
        with col2:
            if st.button("💡 Get AI Tips"):
                with st.spinner("🤖 AI is analyzing your profile..."):
                    ai_tips = generate_ai_tips(profile, st.session_state.progress_logs)
                    if ai_tips:
                        st.session_state.ai_tips = ai_tips
                        st.success("✅ AI tips generated!")
        
        if st.session_state.ai_meal_plan:
            with st.expander("📋 AI-Generated Meal Plan (Personalized)", expanded=True):
                st.markdown(st.session_state.ai_meal_plan)
        
        if st.session_state.ai_tips:
            with st.expander("💡 AI-Generated Tips", expanded=True):
                st.info(st.session_state.ai_tips)

# AI Coach Page
elif page == "🤖 AI Coach":
    if not st.session_state.user_profile:
        st.warning("⚠️ Please setup your profile first!")
        st.stop()
    
    profile = st.session_state.user_profile
    
    st.header("🤖 AI Coach - Your Personal Fitness Assistant")
    
    if not client:
        st.error("⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to secrets.")
        st.info("Add your OpenAI API key in `.streamlit/secrets.toml` to enable AI features.")
        st.stop()
    
    # AI Coach Tabs
    ai_tab1, ai_tab2, ai_tab3, ai_tab4 = st.tabs(["💬 Ask Coach", "🍳 Recipe Generator", "📊 Progress Analysis", "🎯 Daily Motivation"])
    
    with ai_tab1:
        st.subheader("💬 Ask Your AI Coach")
        st.caption("Get personalized advice and answers to your fitness questions")
        
        user_question = st.text_area(
            "What would you like to know?",
            placeholder="E.g., 'What are the best exercises for belly fat?' or 'How can I increase my protein intake?'",
            height=100
        )
        
        if st.button("Ask Coach", type="primary"):
            if user_question:
                with st.spinner("🤖 Coach is thinking..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": f"You are a personal fitness coach helping someone with this profile: Goal: {profile['goal']}, Current Weight: {profile['current_weight']}kg, Target: {profile['target_weight']}kg, Diet: {profile['diet_type']}. Provide helpful, motivating, and practical advice."},
                                {"role": "user", "content": user_question}
                            ],
                            temperature=0.7,
                            max_tokens=800
                        )
                        
                        answer = response.choices[0].message.content
                        st.success("🎓 Coach's Response:")
                        st.markdown(answer)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a question")
    
    with ai_tab2:
        st.subheader("🍳 AI Recipe Generator")
        st.caption("Get custom recipes tailored to your goals")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
        
        with col2:
            recipe_calories = st.number_input("Target Calories", min_value=100, max_value=1000, value=400, step=50)
        
        with col3:
            recipe_diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian", profile['diet_type']], index=2)
        
        special_request = st.text_input("Special Requirements (optional)", placeholder="E.g., 'high protein' or 'low carb' or 'uses chicken'")
        
        if st.button("🍳 Generate Recipe", type="primary"):
            with st.spinner("👨‍🍳 AI Chef is creating your recipe..."):
                try:
                    prompt = f"""
                    Create a detailed {meal_type} recipe:
                    - Diet: {recipe_diet}
                    - Calories: ~{recipe_calories} kcal
                    - Easy to prepare (20-30 min)
                    {f"- Special: {special_request}" if special_request else ""}
                    - Healthy and nutritious
                    
                    Include: Name, Ingredients, Instructions, Nutrition, Time
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a professional chef and nutritionist creating healthy recipes."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=1000
                    )
                    
                    recipe = response.choices[0].message.content
                    st.success("✅ Recipe Generated!")
                    st.markdown(recipe)
                    
                    # Save recipe button
                    if st.button("💾 Save This Recipe"):
                        st.success("Recipe saved! (Feature coming soon)")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with ai_tab3:
        st.subheader("📊 AI Progress Analysis")
        st.caption("Get AI-powered insights on your progress")
        
        if st.session_state.progress_logs and len(st.session_state.progress_logs) >= 2:
            if st.button("🔍 Analyze My Progress", type="primary"):
                with st.spinner("🤖 AI is analyzing your progress..."):
                    analysis = analyze_progress_with_ai(profile, st.session_state.progress_logs)
                    if analysis:
                        st.success("📊 Progress Analysis:")
                        st.markdown(analysis)
                        
                        # Show progress chart
                        st.markdown("---")
                        st.subheader("Weight Trend")
                        weights = [profile['current_weight']] + [log['weight'] for log in st.session_state.progress_logs]
                        st.line_chart(weights)
        else:
            st.info("📝 Log at least 2 weight entries in 'Track Progress' to get AI analysis!")
            st.caption("The more data you log, the better insights AI can provide.")
    
    with ai_tab4:
        st.subheader("🎯 Daily Motivation")
        st.caption("Get personalized motivation from your AI coach")
        
        if st.button("💪 Get Motivated!", type="primary"):
            with st.spinner("🤖 Generating motivation..."):
                try:
                    days_since_start = 0
                    if st.session_state.progress_logs:
                        start_date = datetime.strptime(profile['start_date'], "%Y-%m-%d")
                        days_since_start = (datetime.now() - start_date).days
                    
                    prompt = f"""
                    Create a motivating message for someone on day {days_since_start} of their {profile['goal']} journey.
                    Current: {profile['current_weight']}kg, Target: {profile['target_weight']}kg
                    
                    Make it:
                    - Encouraging and positive
                    - Specific to their goal
                    - Action-oriented
                    - Brief (2-3 sentences)
                    - Include an emoji or two
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a motivational fitness coach providing daily encouragement."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9,
                        max_tokens=200
                    )
                    
                    motivation = response.choices[0].message.content
                    st.success(motivation)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.markdown("---")
        st.subheader("💡 Quick Motivational Tips")
        motivational_quotes = [
            "🌟 'The only bad workout is the one that didn't happen.'",
            "💪 'Your body can stand almost anything. It's your mind you have to convince.'",
            "🎯 'Success is the sum of small efforts repeated day in and day out.'",
            "🔥 'Don't wish for it. Work for it.'",
            "⭐ 'You don't have to be extreme, just consistent.'",
            "🌈 'Progress, not perfection.'",
        ]
        for quote in motivational_quotes:
            st.info(quote)

# Track Progress Page
elif page == "📈 Track Progress":
    if not st.session_state.user_profile:
        st.warning("⚠️ Please setup your profile first!")
        st.stop()
    
    profile = st.session_state.user_profile
    
    st.header("📈 Track Your Progress")
    
    # Current stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Starting Weight", f"{profile['current_weight']} kg")
    with col2:
        if st.session_state.progress_logs:
            latest_weight = st.session_state.progress_logs[-1]['weight']
            change = latest_weight - profile['current_weight']
            st.metric("Current Weight", f"{latest_weight} kg", f"{change:+.1f} kg")
        else:
            st.metric("Current Weight", f"{profile['current_weight']} kg")
    with col3:
        st.metric("Target Weight", f"{profile['target_weight']} kg")
    
    st.markdown("---")
    
    # Log new entry
    st.subheader("📝 Log Today's Progress")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        log_date = st.date_input("Date", value=datetime.now())
    with col2:
        log_weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=profile['current_weight'], step=0.1)
    with col3:
        log_calories = st.number_input("Calories Consumed", min_value=0, max_value=5000, value=2000, step=100)
    
    notes = st.text_area("Notes (optional)", placeholder="How did you feel? Any challenges?")
    
    if st.button("💾 Save Log Entry", type="primary"):
        entry = {
            "date": log_date.strftime("%Y-%m-%d"),
            "weight": log_weight,
            "calories": log_calories,
            "notes": notes
        }
        st.session_state.progress_logs.append(entry)
        st.success("✅ Progress logged successfully!")
        st.balloons()
    
    st.markdown("---")
    
    # Show progress history
    if st.session_state.progress_logs:
        st.subheader("📊 Progress History")
        
        # Create progress chart data
        weights = [profile['current_weight']] + [log['weight'] for log in st.session_state.progress_logs]
        st.line_chart(weights)
        
        st.markdown("---")
        
        st.subheader("📋 Log Entries")
        for i, log in enumerate(reversed(st.session_state.progress_logs)):
            with st.expander(f"📅 {log['date']} - {log['weight']} kg"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Weight:** {log['weight']} kg")
                    st.write(f"**Calories:** {log['calories']} kcal")
                with col2:
                    if log['notes']:
                        st.write(f"**Notes:** {log['notes']}")
    else:
        st.info("📝 No progress logs yet. Start tracking your weight above!")

# Tips & Resources Page
elif page == "📚 Tips & Resources":
    st.header("📚 Tips & Resources")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🥗 Nutrition", "🏋️ Exercise", "😴 Lifestyle", "❓ FAQ"])
    
    with tab1:
        st.subheader("🥗 Nutrition Tips")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### For Weight Loss:
            - **Calorie deficit** is key
            - Eat more **protein** (keeps you full)
            - Choose **whole grains** over refined
            - Load up on **vegetables**
            - Avoid sugary drinks
            - Practice **portion control**
            - Eat slowly and mindfully
            - Don't skip meals
            """)
            
            st.markdown("""
            ### High-Protein Foods:
            **Vegetarian:**
            - Paneer, Tofu, Lentils
            - Chickpeas, Kidney beans
            - Greek yogurt, Cottage cheese
            - Quinoa, Oats
            
            **Non-Vegetarian:**
            - Chicken breast, Fish
            - Eggs, Lean meat
            - Turkey, Tuna
            """)
        
        with col2:
            st.markdown("""
            ### For Weight Gain:
            - **Calorie surplus** needed
            - Eat **frequently** (5-6 meals)
            - Include **healthy fats**
            - **Protein** after workouts
            - Drink calories (smoothies, shakes)
            - Don't fill up on water before meals
            - Eat larger portions
            - Add nuts and dried fruits
            """)
            
            st.markdown("""
            ### Healthy Snacks:
            - Nuts and seeds
            - Fruits with nut butter
            - Protein bars
            - Greek yogurt
            - Boiled eggs
            - Hummus with veggies
            - Roasted chickpeas
            - Protein smoothies
            """)
    
    with tab2:
        st.subheader("🏋️ Exercise Guidelines")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### For Weight Loss:
            **Cardio (5-6 days/week):**
            - Running/Jogging: 30-45 min
            - Cycling: 45-60 min
            - Swimming: 30-45 min
            - HIIT workouts: 20-30 min
            - Brisk walking: 60 min
            
            **Strength Training (3-4 days/week):**
            - Build muscle to boost metabolism
            - Full body workouts
            - Focus on compound movements
            - Don't skip leg day!
            """)
        
        with col2:
            st.markdown("""
            ### For Weight Gain:
            **Strength Training (4-5 days/week):**
            - Focus on **progressive overload**
            - Compound exercises:
              - Squats, Deadlifts
              - Bench press, Rows
              - Overhead press
            - 8-12 reps per set
            - 3-4 sets per exercise
            
            **Cardio (2-3 days/week):**
            - Keep it moderate
            - 20-30 minutes
            - Don't overdo cardio
            """)
        
        st.info("""
        💡 **Remember:** Exercise + Diet = Best Results!
        
        Always warm up before exercise and cool down after. Listen to your body and rest when needed.
        """)
    
    with tab3:
        st.subheader("😴 Lifestyle Tips")
        
        st.markdown("""
        ### Sleep 😴
        - **7-8 hours** is essential
        - Poor sleep affects hormones
        - Lack of sleep increases hunger
        - Maintain consistent schedule
        - Avoid screens before bed
        
        ### Stress Management 🧘
        - High stress = weight gain
        - Practice meditation
        - Deep breathing exercises
        - Yoga or stretching
        - Take breaks during work
        
        ### Hydration 💧
        - Drink **3-4 liters** water daily
        - More if exercising
        - Water helps metabolism
        - Drink before meals (reduces appetite)
        
        ### Consistency 📅
        - **Don't aim for perfection**
        - 80/20 rule (80% healthy, 20% flexible)
        - One bad meal won't ruin progress
        - Get back on track immediately
        - Track progress weekly
        - Take measurements (not just weight)
        - Progress photos help
        
        ### Avoid ❌
        - Crash diets
        - Skipping meals
        - Too much processed food
        - Alcohol (empty calories)
        - Late night eating
        - Comparing yourself to others
        """)
    
    with tab4:
        st.subheader("❓ Frequently Asked Questions")
        
        with st.expander("How fast should I lose/gain weight?"):
            st.markdown("""
            **Safe Rate:**
            - **Weight Loss:** 0.5-1 kg per week
            - **Weight Gain:** 0.5-1 kg per week
            
            Faster changes can be unhealthy and unsustainable!
            """)
        
        with st.expander("Can I eat my favorite foods?"):
            st.markdown("""
            **Yes!** Follow the 80/20 rule:
            - 80% of the time: Healthy, nutritious foods
            - 20% of the time: Enjoy your favorites
            
            This makes the plan sustainable long-term.
            """)
        
        with st.expander("Do I need supplements?"):
            st.markdown("""
            **Not necessarily!** Focus on whole foods first.
            
            **May be helpful:**
            - Protein powder (if you struggle to meet protein goals)
            - Multivitamin (if diet is limited)
            - Vitamin D (if you don't get sun)
            
            Consult a doctor before taking any supplements.
            """)
        
        with st.expander("What if I'm not seeing results?"):
            st.markdown("""
            **Possible reasons:**
            1. Not tracking calories accurately
            2. Not being consistent enough
            3. Unrealistic timeframe
            4. Medical condition (consult doctor)
            5. Not enough sleep/too much stress
            
            **Give it time!** Real change takes 4-6 weeks to show.
            """)
        
        with st.expander("Can I skip breakfast?"):
            st.markdown("""
            **It depends!** Some people do well with intermittent fasting.
            
            What matters most is:
            - **Total daily calories**
            - **Macro distribution**
            - **Consistency**
            
            Eat when it works best for YOUR schedule and hunger.
            """)

st.markdown("---")
st.caption("💪 FitLife - Your journey to a healthier you! Remember: Consistency > Perfection")

