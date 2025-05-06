import json
import re
import os

def parse_markdown_links(text):
    """Parses markdown links like [Text](URL)"""
    links = re.findall(r'\[(.*?)\]\((.*?)\)', text)
    return links

def process_current_events(input_file, output_file):
    """Processes the markdown current events file into JSON, extracting links."""
    events = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.split('---\n')
        
        for block in blocks:
            if not block.strip() or block.startswith("#"):
                continue
                
            headline_match = re.search(r'\*\*Headline:\*\* \[(.*?)\]\((.*?)\)', block)
            summary_match = re.search(r'\*\*Summary:\*\* (.*?)(?=\n\*\*|$)', block, re.DOTALL)
            date = "May 3-5, 2025" # Placeholder date

            if headline_match:
                headline_text = headline_match.group(1).strip()
                headline_url = headline_match.group(2).strip()
                summary = summary_match.group(1).strip() if summary_match else "No summary available."
                
                events.append({
                    "headline": headline_text,
                    "url": headline_url,
                    "summary": summary,
                    "date": date
                })

    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
        return None
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return None

    print(f"Successfully processed {len(events)} current events")
    return {"events": events} 

def process_movies_final_v13(input_file, output_file):
    """Processes the markdown movie data file into JSON using string methods (v13 - Final)."""
    movies = []
    source_info = "Unknown Date"
    current_movie = None
    print("--- Starting Movie Processing (Final v13) ---")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines):
            line = line.strip()

            if not line:
                if current_movie:
                    movies.append(current_movie)
                    current_movie = None
                continue

            if line.startswith("# Top Movies"):
                match = re.search(r'\((.*?)\)', line)
                if match: source_info = match.group(1).strip()
                continue
            if line.startswith("Source:"):
                continue

            # Check for title line based on debug findings (starts/ends with **, contains number.)
            is_title = False
            if line.startswith("**") and (line.endswith("**") or line.endswith("***")):
                # Extract content between the double asterisks
                inner_content = line[2:-2] if line.endswith("**") else line[2:-3]
                
                # Split at the first period
                if '.' in inner_content:
                    parts = inner_content.split('.', 1)
                    rank_str = parts[0].strip()
                    if rank_str.isdigit():
                        rank = int(rank_str)
                        title = parts[1].strip()
                        is_title = True
                        
                        if current_movie: # Save previous movie
                            movies.append(current_movie)
                        
                        current_movie = {
                            "rank": rank,
                            "title": title,
                            "weekend_gross": "N/A",
                            "total_gross": "N/A",
                            "weeks_released": "N/A",
                            "summary": "",
                            "stars": "N/A"
                        }
                        continue # Move to next line after finding title
            
            # Check for detail line if not a title and inside a movie block
            if not is_title and current_movie and line.startswith("*   "):
                detail_line = line[4:]
                if detail_line.startswith("**Weekend Gross:**"): 
                    current_movie["weekend_gross"] = detail_line.split(":**", 1)[1].strip()
                elif detail_line.startswith("**Total Gross:**"): 
                    current_movie["total_gross"] = detail_line.split(":**", 1)[1].strip()
                elif detail_line.startswith("**Weeks Released:**"): 
                    current_movie["weeks_released"] = detail_line.split(":**", 1)[1].strip()
                elif detail_line.startswith("**Summary:**"): 
                    current_movie["summary"] = detail_line.split(":**", 1)[1].strip()
                elif detail_line.startswith("**Stars:**"): 
                    current_movie["stars"] = detail_line.split(":**", 1)[1].strip()
                continue
            
            # If line is not blank, not header, not title, and not a detail line for the current movie,
            # it might indicate the end of the previous movie block if one was active.
            elif not is_title:
                if current_movie:
                    movies.append(current_movie)
                    current_movie = None

        # Append the last movie after loop finishes
        if current_movie:
            movies.append(current_movie)
            
        # Clean up summaries
        for movie in movies:
            movie["summary"] = movie["summary"].strip()
            if not movie["summary"]:
                 movie["summary"] = "No summary available."

    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
        return None
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return None

    movies.sort(key=lambda x: x.get('rank', float('inf')))
    print(f"--- Finished Movie Processing (Final v13) ---")
    print(f"Successfully processed {len(movies)} movies (final string methods v13)")
    return {"movies": movies, "movie_source_info": source_info}

def process_simple_data(input_file, output_file, section_key):
    data_list = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            if lines and lines[0].startswith("#"):
                lines = lines[1:]
            data_list = lines 
    except FileNotFoundError:
        print(f"Warning: Input file {input_file} not found. Skipping.")
        return None
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return None

    print(f"Successfully processed {len(data_list)} items for {section_key}")
    return {section_key: data_list}

if __name__ == "__main__":
    static_dir = "src/static"
    os.makedirs(static_dir, exist_ok=True)
    
    combined_data = {}

    events_data = process_current_events(os.path.join(static_dir, "current_events.txt"), os.path.join(static_dir, "current_events.json"))
    if events_data: combined_data.update(events_data)

    # --- Process Movies (Step 018 - Final v13) ---
    movies_data = process_movies_final_v13(os.path.join(static_dir, "movie_data.txt"), os.path.join(static_dir, "movie_data.json"))
    if movies_data: combined_data.update(movies_data)
    # ---------------------------------------------

    music_data = process_simple_data(os.path.join(static_dir, "music_data.txt"), os.path.join(static_dir, "music_data.json"), "music")
    if music_data: combined_data.update(music_data)

    sports_data = process_simple_data(os.path.join(static_dir, "sports_news.txt"), os.path.join(static_dir, "sports_news.json"), "sports")
    if sports_data: combined_data.update(sports_data)
        
    combined_output_file = os.path.join(static_dir, "trivia_data.json")
    try:
        with open(combined_output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2)
        print(f"Successfully combined data into {combined_output_file}")
    except Exception as e:
        print(f"Error writing combined JSON to {combined_output_file}: {e}")

