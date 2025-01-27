import json
import time
import pickle 
import argparse
import requests
import subprocess
from keys import *
import pandas as pd
from typing import Dict, Any, Tuple, List
from datetime import datetime
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException


def save_dict(dictionary: Dict, dictionary_name: str, verbose: bool=False) -> None:
    """
    Save a dictionary to a pickle file.

    Args:
        dictionary (Dict): The dictionary to save.
        dictionary_name (str): The name of the file to save the dictionary to.
        verbose (bool, optional): Enable verbose output. Defaults to False.
    """
    with open(f'{dictionary_name}.pkl', 'wb') as f:
        pickle.dump(dictionary, f)
    if verbose:
        print(f'Dictionary saved as "{dictionary_name}.pkl"')

def load_dict(dictionary_name: str) -> Dict:
    """
    Load a dictionary from a pickle file.

    Args:
        dictionary_name (str): The name of the file to load the dictionary from.

    Returns:
        Dict: The loaded dictionary.
    """
    with open(f'{dictionary_name}.pkl', 'rb') as f:
        loaded_dict = pickle.load(f)
    return loaded_dict

def google_search(query: str, api_key: str, search_engine_id: str, **kwargs: Any) -> Dict:
    """
    Perform a Google search using the Custom Search JSON API.

    Args:
        query (str): The search query.
        api_key (str): API key for the Google Custom Search JSON API.
        search_engine_id (str): Search engine ID to use for the search.
        **kwargs: Additional parameters for the search.

    Returns:
        Dict: JSON response from the Google Custom Search API.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': search_engine_id,
        **kwargs
    }
    
    response = requests.get(url, params=params)
    return response.json()

def get_links(query: str, api_key: str, search_engine_id: str, lim: int = 1, **kwargs: Any) -> str:
    """
    Get the first link from the Google search results.

    Args:
        query (str): The search query.
        api_key (str): API key for the Google Custom Search JSON API.
        search_engine_id (str): Search engine ID to use for the search.
        lim (int, optional): Limit for the number of items to process. Defaults to 1.
        **kwargs: Additional parameters for the search.

    Returns:
        str: The first link from the search results.
    """
    results = google_search(query, api_key, search_engine_id, **kwargs)
    return results.get('items', [])[0]['link']

def duckduckgo_search(query: str, **kwargs: Any) -> str:
    """
    Perform a search using the DuckDuckGo Instant Answer API with a backoff mechanism.

    Args:
        query (str): The search query.
        **kwargs: Additional parameters for the search.

    Returns:
        str: URL of the first search result.
    """
    max_retries = 10
    initial_delay = 5

    for attempt in range(max_retries):
        try:
            results = DDGS().text(f'{query} BC', region='ca-en', safesearch='off', 
                                  timelimit='n', max_results=1)
            return results[0]['href']
        except DuckDuckGoSearchException as e:
            if "Ratelimit" in str(e) and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                print(f"Rate limit hit. Waiting {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                raise
    raise DuckDuckGoSearchException("Max retries reached. Unable to complete search.")

def scrap_link(association: str) -> str:
    """
    Scrape the link of an association using a subprocess call to scraper.py.

    Args:
        association (str): The name of the association.

    Returns:
        str: The scraped link of the association.
    """
    source_link = f'https://duckduckgo.com/?t=h_&q={association.replace(" ", "+")}&ia=web'
    prompt = f"find the link of {association}"
    
    result = subprocess.run(['python3', 'scraper.py', '-prompt', prompt, 
                             '-source', source_link],
                            capture_output=True, text=True)
    l1 = result.stdout
    l2 = json.loads(l1)
    link = l2['link']
    return link

def find_websites(source_link: str, search_engine="ddg", verbose : bool=False) -> tuple:
    """
    Find the names and links of the first n associations from the source link.

    Args:
        source_link (str): Source link to scrape the associations from.
        search_engine (str, optional): Search engine to use for the search.

    Returns:
        tuple: A tuple containing a list of association names and a list of their corresponding links.
    """

    prompt = f"find the names of all the associations listed in the website {source_link}"
    
    result = subprocess.run(['python3', 'scraper.py', '-prompt', prompt, 
                             '-source', source_link],
                            capture_output=True, text=True)
    if verbose:
        print(f'Finding the names of the associations done.')

    if result.stdout:
        resdict = json.loads(result.stdout)
        NPs_names = resdict[list(resdict.keys())[0]]
    else:
        return result.stderr
    
    NPs_links = {}
    for n in range(len(NPs_names)):
        np = NPs_names[n]
        print(f'{n+1}/{len(NPs_names)} | {np}')
        if search_engine == 'google':
            NPs_links[np] = google_search(np, search_api_key, search_engine_id, lim=1)
        elif search_engine == 'ddg':
            NPs_links[np] = duckduckgo_search(np)
        elif search_engine == 'gemini':
            NPs_links[np] = scrap_link(np)
    
    if verbose:
        print(f'Finding the links of the associations done.')

    return NPs_names, NPs_links

def get_np_info(limit: int, links: List[str], NPs_names: List[str], verbose: bool=False) -> Dict:
    """
    Get information about non-profit organizations.

    Args:
        limit (int): Limit for the number of items to process.
        links (List[str]): List of links to the non-profit organizations.
        NPs_names (List[str]): List of names of the non-profit organizations.
        verbose (bool, optional): Enable verbose output. Defaults to False.

    Returns:
        Dict: Dictionary containing information about the non-profit organizations.
    """
    NPs_dict = {}
    prompt = "find these infos about the no-profit organization:\
              name, location, type, description, size, contacts, linkedin.\
              For linkedin, give the link;\
              for type, select the field where the no-prift operates, e.g. health, environment, etc. Keep it to one, max two words."
    
    for n in range(limit):
        source_link = links[n]
        name = NPs_names[n]
        result = subprocess.run(['python3', 'scraper.py', '-prompt', prompt, 
                                 '-source', source_link],
                                capture_output=True, text=True)
        
        if result.stdout:
            NPs_dict[name] = json.loads(result.stdout)
            NPs_dict[name]['name'] = name
            NPs_dict[name]['link'] = source_link.rsplit('/', 1)[0]
        else:
            print(f"{n+1}/{limit} | {name}\n{result.stderr}")
        
        if verbose:
            print(f'{n+1}/{limit} | done with {name}')

    return NPs_dict

def create_database(NPs_dict: Dict, verbose: bool=False) -> pd.DataFrame:
    """
    Create a database from the given dictionary of non-profit associations.

    Args:
        NPs_dict (Dict): Dictionary containing non-profit associations data.

    Returns:
        pd.DataFrame: DataFrame containing the non-profit associations data.
    """
    db = pd.DataFrame(columns=['name', 'location', 'description', 'size', 
                               'contacts', 'social_media', 'link'])

    for key in NPs_dict.keys():
        NPs_dict[key]['contacts'] = str(NPs_dict[key]['contacts'])[1:-1]
        df = pd.DataFrame(NPs_dict[key], index=[0])
        db = pd.concat([db, df], ignore_index=True)
    
    if verbose:
        print('Database created.')
    
    return db

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Run the automation script with given parameters.')
    parser.add_argument('-n', '--n_associations', type=int, required=True, help='Number of associations to process')
    parser.add_argument('-l', '--limit', type=int, required=True, help='Limit for the number of items to process')
    parser.add_argument('-s', '--source_link', type=str, required=True, help='Source link for the associations')
    parser.add_argument('-p', '--path', type=str, default='../', help='Path to database directory')
    parser.add_argument('-v', '--verbose', type=bool, default=False, help='Enable verbose output')
    return parser.parse_args()


def save_db(db: pd.DataFrame, path: str, verbose: bool=True) -> None:
    """ 
    Save the database to a CSV file. 
    """ 
    dt = datetime.now().strftime("%Y%m%d-%H%M")[2:]
    path = path
    db.to_csv(f'{path}associations_{dt}.csv', index=False)
    if verbose:
        print(f'Database saved to "{path}" as\n"associations_{dt}.csv"')


def main(n_associations: int, limit: int, path: str, verbose: bool) -> pd.DataFrame:
    """
    Main function to run the automation script.

    Args:
        n_associations (int): Number of associations to process.
        limit (int): Limit for the number of items to process.
        source_link (str): Source link for the associations.
        verbose (bool): Enable verbose output.

    Returns:
        pd.DataFrame: DataFrame containing the non-profit associations data.
    """
    start = datetime.now()
    dbd = load_dict(f'{path}/links')
    NPs_names = list(dbd.keys())[:n_associations]
    links = [f'{dbd[np]}/about' for np in NPs_names]
    NPs_dict = get_np_info(limit, links, NPs_names, verbose)
    db = create_database(NPs_dict)
    end = datetime.now()
    
    if verbose:
        print(f'\nTime taken: {end - start}')
    
    return db

if __name__ == "__main__":

    args = parse_arguments()
    db = main(args.n_associations, args.limit, args.source_link, args.verbose)
    save_db(db=db, verbose=args.verbose, path=args.path)
    
    if args.verbose:
        print(db)