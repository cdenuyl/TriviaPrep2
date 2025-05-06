import sys
import os
import json
import random
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify, request, url_for

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Corrected Flask app initialization
app = Flask(__name__, static_folder="static", template_folder="./")

DATA_FILE = os.path.join(app.static_folder, "trivia_data.json")
GEO_QUIZ_FILE = os.path.join(app.static_folder, "geo_quiz_data.json")

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
    sports = trivia_data.get("sports", [])
    movie_source_info = trivia_data.get("movie_source_info", "Unknown Date")
    
    return render_template("index.html", 
                           events=events, 
                           movies=movies, 
                           music=music, 
                           sports=sports,
                           movie_source_info=movie_source_info)

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

    search_query = f"trivia questions about {query}"
    # Corrected line: Use single quotes inside the f-string's replace method
    search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    results = []
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to find search result descriptions (this is fragile and might break)
        # Google often uses divs with specific classes, but these change.
        
        # Example 1: Look for divs that might contain result snippets (Class names are examples and change frequently)
        potential_snippet_classes = ["BNeawe", "s3v9rd", "AP7Wnd"] # Common classes, but unreliable
        for class_name in potential_snippet_classes:
             snippets = soup.find_all("div", class_=class_name)
             for snippet in snippets:
                 text = snippet.get_text(separator=" ", strip=True)
                 if text and len(text) > 20 and "?" in text: # Basic filter for question-like text
                     # Avoid adding duplicates
                     if text not in results:
                         results.append(text)
                         if len(results) >= 15:
                             break
             if len(results) >= 15:
                 break       
        
        # Example 2: Fallback - Look for text in paragraph tags if few results found
        if len(results) < 10:
             paragraphs = soup.find_all("p")
             for p in paragraphs:
                 text = p.get_text(strip=True)
                 # Basic filtering for relevance (very crude)
                 if query.lower() in text.lower() and "?" in text and len(text) > 20:
                     # Avoid adding duplicates
                     if text not in results:
                         results.append(text)
                         if len(results) >= 15:
                             break

        # If still no results, return a message
        if not results:
            results.append(f"Could not find trivia questions for '{query}'. Try a different category.")
        
        # Limit to 15 results
        results = results[:15]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching search results: {e}")
        return jsonify({"error": f"Failed to fetch search results: {e}"}), 500
    except Exception as e:
        print(f"Error parsing search results: {e}")
        return jsonify({"error": f"Failed to parse search results: {e}"}), 500

    return jsonify(results)

@app.route("/geo_quiz/question", methods=["GET"])
def get_geo_question():
    """Gets a random geography quiz question."""
    geo_data = load_data(GEO_QUIZ_FILE)
    if not geo_data or not isinstance(geo_data, list):
        return jsonify({"error": "Could not load geography quiz data."}), 500
    
    question = random.choice(geo_data)
    # Ensure image path is correct for web access
    if "image" in question and question["image"]:
        # Assuming image path is relative to static folder, e.g., "images/world_map_outline.png"
        question["image_url"] = url_for("static", filename=question["image"])
    else:
        question["image_url"] = None
        
    return jsonify(question)

if __name__ == "__main__":
    # Make sure to run on 0.0.0.0 to be accessible externally
    app.run(host="0.0.0.0", port=5000, debug=True) 

