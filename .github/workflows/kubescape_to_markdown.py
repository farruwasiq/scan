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

    # Extract summary information
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
    action_required_count = 0

    for control_id, control in controls_data.items():
        if control.get('statusInfo', {}).get('status') == 'failed':
            failed_count += 1

    output_string += f"**Controls:** {total_controls} (Failed: {failed_count}, Action Required: N/A)\n\n"

    output_string += "**Resources (Summary with Potential Data Gaps)**\n\n"
    output_string += "  **Note:** Rule-level details (Severity, Docs, Assisted Remediation) may be incomplete or inaccurate in this summary table. For detailed findings, refer to the 'resourceResults' section of the JSON or consider using a resource-centric report.\n\n"


    table_data = []
    headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]

    # Create a dictionary to map control names to details from resourceResults
    control_details_map = {}
    if 'resourceResults' in data and isinstance(data['resourceResults'], list):
        for resource_result in data['resourceResults']:
            if 'controls' in resource_result and isinstance(resource_result['controls'], list):
                for resource_control in resource_result['controls']:
                    control_id = resource_control.get('controlID')
                    if control_id:
                        # Store details, potentially overwriting if the same ID appears multiple times
                        if 'rules' in resource_control and isinstance(resource_control['rules'], list) and resource_control['rules']: #Check if rules exist
                            # Concatenate details from all rules for the same control ID
                            severity_list = []
                            docs_list = []
                            assisted_remediation_list = []
                            for rule in resource_control['rules']:
                                severity_list.append(rule.get('severity', 'N/A'))
                                docs_list.append(rule.get('remediation', 'N/A'))
                                assisted_remediation_list.extend(rule.get('fixPaths', []))

                            # Join the lists with newlines if there are multiple values
                            control_details_map[control_id] = {
                                'severity': "\n".join(severity_list) or 'N/A',
                                'docs': "\n".join(docs_list) or 'N/A',
                                'assisted_remediation': "\n".join([f"`{path}`" for path in assisted_remediation_list]) or 'N/A'
                            }


    for control_id, control in controls_data.items():
        severity = "N/A"
        control_name = control.get('name', 'N/A')
        docs_url = "N/A"
        assisted_remediation = "N/A"

        # Try to get details from the map
        if control_id in control_details_map:
            details = control_details_map[control_id]
            severity = details['severity']
            docs_url = details['docs']
            assisted_remediation = details['assisted_remediation']

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