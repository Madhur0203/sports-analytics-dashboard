import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Sports Analytics Dashboard", layout="wide")

st.title("Sports Analytics Dashboard")
st.write("Select a dataset and click the button to run analysis.")

urls = {
    "nba_2021": "https://www.basketball-reference.com/leagues/NBA_2021.html",
    "nba_2022": "https://www.basketball-reference.com/leagues/NBA_2022.html",
    "nba_2023": "https://www.basketball-reference.com/leagues/NBA_2023.html",
    "nba_2024": "https://www.basketball-reference.com/leagues/NBA_2024.html",
    "premier_league_2023": "https://fbref.com/en/comps/9/PL/2022-2023-Premier-League-Stats",
}

table_ids = {
    "nba_2021": "per_game-team",
    "nba_2022": "per_game-team",
    "nba_2023": "per_game-team",
    "nba_2024": "per_game-team",
    "premier_league_2023": "stats_standard",
}

headers = {"User-Agent": "Mozilla/5.0"}

def fetch_table(url, table_id):
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", id=table_id)

    if not table:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if table_id in comment:
                comment_soup = BeautifulSoup(comment, "html.parser")
                table = comment_soup.find("table", id=table_id)
                if table:
                    break

    if not table:
        st.error("Could not find the table on the page.")
        return None

    headers_list = [th.text.strip() for th in table.thead.find_all("th") if th.text.strip() != "Rk"]
    rows = []

    for row in table.tbody.find_all("tr"):
        if row.get("class") and "thead" in row["class"]:
            continue
        cols = row.find_all("td")
        stats = [td.text.strip() for td in cols]
        if len(stats) == len(headers_list):
            rows.append(stats)

    return pd.DataFrame(rows, columns=headers_list)

dataset = st.selectbox("Choose dataset", list(urls.keys()))

if st.button("Run Analysis"):
    with st.spinner("Fetching and analyzing data..."):
        df = fetch_table(urls[dataset], table_ids[dataset])

    if df is not None and not df.empty:
        st.success("Data loaded successfully.")

        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)

        if "PTS" in df.columns:
            df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
            df = df.dropna(subset=["PTS"])

            st.subheader("Summary Statistics")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Mean", f"{df['PTS'].mean():.2f}")
            c2.metric("Median", f"{df['PTS'].median():.2f}")
            c3.metric("Mode", f"{df['PTS'].mode().iloc[0] if not df['PTS'].mode().empty else 'N/A'}")
            c4.metric("Min", f"{df['PTS'].min():.2f}")
            c5.metric("Max", f"{df['PTS'].max():.2f}")

            top10 = df.sort_values("PTS", ascending=False).head(10)

            st.subheader("Top 10 Teams by Points")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=top10, x="PTS", y="Team", hue="Team", legend=False, ax=ax1)
            st.pyplot(fig1)

            st.subheader("Points Distribution")
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.histplot(df["PTS"], kde=True, bins=15, ax=ax2)
            st.pyplot(fig2)
        else:
            st.warning("This dataset does not contain a PTS column, so no stats/charts were generated.")