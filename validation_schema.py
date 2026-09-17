import pandas as pd
import pandera.pandas as pa

CAMPAIGN_MAP = {
    1: "Welcome to the club",
    2: "You almost completed your order",
    3: "Offers tailored just for you",
    4: "Thanks for choosing us",
    5: "Our monthly newsletter",
}

CAMPAIGN_NAMES = list(CAMPAIGN_MAP.values())


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


# opened_at before send_date
def check_opened_after_send(df: pd.DataFrame) -> pd.Series:
    return df["opened_date"].isna() | (df["opened_date"] >= df["send_date"])


# clicked_at before opened_at and invalid click/open relationship
def check_clicked_after_opened(df: pd.DataFrame) -> pd.Series:
    no_click = df["clicked_date"].isna()
    valid_click = df["opened_date"].notna() & (df["clicked_date"] >= df["opened_date"])
    return no_click | valid_click


# transaction_date before send_date
def check_transaction_after_send(df: pd.DataFrame) -> pd.Series:
    return df["transaction_date"].isna() | (df["transaction_date"] >= df["send_date"])


# mismatched campaign_id - campaign_name
def check_campaign_id_matches_name(df: pd.DataFrame) -> pd.Series:
    expected_names = df["campaign_id"].map(CAMPAIGN_MAP)
    return df["campaign_name"] == expected_names


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
        "send_date": pa.Column(pa.Date, coerce=True),
        "opened_date": pa.Column(pa.Date, coerce=True, nullable=True),
        "clicked_date": pa.Column(pa.Date, coerce=True, nullable=True),
        "bounced": pa.Column(bool, pa.Check.isin(["True", "False"])),
        "transaction_id": pa.Column(
            pd.Int64Dtype,
            pa.Check(is_valid_id, element_wise=True),
            nullable=True,
            unique=True,
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
        pa.Check(
            check_campaign_id_matches_name,
            error="campaign_id inconsistent with campaign_name",
        ),
    ],
)


raw_df = pd.read_csv("data/email_marketing_dataset.csv")

try:
    validated = raw_email_schema.validate(raw_df, lazy=True)
    print("All rows passed.")
except pa.errors.SchemaErrors as exc:
    failed_idx = exc.failure_cases["index"].dropna().unique()
    rejected_df = raw_df.loc[failed_idx]

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
