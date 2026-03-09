# Author: Madhur Gattani
# Date: 28 April 2025
# Purpose: Final project ITC

# Instructions:
# This project has more charts than the base project which me and my group made. 
# It completes all the requirements without any error and includes additional features that I added.

# 1. If you are running this project in VS Code or any other application, 
# --> Install Python 3.10.7 (as in this version, libraries work properly and don't give any errors)
# 2. If running in Google Colab, you won't have to install any libraries. 
# --> On the left side of Colab, you will see a file option (as a logo). 
#     All the CSV files and graphs will be there. From there, you can check them.

# All computations will be shown in the terminal below.
# After every scraping of webpages, it will display whether the data in the file has changed or is unchanged.
# I have also attached an ITC_Project_checklist.txt to display the checklist of the requirements of the project and what additional features it has.

# Import necessary libraries
import requests  # For making HTTP requests
from bs4 import BeautifulSoup, Comment  # For parsing HTML and handling HTML comments
import pandas as pd  # For data manipulation and analysis
import matplotlib.pyplot as plt  # For creating static, animated, and interactive plots
import seaborn as sns  # For advanced visualizations (built on top of matplotlib)
import os  # For interacting with the operating system (e.g., checking files)
from datetime import datetime  # For getting the current date and time

# Step 1: Define URLs from 5 different websites (including one with daily data change)
urls = {
    "nba_2021": "https://www.basketball-reference.com/leagues/NBA_2021.html",  # NBA 2021 season stats
    "nba_2022": "https://www.basketball-reference.com/leagues/NBA_2022.html",  # NBA 2022 season stats
    "nba_2023": "https://www.basketball-reference.com/leagues/NBA_2023.html",  # NBA 2023 season stats
    "nba_2024": "https://www.basketball-reference.com/leagues/NBA_2024.html",  # NBA 2024 season stats (current)
    "premier_league_2023": "https://fbref.com/en/comps/9/PL/2022-2023-Premier-League-Stats"  # Premier League 2022-2023 stats
}

# Define headers to mimic a real browser request
headers = {"User-Agent": "Mozilla/5.0"}

# Step 2: Define the table IDs we want to scrape from each page
table_ids = {
    "nba_2021": "per_game-team",  # Table ID for NBA 2021
    "nba_2022": "per_game-team",  # Table ID for NBA 2022
    "nba_2023": "per_game-team",  # Table ID for NBA 2023
    "nba_2024": "per_game-team",  # Table ID for NBA 2024
    "premier_league_2023": "stats_standard"  # Table ID for Premier League
}

# Dictionary to store DataFrames after scraping
dataframes = {}

# Step 3: Function to fetch and parse table using BeautifulSoup
def fetch_table(url, table_id):
    response = requests.get(url, headers=headers)  # Make HTTP request
    if response.status_code != 200:  # Check if the response is OK
        print(f"❌ Failed to fetch {url}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')  # Parse HTML
    table = soup.find('table', id=table_id)  # Try finding the table normally

    if not table:
        # Some tables are inside HTML comments, so we need to handle that
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))  # Find all comments
        for comment in comments:
            if table_id in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')  # Parse the comment
                table = comment_soup.find('table', id=table_id)  # Try finding the table inside the comment
                if table:
                    break
    if not table:
        print(f"❌ Table {table_id} not found in {url}")
        return None

    # Extract table headers (excluding "Rk" which is usually just a ranking number)
    headers_list = [th.text.strip() for th in table.thead.find_all('th') if th.text.strip() != "Rk"]
    rows = []
    
    # Extract each row's data
    for row in table.tbody.find_all('tr'):
        if row.get('class') and 'thead' in row['class']:  # Skip header rows within tbody
            continue
        cols = row.find_all('td')  # Get all columns
        stats = [td.text.strip() for td in cols]  # Clean each cell
        if len(stats) == len(headers_list):  # Make sure row matches header length
            rows.append(stats)

    df = pd.DataFrame(rows, columns=headers_list)  # Create DataFrame
    return df

# Step 4: Summarization Function - Calculates basic stats
def summarize_column(df, col_name, label):
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')  # Convert column to numeric
    print(f"\n📊 Summary for {label} - {col_name}")
    print(f"Mean: {df[col_name].mean():.2f}")  # Mean
    print(f"Median: {df[col_name].median():.2f}")  # Median
    print(f"Mode: {df[col_name].mode().iloc[0] if not df[col_name].mode().empty else 'N/A'}")  # Mode
    print(f"Min: {df[col_name].min()}")  # Minimum value
    print(f"Max: {df[col_name].max()}")  # Maximum value

# Step 5: Check if the file data has changed compared to previous run
def check_if_file_changed(filename, new_df, label):
    if not os.path.exists(filename):  # If the file doesn't exist
        print(f"🆕 {filename} created.")
        return
    old_df = pd.read_csv(filename)  # Read old data
    
    # Compare only 'Team' and 'PTS' columns to check for changes
    if "Team" in old_df.columns and "PTS" in old_df.columns:
        old_df = old_df[["Team", "PTS"]]
        new_df_temp = new_df[["Team", "PTS"]]

        changed_rows = []
        merged = old_df.merge(new_df_temp, on="Team", how="outer", suffixes=('_old', '_new'))  # Merge on Team name
        for idx, row in merged.iterrows():
            if pd.isna(row['PTS_old']) or pd.isna(row['PTS_new']):
                continue
            if float(row['PTS_old']) != float(row['PTS_new']):  # Detect if points changed
                changed_rows.append(f"Team {row['Team']} changed: {row['PTS_old']} ➔ {row['PTS_new']}")

        if changed_rows:
            print(f"⚡ {label.upper()}: Data changed!")
        else:
            print(f"✅ {label.upper()}: No data changes.")

# Step 6: Scrape, Save, Summarize, and Chart
sns.set(style="whitegrid")  # Set Seaborn plotting style

# Get current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n🕒 Scraping Time: {timestamp}")

# Loop through each URL and process
for key, url in urls.items():
    print(f"\n🔵 Scraping {key.upper()} from {url}")
    df = fetch_table(url, table_ids[key])  # Fetch data
    if df is not None:
        filename = f"{key}.csv"  # CSV filename
        check_if_file_changed(filename, df, key)  # Compare old vs new data
        df.to_csv(filename, index=False)  # Save CSV
        dataframes[key] = df  # Store DataFrame in dictionary

        # Summarize basic statistics if 'PTS' exists
        if "PTS" in df.columns:
            summarize_column(df, "PTS", key.upper())

        # Ensure 'PTS' is numeric
        df["PTS"] = pd.to_numeric(df["PTS"], errors='coerce')
        df = df.dropna(subset=["PTS"])  # Drop rows where 'PTS' is NaN

        # Debugging: show first few rows
        print(f"📊 Data for {key.upper()} after cleaning:")
        print(df[["Team", "PTS"]].head())

        # Skip if dataframe is empty after cleaning
        if df.empty:
            print(f"⚠️ No valid 'PTS' data to plot for {key.upper()}. Skipping chart.")
            continue

        # Plot top 10 teams based on Points
        top10 = df.sort_values("PTS", ascending=False).head(10)

        # 1. Bar Chart
        plt.figure(figsize=(12, 7))
        sns.barplot(data=top10, x="PTS", y="Team", hue="Team", palette="rocket", legend=False)  
        plt.title(f"Top 10 Teams by Points Per Game ({key.upper()})", fontsize=14)
        plt.xlabel("Points Per Game", fontsize=12)
        plt.ylabel("Team", fontsize=12)
        plt.tight_layout()
        bar_chart_filename = f"{key}_bar_chart.png"
        plt.savefig(bar_chart_filename)  # Save bar chart
        print(f"🖼️ Saved Bar chart as {bar_chart_filename}")
        plt.close()

        # 2. Pie Chart
        top10 = top10.head(5)  # Only top 5 for pie chart
        plt.figure(figsize=(7, 7))
        plt.pie(top10["PTS"], labels=top10["Team"], autopct="%1.1f%%", startangle=140, colors=sns.color_palette("coolwarm", len(top10))) 
        plt.title(f"Top 5 Teams by Points ({key.upper()})", fontsize=14)
        plt.tight_layout()
        pie_chart_filename = f"{key}_pie_chart.png"
        plt.savefig(pie_chart_filename)  # Save pie chart
        print(f"🖼️ Saved Pie chart as {pie_chart_filename}")
        plt.close()

        # 3. Scatter Plot (only if 'Age' column exists)
        if "Age" in df.columns and "PTS" in df.columns:
            plt.figure(figsize=(8, 6))
            sns.scatterplot(data=df, x="Age", y="PTS", hue="Team", palette="Set2", legend=False)  
            plt.title(f"Age vs PTS for Teams ({key.upper()})", fontsize=14)
            plt.xlabel("Age", fontsize=12)
            plt.ylabel("Points Per Game", fontsize=12)
            plt.tight_layout()
            scatter_chart_filename = f"{key}_scatter_chart.png"
            plt.savefig(scatter_chart_filename)  # Save scatter plot
            print(f"🖼️ Saved Scatter chart as {scatter_chart_filename}")
            plt.close()

        # 4. Histogram (distribution of points)
        plt.figure(figsize=(8, 6))
        sns.histplot(df["PTS"], kde=True, color='blue', bins=15)  
        plt.title(f"Distribution of Points Per Game ({key.upper()})", fontsize=14)
        plt.xlabel("Points Per Game", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.tight_layout()
        hist_chart_filename = f"{key}_histogram.png"
        plt.savefig(hist_chart_filename)  # Save histogram
        print(f"🖼️ Saved Histogram as {hist_chart_filename}")
        plt.close()

        # 5. Line graph (Points across top 10 teams)
        plt.figure(figsize=(12, 7))
        sns.lineplot(data=top10, x="Team", y="PTS", marker='o', color='green', hue="Team", legend=False) 
        plt.title(f"Points Per Game Across Teams ({key.upper()})", fontsize=14)
        plt.xlabel("Team", fontsize=12)
        plt.ylabel("Points Per Game", fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        line_chart_filename = f"{key}_line_chart.png"
        plt.savefig(line_chart_filename)  # Save line graph
        print(f"🖼️ Saved Line chart as {line_chart_filename}")
        plt.close()

# Final message after everything is done
print("\n✅ All tasks completed!")
