import json
import sys
from tabulate import tabulate

def convert_kubescape_json_to_markdown(json_file_path):
    """
    Reads a Kubescape JSON output file, extracts relevant information,
    and converts it into a Markdown table format.  Now includes
    vulnerability and remediation data.

    Args:
        json_file_path (str): The path to the Kubescape JSON output file.

    Returns:
        str: A Markdown table representing the Kubescape scan results,
             or an error message if the file cannot be processed.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Error: File not found at {json_file_path}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON format in {json_file_path}"
    except Exception as e:
        return f"Error: An unexpected error occurred: {e}"

    if not isinstance(data, dict) or "summaryDetails" not in data or "controls" not in data["summaryDetails"]:
        return "Error: Invalid Kubescape JSON structure.  Expected 'summaryDetails' and 'controls' fields."

    controls = data["summaryDetails"]["controls"]
    table_data = []
    headers = ["Control ID", "Name", "Status", "Compliance Score", "Category", "Vulnerability", "Remediation"]  # Added headers

    for control_id, control_data in controls.items():
        # Handle missing keys gracefully.  Important for robustness.
        name = control_data.get("name", "N/A")
        status = control_data.get("statusInfo", {}).get("status", "N/A")
        compliance_score = control_data.get("complianceScore", "N/A")
        category = control_data.get("category", {}).get("name", "N/A")

        #  Get vulnerability and remediation info.  Adjust the key names
        #  based on the *actual* structure of your JSON.  This is the
        #  most likely place you'll need to customize.
        vulnerability = control_data.get("vulnerability", "N/A")  #  <--  ADJUST THIS KEY
        remediation = control_data.get("remediation", "N/A")      #  <--  ADJUST THIS KEY

        table_data.append([control_id, name, status, compliance_score, category, vulnerability, remediation])

    if not table_data:
        return "No controls found in Kubescape JSON output."

    return tabulate(table_data, headers=headers, tablefmt="github")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_table = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_table)
