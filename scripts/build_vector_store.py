"""
Build vector store for ICD-10 G-codes using hierarchical clustering with LangChain.

This script:
1. Loads ICD-10 codes from g_codes.csv
2. Generates embeddings using OpenAI's text-embedding-3-large via LangChain
3. Performs hierarchical clustering to group similar codes
4. Stores each cluster in a separate Chroma collection using LangChain
5. Persists the vector store locally for reuse
"""

import os
import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
import sys

# LangChain imports
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Add Django app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_coding_app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_coding_app.settings')

import django
django.setup()

from app.models import ICD10Code

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Constants
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'g_codes.csv')
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
EMBEDDING_MODEL = "text-embedding-3-large"


def load_codes():
    """
    Load ICD-10 codes from CSV and populate the database.

    :return: DataFrame of codes
    """
    print("Loading ICD-10 codes from CSV...")
    df = pd.read_csv(CSV_PATH)

    print(f"Loaded {len(df)} ICD-10 codes")

    # Populate database
    print("Populating ICD10Code table in database...")
    for _, row in df.iterrows():
        ICD10Code.objects.get_or_create(
            icd_code=row['icd_code'],
            defaults={
                'short_description': row['short_description'],
                'long_description': row['long_description']
            }
        )
    print(f"Database now has {ICD10Code.objects.count()} ICD-10 codes")

    return df


def generate_embeddings(df: pd.DataFrame, embedding_function: OpenAIEmbeddings) -> np.ndarray:
    """
    Generate embeddings for all code descriptions using LangChain.

    :param df: DataFrame with code descriptions
    :param embedding_function: LangChain OpenAI embeddings function
    :return: Array of embeddings
    """
    print("Generating embeddings using LangChain (this will take a few minutes)...")
    embeddings = []

    for idx, row in df.iterrows():
        if idx % 50 == 0:
            print(f"  Processed {idx}/{len(df)} codes...")

        # Use LangChain's embed_query method
        embedding = embedding_function.embed_query(row['long_description'])
        embeddings.append(embedding)

    print(f"Generated {len(embeddings)} embeddings")
    return np.array(embeddings)


def find_optimal_clusters(embeddings: np.ndarray, min_k: int, max_k: int, step: int) -> int:
    """
    Find optimal number of clusters using silhouette score.

    :param embeddings: Array of embeddings
    :param min_k: Minimum number of clusters to try
    :param max_k: Maximum number of clusters to try
    :param step: Step size for trying different k values
    :return: Optimal number of clusters
    """
    print(f"Finding optimal number of clusters (trying k={min_k} to {max_k})...")
    best_score = -1
    best_k = min_k

    for k in range(min_k, max_k + 1, step):
        clusterer = AgglomerativeClustering(n_clusters=k)
        labels = clusterer.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        print(f"  k={k}: silhouette score = {score:.4f}")

        if score > best_score:
            best_score = score
            best_k = k

    print(f"Optimal number of clusters: {best_k} (score: {best_score:.4f})")
    return best_k


def perform_clustering(embeddings: np.ndarray, n_clusters: int) -> np.ndarray:
    """
    Perform hierarchical clustering on embeddings.

    :param embeddings: Array of embeddings
    :param n_clusters: Number of clusters
    :return: Cluster labels for each code
    """
    print(f"Performing hierarchical clustering with {n_clusters} clusters...")
    clusterer = AgglomerativeClustering(n_clusters=n_clusters)
    labels = clusterer.fit_predict(embeddings)
    print(f"Clustering complete. Cluster distribution:")

    unique, counts = np.unique(labels, return_counts=True)
    for cluster_id, count in zip(unique, counts):
        print(f"  Cluster {cluster_id}: {count} codes")

    return labels


def build_chroma_collections(df: pd.DataFrame, embeddings: np.ndarray,
                            cluster_labels: np.ndarray, embedding_function: OpenAIEmbeddings):
    """
    Build Chroma collections using LangChain, one per cluster.

    :param df: DataFrame with code data
    :param embeddings: Array of embeddings
    :param cluster_labels: Cluster assignments
    :param embedding_function: LangChain OpenAI embeddings function
    """
    print("Building Chroma vector store using LangChain...")

    # Get unique clusters
    unique_clusters = np.unique(cluster_labels)

    for cluster_id in unique_clusters:
        collection_name = f"g_codes_cluster_{cluster_id}"
        print(f"Building collection: {collection_name}")

        # Get codes for this cluster
        cluster_mask = cluster_labels == cluster_id
        cluster_df = df[cluster_mask].copy()
        cluster_embeddings = embeddings[cluster_mask]

        # Create LangChain Document objects with page_content as long_description
        documents = []
        for idx, row in cluster_df.iterrows():
            doc = Document(
                page_content=row['long_description'],  # Required: use long_description as page_content
                metadata={
                    'icd_code': row['icd_code'],
                    'short_description': row['short_description'],
                    'cluster_id': int(cluster_id)
                }
            )
            documents.append(doc)

        # Convert embeddings to list format for LangChain
        embeddings_list = [emb.tolist() for emb in cluster_embeddings]

        # Create Chroma vector store using LangChain with pre-computed embeddings
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            collection_name=collection_name,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_metadata={"cluster_id": int(cluster_id)}
        )

        print(f"  Added {len(documents)} codes to {collection_name}")

    print(f"Vector store built and persisted to {CHROMA_PERSIST_DIR}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Building ICD-10 G-Codes Vector Store with LangChain")
    print("=" * 60)

    # Initialize LangChain OpenAI embeddings
    print("Initializing LangChain OpenAI embeddings...")
    embedding_function = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

    # Step 1: Load codes
    df = load_codes()

    # Step 2: Generate embeddings using LangChain
    embeddings = generate_embeddings(df, embedding_function)

    # Step 3: Find optimal number of clusters
    '''Upon inspection, a value of k greater than 100 might improve the clustering quality.
        The consequence is that creating the code chart takes MUCH longer.
    '''
    optimal_k = find_optimal_clusters(embeddings, min_k=60, max_k=80, step=2)

    # Step 4: Perform clustering
    cluster_labels = perform_clustering(embeddings, optimal_k)

    # Step 5: Build Chroma collections using LangChain
    build_chroma_collections(df, embeddings, cluster_labels, embedding_function)

    print("=" * 60)
    print("Vector store build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
