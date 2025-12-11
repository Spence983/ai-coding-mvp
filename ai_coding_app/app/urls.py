from django.urls import path
from .views import TestView


urlpatterns = [
    #### #! DO NOT MODIFY THIS CODE #! ####

    path("test-view/", TestView.as_view(), name="test-view"),
    
    #### #! END OF DO NOT MODIFY THIS CODE #! ####

    # Create your urls here.
]