"""
Proof of concept for schema-based data validation using Pandera.

Validates a raw email-marketing CSV against `raw_email_schema`.
Rows that fail validation are logged with their rejection reasons and dropped. The remaining rows are re-validated to confirm the cleaned subset conforms to the schema.
"""

import pandas as pd
import pandera.pandas as pa
from validation_schema import raw_data_schema

DATA_PATH = "data/email_marketing_dataset.csv"
REJECTED_LOG_PATH = "output/rejected_rows_log.csv"
VALIDATED_PATH = "output/validated_rows.csv"


@pa.check_output(raw_data_schema, lazy=True)
def load_raw(path: str) -> pd.DataFrame:
    """Loads the raw CSV. Raises SchemaErrors if it doesn't match the schema requirements."""
    return pd.read_csv(path, encoding="utf-8")


def format_reasons(g: pd.DataFrame) -> str:
    """Build one readable rejection reason per failed row, deduplicating schema-level checks so they appear only once."""
    seen = set()
    parts = []
    for r in g.itertuples():
        key = r.check if r.schema_context == "DataFrameSchema" else (r.column, r.check)
        if key in seen:
            continue
        seen.add(key)
        detail = (
            f" (got: {r.failure_case})" if r.schema_context != "DataFrameSchema" else ""
        )
        parts.append(f"col: {r.column}, broken check: {r.check}{detail}")
    return "; ".join(parts)


def build_rejection_report(
    raw_df: pd.DataFrame, failure_cases: pd.DataFrame
) -> pd.DataFrame:
    """Attach a human-readable rejection reason to each failed row."""
    failed_idx = failure_cases["index"].dropna().unique()
    rejected_df = raw_df.loc[failed_idx].sort_index().copy()

    reasons = (
        failure_cases.dropna(subset=["index"]).groupby("index").apply(format_reasons)
    )

    rejected_df["rejection_reason"] = rejected_df.index.map(reasons.to_dict())
    return rejected_df


def main():

    raw_df = pd.read_csv(DATA_PATH)
    print("Starting validation of raw data.")

    try:
        validated_df = load_raw(DATA_PATH)

        print(f"All {len(raw_df)} rows passed validation.")

        validated_df.to_csv(VALIDATED_PATH, index=True)

        return

    except pa.errors.SchemaErrors as exc:

        rejected_df = build_rejection_report(raw_df, exc.failure_cases)
        rejected_df.to_csv(REJECTED_LOG_PATH, index=True)

        print(f"{len(rejected_df)} of {len(raw_df)} rows failed validation.")
        print(f"Rejection log written to {REJECTED_LOG_PATH}")

    # Drop the rejected rows
    clean_df = raw_df.drop(index=rejected_df.index)

    try:
        validated_df = raw_data_schema.validate(clean_df, lazy=True)

        print(f"{len(validated_df)} rows passed validation after dropping rejected.")

        validated_df.to_csv(VALIDATED_PATH, index=True)

    except pa.errors.SchemaErrors as exc:

        print("Unexpected: some rows still fail after dropping rejected.")
        print(exc.failure_cases)


if __name__ == "__main__":
    main()
