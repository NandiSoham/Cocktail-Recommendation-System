import openai
# from google.colab import userdata
import os
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

  search_result = ''
  for result in get_knowledge:
      search_result += f"Title: {result.get('title', 'N/A')}, Base Drink: {result.get('base', 'N/A')}, \n Ingredients: {result.get('ingredients', 'N/A')}, \n Directions: {result.get('directions', 'N/A')}\n"

  completion = openai.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
          {"role": "system", "content": "You are a cocktail recommendation system."},
          {"role": "user", "content": "Answer this user query: " + query + " with the following context: " + search_result}
      ]
  )

  return (completion.choices[0].message.content), search_result

# 6. Conduct query with retrival of sources

st.set_page_config(page_title="Cocktail Recommendation")
st.header("Ask For Cocktail Recommendation")
query = st.text_input("Query")
if query != "":
  response, source_information = handle_user_query(query, collection)
  print(source_information)
  print(response)
  st.write(f"Response: {response}\n\n")




