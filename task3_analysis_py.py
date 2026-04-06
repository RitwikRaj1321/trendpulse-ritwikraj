
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
