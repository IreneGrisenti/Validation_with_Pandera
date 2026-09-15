## Project description  
What does it do


## Data
Since email campaign data with transaction data attached is not publicly available for privacy reasons, I generated a synthetic dataset instead (`data/fake_email_marketing_dataset_300_rows.csv`).  
It simulates 300 recipient-level records of an email marketing campaign.  

20% of the rows were corrupted with one of 12 validation error types to give the Pandera schema a meaningful set of failures to catch. 
The clean values, injected errors and the validation rule each error breaks are logged in `data/fake_email_marketing_injected_errors.csv`

| Column name | Dtype | Description |
|---|---|---|
| `recipient_id` | integer | Unique identifier for the recipient |
| `recipient_name` | string | Name of the recipient |
| `recipient_email` | string | Email address of the recipient |
| `campaign_id` | integer | Unique identifier for the email campaign |
| `campaign_name` | string | Name of the email campaign |
| `campaign_type` | string | Type of email campaign |
| `send_date` | datetime | Date and time the email campaign was sent |
| `opened_at` | datetime | Date and time the recipient opened the email |
| `clicked_at` | datetime | Date and time the recipient clicked a link in the email |
| `bounced` | boolean | Indicates whether the email bounced |
| `transaction_id` | integer | Unique identifier for the transaction |
| `transaction_date` | date | Date of the transaction |
| `transaction_amount` | float | Amount of the transaction |

Injected errors:
- Negative or zero `transaction_amount`
- `transaction_amount` wrong type (non-numeric string)
- Malformed `recipient_email`
- Missing required field (`recipient_name` or `campaign_name`)
- Duplicate `transaction_id`
- Invalid `campaign_type` (value outside the 5 allowed categories)
- `campaign_id` / `campaign_name` mismatch
- `transaction_date` before `send_date`
- `opened_at` / `clicked_at` before `send_date`
- Invalid click/open relationship (`clicked_at` without `opened_at`, or `clicked_at` before `opened_at`)
- Invalid boolean value for `bounced`
- Negative or non-integer `recipient_id` / `campaign_id`

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
│   ├── fake_email_marketing_dataset_300_rows.csv
│   └── fake_email_marketing_injected_errors.csv
├── output/
│
├── pandera_exploration.ipynb   
├── validation_schema.py
├── main.py
├── learning_notes.md
├── README.md
└── requirements.txt
```