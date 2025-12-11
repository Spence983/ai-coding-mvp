#### #! DO NOT MODIFY THIS CODE #! ####

import requests

API_BASE_URL = "http://localhost:8000"

def test_api() -> dict:
    """
    Test the API by making a GET request to the test-view endpoint.

    :return: The JSON response from the test-view endpoint.
    :rtype: dict
    """
    response = requests.get(f"{API_BASE_URL}/app/test-view/")
    return response.json()


#### #! END OF DO NOT MODIFY THIS CODE #! ####

# Build your script here.

def get_chart_schema() -> dict:
    """
    Get the chart schema from the API.

    :return: The API response.
    :rtype: dict
    """
    pass

def transform_chart_to_json() -> dict:
    """
    Transform a chart to a JSON object.

    :return: The JSON object of the chart.
    :rtype: dict
    """
    pass

def upload_chart() -> dict:
    """
    Upload a chart to the API.

    :return: The API response.
    :rtype: dict
    """
    pass

def list_charts() -> dict:
    """
    List all the charts in the API.

    :return: The API response.
    :rtype: dict
    """
    pass

def code_chart() -> dict:
    """
    Code a chart using the API.

    :return: The API response.
    :rtype: dict
    """
    pass


#### #! DO NOT MODIFY THIS CODE #! ####

def build_output() -> str:
    """
    Print the output of the script.
    """

    print("##### OUTPUT GENERATION #####")
    print()
    
    print("Test Output:")
    print()
    print(test_api())

    print()
    print("--------------------------------")
    print()

    print("1. Chart Schema:")
    print()
    print(get_chart_schema())

    print()
    print("--------------------------------")
    print()

    print("2. Chart to JSON:")
    print()
    print(transform_chart_to_json())

    print()
    print("--------------------------------")
    print()

    print("3. Upload Chart:")
    print()
    print(upload_chart())

    print()
    print("--------------------------------")
    print()

    print("4. List Charts:")
    print()
    print(list_charts())

    print()
    print("--------------------------------")
    print()

    print("5. Code Chart:")
    print()
    print(code_chart())

    print()
    print("--------------------------------")
    print()

    print("##### END OF OUTPUT GENERATION #####")

build_output()

#### #! END OF DO NOT MODIFY THIS CODE #! ####
