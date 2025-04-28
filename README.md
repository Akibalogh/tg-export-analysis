# tg-export-analysis

This repository analyzes Telegram conversations to identify leads or prospects who stopped responding, and provides scripts to export and analyze live Telegram chat data via the API.

## Features

- Parses exported Telegram JSON data to identify conversation gaps  
- Connects live to the Telegram API to fetch recent messages  
- Exports all private chats, group chats, and DMs into a local database (`messages.db`)  
- Enables regular follow-up reporting and conversation recovery  

## How to Export Telegram Data (Manual JSON Export)

1. Open **Telegram Desktop**  
2. Go to **Settings → Advanced → Export Telegram data**  
3. Configure the export:  
   - **Uncheck**: *Photos*, *Story archive*  
   - **Check**: *Personal chats*, *Private groups*  
   - Under *Private groups*, **uncheck**: *Only my messages*  
   - Under *Location and format*, select: **Machine-readable JSON**  
4. Click **Export**, then download when ready

Place the resulting `result.json` file into this project directory.

## Live Telegram API Scripts

These scripts connect directly to Telegram servers using Telethon.

### Analyze Recent Activity

```bash
python telegram_analysis.py
```
- Fetches recent DMs and private group chats  
- Identifies active conversations and sales rep activity  

### Export All Messages to Local Database

```bash
python export_tg_to_db.py
```
- Downloads the full message history  
- Stores all messages into a local SQLite database (`messages.db`)  
- Columns include: `date`, `sender_name`, `chat_title`, `text`, and metadata  

## Manual Follow-Up Report Generation

```bash
python generate_followups_report.py
```
- Parses exported `result.json` Telegram data  
- Highlights leads or prospects who dropped off  

## Requirements

- Python 3.8+  
- Libraries:  
  - `telethon`  
  - `sqlalchemy`  
  - `pandas`  
  - `openpyxl`  
  - `python-dotenv`  
- See `requirements.txt` for full list

## License

MIT
