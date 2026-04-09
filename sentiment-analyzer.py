import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.title("📊 Madsion Mallards & Night Mares Survey Sentiment Analyzer")

st.write("Upload survey Excel files and generate sentiment insights.")

# -------------------------
# FILE UPLOAD
# -------------------------

uploaded_files = st.file_uploader(
    "Upload survey Excel files",
    type=["xlsx"],
    accept_multiple_files=True
)

# -------------------------
# USER INPUT FOR COLUMNS
# -------------------------

review_columns = st.text_area(
    "Review Columns (comma separated)",
    """What improvements can be made to the food and beverage experience from a fan perspective?,
Please provide any additional comments on on-field promotions you enjoyed, did not enjoy, or would like to see in the future.,
What was your favorite part of coming to the Mallards game?"""
)

rating_columns = st.text_area(
    "Rating Columns (comma separated)",
    """Overall, how was your ticketing experience?,
Overall, what was your food and beverage experience?,
Overall, what was your experience in the Paul Davis Team Store?,
Overall, please rate the On-Field Promotions on a scale of 1 to 10.,
On a scale of 1-10, how good of a value would you say your Mallards game experience was?"""
)

run_button = st.button("Run Sentiment Analysis")

# -------------------------
# SENTIMENT ANALYZER
# -------------------------

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(review, rating):

    if pd.notna(rating):
        if rating >= 6:
            return "Positive"
        elif rating <= 4:
            return "Negative"
        else:
            return "Neutral"

    if isinstance(review, str):
        score = analyzer.polarity_scores(review)["compound"]

        if score > 0.05:
            return "Positive"
        elif score < -0.05:
            return "Negative"

    return "Neutral"


# -------------------------
# PROCESS FILES
# -------------------------

if run_button:

    if not uploaded_files:
        st.warning("Please upload at least one Excel file.")
        st.stop()

    # Clean user input column lists
    review_cols = [c.strip() for c in review_columns.split(",") if c.strip()]
    rating_cols = [c.strip() for c in rating_columns.split(",") if c.strip()]

    combined_data = []

    for file in uploaded_files:

        st.subheader(f"Processing {file.name}")

        df = pd.read_excel(file)

        # Normalize column names
        df.columns = df.columns.str.strip()

        # Debug: show detected columns
        st.write("Detected columns:", df.columns.tolist())

        # Convert rating columns to numeric
        for col in rating_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        sentiments = []

        for _, row in df.iterrows():

            sentiment = "Neutral"

            # Check rating columns first
            for col in rating_cols:
                if col in df.columns and pd.notna(row[col]):
                    sentiment = get_sentiment(None, row[col])
                    if sentiment != "Neutral":
                        break

            # If still neutral, check review text
            if sentiment == "Neutral":
                for col in review_cols:
                    if col in df.columns and pd.notna(row[col]):
                        sentiment = get_sentiment(row[col], None)
                        if sentiment != "Neutral":
                            break

            sentiments.append(sentiment)

        df["Sentiment"] = sentiments

        # Debug: show sentiment distribution per file
        st.write("Sentiment counts:", df["Sentiment"].value_counts())

        combined_data.append(df)

        st.success(f"{file.name} processed")

    # -------------------------
    # COMBINE DATA
    # -------------------------

    final_df = pd.concat(combined_data, ignore_index=True)

    st.subheader("Data Preview")
    st.dataframe(final_df.head())

    # -------------------------
    # FILTER UI
    # -------------------------

    st.subheader("Filter Results")

    sentiment_filter = st.selectbox(
        "Filter by Sentiment",
        ["All","Positive","Neutral","Negative"]
    )

    if sentiment_filter != "All":
        filtered_df = final_df[final_df["Sentiment"] == sentiment_filter]
    else:
        filtered_df = final_df

    st.dataframe(filtered_df)

    # -------------------------
    # SENTIMENT DISTRIBUTION
    # -------------------------

    st.subheader("Sentiment Distribution")

    sentiment_counts = final_df["Sentiment"].value_counts()
    st.bar_chart(sentiment_counts)

    # -------------------------
    # CREATE UPDATED EXCEL FILE
    # -------------------------

    import io

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Sentiment Results")

    output.seek(0)

    # -------------------------
    # DOWNLOAD BUTTON
    # -------------------------

    st.download_button(
        label="Download Updated Excel File",
        data=output,
        file_name="survey_with_sentiment.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("Excel file with sentiment analysis is ready for download.")
