import sys
import os
import json
import random
import requests
import html # Import the html module
from flask import Flask, render_template, jsonify, request, session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__, static_folder="static", template_folder="./")
app.secret_key = os.urandom(24)

DATA_FILE = os.path.join(app.static_folder, "trivia_data.json")
OPENTDB_API_URL = "https://opentdb.com/api.php"
OPENTDB_CATEGORIES_URL = "https://opentdb.com/api_category.php"

def load_data(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found at {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred loading {filepath}: {e}")
        return {}

@app.route("/")
def index():
    trivia_data = load_data(DATA_FILE)
    events = trivia_data.get("events", [])
    movies = trivia_data.get("movies", [])
    music = trivia_data.get("music", [])
    movie_source_info = trivia_data.get("movie_source_info", "Unknown Date")
    tv_shows = trivia_data.get("tv_shows", [])
    hockey_news = trivia_data.get("hockey_news", [])
    baseball_news = trivia_data.get("baseball_news", [])
    tennis_news = trivia_data.get("tennis_news", [])
    golf_news = trivia_data.get("golf_news", [])
    
    return render_template("index.html", 
                           events=events, 
                           movies=movies, 
                           music=music, 
                           movie_source_info=movie_source_info,
                           tv_shows=tv_shows,
                           hockey_news=hockey_news,
                           baseball_news=baseball_news,
                           tennis_news=tennis_news,
                           golf_news=golf_news)

@app.route("/update_data", methods=["POST"])
def update_data_route(): # Renamed to avoid conflict with function name 'update_data'
    script_path = os.path.join(os.path.dirname(__file__), "..", "process_data.py")
    venv_python = os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python3.11")
    project_dir = os.path.dirname(os.path.dirname(__file__))
    
    if not os.path.exists(script_path):
        return jsonify({"success": False, "message": "Processing script not found."}), 500

    if not os.path.exists(venv_python):
         venv_python = "python3.11"

    try:
        print(f"Running update script: {venv_python} {script_path} in {project_dir}")
        result = os.system(f"cd \"{project_dir}\" && \"{venv_python}\" \"{script_path}\"") 
        if result == 0:
            return jsonify({"success": True, "message": "Trivia data refreshed successfully."})
        else:
             return jsonify({"success": False, "message": f"Data processing script failed with exit code {result}."}), 500
    except Exception as e:
        print(f"Error running update script: {e}")
        return jsonify({"success": False, "message": f"Error running update script: {e}"}), 500

# --- Start: Updated Trivia Quiz API Endpoints ---
@app.route("/api/get_trivia_categories", methods=["GET"])
def get_trivia_categories():
    """Fetches all trivia categories from OpenTDB."""
    try:
        response = requests.get(OPENTDB_CATEGORIES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        categories = data.get("trivia_categories", [])
        if not categories:
            return jsonify({"success": False, "error": "Could not fetch trivia categories from API."}), 500
        return jsonify({"success": True, "categories": categories})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trivia categories: {e}")
        return jsonify({"success": False, "error": f"Failed to fetch categories: {e}"}), 500
    except Exception as e:
        print(f"Unexpected error fetching categories: {e}")
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500

@app.route("/api/fetch_quiz_questions", methods=["GET"])
def fetch_quiz_questions_from_api():
    """Fetches quiz questions from OpenTDB API based on category and difficulty."""
    amount = 50
    category_id = request.args.get("category") # Expecting category ID
    difficulty = request.args.get("difficulty", "any")
    q_type = request.args.get("type", "any") # Retain type flexibility, default to any

    params = {"amount": amount}
    if category_id and category_id.lower() != "any" and category_id.isdigit():
        params["category"] = int(category_id)
    if difficulty and difficulty.lower() != "any":
        params["difficulty"] = difficulty
    if q_type and q_type.lower() != "any":
        params["type"] = q_type

    try:
        response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("response_code") == 0:
            processed_questions = []
            for idx, q_data in enumerate(data.get("results", [])):
                question_text = html.unescape(q_data.get("question"))
                correct_answer = html.unescape(q_data.get("correct_answer"))
                incorrect_answers = [html.unescape(ans) for ans in q_data.get("incorrect_answers", [])]
                
                options = incorrect_answers + [correct_answer]
                random.shuffle(options)
                
                processed_questions.append({
                    "id": f"api_q_{idx}_{random.randint(1000,9999)}",
                    "question": question_text,
                    "options": options,
                    "answer": correct_answer,
                    "type": q_data.get("type"),
                    "difficulty": q_data.get("difficulty"),
                    "category": q_data.get("category")
                })
            
            if not processed_questions:
                session["current_quiz_batch"] = []
                session["seen_in_batch_questions"] = []
                return jsonify({"success": False, "error": "The API returned no questions for your selected criteria. Please try different options."}), 200
            
            session["current_quiz_batch"] = processed_questions
            session["seen_in_batch_questions"] = []
            return jsonify({"success": True, "message": f"{len(processed_questions)} questions fetched successfully.", "count": len(processed_questions)})
        else:
            error_message = f"OpenTDB API Error (Code: {data.get("response_code")}): "
            if data.get("response_code") == 1: error_message += "Not enough questions for your query."
            elif data.get("response_code") == 2: error_message += "Invalid API parameter."
            elif data.get("response_code") == 5: error_message += "Rate limit exceeded. Please wait ~5 seconds."
            else: error_message += "Unknown API error."
            return jsonify({"success": False, "error": error_message}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch questions from OpenTDB: {e}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500

@app.route("/api/get_quiz_question", methods=["GET"])
def get_quiz_question():
    """Gets a random quiz question from the current fetched batch."""
    current_batch = session.get("current_quiz_batch", [])
    if not current_batch:
        return jsonify({"error": "No questions fetched yet. Please fetch a new set.", "end_of_batch": True}), 404

    seen_in_batch_ids = session.get("seen_in_batch_questions", [])
    available_questions = [q for q in current_batch if q.get("id") not in seen_in_batch_ids]

    if not available_questions:
        return jsonify({"error": "All questions in this batch have been answered. Fetch a new set?", "end_of_batch": True}), 200

    question = random.choice(available_questions)
    seen_in_batch_ids.append(question.get("id"))
    session["seen_in_batch_questions"] = seen_in_batch_ids
    question["image_url"] = None # OpenTDB is text-based
    return jsonify(question)

# --- End: Updated Trivia Quiz API Endpoints ---

# --- Start: Category Search (Free Text - Placeholder for future implementation) ---
@app.route("/api/search_trivia_freetext", methods=["GET"])
def search_trivia_freetext():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    # Placeholder for Option C: Experimental Web Search
    # This will be implemented in a later step as per the plan.
    print(f"Received free-text search query: {query}. Implementation pending.")
    # For now, return a message indicating it's not yet implemented or a dummy response.
    return jsonify([f"Free-text search for \"{query}\" is under development. Please check back later."])
# --- End: Category Search ---


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

