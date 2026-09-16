import pandas as pd
import pandera.pandas as pa

CAMPAIGN_NAMES = [
    "Welcome to the club",
    "You almost completed your order",
    "Offers tailored just for you",
    "Thanks for choosing us",
    "Our monthly newsletter",
]
CAMPAIGN_TYPES = ["welcome", "abandoned cart", "promo", "transactional", "newsletter"]


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


# campaign_id / campaign_name mismatch


# opened_at before send_date
def check_opened_after_send(df):
    return df["opened_date"].isna() | (df["opened_date"] >= df["send_date"])


# clicked_at before opened_at and invalid click/open relationship 
def check_clicked_after_opened(df):
    no_click = df["clicked_date"].isna()
    valid_click = df["opened_date"].notna() & (df["clicked_date"] >= df["opened_date"])
    return no_click | valid_click


# transaction_date before send_date
def check_transaction_after_send(df):
    return df["transaction_date"].isna() | (df["transaction_date"] >= df["send_date"])


raw_email_schema = pa.DataFrameSchema(
    {
        "recipient_id": pa.Column(int, pa.Check(is_valid_id, element_wise=True)),
        "recipient_name": pa.Column(str, coerce=True),
        "recipient_email": pa.Column(
            str, pa.Check.str_matches(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$"), coerce=True
        ),
        "campaign_id": pa.Column(
            int, pa.Check(is_valid_id, element_wise=True), coerce=True
        ),
        "campaign_name": pa.Column(str, pa.Check.isin(CAMPAIGN_NAMES), coerce=True),
        "campaign_type": pa.Column(str, pa.Check.isin(CAMPAIGN_TYPES), coerce=True),
        "send_date": pa.Column(pa.Date, coerce=True),
        "opened_date": pa.Column(pa.Date, coerce=True, nullable=True),
        "clicked_date": pa.Column(pa.Date, coerce=True, nullable=True),
        "bounced": pa.Column(bool, pa.Check.isin(["True", "False"])),
        "transaction_id": pa.Column(
            pd.Int64Dtype, pa.Check(is_valid_id, element_wise=True), nullable=True, unique=True
        ),
        "transaction_date": pa.Column(pa.Date, coerce=True, nullable=True),
        "transaction_amount": pa.Column(
            float, pa.Check(is_valid_amount, element_wise=True), nullable=True
        ),
    },
    checks=[
        pa.Check(
            check_transaction_after_send, error="transaction_date before send_date"
        ),
        pa.Check(check_opened_after_send, error="opened_at before send_date"),
        pa.Check(check_clicked_after_opened, error="clicked_at before opened_at"),
    ],
)


df = pd.read_csv("data/fake_email_marketing_dataset_300_rows.csv")

try:
    validated = raw_email_schema.validate(df, lazy=True)
    print("All rows passed.")
except pa.errors.SchemaErrors as exc:
    failed_idx = exc.failure_cases["index"].dropna().unique()
    rejected_df = df.loc[failed_idx]

    reasons = (
        exc.failure_cases.dropna(subset=["index"])
        .groupby("index")
        .apply(
            lambda g: "; ".join(
                f"{r.column}: {r.check} (got {r.failure_case})" for r in g.itertuples()
            )
        )
    )

    rejected_rows_with_reason_df = rejected_df.copy()
    rejected_rows_with_reason_df = rejected_rows_with_reason_df.sort_index()
    rejected_rows_with_reason_df["rejection_reason"] = (
        rejected_rows_with_reason_df.index.map(reasons)
    )

    print(rejected_df)

    rejected_rows_with_reason_df.to_csv("output/rejected_rows_log.csv", index=True)
