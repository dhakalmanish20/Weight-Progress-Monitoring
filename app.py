import sqlite3  
import datetime  
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify  
import requests  
import math  
import os  
from werkzeug.utils import secure_filename  
  
app = Flask(__name__)  
app.secret_key = "my_secret_key"  # Change to a secure key in production  
DATABASE = "wm3.db"  
  
# Configure upload folder  
UPLOAD_FOLDER = 'static/profile_pics'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  
  
# Allowed extensions for profile pictures  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  
  
# =======================  
# DATABASE HELPER METHODS  
# =======================  
  
def get_db():  
    if not hasattr(g, "sqlite_db"):  
        g.sqlite_db = sqlite3.connect(DATABASE)  
        g.sqlite_db.row_factory = sqlite3.Row  
    return g.sqlite_db  
  
@app.teardown_appcontext  
def close_db(error):  
    if hasattr(g, "sqlite_db"):  
        g.sqlite_db.close()  
  
def init_db():  
    with sqlite3.connect(DATABASE) as db:  
        # Users table  
        db.execute(  
            """  
            CREATE TABLE IF NOT EXISTS users (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                username TEXT UNIQUE NOT NULL,  
                email TEXT UNIQUE NOT NULL,  
                password TEXT NOT NULL,  
                age INTEGER,  
                height REAL,  
                weight REAL,  
                starting_weight REAL,  
                experience TEXT,  
                goal TEXT,  
                goal_weight REAL,  
                profile_picture TEXT,  
                notifications_enabled INTEGER DEFAULT 1  
            )  
            """  
        )  
        # Food logs table  
        db.execute(  
            """  
            CREATE TABLE IF NOT EXISTS food_logs (  
                food_log_id INTEGER PRIMARY KEY AUTOINCREMENT,  
                user_id INTEGER,  
                date TEXT,  
                food_name TEXT,  
                quantity REAL,  
                calories REAL,  
                protein REAL,  
                fats REAL,  
                carbs REAL,  
                FOREIGN KEY(user_id) REFERENCES users(id)  
            )  
            """  
        )  
        # Exercise logs table  
        db.execute(  
            """  
            CREATE TABLE IF NOT EXISTS exercise_logs (  
                exercise_log_id INTEGER PRIMARY KEY AUTOINCREMENT,  
                user_id INTEGER,  
                date TEXT,  
                exercise_name TEXT,  
                duration_minutes REAL,  
                calories_burned REAL,  
                distance REAL,  
                FOREIGN KEY(user_id) REFERENCES users(id)  
            )  
            """  
        )  
        # Achievements table  
        db.execute(  
            """  
            CREATE TABLE IF NOT EXISTS achievements (  
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,  
                user_id INTEGER,  
                title TEXT,  
                description TEXT,  
                date_achieved TEXT,  
                FOREIGN KEY(user_id) REFERENCES users(id)  
            )  
            """  
        )  
        db.commit()  
  
# ========================  
# ML MODELS - HARD-CODED  
# ========================  
  
class LinearRegressionCustom:  
    def __init__(self, learning_rate=0.000001, iterations=1000):  
        self.learning_rate = learning_rate  
        self.iterations = iterations  
        self.a = 0.0  
        self.b = 0.0  
        self.c = 0.0  
  
    def fit(self, data):  
        m = len(data)  
        for _ in range(self.iterations):  
            da = db = dc = 0  
            for (cal, exer, w_change) in data:  
                pred = self.a * cal + self.b * exer + self.c  
                error = pred - w_change  
                da += error * cal  
                db += error * exer  
                dc += error  
            self.a -= (self.learning_rate * da) / m  
            self.b -= (self.learning_rate * db) / m  
            self.c -= (self.learning_rate * dc) / m  
  
    def predict(self, cal, exer):  
        return self.a * cal + self.b * exer + self.c  
  
class KNNRecommenderCustom:  
    def __init__(self, k=3):  
        self.k = k  
        self.data = []  
  
    def load_data(self, file_path):  
        import json  
        with open(file_path, "r") as f:  
            raw_data = json.load(f)  
        for ex in raw_data:  
            difficulty_map = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}  
            difficulty = difficulty_map.get(ex.get("difficulty", "intermediate").lower(), 2)  
            equipment = 0 if ex.get("equipment", "").lower() == "bodyweight" else 1  
            feature_vector = [difficulty, equipment]  
            self.data.append((feature_vector, ex))  
  
    def _distance(self, vec1, vec2):  
        return math.sqrt(sum((u - d) ** 2 for u, d in zip(vec1, vec2)))  
  
    def recommend(self, user_experience, preference):  
        # Map user experience to numeric value  
        difficulty_map = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}  
        user_difficulty = difficulty_map.get(user_experience.lower(), 2)  
  
        # Map equipment preference to numeric value  
        equipment_pref = 0 if preference.lower() == "calisthenics" else 1  
  
        user_vector = [user_difficulty, equipment_pref]  
  
        distances = []  
        for feature_vector, exercise_info in self.data:  
            dist = self._distance(user_vector, feature_vector)  
            distances.append((dist, exercise_info))  
  
        distances.sort(key=lambda x: x[0])  
        top_k = distances[:self.k]  
  
        recommendations = [item[1] for item in top_k]  
        return recommendations  
  
# Hard-coded TRAINING DATA for linear regression  
lr_data = [  
    (2000, 30, -0.4),  
    (2200, 25, -0.2),  
    (2500, 20, 0.1),  
    (2300, 40, -0.3),  
    (1800, 15, -0.6),  
    (2700, 10, 0.3),  
    (2100, 20, -0.2),  
    (1900, 35, -0.5),  
    (3000, 50, 0.4),  
    (1600, 0, -0.7),  
]  
  
lr_model = LinearRegressionCustom(learning_rate=0.0000001, iterations=1000)  
lr_model.fit(lr_data)  
  
# Initialize the KNN model  
knn_model = KNNRecommenderCustom(k=5)  
exercise_data_path = os.path.join(os.path.dirname(__file__), "exercise_data.json")  
knn_model.load_data(exercise_data_path)  
  
# =====================  
# ROUTES  
# =====================  
  
@app.route("/")  
def index():  
    return render_template("index.html")  
  
@app.route("/signup", methods=["GET", "POST"])  
def signup():  
    if request.method == "POST":  
        username = request.form.get("username")  
        email = request.form.get("email")  
        password = request.form.get("password")  
        age = request.form.get("age")  
        height = request.form.get("height")  
        weight = request.form.get("weight")  
        experience = request.form.get("experience")  
        goal = request.form.get("goal")  
        goal_weight = request.form.get("goal_weight")  
        starting_weight = weight  # Assume the starting weight is the initial weight  
  
        db = get_db()  
        try:  
            db.execute(  
                """  
                INSERT INTO users (username, email, password, age, height, weight, starting_weight, experience, goal, goal_weight)  
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  
                """,  
                (username, email, password, age, height, weight, starting_weight, experience, goal, goal_weight),  
            )  
            db.commit()  
            return redirect(url_for("login"))  
        except Exception as e:  
            print("[ERROR]", e)  
            return "Error creating user. Possibly username/email already taken."  
    return render_template("signup.html")  
  
@app.route("/login", methods=["GET", "POST"])  
def login():  
    if request.method == "POST":  
        username = request.form.get("username")  
        password = request.form.get("password")  
  
        db = get_db()  
        user = db.execute(  
            "SELECT * FROM users WHERE username=? AND password=?",  
            (username, password),  
        ).fetchone()  
  
        if user:  
            session["user_id"] = user["id"]  
            session["username"] = user["username"]  
            return redirect(url_for("profile"))  
        else:  
            return "Invalid credentials."  
    return render_template("login.html")  
  
@app.route("/logout")  
def logout():  
    session.clear()  
    return redirect(url_for("index"))  
  
def allowed_file(filename):  
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS  
  
@app.route("/log_food", methods=["POST"])  
def log_food():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
  
    user_id = session["user_id"]  
    food_name = request.form.get("food_name")  
    quantity = float(request.form.get("quantity"))  # In standard servings, e.g., 1  
  
    API_KEY = "6Wbyfeg0hCWWLHy8B9Hpkfu2RZbWw7KzyvgaJ13y"  # Replace with your actual API key  
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={API_KEY}&pageSize=1"  
    response = requests.get(url)  
    food_data = response.json()  
  
    if "foods" in food_data and len(food_data["foods"]) > 0:  
        food_item = food_data["foods"][0]  
        # Get nutrients  
        nutrients = {nutrient.get('nutrientId'): nutrient.get('value') for nutrient in food_item.get('foodNutrients', [])}  
  
        # Nutrient IDs from FoodData Central API  
        calories_id = 1008  
        protein_id = 1003  
        fats_id = 1004  
        carbs_id = 1005  
  
        calories = nutrients.get(calories_id, 0) * quantity  
        protein = nutrients.get(protein_id, 0) * quantity  
        fats = nutrients.get(fats_id, 0) * quantity  
        carbs = nutrients.get(carbs_id, 0) * quantity  
  
        # Insert into food_logs  
        db = get_db()  
        db.execute(  
            """  
            INSERT INTO food_logs (user_id, date, food_name, quantity, calories, protein, fats, carbs)  
            VALUES (?, DATE('now'), ?, ?, ?, ?, ?, ?)  
            """,  
            (user_id, food_name, quantity, calories, protein, fats, carbs),  
        )  
        db.commit()  
    else:  
        # Handle the case where food is not found  
        pass  # Add appropriate error handling  
  
    # Check for achievement: 'First Food Logged'  
    db = get_db()  
    food_log_count = db.execute(  
        "SELECT COUNT(*) FROM food_logs WHERE user_id = ?",  
        (user_id,)  
    ).fetchone()[0]  
  
    if food_log_count == 1:  
        # This is the first food log, add achievement  
        db.execute(  
            """  
            INSERT INTO achievements (user_id, title, description, date_achieved)  
            VALUES (?, ?, ?, DATE('now'))  
            """,  
            (user_id, 'First Food Logged', 'You logged your first food!')  
        )  
        db.commit()  
  
    return redirect(url_for("profile"))  
  
@app.route("/log_exercise", methods=["POST"])  
def log_exercise():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
  
    user_id = session["user_id"]  
    exercise_name = request.form.get("exercise_name")  
    duration_minutes = float(request.form.get("duration"))  
    distance = request.form.get("distance")  # New field  
    if distance:  
        distance = float(distance)  
    else:  
        distance = None  
  
    # Fetch user's weight  
    db = get_db()  
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()  
    user_weight = float(user["weight"]) if user["weight"] else 70.0  # Default weight  
  
    # For exercises like running, walking, cycling, we have predefined MET values  
    met_values = {  
        "running": 9.8,  
        "walking": 3.5,  
        "cycling": 7.5,  
        "swimming": 8.0,  
        "weightlifting": 6.0,  
    }  
    met = met_values.get(exercise_name.lower(), 5.0)  # Default MET  
  
    # Calculate calories burned  
    calories_burned = met * user_weight * (duration_minutes / 60.0)  
  
    # Insert into exercise_logs  
    db.execute(  
        """  
        INSERT INTO exercise_logs (user_id, date, exercise_name, duration_minutes, calories_burned, distance)  
        VALUES (?, DATE('now'), ?, ?, ?, ?)  
        """,  
        (user_id, exercise_name, duration_minutes, calories_burned, distance),  
    )  
    db.commit()  
  
    # Check for achievement: 'First Exercise Logged'  
    exercise_log_count = db.execute(  
        "SELECT COUNT(*) FROM exercise_logs WHERE user_id = ?",  
        (user_id,)  
    ).fetchone()[0]  
  
    if exercise_log_count == 1:  
        # This is the first exercise log, add achievement  
        db.execute(  
            """  
            INSERT INTO achievements (user_id, title, description, date_achieved)  
            VALUES (?, ?, ?, DATE('now'))  
            """,  
            (user_id, 'First Exercise Logged', 'You logged your first exercise!')  
        )  
        db.commit()  
  
    # Check cumulative distance achievements  
    total_running_distance = db.execute(  
        "SELECT SUM(distance) FROM exercise_logs WHERE user_id = ? AND exercise_name = 'running'",  
        (user_id,)  
    ).fetchone()[0] or 0  
  
    distance_achievements = [  
        (1, "Ran 1 km"),  
        (10, "Ran 10 km"),  
        (20, "Ran 20 km"),  
        (50, "Ran 50 km"),  
        (100, "Ran 100 km"),  
    ]  
  
    for dist, title in distance_achievements:  
        achievement_exists = db.execute(  
            "SELECT 1 FROM achievements WHERE user_id = ? AND title = ?",  
            (user_id, title)  
        ).fetchone()  
        if total_running_distance >= dist and not achievement_exists:  
            db.execute(  
                """  
                INSERT INTO achievements (user_id, title, description, date_achieved)  
                VALUES (?, ?, ?, DATE('now'))  
                """,  
                (user_id, title, f'You have run a total of {dist} km!')  
            )  
            db.commit()  
  
    return redirect(url_for("profile"))  
  
@app.route("/complete_exercise", methods=["POST"])  
def complete_exercise():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
    user_id = session["user_id"]  
    exercise_name = request.form.get("exercise_name")  
    duration_minutes = float(request.form.get("duration_minutes"))  
    # Fetch user's weight  
    db = get_db()  
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()  
    user_weight = float(user["weight"]) if user["weight"] else 70.0  # Default weight  
  
    # For simplicity, we can estimate MET based on intensity from exercise data  
    met_values = {  
        "low": 3.0,  
        "medium": 5.0,  
        "high": 7.0  
    }  
  
    # Get exercise details from exercise_data.json  
    exercise_data = next((ex for ex in knn_model.data if ex[1]['name'] == exercise_name), None)  
    if exercise_data:  
        exercise_info = exercise_data[1]  
        intensity = exercise_info.get('intensity', 'medium').lower()  
        met = met_values.get(intensity, 5.0)  
    else:  
        met = 5.0  
  
    calories_burned = met * user_weight * (duration_minutes / 60.0)  
  
    # Insert into exercise_logs  
    db.execute(  
        """  
        INSERT INTO exercise_logs (user_id, date, exercise_name, duration_minutes, calories_burned)  
        VALUES (?, DATE('now'), ?, ?, ?)  
        """,  
        (user_id, exercise_name, duration_minutes, calories_burned),  
    )  
    db.commit()  
  
    return redirect(url_for("profile"))  
  
# ... [other imports and code]  
  
@app.route("/profile", methods=["GET", "POST"])  
def profile():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
  
    user_id = session["user_id"]  
    db = get_db()  
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()  
  
    # Get today's date  
    today = datetime.date.today().isoformat()  
  
    # Get today's food logs  
    food_logs = db.execute(  
        "SELECT * FROM food_logs WHERE user_id = ? AND date = ?",  
        (user_id, today)  
    ).fetchall()  
  
    # Sum up total calories and nutrients  
    total_calories = sum([log["calories"] for log in food_logs]) or 0  
    total_protein = sum([log["protein"] for log in food_logs]) or 0  
    total_fats = sum([log["fats"] for log in food_logs]) or 0  
    total_carbs = sum([log["carbs"] for log in food_logs]) or 0  
  
    # Get today's exercise logs  
    exercise_logs = db.execute(  
        "SELECT * FROM exercise_logs WHERE user_id = ? AND date = ?",  
        (user_id, today)  
    ).fetchall()  
  
    # Sum up total calories burned  
    total_calories_burned = sum([log["calories_burned"] for log in exercise_logs]) or 0  
  
    # Predict weight progression  
    if total_calories > 0:  
        daily_cal = total_calories  
        daily_exer = total_calories_burned  
  
        # Predict the next few weeks  
        if user["weight"] and user["weight"] != 'None':  
            current_weight = float(user["weight"])  
        elif user["starting_weight"] and user["starting_weight"] != 'None':  
            current_weight = float(user["starting_weight"])  
        else:  
            current_weight = 70.0  # default weight  
  
        weeks_to_predict = 6  
        predicted_weights = []  
        w = current_weight  
  
        for _ in range(weeks_to_predict):  
            w_change = lr_model.predict(daily_cal, daily_exer)  
            w += w_change  
            predicted_weights.append(round(w, 2))  
    else:  
        predicted_weights = None  # No predictions if there's no data  
  
    # Recommend exercises using KNN  
    eq_pref = request.args.get("eq_pref", "calisthenics")  # Default to calisthenics  
    recommended_exercises = knn_model.recommend(  
        user_experience=user["experience"] if user["experience"] else "beginner",  
        preference=eq_pref,  
    )  
  
    # Calculate progress towards goal  
    if user["weight"] and user["weight"] != 'None':  
        current_weight = float(user["weight"])  
    elif user["starting_weight"] and user["starting_weight"] != 'None':  
        current_weight = float(user["starting_weight"])  
    else:  
        current_weight = 70.0  # default weight  
  
    if user["goal_weight"] and user["goal_weight"] != 'None':  
        goal_weight = float(user["goal_weight"])  
    else:  
        goal_weight = current_weight  # Assuming goal is the same as current if not provided  
  
    total_weight_to_lose = abs(float(user["starting_weight"] or current_weight) - goal_weight)  
    weight_lost = abs(float(user["starting_weight"] or current_weight) - current_weight)  
    if total_weight_to_lose > 0:  
        progress_percentage = (weight_lost / total_weight_to_lose) * 100  
        progress_percentage = min(progress_percentage, 100)  
    else:  
        progress_percentage = 0  
  
    # Fetch achievements  
    achievements = db.execute(  
        "SELECT * FROM achievements WHERE user_id = ?",  
        (user_id,)  
    ).fetchall()  
  
    # Get total calories consumed data for the chart  
    calories_data = []  
    dates = []  
    for i in range(7):  
        date = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()  
        dates.append(date)  
        calories = db.execute(  
            "SELECT SUM(calories) FROM food_logs WHERE user_id = ? AND date = ?",  
            (user_id, date)  
        ).fetchone()[0] or 0  
        calories_data.append(calories)  
    calories_data = calories_data[::-1]  
    dates = dates[::-1]  
  
    # Get total calories burned data for the chart  
    calories_burned_data = []  
    for i in range(7):  
        date = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()  
        calories_burned = db.execute(  
            "SELECT SUM(calories_burned) FROM exercise_logs WHERE user_id = ? AND date = ?",  
            (user_id, date)  
        ).fetchone()[0] or 0  
        calories_burned_data.append(calories_burned)  
    calories_burned_data = calories_burned_data[::-1]  
  
    return render_template(  
        "profile.html",  
        user=user,  
        predicted_weights=predicted_weights,  
        total_calories=total_calories,  
        total_protein=total_protein,  
        total_fats=total_fats,  
        total_carbs=total_carbs,  
        total_calories_burned=total_calories_burned,  
        recommended_exercises=recommended_exercises,  
        progress_percentage=progress_percentage,  
        current_weight=current_weight,  
        achievements=achievements,  
        calories_data=calories_data,  
        dates=dates,  
        calories_burned_data=calories_burned_data,  
    )  
  
@app.route("/get_food_recommendation")  
def get_food_recommendation():  
    if "user_id" not in session:  
        return jsonify({"meal": None})  
  
    user_id = session["user_id"]  
    db = get_db()  
  
    # Get today's date  
    today = datetime.date.today().isoformat()  
  
    # Get total nutrient intake today  
    nutrients = db.execute(  
        "SELECT SUM(calories) as calories, SUM(protein) as protein, SUM(fats) as fats, SUM(carbs) as carbs " +  
        "FROM food_logs WHERE user_id = ? AND date = ?",  
        (user_id, today)  
    ).fetchone()  
  
    total_calories = nutrients['calories'] or 0  
    total_protein = nutrients['protein'] or 0  
    total_fats = nutrients['fats'] or 0  
    total_carbs = nutrients['carbs'] or 0  
  
    # Target nutrient intakes (simple example, can be customized per user)  
    target_protein = 50.0  # grams  
    target_fats = 70.0     # grams  
    target_carbs = 310.0   # grams  
  
    remaining_calories = 2000 - total_calories  # Assuming 2000 kcal daily goal  
  
    remaining_protein = target_protein - total_protein if target_protein - total_protein > 0 else 0  
    remaining_fats = target_fats - total_fats if target_fats - total_fats > 0 else 0  
    remaining_carbs = target_carbs - total_carbs if target_carbs - total_carbs > 0 else 0  
  
    # Fetch food recommendations  
    API_KEY = "6Wbyfeg0hCWWLHy8B9Hpkfu2RZbWw7KzyvgaJ13y"  # Replace with your actual API key from USDA  
    recommendations = []  
  
    # Search for foods that can help meet the remaining nutrients  
    query = ""  
    if remaining_protein >= remaining_fats and remaining_protein >= remaining_carbs:  
        query = "high protein"  
    elif remaining_fats >= remaining_protein and remaining_fats >= remaining_carbs:  
        query = "high fat"  
    else:  
        query = "high carb"  
  
    endpoint = f"https://api.nal.usda.gov/fdc/v1/foods/search"  
    params = {  
        'api_key': API_KEY,  
        'query': query,  
        'pageSize': 10,  
        'sortBy': 'dataType.keyword',  
        'sortOrder': 'asc'  
    }  
  
    response = requests.get(endpoint, params=params)  
    data = response.json()  
  
    if "foods" in data:  
        for food in data["foods"]:  
            nutrients = {nutrient.get('nutrientId'): nutrient.get('value') for nutrient in food.get('foodNutrients', [])}  
            calories = nutrients.get(1008, 0)  
            protein = nutrients.get(1003, 0)  
            fats = nutrients.get(1004, 0)  
            carbs = nutrients.get(1005, 0)  
            recommendations.append({  
                'description': food['description'],  
                'calories': calories,  
                'protein': protein,  
                'fats': fats,  
                'carbs': carbs,  
                'url': f"https://www.myfitnesspal.com/food/search?search={food['description'].replace(' ', '+')}"  
            })  
  
    # Remove duplicates  
    seen = set()  
    unique_recommendations = []  
    for rec in recommendations:  
        if rec['description'] not in seen:  
            unique_recommendations.append(rec)  
            seen.add(rec['description'])  
  
    # Get top recommendations  
    top_recommendations = unique_recommendations[:5]  
  
    return jsonify({"meals": top_recommendations})  
  
@app.route("/user_profile", methods=["GET", "POST"])  
def user_profile():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
  
    db = get_db()  
    user_id = session["user_id"]  
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()  
  
    if request.method == "POST":  
        # Handle form submission to update personal info  
        age = request.form.get("age")  
        height = request.form.get("height")  
        weight = request.form.get("weight")  
        goal_weight = request.form.get("goal_weight")  
        experience = request.form.get("experience")  
        goal = request.form.get("goal")  
        starting_weight = request.form.get("starting_weight")  
  
        db.execute(  
            """  
            UPDATE users SET age = ?, height = ?, weight = ?, goal_weight = ?, experience = ?, goal = ?, starting_weight = ?  
            WHERE id = ?  
            """,  
            (age, height, weight, goal_weight, experience, goal, starting_weight, user_id)  
        )  
        db.commit()  
  
        # Handle profile picture upload  
        if 'profile_picture' in request.files:  
            file = request.files['profile_picture']  
            if file and allowed_file(file.filename):  
                filename = secure_filename(file.filename)  
                filename = f"user_{user_id}_{filename}"  
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)  
                file.save(filepath)  
                # Update user's profile_picture in the database  
                db.execute("UPDATE users SET profile_picture = ? WHERE id = ?", (filename, user_id))  
                db.commit()  
  
        return redirect(url_for("user_profile"))  
  
    return render_template("user_profile.html", user=user)  
  
@app.route("/settings", methods=["GET", "POST"])  
def settings():  
    if "user_id" not in session:  
        return redirect(url_for("login"))  
  
    db = get_db()  
    user_id = session["user_id"]  
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()  
  
    if request.method == "POST":  
        # Handle settings update  
        notifications_enabled = 1 if request.form.get("notifications_enabled") == 'on' else 0  
        db.execute("UPDATE users SET notifications_enabled = ? WHERE id = ?", (notifications_enabled, user_id))  
        db.commit()  
        return redirect(url_for("settings"))  
  
    return render_template("settings.html", user=user)  
  
if __name__ == "__main__":  
    with app.app_context():  
        init_db()  
    app.run(debug=True)  