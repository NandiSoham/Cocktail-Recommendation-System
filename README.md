
# Cocktail-Recommendation-System




## 🌟 Project Overview:
This project is based on Cocktail Recommendation System, which utilizes the Retrieval-Augmented Generation (RAG) approach to provide users with personalized cocktail recommendations based on their queries. Leveraging state-of-the-art machine learning and natural language processing techniques, the system delivers accurate and relevant recommendations. The system employs MongoDB for data storage and retrieval, Hugging Face's Datasets library for dataset management, OpenAI for text embeddings and chat completion, and Google Colab as the development environment.


## ⚙️ Steps
 - __Libraries Installation__

- __Data Preparation__
    - __Load Dataset:__ Utilize Hugging Face's Datasets library to load the cocktail recipes dataset.
    - __Data Cleaning and Preparation:__ Clean the dataset by processing ingredients and removing missing values.
    - __Create Embeddings with OpenAI:__ Generate embeddings for cocktail ingredients using OpenAI's text embedding model.

- __Vector Database Setup and Data Ingestion__
    - __Connect to MongoDB:__ Establish connection to MongoDB Atlas using the provided URI.
    - __Data Ingestion:__ Ingest cleaned data into MongoDB collection for vector search.
## Dependencies:
- Hugging Face's Datasets library
- pandas
- numpy
- OpenAI
- pymongo
- Google Colab (for development environment)
