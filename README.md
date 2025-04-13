# Movie Scraper
## Setup and Running ##
* make sure python is installed and cd into the same folder as the program.
* install beautiful soup with the command:
```
  python -m pip install beautifulsoup4
```
* make sure to replace api_key.example with your own api key in a file called api_key.txt This can be generated at www.omdbapi.com
* specify targeted profile by changing the profile variable in script.py or specify it when running the program. For example,
```
  python script.py watermullins
```
## Output ##
* movies will be printed line by line as the program searches for film information
* the script will write the results to a json and a csv file.
* the results are written in the order they are read from one's profile, which is chronological from newest to oldest rated films
