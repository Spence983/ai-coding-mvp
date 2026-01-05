from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import TestModel, Chart, Note, ICD10Code, CodeAssignment

#### #! DO NOT MODIFY THIS CODE #! ####

class TestView(APIView):
    """
    This is a test view for the app. It returns a list of all the records in the TestModel.
    """

    def get(self, request: Request) -> Response :
        f"""
        Get all the records from the TestModel and return them as a list of dictionaries.

        :param request: The HTTP request object.

        :return: A JSON response containing the list of records.
        :rtype: Response
        """
        records = TestModel.objects.all()
        return Response([record.to_dict() for record in records], status=status.HTTP_200_OK)

#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Create your views here.
class ChartSchemaView(APIView):
    """
    Returns the schema definition for how charts are stored in the database.
    Dynamically generates schema from the Chart and Note models.
    """

    def get(self, request: Request) -> Response:
        """
        Get the database schema for Chart and Note models by introspecting the models.

        :param request: The HTTP request object
        :return: JSON response containing the schema definition
        :rtype: Response
        """
        def get_field_info(field):
            """Helper function to extract readable field information."""
            field_type = field.get_internal_type()
            info = {"type": field_type}

            if hasattr(field, 'max_length') and field.max_length:
                info["max_length"] = field.max_length
            if field.unique:
                info["unique"] = True
            if field.db_index:
                info["indexed"] = True
            if field.primary_key:
                info["primary_key"] = True
            if hasattr(field, 'related_model') and field.related_model:
                info["foreign_key_to"] = field.related_model.__name__
                if hasattr(field.remote_field, 'on_delete'):
                    info["on_delete"] = field.remote_field.on_delete.__name__
                if hasattr(field.remote_field, 'related_name'):
                    info["related_name"] = field.remote_field.related_name

            return info

        schema = {}

        # Get Chart schema
        chart_fields = {}
        for field in Chart._meta.get_fields():
            if not field.many_to_many and not field.one_to_many:
                chart_fields[field.name] = get_field_info(field)

        schema["Chart"] = chart_fields

        # Get Note schema
        note_fields = {}
        for field in Note._meta.get_fields():
            if not field.many_to_many and not field.one_to_many:
                note_fields[field.name] = get_field_info(field)

        schema["Note"] = note_fields

        return Response(schema, status=status.HTTP_200_OK)


class UploadChartView(APIView):
    """
    Handles uploading a medical chart to the database.
    Implements idempotency - won't create duplicates if same chart uploaded twice.
    """

    def post(self, request: Request) -> Response:
        """
        Upload a chart with its notes to the database.

        Expected input format:
        {
            "case_id": "case12",
            "visit_info": "In-Person Visit 3/18/2025, 14:30 EST",
            "notes": [
                {
                    "note_id": "note-hpi-case12",
                    "title": "HPI",
                    "content": "Patient has a 5-year history..."
                },
                ...
            ]
        }

        :param request: The HTTP request object containing chart data
        :return: JSON response with success message and chart count
        :rtype: Response
        """
        data = request.data

        # Validate required fields
        if 'case_id' not in data or 'visit_info' not in data or 'notes' not in data:
            return Response(
                {"error": "Missing one or more required fields: case_id, visit_info, notes"},
                status=status.HTTP_400_BAD_REQUEST
            )

        case_id = data['case_id']

        # Check for idempotency - if chart already exists, return existing
        existing_chart = Chart.objects.filter(case_id=case_id).first()
        if existing_chart:
            total_count = Chart.objects.count()
            return Response(
                {
                    "message": f"Chart with case_id '{case_id}' already exists. No duplicate created.",
                    "count": total_count
                },
                status=status.HTTP_200_OK
            )

        # Create the chart
        chart = Chart.objects.create(
            case_id=case_id,
            visit_info=data['visit_info']
        )

        # Create associated notes
        notes_data = data['notes']
        for note_data in notes_data:
            Note.objects.create(
                chart=chart,
                note_id=note_data['note_id'],
                title=note_data['title'],
                content=note_data['content']
            )

        # Get total count of charts
        total_count = Chart.objects.count()

        return Response(
            {
                "message": "Successfully uploaded chart to SQLite database!",
                "count": total_count
            },
            status=status.HTTP_201_CREATED
        )


class ListChartsView(APIView):
    """
    Returns all charts stored in the database with their associated notes.
    """

    def get(self, request: Request) -> Response:
        """
        Get all charts from the database.

        :param request: The HTTP request object
        :return: JSON response containing all charts with their notes
        :rtype: Response
        """
        charts = Chart.objects.all()
        return Response(
            [chart.to_dict() for chart in charts],
            status=status.HTTP_200_OK
        )


class CodeChartView(APIView):
    """
    AI-powered medical chart coding using semantic search on ICD-10 codes.
    Uses hierarchical clustering and vector similarity to assign codes to notes.
    """

    def post(self, request: Request) -> Response:
        """
        Code a medical chart by assigning ICD-10 codes to each note using semantic search with LangChain.

        Expected input format:
        {
            "case_id": "case12",
            "save": true  # Optional: whether to persist results to database
        }

        :param request: The HTTP request object containing case_id and save flag
        :return: JSON response with list of assigned codes and similarity scores
        :rtype: Response
        """
        import os
        from dotenv import load_dotenv
        from langchain_openai import OpenAIEmbeddings
        from langchain_chroma import Chroma
        import chromadb

        # Load environment variables
        load_dotenv()

        data = request.data

        # Validate required fields
        if 'case_id' not in data:
            return Response(
                {"error": "Missing required field: case_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        case_id = data['case_id']
        save = data.get('save', False)

        # Get the chart
        try:
            chart = Chart.objects.get(case_id=case_id)
        except Chart.DoesNotExist:
            return Response(
                {"error": f"Chart with case_id '{case_id}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all notes for the chart
        notes = chart.notes.all()

        if not notes:
            return Response(
                {"error": f"No notes found for chart '{case_id}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize LangChain OpenAI embeddings
        embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=os.getenv('OPENAI_API_KEY')
        )

        # Get Chroma persist directory
        chroma_persist_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'chroma_db'
        )

        # Get all cluster collection names
        chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)
        collections = chroma_client.list_collections()

        results = []

        for note in notes:
            # Search across all clusters to find best match using LangChain
            best_match = None
            best_score = -1

            for collection_metadata in collections:
                # Load vector store using LangChain
                vectorstore = Chroma(
                    collection_name=collection_metadata.name,
                    embedding_function=embedding_function,
                    persist_directory=chroma_persist_dir
                )

                # Perform similarity search with k=1 (top match in this cluster)
                docs_and_scores = vectorstore.similarity_search_with_relevance_scores(
                    note.content,
                    k=1
                )

                if docs_and_scores:
                    doc, similarity = docs_and_scores[0]

                    if similarity > best_score:
                        best_score = similarity
                        best_match = {
                            'icd_code': doc.metadata['icd_code'],
                            'short_description': doc.metadata['short_description'],
                            'similarity_score': similarity
                        }

            if best_match:
                result = {
                    'note_id': note.note_id,
                    'note_title': note.title,
                    'icd_code': best_match['icd_code'],
                    'short_description': best_match['short_description'],
                    'similarity_score': round(best_match['similarity_score'], 4)
                }
                results.append(result)

                # Save to database if requested
                if save:
                    icd_code_obj = ICD10Code.objects.get(icd_code=best_match['icd_code'])
                    CodeAssignment.objects.update_or_create(
                        note=note,
                        icd_code=icd_code_obj,
                        defaults={'similarity_score': best_match['similarity_score']}
                    )

        return Response(
            {
                "case_id": case_id,
                "codes": results,
                "saved": save
            },
            status=status.HTTP_200_OK
        )
