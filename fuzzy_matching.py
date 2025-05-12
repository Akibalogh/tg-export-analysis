import pandas as pd
from fuzzywuzzy import process
import re

# Load the CSV files with headers
tg_path = './tg.csv'
hubspot_path = './hubspot.csv'

# Load the CSV files with headers
tg_chats = pd.read_csv(tg_path)
hubspot_deals = pd.read_csv(hubspot_path)

# === Regex Cleaning Function for TG Chat Titles Only ===

def clean_client_name(name):
    # Remove DLC-like wrappers and standalone DLC
    name = re.sub(r'(?i)\bd[lc]{2}(\.?\s*link)?\b', '', name)  # DLC, DCL, DLC.Link
    name = re.sub(r'(?i)\bdlc\s*btc\b', '', name)
    name = re.sub(r'(?i)\biBTC\b', '', name)
    name = re.sub(r'(?i)^link[<>|/\\\-\s]*', '', name)

    # Remove parenthetical suffixes like (fmr. XYZ), (formerly XYZ), etc.
    name = re.sub(r'\s*\((fmr\.?|formerly|prev\.?) [^)]+\)', '', name, flags=re.IGNORECASE)

    # Remove symbols and collapse whitespace
    name = re.sub(r'[<>|/\\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    # Remove if starts with "Aki"
    if name.lower().startswith("aki "):
        name = name[4:].strip()

    return name

# Apply the cleaning function to the TG chat titles
tg_chats['cleaned_chat_title'] = tg_chats['chat_title'].apply(clean_client_name)

# Initialize a list to store the matches
matches = []

# Iterate through each cleaned Telegram chat title
for tg_chat, original_chat in zip(tg_chats['cleaned_chat_title'], tg_chats['chat_title']):
    # Apply fuzzy matching against raw HubSpot deal names
    match, score, _ = process.extractOne(tg_chat, hubspot_deals['hubspot_deal_name'])
    
    # Get the pipeline associated with the matched deal
    deal_pipeline = hubspot_deals.loc[hubspot_deals['hubspot_deal_name'] == match, 'pipeline'].values[0]

    # Append the match, along with its score and pipeline
    matches.append({
        'original_chat_title': original_chat,
        'cleaned_chat_title': tg_chat,
        'matched_deal_name': match,
        'match_score': score,
        'pipeline': deal_pipeline
    })

# Create the matches DataFrame
matches_df = pd.DataFrame(matches)

# Filter for matches with a score above a certain threshold (e.g., 70)
matches_df = matches_df[matches_df['match_score'] >= 70]

# Save to CSV
output_path = './chat_mappings.csv'
matches_df.to_csv(output_path, index=False)

print(f"Saved locally as: {output_path}")
