
import requests #for making api

import json
import time
import os
from datetime import datetime

# Function to categorize stories based on keywords in the title
def assign_category(title):
    title = title.lower()
    if 'ai' in title or 'ml' in title or 'intelligence' in title:
        return 'AI/ML'
    elif 'show hn' in title:
        return 'Showcase'
    elif 'python' in title or 'rust' in title or 'coding' in title:
        return 'Programming'
    elif 'startup' in title or 'business' in title:
        return 'Business'
    else:
        return 'General Tech'

def run_scraper():
    # 1. Setup: Create data directory
    folder = 'data'
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created directory: {folder}")

    # 2. Fetch Story IDs
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        response = requests.get(top_stories_url)
        response.raise_for_status()
        # We need 125 stories (25 per category loop)
        all_ids = response.json()[:125]
    except Exception as e:
        print(f"Initial API call failed: {e}")
        return

    extracted_data = []

    # 3. Process Stories in batches of 25
    for index, post_id in enumerate(all_ids):
        try:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{post_id}.json"
            item_res = requests.get(item_url)
            item_res.raise_for_status()
            story = item_res.json()

            # Ensure the item is actually a story (some IDs might be jobs or polls)
            if story.get('type') != 'story':
                continue

            # Extract specific fields required by the task
            record = {
                "post_id": story.get("id"),
                "title": story.get("title", "No Title"),
                "category": assign_category(story.get("title", "")),
                "score": story.get("score", 0),
                "num_comments": story.get("descendants", 0), # 'descendants' is the API field
                "author": story.get("by", "unknown"),
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            extracted_data.append(record)

            # Throttling requirement: 2s sleep per 'category' (every 25 items)
            if (index + 1) % 25 == 0:
                print(f"Processed {index + 1} items. Pausing for 2 seconds...")
                time.sleep(2)

        except Exception as err:
            print(f"Skipping story {post_id} due to error: {err}")
            continue

    # 4. Save to JSON
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{folder}/trends_{date_str}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=4)

    print("-" * 30)
    print(f"Success! Collected {len(extracted_data)} stories.")
    print(f"File saved at: {filename}")

if __name__ == "__main__":
    run_scraper()

import pandas as pd
import os
import glob

#task 2

# first  find the json file in data folder
# used glob because the filename has today's date in it
files = glob.glob("data/trends_*.json")

if len(files) == 0:
    print("no json file found in data folder, run task1 first")
else:
    filepath = files[0]

    # reading  json into a dataframe
    df = pd.read_json(filepath)
    total = len(df)
    print("Loaded", total, "stories from", filepath)

    # cleaning starts

    # removing duplicate stories using post_id
    # same story can appear in multiple categories so removing
    before = len(df)
    df = df.drop_duplicates(subset=["post_id"])
    print("After removing duplicates:", len(df))

    # some stories  not have title or score or id
    # those are not usuaable so dropping them
    df = df.dropna(subset=["post_id", "title", "score"])
    print("After removing nulls:", len(df))

    # score and num_comments should be whole numbers not decimals
    df["score"] = df["score"].astype(int)
    df["num_comments"] = df["num_comments"].fillna(0).astype(int)

    # stories with very low score are not useful
    # keeping only score 5 and above
    df = df[df["score"] >= 5]
    print("After removing low scores:", len(df))

    # cleaning up extra spaces in titles
    # sometimes api returns titles with spaces at start or end
    df["title"] = df["title"].str.strip()

    # ---saving the clean data---

    # making sure data folder is there
    os.makedirs("data", exist_ok=True)

    # saving to csv
    save_path = "data/trends_clean.csv"
    df.to_csv(save_path, index=False)

    print("\nSaved", len(df), "rows to", save_path)

    # how many stories in each category
    print("\nStories per category:")
    category_count = df["category"].value_counts()
    for cat, count in category_count.items():
        print(" ", cat, "\t", count)

import pandas as pd
import numpy as np

# reading the csv file
df = pd.read_csv("data/trends_clean.csv")

# task 1 - load and explore
print("Loaded data:", df.shape)
print()
print("First 5 rows:")
print(df.head())
print()

# finding average score and comments
a = df["score"].mean()
b = df["num_comments"].mean()
print("Average score    :", round(a, 3))
print("Average comments :", round(b))
print()

# task 2 - numpy stats
s = df["score"].values

print("--- NumPy Stats ---")
print("Mean score   :", round(np.mean(s), 3))
print("Median score :", round(np.median(s), 3))
print("Std deviation:", round(np.std(s), 3))
print("Max score    :", np.max(s))
print("Min score    :", np.min(s))
print()

# which category has most stories
c = df["category"].value_counts()
print("Most stories in:", c.index[0], "(", c.iloc[0], "stories )")
print()

# story with most comments
i = df["num_comments"].idxmax()
print("Most commented story:", df["title"][i], "-", df["num_comments"][i], "comments")
print()

# task 3 - adding new columns
df["engagement"] = df["num_comments"] / (df["score"] + 1)
df["is_popular"] = df["score"] > df["score"].mean()

# task 4 - saving file
df.to_csv("data/trends_analysed.csv", index=False)
print("Saved to data/trends_analysed.csv")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

#  1 SETUP

# Load the analysed dataset produced in Task 3
df = pd.read_csv("data/trends_analysed.csv")

# Make sure the output folder exists before we try to save anything
if not os.path.exists("outputs"):
    os.makedirs("outputs")

print("Data loaded successfully!")
print(f"Total rows: {len(df)}")
print(f"Columns available: {list(df.columns)}")


#  2 CHART 1 – TOP 10 STORIES BY SCORE (horizontal bar chart)

# Sort by score descending and grab the top 10
top10 = df.sort_values("score", ascending=False).head(10).copy()

# Long titles make the chart messy, so clip anything over 50 characters
top10["short_title"] = top10["title"].apply(
    lambda t: t[:50] + "..." if len(str(t)) > 50 else str(t)
)

# Plot – barh draws bars left-to-right, which reads more naturally for rankings
fig1, ax1 = plt.subplots(figsize=(10, 6))

ax1.barh(top10["short_title"], top10["score"], color="steelblue")

# Flip the y-axis so the highest score sits at the top
ax1.invert_yaxis()

ax1.set_xlabel("Score")
ax1.set_ylabel("Story Title")
ax1.set_title("Top 10 HackerNews Stories by Score")

plt.tight_layout()

# Always save BEFORE show() – after show() the figure is cleared
plt.savefig("outputs/chart1_top_stories.png", dpi=150)
plt.show()
print("Chart 1 saved.")


#  3 CHART 2 – STORIES PER CATEGORY (vertical bar chart)

# Count how many stories belong to each category
category_counts = df["category"].value_counts()

# Pick a distinct colour for every bar so they're easy to tell apart visually
bar_colors = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12",
    "#9b59b6", "#1abc9c", "#e67e22", "#34495e",
]

fig2, ax2 = plt.subplots(figsize=(9, 5))

ax2.bar(
    category_counts.index,
    category_counts.values,
    color=bar_colors[: len(category_counts)],
)

ax2.set_xlabel("Category")
ax2.set_ylabel("Number of Stories")
ax2.set_title("Number of Stories per Category")
plt.xticks(rotation=30, ha="right")

plt.tight_layout()
plt.savefig("outputs/chart2_categories.png", dpi=150)
plt.show()
print("Chart 2 saved.")


#  4 CHART 3 – SCORE vs COMMENTS scatter plot

# Split the data into two groups based on the is_popular flag
popular     = df[df["is_popular"] == True]
not_popular = df[df["is_popular"] == False]

fig3, ax3 = plt.subplots(figsize=(8, 6))

# Plot each group with its own colour so they're distinguishable in the legend
ax3.scatter(
    not_popular["score"], not_popular["num_comments"],
    color="grey", alpha=0.6, label="Not Popular", s=40,
)
ax3.scatter(
    popular["score"], popular["num_comments"],
    color="tomato", alpha=0.8, label="Popular", s=60,
)

ax3.set_xlabel("Score")
ax3.set_ylabel("Number of Comments")
ax3.set_title("Score vs Number of Comments")
ax3.legend(title="Popularity")

plt.tight_layout()
plt.savefig("outputs/chart3_scatter.png", dpi=150)
plt.show()
print("Chart 3 saved.")


# BONUS – COMBINED DASHBOARD

# Lay all three charts side-by-side in one figure
fig4, axes = plt.subplots(1, 3, figsize=(18, 6))
fig4.suptitle("TrendPulse Dashboard", fontsize=16, fontweight="bold")

# --- Panel A: top stories ---
axes[0].barh(top10["short_title"], top10["score"], color="steelblue")
axes[0].invert_yaxis()
axes[0].set_title("Top 10 Stories by Score")
axes[0].set_xlabel("Score")

#  Panel B stories per category
axes[1].bar(
    category_counts.index,
    category_counts.values,
    color=bar_colors[: len(category_counts)],
)
axes[1].set_title("Stories per Category")
axes[1].set_xlabel("Category")
axes[1].set_ylabel("Count")
axes[1].tick_params(axis="x", rotation=30)

# Panel C score vs comments
axes[2].scatter(
    not_popular["score"], not_popular["num_comments"],
    color="grey", alpha=0.6, label="Not Popular", s=30,
)
axes[2].scatter(
    popular["score"], popular["num_comments"],
    color="tomato", alpha=0.8, label="Popular", s=50,
)
axes[2].set_title("Score vs Comments")
axes[2].set_xlabel("Score")
axes[2].set_ylabel("Comments")
axes[2].legend()

plt.tight_layout()
plt.savefig("outputs/dashboard.png", dpi=150)
plt.show()
print("Dashboard saved.")

print("\nAll done! Check the outputs/ folder for your PNG files.")
