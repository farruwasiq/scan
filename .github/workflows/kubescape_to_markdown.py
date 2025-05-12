import json
import sys
from tabulate import tabulate

def convert_kubescape_json_to_markdown(json_file_path):
    """
    Converts Kubescape JSON output to a Markdown table, focusing on the summary details,
    and includes application name and namespace for failed "Applications credentials in configuration files" controls,
    formatted to resemble the screenshot.

    Args:
        json_file_path (str): Path to the Kubescape JSON output file.

    Returns:
        str: A Markdown representation of the Kubescape summary, or an error message.
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
    output = ""

    for control_id, control_data in controls.items():
        control_name = control_data['name']
        status = control_data['statusInfo']['status']
        compliance_score = control_data.get('complianceScore', 'N/A')
        category = control_data['category']['name']

        if control_name == "Applications credentials in configuration files" and status == "failed":
            output += f"Control Name: {control_name}\n"
            output += f"Status: {status}\n"
            output += f"Compliance Score: {compliance_score}\n"
            output += f"Category: {category}\n\n"
            output += "Failed Resources:\n"

            if 'results' in control_data:
                for result in control_data['results']:
                    if result['status'] == 'failed' and 'resourceInfo' in result:
                        resource_info = result['resourceInfo']
                        namespace = resource_info.get('namespace', 'N/A')
                        name = resource_info.get('name', 'N/A')
                        apiVersion = resource_info.get('apiVersion', 'N/A')
                        kind = resource_info.get('kind', 'N/A')

                        output += f"  API Version: {apiVersion}\n"
                        output += f"  Kind: {kind}\n"
                        output += f"  Name: {name}\n"
                        output += f"  Namespace: {namespace}\n\n"
            else:
                output += "  No failed resources found.\n"
            return output

    output += "No 'Applications credentials in configuration files' failures found."
    return output

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)
