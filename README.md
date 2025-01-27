# noProfit_dataBase

Scripts to create a database with non-profit organizations information.

## Overview

This project contains scripts to scrape information about non-profit organizations from various sources and compile the data into a structured database. The main script automates the process of finding, scraping, and storing information about non-profit organizations.

## Files

### `automation.py`

This is the main script that orchestrates the entire process. It includes functions to:

- Parse command-line arguments.
- Find websites of non-profit organizations.
- Scrape information from these websites.
- Create a database from the scraped information.

#### Key Functions:

- `parse_arguments()`: Parses command-line arguments.
- `find_websites(n_associations, source_link)`: Finds the names and links of the first `n` associations from the source link.
- `get_np_info(limit, links, NPs_names, verbose)`: Gets information about non-profit organizations.
- `create_database(NPs_dict)`: Creates a database from the given dictionary of non-profit associations.
- `main(n_associations, limit, source_link, verbose)`: Main function to run the automation script.

### `scraper.py`

This script is used to scrape specific information from a given source link based on a provided prompt. It is called by the `automation.py` script to perform the actual scraping.

### `keys.py`

This file contains API keys and other sensitive information required for the scripts to function. It is not included in the repository for security reasons.

### `README.md`

This file provides an overview of the project and explanations of the files in the directory.

## Usage

To run the main script, use the following command:

```sh
python3 automation.py -n <number_of_associations> -l <limit> -s <source_link> [-v]
```

### Arguments:

- `-n`, `--n_associations`: Number of associations to process.
- `-l`, `--limit`: Limit for the number of items to process.
- `-s`, `--source_link`: Source link for the associations.
- `-v`, `--verbose`: Enable verbose output (optional).

### Example:

```sh
python3 automation.py -n 10 -l 10 -s "https://www.amcnposolutions.com/directory-of-canadian-not-for-profit-associations/bc-a-to-c/" -v
```

In alternative, one can use the `run.sh` file. Just modify it appropriately and run it from terminal.

### Dependencies

- `requests`
- `pandas`
- `argparse`
- `subprocess`
- `json`
- `pickle`
- `datetime`
- `duckduckgo_search`

Make sure to install the required dependencies before running the scripts.

### License

This project is licensed under the MIT License.