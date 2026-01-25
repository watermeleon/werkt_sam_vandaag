

## Extract Sam's schedule and auto-generate HTML code
A friend of mine, Sam, has a confusing schedule and I like to bother him, however, lately I never know if he's working or not. 
Therefore I have created this repo, to create easy viewable html code from the pdfs of his schedule he sends me. 

### Steps:

```
# 1. Extract all sams schedules from the pdfs (ignore all other names)
python auto_process_all_pdfs.py

# 2. Turn the pdfs into easily viewable HTML code
python schedule_html_generator.py
```

## Understanding the code:

- `cell_detector.py` : Loads the pdf and tries to find all the cells through using pdfplumber. 
    - The dificulty is that pdfplumber is not perfect for tables. I had the issue that values from different rows were interfering. To fix this we auto set that the separation based on the name column (which was done right every time), should extend to the other columns. 
- `schedule_extractor_minimal.py` : After cell_detector.py, this code will select the relevant shifts per employee. 
    - We also provide the code which year and month we are in, for clean output of the data per shift
- `auto_process_all_pdfs.py` : Will run the schedule extractor for all the pdfs in "./pdfs/" folder. It will detect the location and the month from the pdf filename.
- `schedule_html_generator.py` : Will generate the html. It also has the logic, mentioning which shift values mean what. E.g. "N": "Nachtdienst".