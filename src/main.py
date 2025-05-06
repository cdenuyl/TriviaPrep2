import sys
import os
import json
import random
import requests
from bs4 import BeautifulSoup
import re # For category search (though likely to be removed)
import html
from flask import Flask, render_template, jsonify, request, url_for, session

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Corrected Flask app initialization
app = Flask(__name__, static_folder="static", template_folder="./")
app.secret_key = os.urandom(24) # Needed for session management

DATA_FILE = os.path.join(app.static_folder, "trivia_data.json")
# GEO_QUIZ_FILE = os.path.join(app.static_folder, "geo_quiz_data.json") # Static file, replaced by API
OPENTDB_API_URL = "https://opentdb.com/api.php"
OPENTDB_CATEGORIES_URL = "https://opentdb.com/api_category.php"

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

@app.route("/api/get_trivia_categories", methods=["GET"])
def get_trivia_categories():
    """Fetches the list of trivia categories from OpenTDB."""
    try:
        response = requests.get(OPENTDB_CATEGORIES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        categories = data.get("trivia_categories", [])
        # Add an "Any Category" option for the quiz, not for search
        # For search, user must pick a specific category if using API
        # For quiz, "Any" can be an option that doesn't send a category param to OpenTDB
        # However, the user specifically asked for a dropdown of categories for the quiz too.
        # So, we will just return the categories as is, and the frontend can decide if it wants to add an "Any" option locally.
        return jsonify(categories)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trivia categories: {e}")
        return jsonify({"error": f"Failed to fetch trivia categories: {e}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred while fetching categories: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

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
        return jsonify({"success": False, "message": f"Error running update script: {e}"})

@app.route("/api/search_trivia_by_category", methods=["GET"])
def search_trivia_by_category():
    """Fetches trivia questions from OpenTDB for a specific category."""
    category_id = request.args.get("category_id")
    difficulty = request.args.get("difficulty", "any") # easy, medium, hard, or any
    # q_type = request.args.get("type", "any") # multiple, boolean, or any - For search, let's default to any type
    amount = 20 # Fetch up to 20 questions for search display

    if not category_id:
        return jsonify({"error": "Category ID is required."}), 400

    params = {
        "amount": amount,
        "category": category_id,
    }
    if difficulty != "any":
        params["difficulty"] = difficulty
    # if q_type != "any":
    #     params["type"] = q_type
    
    try:
        response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("response_code") == 0:
            processed_questions = []
            for q_data in data.get("results", []):
                question_text = html.unescape(q_data.get("question"))
                correct_answer = html.unescape(q_data.get("correct_answer"))
                incorrect_answers = [html.unescape(ans) for ans in q_data.get("incorrect_answers", [])]
                
                # For search display, we might just show the question and correct answer
                processed_questions.append({
                    "question": question_text,
                    "answer": correct_answer,
                    "category_name": q_data.get("category"), # OpenTDB includes category name in results
                    "difficulty": q_data.get("difficulty"),
                    "type": q_data.get("type"),
                    "incorrect_answers": incorrect_answers # Keep these in case UI wants to show options
                })
            if not processed_questions:
                 return jsonify([f"No trivia questions found for the selected criteria in category ID {category_id}. Try a different difficulty or category."])
            return jsonify(processed_questions)
        else:
            error_message = f"OpenTDB API Error (Code: {data.get('response_code')}) for category search: "
            if data.get("response_code") == 1: 
                error_message = f"The API doesn\'t have enough questions for category ID {category_id} with difficulty \'{difficulty}\'. Please try different options."
            elif data.get("response_code") == 2: 
                error_message = "Invalid parameter sent to the Trivia API for category search. This is an internal error."
            elif data.get("response_code") == 5: 
                error_message = "You\'re requesting questions too frequently from the API for category search. Please wait and try again."
            else: 
                error_message = f"An unknown error occurred with the Trivia API (Code: {data.get("response_code")}) for category search."
            # Return as a list with a single error string to match expected format of search results
            return jsonify([error_message]) 

    except requests.exceptions.RequestException as e:
        return jsonify([f"Failed to fetch trivia for category search: {e}"])
    except Exception as e:
        return jsonify([f"An unexpected error occurred during category search: {e}"])

# Old search_category route - to be removed or commented out
# @app.route("/search_category", methods=["GET"])
# def search_category():
#     """Handles category search requests by scraping Google search results."""
#     query = request.args.get("query", "")
#     if not query:
#         return jsonify({"error": "Query parameter is missing"}), 400
# 
#     # Make the search query more specific for trivia questions
#     # search_query = f"trivia questions and answers about {query}" # Original
#     search_query = f"trivia questions {query}" # Simpler query
#     encoded_query = urllib.parse.quote_plus(search_query)
#     search_url = f"https://www.google.com/search?q={encoded_query}&num=20&hl=en"  # Request more results, add hl=en for consistency
#     
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#         "Accept-Language": "en-US,en;q=0.9"
#     }
# 
#     results = []
#     try:
#         print(f"Fetching search results for query: \'{search_query}\' from: {search_url}")
#         response = requests.get(search_url, headers=headers, timeout=15)
#         response.raise_for_status()
#         print(f"Search response status: {response.status_code}")
# 
#         # Save HTML for debugging
#         # with open(f"/home/ubuntu/search_results_{query.replace(\' \\[\s\\]+\", \"_\")}.html", "w", encoding="utf-8") as f_html:
#         #     f_html.write(response.text)
#         # print(f"Saved HTML to /home/ubuntu/search_results_{query.replace(\' \\[\s\\]+\", \"_\")}.html")
# 
#         soup = BeautifulSoup(response.text, "html.parser")
# 
#         # Google's structure changes. Try to find main result blocks.
#         # Common container for results is often a div with class 'g' or specific data attributes.
#         # Let's try a more general approach to find potential result blocks.
#         result_blocks = soup.find_all("div", class_="g") # A common container for search results
#         if not result_blocks:
#             # Broader search for divs that might contain results if 'g' is not found
#             result_blocks = soup.find_all("div", jscontroller=True, jsaction=True, data_hveid=True)
#         
#         print(f"Found {len(result_blocks)} potential result blocks using initial selectors.")
# 
#         if not result_blocks: # If still no blocks, try another common pattern
#             result_blocks = soup.select("div.Gx5Zad, div.kvgmc, div.g")
#             print(f"Found {len(result_blocks)} potential result blocks using secondary selectors.")
# 
# 
#         for i, block in enumerate(result_blocks):
#             # print(f"--- Processing Block {i+1} ---")
#             # print(block.prettify()[:500]) # Print first 500 chars of block for inspection
# 
#             title_tag = block.find("h3")
#             title = title_tag.get_text(strip=True) if title_tag else None
#             
#             link_tag = block.find("a", href=True)
#             link = link_tag["href"] if link_tag else None
# 
#             # Try to get a descriptive snippet. Google often uses divs with specific roles or classes.
#             # This part is highly susceptible to changes in Google's HTML structure.
#             snippet_parts = []
#             # Look for text directly within the block, avoiding script/style tags
#             for element in block.find_all(string=True):
#                 if element.parent.name not in ["style", "script", "[document]", "head", "title"] and str(element).strip():
#                     snippet_parts.append(str(element).strip())
#             
#             snippet = " ".join(snippet_parts)
#             # Clean up snippet a bit
#             snippet = re.sub(r"\s+", " ", snippet).strip()
#             
#             # Heuristic: if title is part of the snippet, remove it to avoid redundancy if snippet is long enough
#             if title and snippet.startswith(title) and len(snippet) > len(title) + 10:
#                 snippet = snippet[len(title):].strip(" :-·")
#             
#             # print(f"Title: {title}")
#             # print(f"Link: {link}")
#             # print(f"Raw Snippet: {snippet[:200]}...")
# 
#             # Add to results if it seems like a trivia question or useful fact
#             # Prioritize items with question marks or that seem factual
#             if title and snippet and len(snippet) > 30:
#                 # Check for question marks or keywords like "what is", "who is", "facts about"
#                 if "?" in title or "?" in snippet or any(kw in title.lower() for kw in ["facts", "trivia"]) or any(kw in snippet.lower() for kw in ["facts", "trivia"]):
#                     # Try to format as "Question: Answer" or just the fact
#                     # This is a very basic heuristic
#                     formatted_result = f"{title}: {snippet[:250]}..."
#                     if "?" in title and snippet:
#                         formatted_result = f"{title} - {snippet[:200]}..."
#                     elif "?" in snippet:
#                         formatted_result = snippet[:300]
#                     
#                     if formatted_result not in results:
#                         results.append(formatted_result)
#                         # print(f"Added to results: {formatted_result}")
# 
#             elif title and ("?" in title or any(kw in title.lower() for kw in ["facts", "trivia"])):
#                 if title not in results:
#                     results.append(title)
#                     # print(f"Added title to results: {title}")
#             
#             if len(results) >= 20:
#                 break
#         
#         # If structured search yields few results, try a more general text extraction for lines with question marks
#         if len(results) < 5:
#             print("Few results from structured block search, trying broader text search for questions.")
#             all_text_lines = soup.get_text(separator="\n").split("\n")
#             for line in all_text_lines:
#                 line = line.strip()
#                 if "?" in line and len(line) > 20 and len(line) < 300:
#                     # Avoid common non-trivia questions/navigation text
#                     if not any(phrase in line.lower() for phrase in ["what is your question", "how can i help", "search results for", "related searches", "people also ask", "sign in", "privacy", "terms", "feedback"]):
#                         if line not in results:
#                             results.append(line)
#                             # print(f"Added from broad search: {line}")
#                 if len(results) >= 20:
#                     break
# 
#         if not results:
#             results.append(f"Could not find enough relevant trivia questions for \'{query}\'. Try a different or more specific category.")
#         
#         print(f"Final number of results for query \'{query}\': {len(results)}")
#         results = results[:20] # Ensure max 20 results
# 
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching search results for \'{query}\': {e}")
#         return jsonify({"error": f"Failed to fetch search results: {e}"}), 500
#     except Exception as e:
#         print(f"Error parsing search results for \'{query}\': {e}")
#         return jsonify({"error": f"Failed to parse search results: {e}"}), 500
# 
#     return jsonify(results)

@app.route("/api/fetch_quiz_questions", methods=["GET"])
def fetch_quiz_questions_from_api():
    """Fetches quiz questions from OpenTDB API for a given category and difficulty."""
    amount = 50 # As requested by user
    category_id = request.args.get("category_id") # Will be passed from frontend
    difficulty = request.args.get("difficulty", "any") # easy, medium, hard, or any
    q_type = request.args.get("type", "any") # multiple, boolean, or any

    params = {
        "amount": amount,
    }
    if category_id and category_id.lower() != "any" and category_id != "0": # "0" or "any" might be used for "Any Category"
        params["category"] = category_id
    if difficulty != "any":
        params["difficulty"] = difficulty
    if q_type != "any":
        params["type"] = q_type
    
    # Use default encoding as per user request (no 'encode' parameter needed for default)

    try:
        print(f"Fetching quiz questions with params: {params}")
        response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4XX or 5XX)
        data = response.json()

        if data.get("response_code") == 0:
            processed_questions = []
            for idx, q_data in enumerate(data.get("results", [])):
                question_text = html.unescape(q_data.get("question"))
                correct_answer = html.unescape(q_data.get("correct_answer"))
                incorrect_answers = [html.unescape(ans) for ans in q_data.get("incorrect_answers", [])]
                
                options = incorrect_answers + [correct_answer]
                random.shuffle(options) # Shuffle options for display
                
                processed_questions.append({
                    "id": f"api_quiz_{idx}_{random.randint(1000,9999)}", 
                    "question": question_text,
                    "options": options,
                    "answer": correct_answer,
                    "type": q_data.get("type"),
                    "difficulty": q_data.get("difficulty"),
                    "category": q_data.get("category")
                })
            
            session["current_quiz_batch"] = processed_questions
            session["seen_in_batch_quiz_questions"] = [] 
            return jsonify({"success": True, "message": f"{len(processed_questions)} questions fetched successfully.", "count": len(processed_questions)})
        else:
            error_message = f"OpenTDB API Error (Code: {data.get('response_code')}) for quiz: "
            if data.get('response_code') == 1: 
                error_message = "The API doesn't have enough questions for the selected criteria. Please try different options."
            elif data.get('response_code') == 2: 
                error_message = "Invalid parameter sent to the Trivia API. This is an internal error."
            elif data.get('response_code') == 5: 
                error_message = "You're requesting questions too frequently from the API. Please wait about 10 seconds and try again."
            else: 
                error_message = f"An unknown error occurred with the Trivia API (Code: {data.get('response_code')})."
            return jsonify({"success": False, "error": error_message}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch quiz questions from OpenTDB: {e}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred during quiz question fetching: {e}"}), 500

@app.route("/api/quiz_question", methods=["GET"])
def get_quiz_question():
    """Gets a random quiz question from the current fetched batch, ensuring no repeats within the batch."""
    current_batch = session.get("current_quiz_batch", [])
    if not current_batch:
        return jsonify({"error": "No questions fetched yet. Please fetch a new set of questions.", "end_of_quiz_batch": True}), 404

    seen_in_batch_ids = session.get("seen_in_batch_quiz_questions", [])
    
    available_questions = [q for q in current_batch if q.get("id") not in seen_in_batch_ids]

    if not available_questions:
        return jsonify({"error": "All questions in the current batch have been answered. Fetch a new set?", "end_of_quiz_batch": True}), 200

    question = random.choice(available_questions)
    
    seen_in_batch_ids.append(question.get("id"))
    session["seen_in_batch_quiz_questions"] = seen_in_batch_ids
    
    question["image_url"] = None # OpenTDB questions don't have images by default
        
    return jsonify(question)

if __name__ == "__main__": Test the search_category function
    print("--- Testing search_category with query: colors ---")
    with app.test_request_context("/search_category?query=colors"):
        response_colors = search_category()
        try:
            print(json.dumps(response_colors.get_json(), indent=2))
        except Exception as e:
            print(f"Error printing JSON for colors: {e}")
            print(response_colors.data.decode())

    print("\n--- Testing search_category with query: world capitals ---")
    with app.test_request_context("/search_category?query=world capitals"):
        response_capitals = search_category()
        try:
            print(json.dumps(response_capitals.get_json(), indent=2))
        except Exception as e:
            print(f"Error printing JSON for world capitals: {e}")
            print(response_capitals.data.decode())
    
    print("\n--- Testing search_category with query: science facts ---")
    with app.test_request_context("/search_category?query=science facts"):
        response_science = search_category()
        try:
            print(json.dumps(response_science.get_json(), indent=2))
        except Exception as e:
            print(f"Error printing JSON for science facts: {e}")
            print(response_science.data.decode())

    # print("Starting Flask app...") # Comment out app.run for testing search
    # app.run(host="0.0.0.0", port=5000, debug=True)