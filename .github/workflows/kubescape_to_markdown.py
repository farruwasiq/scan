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

    if not isinstance(data, dict) or 'controls' not in data or not isinstance(data['controls'], list):
        return "Error: Invalid Kubescape JSON structure."

    controls_data = data['controls']
    output_string = ""

    if 'apiVersion' in data:
        output_string += f"**ApiVersion:** {data['apiVersion']}\n"
    if 'kind' in data:
        output_string += f"**Kind:** {data['kind']}\n"
    if 'name' in data:
        output_string += f"**Name:** {data['name']}\n"
    if 'namespace' in data:
        output_string += f"**Namespace:** {data['namespace']}\n"
    if 'controls' in data:
        failed_count = sum(1 for control in controls_data if control.get('status', {}).get('status') == 'failed')
        action_required_count = sum(1 for control in controls_data if control.get('status', {}).get('status') == 'actionRequired')
        total_controls = len(controls_data)
        output_string += f"**Controls:** {total_controls} (Failed: {failed_count}, action required: {action_required_count})\n\n"

    output_string += "**Resources**\n\n"

    table_data = []
    headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]

    for control in controls_data:
        if 'rules' in control and isinstance(control['rules'], list):
            for rule in control['rules']:
                severity = rule.get('severity', 'N/A')
                control_name = rule.get('name', 'N/A')
                docs_url = rule.get('remediation', 'N/A')
                assisted_remediation = rule.get('fixPaths', [])

                remediation_str = ""
                if assisted_remediation:
                    remediation_str = "\n".join([f"`{path}`" for path in assisted_remediation])
                else:
                    remediation_str = "N/A"

                table_data.append([severity, control_name, docs_url, remediation_str])

    output_string += tabulate(table_data, headers=headers, tablefmt="grid")
    return output_string

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)