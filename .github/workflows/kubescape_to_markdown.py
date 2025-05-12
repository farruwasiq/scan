import json
import sys
from tabulate import tabulate

def convert_kubescape_json_to_markdown(json_file_path):
    """
    Converts Kubescape JSON output to Markdown tables, including fix paths and exceptions.

    Args:
        json_file_path (str): Path to the Kubescape JSON output file.

    Returns:
        str:  Markdown tables representing the Kubescape data,
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

        # 3. Fix Paths Table (within Summary Details)
        fix_paths = []
        for control_id, control_data in controls.items():
            if 'results' in control_data:
                for result in control_data['results']:
                    if 'fixPath' in result:
                        resource_id = result.get('resourceID', 'N/A')  # Get resource ID
                        fix_path_data = result['fixPath']
                        path = fix_path_data.get('path', 'N/A')
                        value = fix_path_data.get('value', 'N/A')
                        fix_paths.append([control_id, resource_id, path, value])  # Include Control ID

        if fix_paths:
            fix_path_headers = ["Control ID", "Resource ID", "Fix Path", "Value"]
            markdown_output += "## Suggested Fix Paths\n"
            markdown_output += tabulate(fix_paths, headers=fix_path_headers, tablefmt="github") + "\n\n"

        # 4. Exceptions Table (within Summary Details)
        exceptions = []
        for control_id, control_data in controls.items():
             if 'exception' in control_data:
                for exception_data in control_data['exception']:
                    exception_name = exception_data.get('name', 'N/A')
                    exception_guid = exception_data.get('guid', 'N/A')
                    attributes = exception_data.get('attributes', {})
                    system_exception = attributes.get('systemException', 'N/A')
                    policy_type = exception_data.get('policyType', 'N/A')
                    exceptions.append([control_id, exception_guid, exception_name, system_exception, policy_type])

        if exceptions:
            exception_headers = ["Control ID","GUID", "Exception Name", "System Exception", "Policy Type"]
            markdown_output += "## Exceptions\n"
            markdown_output += tabulate(exceptions, headers=exception_headers, tablefmt="github") + "\n\n"
    
    # 5. Cluster Metadata Table
    if 'metadata' in data and 'clusterMetadata' in data['metadata']:
        cluster_metadata = data['metadata']['clusterMetadata']
        cluster_metadata_headers = ["Attribute", "Value"]
        cluster_metadata_table_data = []
        for key, value in cluster_metadata.items():
            cluster_metadata_table_data.append([key, value])
        markdown_output += "## Cluster Metadata\n"
        markdown_output += tabulate(cluster_metadata_table_data, headers=cluster_metadata_headers, tablefmt="github") + "\n\n"

    # 6. Scan Metadata Table
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
