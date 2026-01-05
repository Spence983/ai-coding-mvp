"""
Inspect the hierarchical clustering results stored in ChromaDB.

This script reads all cluster collections and displays:
- Cluster distribution (how many codes in each cluster)
- Sample codes from each cluster to understand the grouping logic
"""

import os
import sys
import chromadb
from collections import defaultdict

# Add Django app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_coding_app'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_coding_app.settings')

import django
django.setup()

# Constants
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')


def inspect_clusters():
    """Inspect all cluster collections and display their contents."""
    print("=" * 80)
    print("ICD-10 G-Codes Hierarchical Clustering Analysis")
    print("=" * 80)
    print()

    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Get all collections
    collections = chroma_client.list_collections()

    print(f"Total clusters found: {len(collections)}")
    print()

    # Sort collections by cluster ID
    cluster_data = []

    for collection_metadata in collections:
        collection = chroma_client.get_collection(collection_metadata.name)

        # Get all items in this collection
        results = collection.get(include=['metadatas', 'documents'])

        cluster_id = collection_metadata.metadata.get('cluster_id', -1)
        cluster_data.append({
            'cluster_id': cluster_id,
            'name': collection_metadata.name,
            'count': len(results['ids']),
            'codes': results['metadatas'],
            'descriptions': results['documents']
        })

    # Sort by cluster_id
    cluster_data.sort(key=lambda x: x['cluster_id'])

    # Display cluster distribution
    print("Cluster Distribution:")
    print("-" * 80)
    for cluster in cluster_data:
        print(f"Cluster {cluster['cluster_id']:2d}: {cluster['count']:3d} codes")
    print()

    # Display all codes from each cluster
    print("All Codes from Each Cluster:")
    print("=" * 80)

    for cluster in cluster_data:
        print()
        print(f"CLUSTER {cluster['cluster_id']} ({cluster['count']} codes total)")
        print("-" * 80)

        # Show all codes from this cluster
        for i in range(cluster['count']):
            code_data = cluster['codes'][i]
            print(f"  {code_data['icd_code']:6s}: {code_data['short_description']}")

    print()
    print("=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    inspect_clusters()
