# Capstone Project: Chat with Data

This is my project for the Generative AI capstone. I built a Streamlit app that lets you have a conversation with a database full of movies.

It's not just a simple chatbot—it can actually understand what you're asking for and then write its own SQL queries to find the answer.

## What It Does

- **Chat with Data:** You can ask the AI (Google's Gemini model) plain-English questions like, "What are the 5 highest-rated movies?" or "Show me the poster URL for Inception."
- **Runs Real Queries:** The agent takes your question, writes a SQL query, and runs it against a local SQLite database that has over 9,000 movies in it.
- **Safety First:** I added a safety check to make sure the agent can't run any dangerous queries. It will block anything with words like `DELETE`, `DROP`, `UPDATE`, etc.
- **Live Dashboard:** The sidebar shows some live stats from the database, like the total number of movies and the total votes they've all received.
- **Real Support Tickets:** If you get stuck or the bot can't help, you can just say, "I need help" or "create a ticket." The bot will then use the GitHub API to create a _real_ issue in this project's repo so I can see what went wrong.

## How to Get It Running

Here’s how to run this on your own machine.

### 1. Clone the Repo

First, just grab the code.

```bash
git clone [https://github.com/Kalibr1/capstone-project-chat-with-data.git](https://github.com/Kalibr1/capstone-project-chat-with-data.git)
cd capstone-project-chat-with-data
```

### 2. Install the Packages

It's always a good idea to use a virtual environment. Once you have one, just install everything from the `requirements.txt` file.

```bash
# Create a virtual env (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install packages
pip install -r requirements.txt
```

### 3. Set Up Your API Keys

The app needs a few secret keys to work.

1.  Create a new folder in the project directory named `.streamlit`.
2.  Inside that folder, create a new file named `secrets.toml`.
3.  Copy and paste the following into that file, filling it out with your own keys:

```toml
# Your Google API key for the Gemini model
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

# --- GitHub Issue Tracker ---
# Your GitHub Personal Access Token (needs 'repo' scope)
GITHUB_TOKEN = "ghp_YOUR_TOKEN_HERE"

# The repo to create issues in (e.g., "username/repo-name")
GITHUB_REPO = "Kalibr1/capstone-project-chat-with-data"
```

### 4. Download the Data (One-Time Step)

Before you run the app for the first time, you need to download the movie dataset. I made a simple script for this.

Just run this once:

```bash
python setup.py
```

This will grab the dataset from Hugging Face and create the `movies.db` file that the app needs.

### 5. Run the App!

That's it. Now you can start the Streamlit app.

```bash
streamlit run app.py
```

It should open up in your browser automatically.

## Tech I Used

- **Python**
- **Streamlit** (for the whole user interface)
- **Google Generative AI (Gemini)** (for the agent and function calling)
- **SQLite** (to store the movie data)
- **Pandas** (for helping with the data)
- **GitHub API** (for the support ticket tool, using `requests`)

## Screenshots

### Main App Interface

![A screenshot of the main chat interface, showing the sidebar and chat history](https://github.com/user-attachments/assets/b8efc92b-39aa-466c-823e-19517553732e)

### Example Data Query

![A screenshot showing a user asking "Show me Poster_Url for 'Inception'" and the bot's correct answer](https://github.com/user-attachments/assets/ae655358-c5bd-417e-8f1b-85b527809186)

### Creating a Support Ticket

![A screenshot of the user asking for help and the bot replying that a GitHub issue has been created, with a link](https://github.com/user-attachments/assets/a1193b4e-15c0-47f3-a969-df26a5d844f9)
