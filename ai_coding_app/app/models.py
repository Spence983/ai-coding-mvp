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
