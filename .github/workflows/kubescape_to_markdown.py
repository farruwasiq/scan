import json
import subprocess
from tabulate import tabulate
import sys

def convert_kubescape_json_to_markdown_with_jq(json_file):
    """
    Reads a Kubescape JSON output file, uses jq to transform it,
    and converts it into a Markdown table.

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

    # jq script to extract and transform the data
    jq_script = """
    {
      apiVersion: .apiVersion,
      kind: .kind,
      name: .name,
      namespace: .namespace,
      controlsSummary: {
        total: .summaryDetails.controls | length,
        failed: (.summaryDetails.controls | map(select(.statusInfo.status == "failed")) | length),
        actionRequired: (.summaryDetails.controls | map(select(.statusInfo.status == "actionRequired")) | length)
      },
      controls: [.summaryDetails.controls[] | {
        controlName: .name,
        controlId: .controlID
      }],
      resourceControls: (.resourceResults // [] | .[] | .controls // [] | .[] | {  # Handle null resourceResults and controls
          controlId: .controlID,
          severity: (.rules[0].severity // "N/A"),
          docs: (.rules[0].remediation // "N/A"),
          assistedRemediation: (.rules[0].fixPaths | join("\\n") // "N/A")
        })
    }
    """

    try:
        process = subprocess.Popen(
            ['jq', '-r', jq_script, json_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Important for Python 3.7+ to get string output
        )
        jq_output, jq_error = process.communicate()
        if jq_error:
            return f"Error running jq: {jq_error}"
        transformed_data = json.loads(jq_output)
    except FileNotFoundError:
        return "Error: jq command not found. Please ensure jq is installed."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

    output_string = ""
    # Extract summary information
    if 'apiVersion' in transformed_data:
        output_string += f"**ApiVersion:** {transformed_data['apiVersion']}\n"
    if 'kind' in transformed_data:
        output_string += f"**Kind:** {transformed_data['kind']}\n"
    if 'name' in transformed_data:
        output_string += f"**Name:** {transformed_data['name']}\n"
    if 'namespace' in transformed_data:
        output_string += f"**Namespace:** {transformed_data['namespace']}\n"


    # Extract control summary
    if 'controlsSummary' in transformed_data:
        output_string += f"**Controls:** {transformed_data['controlsSummary']['total']} (Failed: {transformed_data['controlsSummary']['failed']}, Action Required: {transformed_data['controlsSummary']['actionRequired']})\n\n"

    output_string += "**Resources**\n\n"

    table_data = []
    headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]

    # Create a dictionary to map controlId to controlName
    control_names = {control['controlId']: control['controlName'] for control in transformed_data.controls}

    # Populate table data from the transformed data
    for rc in transformed_data['resourceControls']:
        table_data.append([
            rc['severity'],
            control_names.get(rc['controlId'], "N/A"),  # Use get() to handle missing controlId
            rc['docs'],
            rc['assistedRemediation']
        ])

    output_string += tabulate(table_data, headers=headers, tablefmt="grid")
    return output_string

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown_with_jq(json_file_path)
    print(markdown_output)