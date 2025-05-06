import sys
import os
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib.parse
import html
from flask import Flask, render_template, jsonify, request, url_for, session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Corrected Flask app initialization
app = Flask(__name__, static_folder="static", template_folder="./")
app.secret_key = os.urandom(24) # Needed for session management

DATA_FILE = os.path.join(app.static_folder, "trivia_data.json")
# GEO_QUIZ_FILE = os.path.join(app.static_folder, "geo_quiz_data.json") # Static file, replaced by API
OPENTDB_API_URL = "https://opentdb.com/api.php"

def load_data(filepath):
    """Loads JSON data from a file."""
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
    """Renders the main page with trivia data."""
    trivia_data = load_data(DATA_FILE)
    # Ensure keys exist even if loading fails or data is partial
    events = trivia_data.get("events", [])
    movies = trivia_data.get("movies", [])
    music = trivia_data.get("music", [])
    # sports = trivia_data.get("sports", []) # Old generic sports
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
                           # sports=sports, # Old generic sports
                           movie_source_info=movie_source_info,
                           tv_shows=tv_shows,
                           hockey_news=hockey_news,
                           baseball_news=baseball_news,
                           tennis_news=tennis_news,
                           golf_news=golf_news)
@app.route("/update_data", methods=["POST"])
def update_data():
    """Triggers the data processing script (currently re-processes static files)."""
    script_path = os.path.join(os.path.dirname(__file__), "..", "process_data.py")
    venv_python = os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python3.11")
    project_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Check if process_data.py exists
    if not os.path.exists(script_path):
        return jsonify({"success": False, "message": "Processing script not found."}), 500

    # Check if venv python exists
    if not os.path.exists(venv_python):
         # Fallback to system python if venv not found (might happen in some deployment scenarios)
         venv_python = "python3.11" 

    try:
        # Run the script using the virtual environment's Python
        print(f"Running update script: {venv_python} {script_path} in {project_dir}")
        # Change directory to project root before running script
        result = os.system(f"cd \"{project_dir}\" && \"{venv_python}\" \"{script_path}\"") 
        if result == 0:
            return jsonify({"success": True, "message": "Trivia data refreshed successfully."})
        else:
             return jsonify({"success": False, "message": f"Data processing script failed with exit code {result}."}), 500
    except Exception as e:
        print(f"Error running update script: {e}")
        return jsonify({"success": False, "message": f"Error running update script: {e}"}), 500

@app.route("/search_category", methods=["GET"])
def search_category():
    """Handles category search requests by scraping Google search results."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Query parameter is missing"}), 400

    # Make the search query more specific for trivia questions
    search_query = f"trivia questions and answers about {query}"
    encoded_query = urllib.parse.quote_plus(search_query)
    search_url = f"https://www.google.com/search?q={encoded_query}&num=20"  # Request more results
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    results = []
    try:
        print(f"Fetching search results from: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Search response status: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")

        # Google's structure changes, so this needs to be adaptable.
        # Common patterns for search result blocks:
        # Older: div class="g", div class="srg"
        # Newer: div with data-hveid attribute, or complex nested structures.
        # We'll try a few common selectors for the main result items.
        # This is still fragile and a more robust solution might involve a search API.

        # Attempt 1: Find divs that often contain individual search results.
        # Look for divs that seem to encapsulate a single search result.
        # Common classes (these can change!): "g", "Gx5Zad", "rc", "kvgmc"
        # For simplicity, let's try a broader approach first, then refine if needed.
        
        # Let's look for common containers for search results
        # This selector might need adjustment if Google changes its layout.
        # It targets divs that are likely to be individual search result containers.
        result_blocks = soup.find_all("div", class_=lambda x: x and ("g " in x or "Gx5Zad" in x or "rc" in x or "kvgmc" in x or "V7sr0" in x or "sVXRqc" in x)) 
        if not result_blocks:
            # Fallback to a more generic div if specific classes fail
            result_blocks = soup.find_all("div", class_="g") # A very common old class

        print(f"Found {len(result_blocks)} potential result blocks.")

        for block in result_blocks:
            title_tag = block.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # Snippet can be in various places, often a div following the title's parent link
            # Trying to find a div that contains descriptive text
            snippet_tag = None
            # Common snippet class names (also change often): "VwiC3b", "s3v9rd", "st", "IsZvec"
            possible_snippet_parents = block.find_all("div", class_=lambda x: x and ("VwiC3b" in x or "s3v9rd" in x or "IsZvec" in x or "MUxGbd" in x))
            if possible_snippet_parents:
                for psp in possible_snippet_parents:
                    # Check if this div is not a parent of another result block
                    if not psp.find("div", class_=lambda x: x and ("g " in x or "Gx5Zad" in x or "rc" in x or "kvgmc" in x or "V7sr0" in x or "sVXRqc" in x)):
                        snippet_text_candidate = psp.get_text(separator=" ", strip=True)
                        if snippet_text_candidate and len(snippet_text_candidate) > 20:
                            snippet_tag = psp # Use the first good one
                            break
            
            snippet = snippet_tag.get_text(separator=" ", strip=True) if snippet_tag else None

            if snippet and "?" in snippet and len(snippet) > 25: # Prioritize snippets that look like questions
                if snippet not in results:
                    results.append(snippet)
            elif title and snippet and len(snippet) > 25: # Combine title and snippet if snippet is substantial
                combined = f"{title}: {snippet}"
                if combined not in results:
                    results.append(combined)
            elif title and "?" in title: # If title itself is a question
                 if title not in results:
                    results.append(title)

            if len(results) >= 20: # Aim for up to 20 results
                break
        
        # If very few results, try a broader text search within the page for question marks
        if len(results) < 5:
            print("Few results from structured search, trying broader text search.")
            all_text = soup.get_text(separator="\n", strip=True)
            potential_questions = []
            for line in all_text.split("\n"):
                line = line.strip()
                if "?" in line and len(line) > 20 and len(line) < 300: # Filter for question-like lines
                    # Avoid common non-trivia questions
                    if not any(phrase in line.lower() for phrase in ["what is", "how to", "can i", "where is", "sign in", "privacy", "terms"]):
                        potential_questions.append(line)
            
            for pq in potential_questions:
                if pq not in results:
                    results.append(pq)
                    if len(results) >= 20:
                        break

        if not results:
            results.append(f"Could not find enough relevant trivia questions for \'{query}\'. Try a different or more specific category.")
        
        print(f"Final number of results for query \'{query}\': {len(results)}")
        results = results[:20] # Ensure max 20 results

    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results for \'{query}\': {e}")
        return jsonify({"error": f"Failed to fetch search results: {e}"}), 500
    except Exception as e:
        print(f"Error parsing search results for \'{query}\': {e}")
        return jsonify({"error": f"Failed to parse search results: {e}"}), 500

    return jsonify(results)
@app.route("/geo_quiz/fetch_questions", methods=["GET"])
def fetch_geo_questions_from_api():
    """Fetches geography quiz questions from OpenTDB API."""
    amount = 50 # As requested by user
    category = 22 # Geography
    difficulty = request.args.get("difficulty", "any") # easy, medium, hard, or any
    q_type = request.args.get("type", "any") # multiple, boolean, or any

    params = {
        "amount": amount,
        "category": category,
    }
    if difficulty != "any":
        params["difficulty"] = difficulty
    if q_type != "any":
        params["type"] = q_type
    
    # Use default encoding as per user request (no 'encode' parameter needed for default)

    try:
        response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4XX or 5XX)
        data = response.json()

        if data.get("response_code") == 0:
            processed_questions = []
            for idx, q_data in enumerate(data.get("results", [])):
                # Decode HTML entities
                question_text = html.unescape(q_data.get("question"))
                correct_answer = html.unescape(q_data.get("correct_answer"))
                incorrect_answers = [html.unescape(ans) for ans in q_data.get("incorrect_answers", [])]
                
                options = incorrect_answers + [correct_answer]
                random.shuffle(options) # Shuffle options for display
                
                processed_questions.append({
                    "id": f"api_{idx}_{random.randint(1000,9999)}", # Create a unique ID for session tracking within this batch
                    "question": question_text,
                    "options": options,
                    "answer": correct_answer,
                    "type": q_data.get("type"),
                    "difficulty": q_data.get("difficulty"),
                    "category": q_data.get("category")
                    # No image_url for OpenTDB questions unless we want to try and find some based on question text (out of scope for now)
                })
            
            # Store this batch in session to serve one by one
            session["current_geo_quiz_batch"] = processed_questions
            session["seen_in_batch_geo_questions"] = [] # Reset seen list for the new batch
            return jsonify({"success": True, "message": f"{len(processed_questions)} questions fetched successfully.", "count": len(processed_questions)})
        else:
            error_message = f"OpenTDB API Error (Code: {data.get('response_code')}): "
            if data.get('response_code') == 1: error_message += "Not enough questions for your query."
            elif data.get('response_code') == 2: error_message += "Invalid API parameter."
            elif data.get('response_code') == 5: error_message += "Rate limit exceeded. Please wait 5 seconds."
            else: error_message += "Unknown API error."
            return jsonify({"success": False, "error": error_message}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch questions from OpenTDB: {e}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {e}"}), 500

@app.route("/geo_quiz/question", methods=["GET"])
def get_geo_question():
    """Gets a random geography quiz question from the current fetched batch, ensuring no repeats within the batch."""
    current_batch = session.get("current_geo_quiz_batch", [])
    if not current_batch:
        return jsonify({"error": "No questions fetched yet. Please fetch a new set of questions.", "end_of_batch": True}), 404

    seen_in_batch_ids = session.get("seen_in_batch_geo_questions", [])
    
    available_questions = [q for q in current_batch if q.get("id") not in seen_in_batch_ids]

    if not available_questions:
        # All questions in the current batch have been seen
        return jsonify({"error": "All questions in the current batch have been answered. Fetch a new set?", "end_of_batch": True}), 200

    question = random.choice(available_questions)
    
    seen_in_batch_ids.append(question.get("id"))
    session["seen_in_batch_geo_questions"] = seen_in_batch_ids
    
    # OpenTDB questions don't have images by default
    question["image_url"] = None 
        
    return jsonify(question)

if __name__ == "__main__":
    # Make sure to run on 0.0.0.0 to be accessible externally
    app.run(host="0.0.0.0", port=5000, debug=True) 

