import sys
import os
import json
import re
import random
import time # Added for simulating update delay
from flask import Flask, render_template, jsonify, request, url_for

# Assuming info_search_web can be called somehow, or we simulate it.
# For now, we will create a placeholder function.
# In a real scenario, this would involve calling the search tool or an external API.
def perform_dynamic_search(category):
    """Placeholder function to simulate dynamic search for trivia questions."""
    print(f"Simulating search for category: {category}")
    # Simulate finding some results
    results = []
    for i in range(15):
        results.append({
            "question": f"What is a notable fact about {category} #{i+1}?",
            "answer": f"This is a simulated answer for {category} fact {i+1}."
        })
    # Add a bit more variety
    results.append({
        "question": f"Who is a famous person associated with {category}?",
        "answer": f"Simulated Famous Person for {category}"
    })
    results.append({
        "question": f"What is a key date related to {category}?",
        "answer": f"Simulated Key Date for {category}"
    })
    return results[:20] # Limit to 20 results as requested

# Placeholder for the actual data update logic
def update_all_trivia_data():
    """Placeholder function to simulate re-gathering and processing all trivia data."""
    print("Simulating data update process...")
    # In a real implementation, this function would:
    # 1. Call functions to scrape/fetch new data for events, music, movies, sports.
    # 2. Save the raw data to temporary files or process directly.
    # 3. Call parsing functions (like those in process_data.py) to create the new trivia_data.json.
    time.sleep(5) # Simulate time taken for fetching and processing
    print("Data update simulation complete.")
    # For this simulation, we don't actually change the file.
    # A real version would overwrite src/static/trivia_data.json
    return True # Indicate success

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__, template_folder=".", static_folder="static")

# Load trivia data from JSON file
def load_json_data(filename):
    filepath = os.path.join(app.static_folder, filename)
    try:
        with open(filepath, "r") as f:
            # Use a cache-busting technique or signal frontend to reload
            # For now, just re-read the file.
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading {filename}: {e}")
        return None

# Global variables to hold loaded data
trivia_data = load_json_data("trivia_data.json") or {}
geo_quiz_questions = load_json_data("geo_quiz_data.json") or []

@app.route("/")
def index():
    # Pass the current loaded data to the template
    # Data might be stale if not updated recently
    global trivia_data
    # Ensure trivia_data is fresh if it was updated
    # trivia_data = load_json_data("trivia_data.json") or {} # Re-load on each request? Or only after update?
    return render_template("index.html", 
                           current_events=trivia_data.get("current_events", []), 
                           music=trivia_data.get("music", {}),
                           movies=trivia_data.get("movies", []),
                           sports=trivia_data.get("sports", {}))

@app.route("/api/search_category", methods=["GET"])
def search_category():
    category = request.args.get("query", "")
    if not category:
        return jsonify({"error": "Query parameter is required"}), 400
    
    # Perform the dynamic search (using placeholder for now)
    results = perform_dynamic_search(category)
    
    return jsonify({"category": category, "results": results})

@app.route("/api/geo_quiz/question", methods=["GET"])
def get_geo_question():
    if not geo_quiz_questions:
        return jsonify({"error": "No geography questions available"}), 500
    
    question = random.choice(geo_quiz_questions)
    
    # Construct full image URL if applicable
    question_for_user = question.copy()
    if question_for_user.get("image"):
        if not question_for_user["image"].startswith(("http", "/")):
             try:
                 question_for_user["image_url"] = url_for("static", filename=question_for_user["image"].replace("static/", "", 1))
             except RuntimeError:
                 question_for_user["image_url"] = "/" + question_for_user["image"] # Fallback
        else:
             question_for_user["image_url"] = question_for_user["image"]
    else:
        question_for_user["image_url"] = None

    # Return question without the correct answer
    if "correct_answer" in question_for_user:
        del question_for_user["correct_answer"]
        
    return jsonify(question_for_user)

@app.route("/api/geo_quiz/check_answer", methods=["POST"])
def check_geo_answer():
    data = request.get_json()
    if not data or "question_id" not in data or "answer" not in data:
        return jsonify({"error": "Missing question_id or answer"}), 400

    question_id = data["question_id"]
    user_answer = data["answer"]

    # Find the question by ID
    question = next((q for q in geo_quiz_questions if q.get("id") == question_id), None)

    if not question:
        return jsonify({"error": "Question not found"}), 404

    correct_answer = question.get("correct_answer")
    is_correct = (user_answer == correct_answer)

    return jsonify({"correct": is_correct, "correct_answer": correct_answer})


@app.route("/api/update_data", methods=["POST"])
def trigger_update_data():
    global trivia_data # Allow modification of the global variable
    success = update_all_trivia_data() # Call the placeholder update function
    if success:
        # Re-load data into memory after update simulation
        trivia_data = load_json_data("trivia_data.json") or {}
        return jsonify({"message": "Data update simulated successfully. Reload the page to see potential changes."}), 200
    else:
        return jsonify({"message": "Data update simulation failed."}), 500

# Example route for getting raw data (optional, for debugging/API use)
@app.route("/api/data")
def get_data():
    return jsonify(trivia_data)

if __name__ == "__main__":
    # Make sure it runs on 0.0.0.0 to be accessible externally if needed
    app.run(host="0.0.0.0", port=5000)

