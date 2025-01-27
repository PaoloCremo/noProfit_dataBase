import json
import argparse
from scrapegraphai.graphs import SmartScraperGraph
from keys import *

# Define the configuration for the scraping pipeline
graph_config = {
    "llm": {
        "model": "google_genai/gemini-1.5-flash-latest",
        "api_key": gemini_api_key,
        
    },
    "verbose": True,
    "headless": True,
}

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run SmartScraperGraph with given prompt and source.')
parser.add_argument('-prompt', type=str, required=True, help='The prompt for the scraper')
parser.add_argument('-source', type=str, required=True, help='The source URL for the scraper')
args = parser.parse_args()

# Create the SmartScraperGraph instance
smart_scraper_graph = SmartScraperGraph(
    prompt=args.prompt,
    source=args.source,
    config=graph_config
)

# Run the pipeline
result = smart_scraper_graph.run()

print(json.dumps(result, indent=4))