import json
import re

def parse_current_events(filepath):
    events = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Simple parsing based on numbered list and source in parentheses
            # Assumes format like "1. [Date]: Event description. (Source)"
            # Or "1. Event description. (Source)"
            matches = re.findall(r"^\*\*(\d+)\.\*\*\s*(?:\*\*(.*?):\*\*\s*)?(.*?)\s*\((.*?)\)", content, re.MULTILINE)
            if not matches:
                 # Try another pattern if the first fails, looking for list items
                 matches = re.findall(r"^\d+\.\s+(?:\*\*(.*?):\*\*\s*)?(.*?)\s*\((.*?)\)", content, re.MULTILINE)

            for match in matches:
                # Adjusting index based on found pattern
                if len(match) == 4: # First pattern with number
                    num, date, desc, source = match
                elif len(match) == 3: # Second pattern without number
                    date, desc, source = match
                    num = None # No number captured
                else:
                    continue # Skip if format doesn't match

                events.append({
                    "id": int(num) if num else None,
                    "date": date.strip() if date else None,
                    "description": desc.strip(),
                    "source": source.strip()
                })
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error parsing current events: {e}")
    return events

def parse_music(filepath):
    music = {"top_songs": []}
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Find source
            source_match = re.search(r"Source: (.*?)\((.*?)\)", content)
            if source_match:
                music['source_name'] = source_match.group(1).strip()
                music['source_url'] = source_match.group(2).strip()

            # Find songs - assumes format "1. Song Title - Artist Name"
            matches = re.findall(r"^(\d+)\.\s+(.*?)\s+-\s+(.*?)$", content, re.MULTILINE)
            for rank, title, artist in matches:
                music["top_songs"].append({
                    "rank": int(rank),
                    "title": title.strip(),
                    "artist": artist.strip()
                })
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error parsing music data: {e}")
    return music

def parse_movies(filepath):
    movies = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # Split content by movie entries, assuming they start with "**[Number]. [Title]**"
            movie_blocks = re.split(r'(?=\n\*\*\d+\.)', content)
            source_name = None
            source_url = None
            source_match = re.search(r"Source: (.*?)\((.*?)\)", movie_blocks[0])
            if source_match:
                source_name = source_match.group(1).strip()
                source_url = source_match.group(2).strip()

            for block in movie_blocks:
                if not block.strip() or block.startswith("#") or block.startswith("Source:"):
                    continue

                movie_data = {"source_name": source_name, "source_url": source_url}
                title_match = re.search(r"^\*\*(\d+)\.\s*(.*?)\*\*", block)
                if title_match:
                    movie_data['rank'] = int(title_match.group(1))
                    movie_data['title'] = title_match.group(2).strip()

                gross_match = re.search(r"Weekend Gross:\*\*\s*(.*?)\n", block)
                if gross_match:
                    movie_data['weekend_gross'] = gross_match.group(1).strip()

                total_gross_match = re.search(r"Total Gross:\*\*\s*(.*?)\n", block)
                if total_gross_match:
                    movie_data['total_gross'] = total_gross_match.group(1).strip()

                summary_match = re.search(r"Summary:\*\*\s*(.*?)\n", block)
                if summary_match:
                    movie_data['summary'] = summary_match.group(1).strip()

                stars_match = re.search(r"Stars:\*\*\s*(.*?)\n", block)
                if stars_match:
                    movie_data['stars'] = [star.strip() for star in stars_match.group(1).split(',')]

                if 'title' in movie_data: # Only add if title was found
                    movies.append(movie_data)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error parsing movie data: {e}")
    return movies

def parse_sports(filepath):
    sports = {"categories": {}}
    current_category = None
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            source_match = re.search(r"Source: (.*?)\((.*?)\)", lines[0])
            if source_match:
                 sports['source_name'] = source_match.group(1).strip()
                 sports['source_url'] = source_match.group(2).strip()

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Source:"):
                    continue

                category_match = re.match(r"^\*\*(.*?):\*\*$", line)
                if category_match:
                    current_category = category_match.group(1)
                    sports["categories"][current_category] = []
                elif line.startswith("*") and current_category:
                    # Extract headline and optional date
                    news_item = line[1:].strip()
                    date_match = re.search(r"\((.*?)\)$", news_item)
                    headline = news_item
                    date = None
                    if date_match:
                        date = date_match.group(1).strip()
                        headline = re.sub(r"\s*\(.*?\)$", "", news_item).strip()

                    sports["categories"][current_category].append({
                        "headline": headline,
                        "date": date
                    })
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
    except Exception as e:
        print(f"Error parsing sports data: {e}")
    return sports

if __name__ == "__main__":
    base_path = "/home/ubuntu/trivia_prep_app/src/static/"
    output_path = base_path + "trivia_data.json"

    all_data = {
        "current_events": parse_current_events(base_path + "current_events.txt"),
        "music": parse_music(base_path + "music_data.txt"),
        "movies": parse_movies(base_path + "movie_data.txt"),
        "sports": parse_sports(base_path + "sports_news.txt")
    }

    try:
        with open(output_path, 'w') as outfile:
            json.dump(all_data, outfile, indent=4)
        print(f"Successfully processed data and saved to {output_path}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")

