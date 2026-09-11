## Project description  
What does it do
Where the data comes from


## Quick Start
Clone the repo:  
`git clone https://github.com/IreneGrisenti/Validation_with_Pandera.git`    

Create and activate a virtual environment:  
`cd Validation_with_Pandera`    
`python -m venv .venv`  

`source .venv/bin/activate` (for macOS/Linux)  
or  
`.venv\Scripts\Activate` (for Windows PowerShell)  

Install dependencies:  
`python -m pip install -r requirements.txt`  


## Environment  
Python 3.13.7  
Packages: Jupyter, Pandas, Pandera (see `requirements.txt`)  


## How to run the program
Run the entire notebook to se the test examples.

Run the pipeline from the project root to see the proof of concept:   
`python main.py`


## Project structure

```text
Validation_with_Pandera/
├── data/
├── output/
│
├── pandera_exploration.ipynb   
├── validation_schema.py
├── main.py
├── leaning_notes.md
├── README.md
└── requirements.txt
```