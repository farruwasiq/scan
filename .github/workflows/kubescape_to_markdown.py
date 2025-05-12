import json
import subprocess
from tabulate import tabulate
import sys

def convert_kubescape_json_to_markdown(json_file):
    """
    Reads a Kubescape JSON output file, uses jq to transform it,
    and converts it into a Markdown table. Handles variations in JSON structure.

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

    output_string = ""

    # Extract basic metadata (always try to get this)
    if 'apiVersion' in data:
        output_string += f"**ApiVersion:** {data['apiVersion']}\n"
    if 'kind' in data:
        output_string += f"**Kind:** {data['kind']}\n"
    if 'name' in data:
        output_string += f"**Name:** {data['name']}\n"
    if 'namespace' in data:
        output_string += f"**Namespace:** {data['namespace']}\n"

    # Handle resourceResults (if present)
    if 'resourceResults' in data and data['resourceResults'] is not None:
        jq_script_resource_centric = """
        {
          resources: (.resourceResults[] | {
            resourceID: .resourceID,
            controls: (.controls[] | {
              controlName: .name,
              controlId: .controlID,
              severity: (.rules[0].severity // "N/A"),
              docs: (.rules[0].remediation // "N/A"),
              assistedRemediation: (.rules[0].fixPaths | join("\\n") // "N/A")
            })
          })
        }
        """
        try:
            process = subprocess.Popen(
                ['jq', '-r', jq_script_resource_centric, json_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            jq_output, jq_error = process.communicate()
            if jq_error:
                return f"Error running jq (resource-centric): {jq_error}"
            if not jq_output.strip():
                return "Error: jq produced no output (resource-centric). Check the input JSON."
            transformed_data = json.loads(jq_output)

            output_string += "**Resource Scan Results**\n\n"
            for resource in transformed_data['resources']:
                output_string += f"**Resource ID:** {resource['resourceID']}\n\n"
                table_data = []
                headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]
                for control in resource['controls']:
                    table_data.append([
                        control['severity'],
                        control['controlName'],
                        control['docs'],
                        control['assistedRemediation']
                    ])
                output_string += tabulate(table_data, headers=headers, tablefmt="grid") + "\n\n"

        except Exception as e:
            return f"An unexpected error occurred during resource-centric processing: {e}"

    else:  # Handle cases where resourceResults is missing
        jq_script_summary_only = """
        {
          controlsSummary: {
            total: .summaryDetails.controls | length,
            failed: (.summaryDetails.controls | map(select(.statusInfo.status == "failed")) | length),
            actionRequired: (.summaryDetails.controls | map(select(.statusInfo.status == "actionRequired")) | length)
          },
          controls: [.summaryDetails.controls[] | {
            controlName: .name,
            controlId: .controlID
          }]
        }
        """
        try:
            process = subprocess.Popen(
                ['jq', '-r', jq_script_summary_only, json_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            jq_output, jq_error = process.communicate()
            if jq_error:
                return f"Error running jq (summary-only): {jq_error}"
            if not jq_output.strip():
                return "Error: jq produced no output (summary-only). Check the input JSON."
            transformed_data = json.loads(jq_output)

            if 'controlsSummary' in transformed_data:
                output_string += f"**Controls Summary:** {transformed_data['controlsSummary']['total']} (Failed: {transformed_data['controlsSummary']['failed']}, Action Required: {transformed_data['controlsSummary']['actionRequired']})\n\n"

            output_string += "**Controls**\n\n"
            table_data = []
            headers = ["Control Name"]
            for control in transformed_data['controls']:
                table_data.append([control['controlName']])
            output_string += tabulate(table_data, headers=headers, tablefmt="grid")

        except Exception as e:
            return f"An unexpected error occurred during summary-only processing: {e}"

    return output_string

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)