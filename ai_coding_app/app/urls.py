from django.urls import path
from .views import TestView, ChartSchemaView, UploadChartView, ListChartsView, CodeChartView


urlpatterns = [
    #### #! DO NOT MODIFY THIS CODE #! ####

    path("test-view/", TestView.as_view(), name="test-view"),
    
    #### #! END OF DO NOT MODIFY THIS CODE #! ####

    # Create your urls here.
    path("chart-schema/", ChartSchemaView.as_view(), name="chart-schema"),
    path("upload-chart/", UploadChartView.as_view(), name="upload-chart"),
    path("charts/", ListChartsView.as_view(), name="charts"),
    path("code-chart/", CodeChartView.as_view(), name="code-chart"),
]