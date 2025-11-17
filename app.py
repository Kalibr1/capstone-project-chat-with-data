import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import logging
import json
import os
import requests  # <-- ADDED IMPORT

# --- Configuration ---
DB_FILENAME = "movies.db"
TABLE_NAME = "movies"

# A new, more descriptive schema to "teach" the model
# UPDATED to match the user's screenshot exactly.
DB_SCHEMA_DESCRIPTION = f"""
Table Name: {TABLE_NAME}

Columns:
- ROWID (INTEGER): The unique internal identifier for the movie row. Use this for any queries needing a unique ID.
- Release_Date (TEXT): The date the movie was released (e.g., 'YYYY-MM-DD').
- Title (TEXT): The main title of the movie.
- Overview (TEXT): A text summary of the movie's plot.
- Popularity (REAL): A numeric score for the movie's popularity.
- Vote_Count (INTEGER): The total number of votes received.
- Vote_Average (REAL): The average rating from 0.0 to 10.0.
- Original_Language (TEXT): A two-letter code for the original language (e.g., 'en', 'fr').
- Genre (TEXT): A JSON string representing a list of genres.
    - Example: '[{{"id": 28, "name": "Action"}}, {{"id": 12, "name": "Adventure"}}]'
    - To query a genre, you MUST use the LIKE operator.
    - Example Query: WHERE Genre LIKE '%"name": "Action"%'
- Poster_Url (TEXT): A URL to the movie's poster image.
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Safety Check ---
# We must prevent the LLM from executing harmful commands
BANNED_SQL_KEYWORDS = [
    "delete", "drop", "update", "insert", "alter",
    "truncate", "grant", "revoke", "shutdown"
]

def is_query_safe(sql_query: str) -> bool:
    """Checks if the query contains any banned keywords."""
    query_lower = sql_query.lower()
    for keyword in BANNED_SQL_KEYWORDS:
        if keyword in query_lower:
            logger.warning(f"Banned keyword '{keyword}' found in query: {sql_query}")
            return False
    return True

# --- Tool 1: Database Query Tool ---
def query_database(sql_query: str) -> str:
    """
    Runs a safe SQL query on the 'movies.db' database and returns the results.
    Only read-only (SELECT) queries are allowed.
    """
    logger.info(f"Attempting to run query: {sql_query}")

    if not is_query_safe(sql_query):
        return json.dumps({
            "error": "Query is not allowed. Only read-only SELECT statements are permitted."
        })

    if not os.path.exists(DB_FILENAME):
        return json.dumps({
            "error": f"Database file '{DB_FILENAME}' not found. Please run setup.py."
        })

    try:
        conn = sqlite3.connect(DB_FILENAME)
        cur = conn.cursor()
        cur.execute(sql_query)

        results = cur.fetchall()

        # Get column names
        if cur.description:
            colnames = [desc[0] for desc in cur.description]
        else:
            conn.close()
            return json.dumps({"message": "Query executed, but no results to return."})

        conn.close()

        # Format as list of dicts for clarity
        df = pd.DataFrame(results, columns=colnames)

        # Truncate if too long to avoid huge context
        if len(df) > 20:
             return df.head(20).to_json(orient="records") + \
                    f"\n... (truncated, {len(df) - 20} more rows)"

        return df.to_json(orient="records")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return json.dumps({"error": f"An error occurred: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return json.dumps({"error": "An unexpected error occurred."})

# --- Tool 2: Support Ticket Tool (GitHub) ---
def create_support_ticket(title: str, description: str) -> str:
    """
    Creates a new GitHub issue in the specified repository.
    """
    logger.info(f"Attempting to create GitHub issue: {title}")

    # Check for secrets
    if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
        logger.error("Missing GITHUB_TOKEN or GITHUB_REPO in Streamlit secrets.")
        return json.dumps({
            "error": "Failed to create ticket: Server is missing GitHub configuration."
        })

    try:
        token = st.secrets["GITHUB_TOKEN"]
        # e.g., "Kalibr1/capstone-project-chat-with-data"
        repo_url = st.secrets["GITHUB_REPO"]
        
        # GitHub API endpoint for issues
        api_url = f"https://api.github.com/repos/{repo_url}/issues"
        
        # Setup headers and data for the API request
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {
            "title": title,
            "body": description,
        }

        # Make the POST request to create the issue
        response = requests.post(api_url, json=data, headers=headers)
        
        # Check the response
        if response.status_code == 201:
            # Success!
            issue_data = response.json()
            ticket_id = issue_data["number"]
            ticket_url = issue_data["html_url"]
            
            logger.info(f"Successfully created GitHub issue #{ticket_id} at {ticket_url}")
            
            response_payload = {
                "status": "success",
                "ticket_id": f"GH-{ticket_id}",
                "ticket_url": ticket_url,
                "title": title,
                "message": f"Support ticket GH-{ticket_id} has been successfully created. A human will review it at: {ticket_url}"
            }
            return json.dumps(response_payload)
        else:
            # Failed to create issue
            logger.error(f"Failed to create GitHub issue. Status: {response.status_code}, Response: {response.text}")
            return json.dumps({
                "error": f"Failed to create ticket. GitHub API responded with status {response.status_code}.",
                "details": response.text
            })

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while making the request to GitHub: {e}")
        return json.dumps({
            "error": "Failed to create ticket: A network error occurred."
        })
    except Exception as e:
        logger.error(f"An unexpected error in create_support_ticket: {e}")
        return json.dumps({
            "error": "An unexpected error occurred while creating the ticket."
        })

# --- Helper Functions for UI ---
@st.cache_data
def get_db_aggregates():
    """Gets aggregate info for the sidebar."""
    if not os.path.exists(DB_FILENAME):
        return None, None
    try:
        conn = sqlite3.connect(DB_FILENAME)
        total_movies = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
        # UPDATED: Changed from AVG(Vote_Average) to SUM(Vote_Count)
        total_votes = conn.execute(f"SELECT SUM(Vote_Count) FROM {TABLE_NAME}").fetchone()[0]
        conn.close()
        return total_movies, total_votes
    except Exception as e:
        logger.error(f"Error getting aggregates: {e}")
        return None, None

# --- Streamlit UI ---

st.set_page_config(page_title="Data Insights App", layout="wide")

# Sidebar for "Business Information"
with st.sidebar:
    st.title("Data Dashboard")

    total_movies, total_votes = get_db_aggregates()
    if total_movies:
        st.metric("Total Movies in DB", total_movies)
        # UPDATED: Changed the metric to show total votes
        if total_votes:
            st.metric("Total Votes Received", f"{total_votes:,}")

    with st.expander("Sample Queries", expanded=False):
        st.code("How many movies are there?")
        st.code("What are the 5 highest-rated movies?")
        # Update sample query to use real columns
        st.code("Show me the Poster_Url for 'Inception'")
        st.code("I need help, I can't find my query.")

    with st.expander("Database Schema", expanded=False):
        # Use the new, detailed schema description
        st.text(DB_SCHEMA_DESCRIPTION)

# Main Chat Interface
st.title("🎬 Capstone Project: Chat with Data")
st.markdown(
    "Ask me questions about the movie database. I can run queries and create support tickets."
)

# --- Agent Initialization ---
try:
    # Get API key from Streamlit secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

    # Define the tools the model can use
    tools = {
        "query_database": query_database,
        "create_support_ticket": create_support_ticket,
    }

    # System prompt now uses the new, detailed schema
    system_prompt = f"""
    You are a helpful Data Analyst assistant.
    Your goal is to assist users with their questions about a movie database.
    You have two tools:
    1. `query_database`: To run SQL queries on the database.
    2. `create_support_ticket`: To create a support ticket if you cannot help.

    You MUST follow these rules:
    - Only use the provided tools. Do not make up data.
    - When a user asks for data, ALWAYS use the `query_database` tool.
    - Generate a valid SQLite query for the schema provided below.
    - If the user asks for help, or is frustrated, or asks to talk to a human,
      offer to create a support ticket using `create_support_ticket`.
      Ask for a title and description before calling the tool.
    - Be concise and clear in your responses.

    DATABASE SCHEMA:
    {DB_SCHEMA_DESCRIPTION}
    """

    # Initialize the generative model
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=system_prompt,
    )

except Exception as e:
    st.error(f"Error initializing generative model: {e}")
    st.stop()


# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "parts": "Hello! How can I help you with the movie data today?"}
    ]

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] != "function": # Don't display function calls/responses
        with st.chat_message(msg["role"]):
            st.markdown(msg["parts"])

# --- Chat Input and Agent Logic ---
if prompt := st.chat_input("Ask me about the movies..."):
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Start the agent loop
    try:
        # Create the chat session with history
        chat = model.start_chat(history=st.session_state.messages[:-1])

        # Send the new prompt
        response = chat.send_message(
            st.session_state.messages[-1]["parts"],
            tools=tools.values()
        )

        response_part = response.candidates[0].content.parts[0]

        # Keep running tools as long as the model requests them
        while response_part.function_call:
            call = response_part.function_call
            function_name = call.name
            args = dict(call.args)

            logger.info(f"LLM wants to call: {function_name} with args: {args}")

            # Find and call the correct Python function
            if function_name in tools:
                tool_function = tools[function_name]

                # Log and execute the function call
                with st.chat_message("model"):
                    st.write(f"Running tool: `{function_name}`...")

                function_result = tool_function(**args)

                logger.info(f"Function result: {function_result}")

                function_response_dict = {
                    "function_response": {
                        "name": function_name,
                        "response": {
                            "content": json.loads(function_result)
                        }
                    }
                }

                response = chat.send_message(
                    function_response_dict, # Pass the dict directly
                    tools=tools.values()
                )
                response_part = response.candidates[0].content.parts[0]

            else:
                logger.error(f"Unknown function call: {function_name}")
                response = chat.send_message(
                    f"Error: Unknown tool '{function_name}'",
                    tools=tools.values()
                )
                response_part = response.candidates[0].content.parts[0]

        # Once the loop finishes, we have a final text response
        if response_part.text:
            final_response = response_part.text
        else:
            final_response = "Sorry, I'm not sure how to respond to that."
            logger.warning("Model finished tool loop but did not provide a text response.")

        # Add final response to history and display
        st.session_state.messages.append({"role": "model", "parts": final_response})
        st.chat_message("model").markdown(final_response)

    except Exception as e:
        logger.error(f"An error occurred during the chat loop: {e}")
        st.error(f"An error occurred: {e}")