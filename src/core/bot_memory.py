from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# VectorStore-backed PgVector memory integration
def get_memory(thread_id: str):
    # Define the database connection string. Ensure these environment variables are set.
    # Correctly get the connection string from environment variables
    connection_string = os.environ.get("PGVECTOR_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("PGVECTOR_CONNECTION_STRING environment variable not set.")

    collection_name = f"conversation_{thread_id}"
    embeddings = HuggingFaceEmbeddings()
    
    # Instantiate PGVector with the connection string
    vectorstore = PGVector(
        collection_name=collection_name,
        embedding_function=embeddings,
        connection_string=connection_string,
        # Optionally, specify distance metric, default is cosine
        # distance_strategy="cosine"
    )
    memory = VectorStoreRetrieverMemory(
        retriever=vectorstore.as_retriever(),
        memory_key="chat_history"
    )
    return memory

