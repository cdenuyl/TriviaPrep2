import requests
import json

BASE_URL = "http://127.0.0.1:5000" # Assuming Flask runs on default port locally

# --- Test Trivia Quiz (OpenTDB API) ---
def test_trivia_quiz():
    print("--- Testing Trivia Quiz (OpenTDB API) ---")
    session = requests.Session() # Use a session to maintain Flask session context

    # 1. Fetch a batch of questions (Geography, Easy)
    print("\n1. Fetching batch of Geography questions (Easy)...")
    fetch_params = {"difficulty": "easy"} # Category is hardcoded to Geography (22) in the route
    try:
        response_fetch = session.get(f"{BASE_URL}/geo_quiz/fetch_questions", params=fetch_params, timeout=20)
        response_fetch.raise_for_status()
        data_fetch = response_fetch.json()
        print(f"Fetch Response Status: {response_fetch.status_code}")
        print(f"Fetch Response JSON: {json.dumps(data_fetch, indent=2)}")
        
        if data_fetch.get("success") and data_fetch.get("count", 0) > 0:
            print(f"Successfully fetched {data_fetch.get(\"count\")} questions.")
            # 2. Get a few individual questions from the batch
            for i in range(min(3, data_fetch.get("count", 0))):
                print(f"\n2.{i+1}. Getting an individual question from the batch...")
                response_question = session.get(f"{BASE_URL}/geo_quiz/question", timeout=10)
                response_question.raise_for_status()
                data_question = response_question.json()
                print(f"Individual Question Response Status: {response_question.status_code}")
                print(f"Individual Question JSON: {json.dumps(data_question, indent=2)}")
                if data_question.get("error") and data_question.get("end_of_batch"):
                    print("Reached end of batch or error retrieving question.")
                    break
                elif data_question.get("error"):
                    print(f"Error getting individual question: {data_question.get(\"error\")}")
                    break
        elif data_fetch.get("error"):
            print(f"Error fetching batch: {data_fetch.get(\"error\")}")
        else:
            print("Fetched batch, but no questions or success not true.")

    except requests.exceptions.RequestException as e:
        print(f"RequestException during quiz test: {e}")
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError during quiz test: {e} - Response text: {response_fetch.text if 'response_fetch' in locals() else 'N/A'}")
    except Exception as e:
        print(f"An unexpected error occurred during quiz test: {e}")

    # Test "no questions found" scenario (e.g., by trying to fetch again too quickly or if API has no questions)
    # This is harder to reliably trigger without knowing API specifics for empty results on valid category
    # The backend logic for handling empty `processed_questions` list was added.

# --- Test Free-text Category Search (Google Scraping) ---
def test_category_search():
    print("\n\n--- Testing Free-text Category Search (Google Scraping) ---")
    search_queries = ["famous painters", "world capitals", "chemistry facts"]
    for query in search_queries:
        print(f"\n1. Searching for trivia on: ", query)
        search_params = {"query": query}
        try:
            response_search = requests.get(f"{BASE_URL}/search_category", params=search_params, timeout=20)
            response_search.raise_for_status()
            data_search = response_search.json()
            print(f"Search Response Status: {response_search.status_code}")
            print(f"Search Response JSON (first 3 results if many):")
            if isinstance(data_search, list):
                for i, item in enumerate(data_search[:3]):
                    print(f"  Result {i+1}: {item}")
                if len(data_search) > 3:
                    print(f"  ... and {len(data_search) - 3} more results.")
                if not data_search or (len(data_search) == 1 and "Could not find enough relevant trivia questions" in data_search[0]):
                    print(f"Warning: Search for ", query, " returned no/few relevant results or an error message.")
            else:
                print(f"  Unexpected response format: {json.dumps(data_search, indent=2)}")
        except requests.exceptions.RequestException as e:
            print(f"RequestException during category search for ", query, ": {e}")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError during category search for ", query, ": {e} - Response text: {response_search.text if 'response_search' in locals() else 'N/A'}")
        except Exception as e:
            print(f"An unexpected error occurred during category search for ", query, ": {e}")

if __name__ == "__main__":
    # Important: Ensure the Flask app (main.py) is running locally on port 5000 before executing this script.
    print("Starting tests... Make sure your Flask application (main.py) is running on http://127.0.0.1:5000")
    test_trivia_quiz()
    test_category_search()
    print("\nTests completed. Review output above.")

