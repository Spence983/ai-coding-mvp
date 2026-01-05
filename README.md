# AI-Powered Medical Chart Coding System

## Overview

This Django-based application provides AI-powered ICD-10 code assignment for medical charts using semantic search with vector embeddings. The system ingests medical charts, stores them in a relational database, and automatically assigns relevant ICD-10 diagnostic codes using LangChain and ChromaDB.

## System Architecture

### Technology Stack
- **Backend Framework**: Django 5.0 + Django REST Framework
- **Database**: SQLite (relational data storage)
- **Vector Store**: ChromaDB (persistent vector database)
- **AI Framework**: LangChain
- **Embeddings**: OpenAI text-embedding-3-large
- **Clustering**: scikit-learn (AgglomerativeClustering)

### Core Components

1. **Chart Ingestion Service** - Processes and stores medical charts with their associated notes
2. **Vector Store Builder** - Creates clustered vector embeddings for ICD-10 codes using LangChain
3. **Semantic Search Engine** - Matches medical notes to ICD-10 codes using similarity search
4. **REST API** - Provides endpoints for chart management and code assignment

## Database Schema Design

### Chart Storage Schema

The chart storage schema follows a normalized relational design to efficiently represent the one-to-many relationship between charts and notes:

**Design Decisions:**
- **Chart Model**: Stores visit-level information with a unique `case_id` as the primary identifier. The `visit_info` field is a TextField to accommodate varying metadata formats without requiring schema changes.
- **Note Model**: Uses a ForeignKey relationship to Chart with CASCADE deletion, ensuring referential integrity. Each note has a unique `note_id` for traceability and includes `title` and `content` fields for structured storage.
- **Normalization**: The one-to-many relationship (Chart → Notes) avoids data duplication and allows flexible querying of individual notes or complete charts.
- **Indexing**: Unique constraints and database indexes on `case_id` and `note_id` ensure fast lookups and prevent duplicates.

### Code Assignment Schema

The code assignment schema captures the many-to-many relationship between medical notes and ICD-10 codes with additional metadata:

**Design Decisions:**
- **ICD10Code Model**: Stores the complete ICD-10 code dataset with `icd_code` as the unique identifier. Includes both `short_description` and `long_description` to support different use cases.
- **CodeAssignment Model**: Implements the many-to-many relationship as an explicit "through" model rather than Django's default ManyToManyField. This allows storing the `similarity_score` (float) and `created_at` (timestamp) for each assignment.
- **Similarity Score**: Stored as a float to preserve precision from the vector search algorithm, enabling quality assessment and filtering.
- **Unique Constraint**: The `unique_together` constraint on `(note, icd_code)` prevents duplicate assignments while allowing updates via `update_or_create`.
- **Ordering**: Default ordering by `-similarity_score` ensures the most relevant codes appear first in queries.

This design supports both real-time code assignment (via API) and historical tracking of coding decisions with their confidence scores.

## Clustering and Code Assignment Methodology

### Hierarchical Clustering Approach

The system uses hierarchical clustering to organize ICD-10 codes into semantically similar groups, improving search efficiency and accuracy.

**Implementation Details:**
1. **Embedding Generation**: All 931 ICD-10 G-codes are embedded using OpenAI's `text-embedding-3-large` model via LangChain, creating 3072-dimensional vector representations.
2. **Optimal Cluster Selection**: scikit-learn's AgglomerativeClustering is applied with varying k values (8-100), and silhouette scores are calculated to identify the optimal number of clusters.
3. **Cluster Storage**: Each cluster is stored as a separate LangChain Chroma collection, with Document objects using `page_content=long_description` and metadata containing the ICD code and descriptions.

**Why Hierarchical Clustering:**
- **Efficiency**: Searching within smaller clusters is faster than searching all 931 codes
- **Semantic Grouping**: Similar conditions (e.g., migraines vs. epilepsy) naturally cluster together
- **Scalability**: The approach scales well if the code set expands
- **Simplicity**: Hierarchical clustering requires minimal hyperparameter tuning compared to more complex methods

### Code Assignment Algorithm

When a medical chart is submitted for coding:

1. **Note Processing**: Each note's content is embedded using the same OpenAI model via LangChain
2. **Cluster Search**: The system searches across all cluster collections using LangChain's `similarity_search_with_relevance_scores(k=1)`
3. **Best Match Selection**: For each cluster, the top matching code is retrieved, and the highest similarity score across all clusters determines the final assignment
4. **Persistence**: If `save=True`, the assignment is stored in the CodeAssignment table with the similarity score and timestamp

**Similarity Metric**: LangChain's relevance scores are used directly, representing the semantic similarity between the note content and ICD-10 code descriptions.

## API Endpoints

### Chart Management

#### GET `/app/chart-schema/`
Returns the schema definition for Chart and Note models.

**Response:**
```json
{
  "Chart": {
    "id": {"type": "AutoField", "required": false},
    "case_id": {"type": "CharField", "required": true},
    "visit_info": {"type": "TextField", "required": true}
  },
  "Note": {
    "id": {"type": "AutoField", "required": false},
    "chart": {"type": "ForeignKey", "required": true},
    "note_id": {"type": "CharField", "required": true},
    "title": {"type": "CharField", "required": true},
    "content": {"type": "TextField", "required": true}
  }
}
```

#### POST `/app/upload-chart/`
Uploads a medical chart with its notes to the database.

**Request:**
```json
{
  "case_id": "case12",
  "visit_info": "In-Person Visit 3/18/2025, 14:30 EST",
  "notes": [
    {
      "note_id": "note-hpi-case12",
      "title": "HPI",
      "content": "Patient has a 5-year history of migraines..."
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully uploaded chart to SQLite database!",
  "count": 1
}
```

**Idempotency**: Attempting to upload the same `case_id` twice returns the existing chart count without creating duplicates.

#### GET `/app/charts/`
Retrieves all charts with their associated notes.

**Response:**
```json
[
  {
    "id": 1,
    "case_id": "case12",
    "visit_info": "In-Person Visit 3/18/2025, 14:30 EST",
    "notes": [
      {
        "id": 1,
        "note_id": "note-hpi-case12",
        "title": "HPI",
        "content": "Patient has a 5-year history..."
      }
    ]
  }
]
```

### Code Assignment

#### POST `/app/code-chart/`
Assigns ICD-10 codes to all notes in a chart using AI-powered semantic search.

**Request:**
```json
{
  "case_id": "case12",
  "save": true
}
```

**Response:**
```json
{
  "case_id": "case12",
  "codes": [
    {
      "note_id": "note-hpi-case12",
      "note_title": "HPI",
      "icd_code": "G43.909",
      "short_description": "Migraine, unspecified, not intractable",
      "similarity_score": 0.8234
    }
  ],
  "saved": true
}
```

**Parameters:**
- `case_id` (required): The chart identifier
- `save` (optional, default=false): If true, persists code assignments to the database

## Setup and Usage

### Prerequisites
- Python 3.13+
- OpenAI API key

### Installation

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables:
```bash
# Create .env file with:
OPENAI_API_KEY=your_api_key_here
```

3. Apply database migrations:
```bash
cd ai_coding_app
python manage.py migrate
```

### Building the Vector Store

**One-time setup** (takes ~5-10 minutes):
```bash
cd ai_coding_app
uv run python ../scripts/build_vector_store.py
```

This script:
1. Loads 931 ICD-10 G-codes from CSV
2. Generates embeddings using LangChain's OpenAIEmbeddings
3. Performs hierarchical clustering with silhouette score optimization
4. Creates LangChain Chroma collections (one per cluster)
5. Persists the vector store to `chroma_db/`

### Running the Application

Start the Django server:
```bash
task run-local
# Or: python ai_coding_app/manage.py runserver
```

The API will be available at `http://localhost:8000`

### Testing

Run the test script (requires server running):
```bash
task test-api
# Or: python scripts/test_api_script.py
```

This executes all API endpoints in sequence:
1. Gets the chart schema
2. Transforms `data/medical_chart.txt` to JSON
3. Uploads the chart
4. Lists all charts
5. Assigns ICD-10 codes with persistence

## Project Structure

```
ai-coding-mvp/
├── ai_coding_app/
│   ├── app/
│   │   ├── models.py          # Database models (Chart, Note, ICD10Code, CodeAssignment)
│   │   ├── views.py           # API endpoints
│   │   ├── urls.py            # URL routing
│   │   ├── admin.py           # Django admin configuration
│   │   └── migrations/        # Database migrations
│   ├── manage.py
│   └── db.sqlite3             # SQLite database
├── scripts/
│   ├── build_vector_store.py  # Vector store creation with LangChain
│   ├── test_api_script.py     # API testing script
│   └── inspect_clusters.py    # Cluster analysis tool
├── data/
│   ├── g_codes.csv            # ICD-10 G-codes dataset
│   └── medical_chart.txt      # Sample medical chart
├── chroma_db/                 # Persisted ChromaDB vector store
├── pyproject.toml             # Python dependencies
├── taskfile.yaml              # Task runner configuration
└── README.md
```

## Key Features

- **LangChain Integration**: Uses LangChain framework for embeddings and vector store management
- **Semantic Search**: AI-powered code matching using vector similarity
- **Hierarchical Clustering**: Optimized search with automatic cluster selection
- **Idempotent Uploads**: Prevents duplicate chart entries
- **Persistent Storage**: Both relational (SQLite) and vector (ChromaDB) data persisted
- **Comprehensive API**: RESTful endpoints for all operations
- **Type Hints**: Full type annotations for better code maintainability
- **Documentation**: Sphinx-style docstrings throughout

## Performance Characteristics

- **Vector Store Build**: ~5-10 minutes (one-time)
- **Chart Upload**: <100ms per chart
- **Code Assignment**: ~2-3 seconds per chart (11 notes)
- **Storage**: ~50MB for vector store, <5MB for SQLite

## Future Enhancements

- Support for additional ICD-10 code categories beyond G-codes
- Batch processing for multiple charts
- Confidence threshold filtering for low-similarity matches
- Integration with electronic health record (EHR) systems
- Real-time code suggestion API during chart documentation
