import json
import sys
from tabulate import tabulate

def convert_kubescape_json_to_markdown(json_file_path):
    """
    Converts Kubescape JSON output to multiple Markdown tables.

    Args:
        json_file_path (str): Path to the Kubescape JSON output file.

    Returns:
        str:  Multiple Markdown tables representing the Kubescape data,
              or an error message.
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

    if not data:
        return "Error: Empty JSON file."

    markdown_output = ""

    # 1. Cluster API Server Information Table
    if 'clusterAPIServerInfo' in data:
        api_info = data['clusterAPIServerInfo']
        api_table_headers = ["Attribute", "Value"]
        api_table_data = [
            ["Major Version", api_info.get('major', 'N/A')],
            ["Minor Version", api_info.get('minor', 'N/A')],
            ["Git Version", api_info.get('gitVersion', 'N/A')],
            ["Git Commit", api_info.get('gitCommit', 'N/A')],
            ["Git Tree State", api_info.get('gitTreeState', 'N/A')],
            ["Build Date", api_info.get('buildDate', 'N/A')],
            ["Go Version", api_info.get('goVersion', 'N/A')],
            ["Compiler", api_info.get('compiler', 'N/A')],
            ["Platform", api_info.get('platform', 'N/A')],
        ]
        markdown_output += "## Cluster API Server Information\n"
        markdown_output += tabulate(api_table_data, headers=api_table_headers, tablefmt="github") + "\n\n"

    # 2. Summary Details - Controls Table
    if 'summaryDetails' in data and 'controls' in data['summaryDetails']:
        controls = data['summaryDetails']['controls']
        controls_table_headers = ["Control ID", "Name", "Status", "Compliance Score", "Category"]
        controls_table_data = []
        for control_id, control_data in controls.items():
            status = control_data['statusInfo']['status']
            compliance_score = control_data.get('complianceScore', 'N/A')
            category_name = control_data['category']['name']
            control_name = control_data['name']  # Get the control name.
            controls_table_data.append([control_id, control_name, status, compliance_score, category_name])
        markdown_output += "## Summary Details - Controls\n"
        markdown_output += tabulate(controls_table_data, headers=controls_table_headers, tablefmt="github") + "\n\n"
    
    # 3. Cluster Metadata
    if 'metadata' in data and 'clusterMetadata' in data['metadata']:
        cluster_metadata = data['metadata']['clusterMetadata']
        cluster_metadata_headers = ["Attribute", "Value"]
        cluster_metadata_table_data = []
        for key, value in cluster_metadata.items():
            cluster_metadata_table_data.append([key, value])
        markdown_output += "## Cluster Metadata\n"
        markdown_output += tabulate(cluster_metadata_table_data, headers=cluster_metadata_headers, tablefmt="github") + "\n\n"

    # 4. Scan Metadata
    if 'metadata' in data and 'scanMetadata' in data['metadata']:
        scan_metadata = data['metadata']['scanMetadata']
        scan_metadata_headers = ["Attribute", "Value"]
        scan_metadata_table_data = [
            ["Target Type", scan_metadata.get('targetType', 'N/A')],
            ["Kubescape Version", scan_metadata.get('kubescapeVersion', 'N/A')],
            ["Format Version", scan_metadata.get('formatVersion', 'N/A')],
            ["Formats", ', '.join(scan_metadata.get('formats', ['N/A']))],  # Join list as string
            ["Target Names", ', '.join(scan_metadata.get('targetNames', ['N/A']))],
            ["Fail Threshold", scan_metadata.get('failThreshold', 'N/A')],
        ]
        markdown_output += "## Scan Metadata\n"
        markdown_output += tabulate(scan_metadata_table_data, headers=scan_metadata_headers, tablefmt="github") + "\n\n"
    
    if not markdown_output:
        return "No suitable data found for table conversion."

    return markdown_output



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    markdown_output = convert_kubescape_json_to_markdown(json_file_path)
    print(markdown_output)
