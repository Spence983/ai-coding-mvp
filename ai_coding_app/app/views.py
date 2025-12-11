from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from .models import TestModel

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
