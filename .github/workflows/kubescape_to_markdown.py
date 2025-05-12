import json
import sys
from tabulate import tabulate

def convert_kubescape_json_to_markdown(json_file_path):
    """
    Converts Kubescape JSON output to a Markdown table, focusing on the summary details.

    Args:
        json_file_path (str): Path to the Kubescape JSON output file.

    Returns:
        str: A Markdown table representing the Kubescape summary, or an error message.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Error: File not found at {json_file_path}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON in {json_file_path}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

    if not data or 'summaryDetails' not in data or 'controls' not in data['summaryDetails']:
        return "Error: Invalid Kubescape JSON format.  Expected 'summaryDetails' and 'controls' fields."

    controls = data['summaryDetails']['controls']
    table_data = []
    headers = ["Control Name", "Status", "Compliance Score", "Category"]

    for control_id, control_data in controls.items():
        status = control_data['statusInfo']['status']
        compliance_score = control_data.get('complianceScore', 'N/A')  # Handle missing score
        category = control_data['category']['name']
        control_name = control_data['name']  # Get the control name
        table_data.append([control_name, status, compliance_score, category])

    # Sort the table by Control Name
    table_data.sort(key=lambda x: x[0])
    markdown_table = tabulate(table_data, headers=headers, tablefmt="github")
    return markdown_table

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)
