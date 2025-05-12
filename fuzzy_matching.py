import pandas as pd
from fuzzywuzzy import process

# Load the CSV files with headers
tg_chats = pd.read_csv('/path/to/tg.csv')
hubspot_deals = pd.read_csv('/path/to/hubspot.csv')

# Initialize a list to store the matches
matches = []

# Iterate through each Telegram chat title
for tg_chat in tg_chats['chat_title']:
    # Apply fuzzy matching
    match, score = process.extractOne(tg_chat, hubspot_deals['hubspot_deal_name'])
    
    # Append the match, along with its score and pipeline
    deal_pipeline = hubspot_deals.loc[hubspot_deals['hubspot_deal_name'] == match, 'pipeline'].values[0]
    matches.append({
        'chat_title': tg_chat,
        'matched_deal_name': match,
        'match_score': score,
        'pipeline': deal_pipeline
    })

# Create the matches DataFrame
matches_df = pd.DataFrame(matches)

# Filter for matches with a score above a certain threshold (e.g., 70)
matches_df = matches_df[matches_df['match_score'] >= 70]

# Save to CSV
output_path = 'chat_mappings.csv'
matches_df.to_csv(output_path, index=False)

print(f"Saved: {output_path}")
