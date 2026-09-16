import pandas as pd
import pandera.pandas as pa

CAMPAIGN_NAMES = ['Welcome to the club', 'You almost completed your order', 'Offers tailored just for you', 'Thanks for choosing us', 'Our monthly newsletter']
CAMPAIGN_TYPES = ['welcome', 'abandoned cart', 'promo', 'transactional', 'newsletter']

def is_valid_amount(x):
    try:
        return float(x) > 0
    except (ValueError, TypeError):
        return False

def is_valid_id(x):
    try:
        return int(x) > 0
    except (ValueError, TypeError):
        return False

email_schema = pa.DataFrameSchema({
    'recipient_id': pa.Column(
        str, 
        pa.Check(is_valid_id, 
        element_wise=True)),
    'recipient_name': pa.Column(str, coerce=True),
    'recipient_email': pa.Column(str, pa.Check.str_matches(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$'), coerce=True),
    'campaign_id': pa.Column(int, pa.Check.greater_than(0), coerce=True),
    'campaign_name': pa.Column(str, pa.Check.isin(CAMPAIGN_NAMES), coerce=True),
    'campaign_type': pa.Column(str, pa.Check.isin(CAMPAIGN_TYPES), coerce=True),
    'send_date': pa.Column(pa.DateTime, coerce=True),
    'opened_at': pa.Column(pa.DateTime, coerce=True, nullable=True),
    'clicked_at': pa.Column(pa.DateTime, coerce=True, nullable=True),
    'bounced': pa.Column(str, pa.Check.isin(['True', 'False'])),
    'transaction_id': pa.Column(
        float, 
        pa.Check(is_valid_id, element_wise=True),
        nullable=True,
        unique=True),
    'transaction_date': pa.Column(pa.Date, coerce=True, nullable=True), 
    'transaction_amount': pa.Column(
        str,
        pa.Check(is_valid_amount, element_wise=True),
        nullable=True)
})


df = pd.read_csv('data/fake_email_marketing_dataset_300_rows.csv')

try:
    validated = email_schema.validate(df, lazy=True)
    print("All rows passed.")
except pa.errors.SchemaErrors as exc:
    print(exc.failure_cases)

df.info()