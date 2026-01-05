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

import re
import os

def get_chart_schema() -> dict:
    """
    Get the chart schema from the API.

    :return: The API response.
    :rtype: dict
    """
    response = requests.get(f"{API_BASE_URL}/app/chart-schema/")
    return response.json()

def transform_chart_to_json() -> dict:
    """
    Transform a chart to a JSON object by parsing the medical chart text file.

    :return: The JSON object of the chart.
    :rtype: dict
    """
    # Path to the medical chart file
    chart_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'medical_chart.txt')

    with open(chart_path, 'r') as f:
        content = f.read()

    # Split into sections
    sections = re.split(r'\n(?=[A-Z\s]+\n)', content)

    notes = []
    visit_info = ""
    case_id = None

    for section in sections:
        lines = section.strip().split('\n')
        if len(lines) < 2:
            continue

        title = lines[0].strip()

        # Find Note ID line
        note_id_line = None
        content_start = 1
        for i, line in enumerate(lines[1:], 1):
            if line.startswith('Note ID:'):
                note_id_line = line
                content_start = i + 1
                break

        if not note_id_line:
            continue

        note_id = note_id_line.replace('Note ID:', '').strip()

        # Extract case_id from first note_id
        if case_id is None and 'case' in note_id:
            case_id = note_id.split('-')[-1]

        # Get content (everything after Note ID line)
        note_content = '\n'.join(lines[content_start:]).strip()

        # Special handling for METADATA
        if title == 'METADATA':
            visit_info = note_content
        else:
            notes.append({
                'note_id': note_id,
                'title': title,
                'content': note_content
            })

    chart_json = {
        'case_id': case_id,
        'visit_info': visit_info,
        'notes': notes
    }

    return chart_json

def upload_chart() -> dict:
    """
    Upload a chart to the API.

    :return: The API response.
    :rtype: dict
    """
    chart_data = transform_chart_to_json()
    response = requests.post(f"{API_BASE_URL}/app/upload-chart/", json=chart_data)
    return response.json()

def list_charts() -> dict:
    """
    List all the charts in the API.

    :return: The API response.
    :rtype: dict
    """
    response = requests.get(f"{API_BASE_URL}/app/charts/")
    return response.json()

def code_chart() -> dict:
    """
    Code a chart using the API.

    :return: The API response.
    :rtype: dict
    """
    # Get the case_id from the transformed chart
    chart_data = transform_chart_to_json()
    case_id = chart_data['case_id']

    # Code the chart with save=True to persist results
    payload = {
        'case_id': case_id,
        'save': True
    }
    response = requests.post(f"{API_BASE_URL}/app/code-chart/", json=payload)
    return response.json()


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
