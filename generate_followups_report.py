import json
import pandas as pd
import re

# === Load the input ===

with open('result.json') as f:
    chats_dict = json.load(f)

print(f"Loaded {len(chats_dict)} chat(s) from result.json")

# === Save last 15 messages for debugging (optional) ===
trimmed_chats = {chat_name: messages[-15:] for chat_name, messages in chats_dict.items()}

with open('tg_exported_last_15.json', 'w') as f:
    json.dump(trimmed_chats, f, indent=2)

# === Sales rep aliases ===

rep_handles = {
    "Aki Balogh": "Aki Balogh",
    "PMM": "Peter Moricz",
    "Amy Wu": "Amy Wu",
    "Walter Wong | Nolem Labs | RockX": "Walter Wong",
    "Kadeem Clarke": "Kadeem Clarke",
    "Mayank | iBTC": "Mayank Sachdev",
    "Dae L": "Dae Lee",
    "Jesse | iBTC": "Jesse Eisenberg",
    "Jesse Eisenberg": "Jesse Eisenberg"
}

# === Find unanswered sales messages ===

unanswered_msgs = []

for chat_name, messages in trimmed_chats.items():
    for i, msg in enumerate(messages):
        sender = msg.get('from')
        if sender in rep_handles:
            replied = any(
                next_msg.get('from') and next_msg.get('from') not in rep_handles
                for next_msg in messages[i+1:]
            )
            if not replied:
                text = msg.get('text')
                if isinstance(text, str):
                    clean_text = text
                else:
                    clean_text = ''.join(
                        t.get('text') if isinstance(t, dict) else str(t) for t in text or []
                    )
                unanswered_msgs.append({
                    'Sales Rep': rep_handles[sender],
                    'Chat Name': chat_name,
                    'Date': msg.get('date'),
                    'Message ID': msg.get('id'),
                    'Message': clean_text
                })

if not unanswered_msgs:
    print("No follow-ups found.")
    exit()

# === Clean client names ===

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

# === Build DataFrame and clean ===

df = pd.DataFrame(unanswered_msgs)
df = df.sort_values('Date').drop_duplicates(['Chat Name', 'Sales Rep'], keep='last')
df['Client'] = df['Chat Name'].apply(clean_client_name)
df = df[df['Client'].str.len() > 1]
df = df[~df['Client'].str.lower().str.startswith('aki')]

# === Output ===

output_df = df[['Sales Rep', 'Client', 'Date', 'Message ID', 'Message']].rename(columns={
    'Date': 'Last Message Date',
    'Message ID': 'Last Message ID'
})

output_file = 'followups_with_reps.xlsx'
output_df.to_excel(output_file, index=False)
print(f"Saved: {output_file}")
