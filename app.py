import openai
import pymongo
import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Set up OpenAI API key
openai.api_key = "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"
EMBEDDING_MODEL = "text-embedding-3-small"

# Function to establish connection to MongoDB
def get_mongo_client(mongo_uri):
    try:
        client = pymongo.MongoClient(mongo_uri)
        print("Connection to MongoDB successful")
        return client
    except pymongo.errors.ConnectionFailure as e:
        print(f"Connection failed: {e}")
        return None

# MongoDB connection URI
mongo_uri = "mongodb+srv://lazzyCoder:dO1qORxPZ4YOeJkZ@cocktaildb.eq81tdu.mongodb.net/?retryWrites=true&w=majority&appName=cocktailDB"
if not mongo_uri:
    print("MONGO_URI not set in environment variables")

mongo_client = get_mongo_client(mongo_uri)

# Ingest data into MongoDB
db = mongo_client['cocktails']
collection = db['cocktailsDB']

# Function to generate an embedding for the given text
def get_embedding(text):
    if not text or not isinstance(text, str):
        return None

    try:
        embedding = openai.embeddings.create(input=text, model=EMBEDDING_MODEL).data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error in get_embedding: {e}")
        return None

# Function to perform a vector search in the MongoDB collection based on the user query
def vector_search(user_query, collection):
    query_embedding = get_embedding(user_query)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "base_embedding_optimised",
                "numCandidates": 150,
                "limit": 5
            }
        },
        {
            "$project": {
                "_id": 0,
                "base": 1,
                "title": 1,
                "ingredients": 1,
                "directions": 1,
                "score": {
                    "$meta": "vectorSearchScore"
                }
            }
        }
    ]

    results = collection.aggregate(pipeline)
    return list(results)

# Function to handle user query and return the response
def handle_user_query(query, collection):
    get_knowledge = vector_search(query, collection)

    search_result = ''
    for result in get_knowledge:
        search_result += f"Title: {result.get('title', 'N/A')}, Base Drink: {result.get('base', 'N/A')}, \n Ingredients: {result.get('ingredients', 'N/A')}, \n Directions: {result.get('directions', 'N/A')}\n"

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a cocktail recommendation system."},
            {"role": "user", "content": "Answer this user query: " + query + " with the following context: " + search_result}
        ]
    )

    return (completion.choices[0].message.content), search_result

# Function to load Lottie animations
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load Lottie animation
lottie_cocktail = load_lottie_url("https://assets4.lottiefiles.com/private_files/lf30_oGlWy5.json")

# Streamlit app setup
st.set_page_config(page_title="Cocktail Recommendation", page_icon="🍸", layout="centered")
st.title("🍹 Cocktail Recommendation System")
st_lottie(lottie_cocktail, height=300)

st.write("Welcome to the Cocktail Recommendation System! Ask for cocktail recipes and recommendations based on your preferences.")

query = st.text_input("Enter your cocktail query here:")

if query:
    response, source_information = handle_user_query(query, collection)
    
    st.subheader("Search Results:")
    st.write(source_information)
    
    st.subheader("Recommendation:")
    st.write(response)
else:
    st.write("Please enter a query to get cocktail recommendations.")

# Additional features can be added here as needed.
