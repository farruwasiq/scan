import json
from tabulate import tabulate
import sys

def convert_kubescape_json_to_markdown(json_file):
    """
    Reads a Kubescape JSON output file and converts it into a Markdown table.

    Args:
        json_file (str): The path to the Kubescape JSON file.

    Returns:
        str: A Markdown formatted table of the Kubescape scan results.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Error: File not found: {json_file}"
    except json.JSONDecodeError:
        return f"Error: Invalid JSON format in: {json_file}"

    if not isinstance(data, dict) or 'summaryDetails' not in data or 'controls' not in data['summaryDetails'] or not isinstance(data['summaryDetails']['controls'], dict):
        return "Error: Invalid Kubescape JSON structure."

    controls_data = data['summaryDetails']['controls']
    output_string = ""

    # Extract summary information (similar to the screenshot)
    if 'apiVersion' in data:
        output_string += f"**ApiVersion:** {data['apiVersion']}\n"
    if 'kind' in data:
        output_string += f"**Kind:** {data['kind']}\n"
    if 'name' in data:
        output_string += f"**Name:** {data['name']}\n"
    if 'namespace' in data:
        output_string += f"**Namespace:** {data['namespace']}\n"

    # Calculate counts for the Controls summary
    total_controls = len(controls_data)
    failed_count = 0
    action_required_count = 0  # Kubescape JSON doesn't directly provide "actionRequired"

    for control_id, control in controls_data.items():
        if control.get('statusInfo', {}).get('status') == 'failed':
            failed_count += 1

    output_string += f"**Controls:** {total_controls} (Failed: {failed_count}, Action Required: N/A)\n\n"  # "Action Required" is not reliably available

    output_string += "**Resources**\n\n"

    table_data = []
    headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]

    for control_id, control in controls_data.items():
        severity = "N/A"  # Severity is not directly available at this level
        control_name = control.get('name', 'N/A')
        docs_url = "N/A"  #  Docs URL is not consistently available
        assisted_remediation = "N/A" # Assisted Remediation is not consistently available

        table_data.append([severity, control_name, docs_url, assisted_remediation])

    output_string += tabulate(table_data, headers=headers, tablefmt="grid")
    return output_string

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)