import openai
import os
# from google.colab import userdata
import pymongo
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"


def get_mongo_client(mongo_uri):
  """Establish connection to the MongoDB."""
  try:
    client = pymongo.MongoClient(mongo_uri)
    print("Connection to MongoDB successful")
    return client
  except pymongo.errors.ConnectionFailure as e:
    print(f"Connection failed: {e}")
    return None

mongo_uri = "mongodb+srv://lazzyCoder:dO1qORxPZ4YOeJkZ@cocktaildb.eq81tdu.mongodb.net/?retryWrites=true&w=majority&appName=cocktailDB"
if not mongo_uri:
  print("MONGO_URI not set in environment variables")

mongo_client = get_mongo_client(mongo_uri)

# Ingest data into MongoDB
db = mongo_client['cocktails']
collection = db['cocktailsDB']

# Delete any existing records in the collection
def get_embedding(text):
    """Generate an embedding for the given text using OpenAI's API."""

    # Check for valid input
    if not text or not isinstance(text, str):
        return None

    try:
        # Call OpenAI API to get the embedding
        embedding = openai.embeddings.create(input=text, model=EMBEDDING_MODEL).data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error in get_embedding: {e}")
        return None

def vector_search(user_query, collection):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    collection (MongoCollection): The MongoDB collection to search.

    Returns:
    list: A list of matching documents.
    """

    # Generate embedding for the user query
    query_embedding = get_embedding(user_query)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search pipeline
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "base_embedding_optimised",
                "numCandidates": 150,  # Number of candidate matches to consider
                "limit": 5  # Return top 5 matches
            }
        },
        {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "base": 1,  # Include the base field
                "title": 1,  # Include the title field
                "ingredients": 1, # Include the ingredients field
                "directions": 1,  # Include the directions field
                "score": {
                    "$meta": "vectorSearchScore"  # Include the search score
                }
            }
        }
    ]

    # Execute the search
    results = collection.aggregate(pipeline)
    return list(results)


def handle_user_query(query, collection):
    get_knowledge = vector_search(query, collection)

    search_result = []
    for result in get_knowledge:
        search_result.append({
            'title': result.get('title', 'N/A'),
            'base': result.get('base', 'N/A'),
            'ingredients': result.get('ingredients', 'N/A'),
            'directions': result.get('directions', 'N/A')
        })

    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a cocktail recommendation system."},
            {"role": "user", "content": "Answer this user query: " + query + " with the following context: " + str(search_result)}
        ]
    )

    return completion.choices[0].message.content, search_result

st.set_page_config(page_title="Cocktail Recommendation", layout="wide")
st.markdown(
    """
    <div style='width: 65%; margin: 0 auto;'>
        <h1 style='text-align: center; color: #1F618D;border-radius: 40px; background: linear-gradient(-225deg, #69EACB 0%, #EACCF8 48%, #6654F1 100%);'>🍹 Cocktail Recommendation 🍸</h1>
    </div>
    """,
    unsafe_allow_html=True
)
query = st.text_input("Ask your cocktail query here", placeholder="E.g., Recommend a refreshing summer cocktail")

if query != "":
    response, search_results = handle_user_query(query, collection)
    # st.markdown(f"<p style='font-size: 18px; font-weight: bold; color: #333333;'>Response:</p> <p style='font-size: 16px; color: #666666;'>{response}</p>", unsafe_allow_html=True)

    # Display search results as cards
    cols = st.columns(3)  # Change the number based on your preference
    for i, result in enumerate(search_results):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div style="border: 3px solid #CCCCCC; border-radius: 5px; padding: 20px; background-color: #17202A;">
                    <h3 style="color: #EC7063; text-align: center;">{result['title']}</h3>
                    <p style="font-weight: bold; color: #A3E4D7;">Base Drink: <span style="color: #FBFCFC;">{result['base']}</span></p>
                    <p style="font-weight: bold; color: #A3E4D7;">Ingredients:</p>
                    <ul style="list-style-type: square; padding-left: 20px; color: #FBFCFC;">
                        {''.join(['<li>' + item + '</li>' for item in result['ingredients']])}
                    </ul>
                    <p style="font-weight: bold; color: #A3E4D7;">Directions:</p>
                    <p style="color: #FBFCFC;">{result['directions']}</p>
                </div>
                """, unsafe_allow_html=True)


                # Add some spacing between cards
                st.markdown("<br>", unsafe_allow_html=True)
