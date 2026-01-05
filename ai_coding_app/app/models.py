from django.db import models

#### #! DO NOT MODIFY THIS CODE #! ####

class TestModel(models.Model):
    """
    This is a test model for the app. An example record has been created in the native SQLite database.

    Attributes:
        field1 (str): A string field
        field2 (int): An integer field
    """

    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()

    def __str__(self) -> str:
        f"""
        Return the string representation of the model instance.

        :return: The string representation of the model instance.
        :rtype: str
        """
        return self.field1
    
    def to_dict(self) -> dict:
        f"""
        Convert the model instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the model instance.
        :rtype: dict
        """
        return {
            'id': self.id,
            'field1': self.field1,
            'field2': self.field2,
        }
    
#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Create your models here.

class Chart(models.Model):
    """
    Represents a medical chart containing multiple notes from a patient visit.

    Attributes:
        case_id (str): Unique identifier for the chart (e.g., 'case12')
        visit_info (str): Information about the visit (date, time, type)
    """
    case_id = models.CharField(max_length=50, unique=True, db_index=True)
    visit_info = models.TextField()

    def __str__(self) -> str:
        """
        Return the string representation of the chart.

        :return: The case ID of the chart
        :rtype: str
        """
        return f"Chart {self.case_id}"

    def to_dict(self) -> dict:
        """
        Convert the chart instance to a dictionary for JSON serialization.
        Includes all associated notes.

        :return: The dictionary representation of the chart
        :rtype: dict
        """
        return {
            'id': self.id,
            'case_id': self.case_id,
            'visit_info': self.visit_info,
            'notes': [note.to_dict() for note in self.notes.all()]
        }


class Note(models.Model):
    """
    Represents a single note within a medical chart.
    Each note has a title, unique ID, and content from the doctor's documentation.

    Attributes:
        chart (Chart): The chart this note belongs to
        note_id (str): Unique identifier for the note (e.g., 'note-hpi-case12')
        title (str): The title/section of the note (e.g., 'HPI', 'PHYSICAL EXAM')
        content (str): The actual content of the medical note
    """
    chart = models.ForeignKey(
        Chart,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note_id = models.CharField(max_length=100, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self) -> str:
        """
        Return the string representation of the note.

        :return: The title and note ID
        :rtype: str
        """
        return f"{self.title} ({self.note_id})"

    def to_dict(self) -> dict:
        """
        Convert the note instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the note
        :rtype: dict
        """
        return {
            'id': self.id,
            'note_id': self.note_id,
            'title': self.title,
            'content': self.content
        }


class ICD10Code(models.Model):
    """
    Represents an ICD-10 code from the G-codes (diseases of the nervous system).

    Attributes:
        icd_code (str): The ICD-10 code identifier (e.g., 'G000')
        short_description (str): Short description of the code
        long_description (str): Detailed description of the code
    """
    icd_code = models.CharField(max_length=20, unique=True, db_index=True)
    short_description = models.CharField(max_length=500)
    long_description = models.TextField()

    def __str__(self) -> str:
        """
        Return the string representation of the ICD-10 code.

        :return: The ICD code and short description
        :rtype: str
        """
        return f"{self.icd_code}: {self.short_description}"

    def to_dict(self) -> dict:
        """
        Convert the ICD-10 code instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the ICD-10 code
        :rtype: dict
        """
        return {
            'id': self.id,
            'icd_code': self.icd_code,
            'short_description': self.short_description,
            'long_description': self.long_description
        }


class CodeAssignment(models.Model):
    """
    Represents the many-to-many relationship between notes and ICD-10 codes.
    Stores the result of AI-powered code assignment with similarity scores.

    Attributes:
        note (Note): The medical note being coded
        icd_code (ICD10Code): The assigned ICD-10 code
        similarity_score (float): Cosine similarity score from vector search (0-1)
        created_at (datetime): Timestamp when the assignment was created
    """
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='code_assignments'
    )
    icd_code = models.ForeignKey(
        ICD10Code,
        on_delete=models.CASCADE,
        related_name='note_assignments'
    )
    similarity_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('note', 'icd_code')
        ordering = ['-similarity_score']

    def __str__(self) -> str:
        """
        Return the string representation of the code assignment.

        :return: The note and code assignment with score
        :rtype: str
        """
        return f"{self.note.note_id} -> {self.icd_code.icd_code} (score: {self.similarity_score:.4f})"

    def to_dict(self) -> dict:
        """
        Convert the code assignment instance to a dictionary for JSON serialization.

        :return: The dictionary representation of the code assignment
        :rtype: dict
        """
        return {
            'id': self.id,
            'note_id': self.note.note_id,
            'icd_code': self.icd_code.icd_code,
            'short_description': self.icd_code.short_description,
            'similarity_score': self.similarity_score,
            'created_at': self.created_at.isoformat()
        }
