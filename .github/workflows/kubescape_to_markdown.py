import json
import sys

def json_to_markdown_table(json_file):
    """
    Converts Kubescape JSON output to multiple Markdown tables.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        dict: A dictionary of Markdown tables, where keys are table names
              and values are the Markdown table strings.
              Returns an empty dictionary if there's an error.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        return {}

    # Save the raw JSON data to a file for inspection
    try:
        with open("kubescape_output.json", "w") as outfile:
            json.dump(data, outfile, indent=4)  # Pretty print for readability
        print("Raw JSON output saved to kubescape_output.json")
    except Exception as e:
        print(f"Error saving raw JSON: {e}")

    tables = {}

    # 1. Summary Details Table
    if "summaryDetails" in data and "controls" in data["summaryDetails"]:
        controls = data["summaryDetails"]["controls"]
        headers = ["Control ID", "Control Name", "Status", "Compliance Score"]
        rows = []
        for control_id, control_data in controls.items():
            control_name = control_data.get("name") or control_data.get("controlName") or control_id or "N/A"
            status = control_data.get("statusInfo", {}).get("status", "N/A")
            compliance_score = control_data.get("complianceScore", "N/A")
            rows.append([control_id, control_name, status, str(compliance_score)])
        tables["Summary Details"] = format_markdown_table(headers, rows)

    # 2. Resources Table
    if "resources" in data and isinstance(data["resources"], list):
        headers = ["Resource ID", "Kind", "Namespace", "Name"]
        rows = []
        for resource in data["resources"]:
            if isinstance(resource, dict) and "object" in resource and isinstance(resource["object"], dict):
                resource_id = resource.get("resourceID", "N/A")
                kind = resource["object"].get("kind", "N/A")
                namespace = resource["object"].get("namespace", "N/A")
                name = resource["object"].get("name", "N/A")
                rows.append([resource_id, kind, namespace, name])
        tables["Resources"] = format_markdown_table(headers, rows)

    # 3.  Frameworks Table
    if "frameworks" in data and isinstance(data["frameworks"], list):
        headers = ["Framework Name", "Status", "Compliance Score"]
        rows = []
        for framework in data["frameworks"]:
            if isinstance(framework, dict):
                name = framework.get("name", "N/A")
                status = framework.get("status", "N/A")
                compliance_score = framework.get("complianceScore", "N/A")
                rows.append([name, status, str(compliance_score)])
        tables["Frameworks"] = format_markdown_table(headers, rows)

    # 4. Results Table
    if "results" in data:
        results = data["results"]
        headers = ["Resource ID", "Control ID", "Control Name", "Status", "Message", "Severity", "Category", "Remediation", "Namespace", "Name"]
        rows = []
        if isinstance(results, list):
            for result in results:
                # print(f"Debugging result: {result}") #remove
                if isinstance(result, dict):
                    resource_id = result.get("resourceID", "N/A")
                    controls_data = result.get("controls", [])

                    # Ensure controls_data is a list before iterating
                    if isinstance(controls_data, list):
                        for control_data in controls_data:
                            control_id = control_data.get("controlID", "N/A")
                            control_name = control_data.get("name") or control_data.get("controlName") or "N/A"
                            status_info = control_data.get("status", {})
                            status = status_info.get("status", "N/A")
                            message = status_info.get("info", "N/A")
                            severity = result.get("severity", "N/A")
                            category = result.get("category", "N/A")
                            remediation = result.get("remediation", "N/A")
                            # Extract namespace and name from the resourceID
                            namespace, name = extract_namespace_name(resource_id)
                            rows.append([resource_id, control_id, control_name, status, message, severity, category, remediation, namespace, name])
                    else:
                        print(f"Warning: 'controls' is not a list for resourceID: {resource_id}, skipping")
                else:
                    print(f"Unexpected result item type: {type(result)}, skipping")
        else:
            print(f"Unexpected results type: {type(results)}, skipping")
        tables["Results"] = format_markdown_table(headers, rows)

    # 5. Control Reports Table (if available)
    if "controlReports" in data:
        control_reports = data["controlReports"]
        headers = ["Control ID", "Control Name", "Failed Resources", "Total Resources"]
        rows = []
        if isinstance(control_reports, list):
            for report in control_reports:
                control_id = report.get("controlID", "N/A")
                control_name = report.get("name", "N/A")
                failed_resources = report.get("failedResources", "N/A")
                total_resources = report.get("totalResources", "N/A")
                rows.append([control_id, control_name, str(failed_resources), str(total_resources)])
            tables["Control Reports"] = format_markdown_table(headers, rows)
        elif isinstance(control_reports, dict):
            for control_id, report_data in control_reports.items():
                control_name = report_data.get("name", "N/A")
                failed_resources = report_data.get("failedResources", "N/A")
                total_resources = report_data.get("totalResources", "N/A")
                rows.append([control_id, control_name, str(failed_resources), str(total_resources)])
            tables["Control Reports"] = format_markdown_table(headers, rows)

    return tables

def format_markdown_table(headers, rows):
    """Formats a list of headers and rows into a Markdown table."""
    if not rows:
        return "No data found for this table."
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        table += "| " + " | ".join(row) + " |\n"
    return table

def extract_namespace_name(resource_id):
    """
    Extracts namespace and name from the resource ID.

    Args:
        resource_id (str): The resource ID string.

    Returns:
        tuple: (namespace, name).  If extraction fails, returns ("N/A", "N/A").
    """
    parts = resource_id.split('/')
    namespace = "N/A"
    name = "N/A"
    if len(parts) > 1:
        # Heuristically find a part that might contain namespace/name
        for i in range(len(parts) - 1):
            if parts[i] and parts[i+1]:
                if parts[i] != "v1": # added this line
                    namespace = parts[i]
                    name = parts[i+1]
                    break
    elif len(parts) == 1:
        name = parts[0]
    return namespace, name

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    markdown_tables = json_to_markdown_table(json_file)

    if markdown_tables:
        for table_name, table_content in markdown_tables.items():
            print(f"\n## {table_name}\n")
            print(table_content)
    else:
        print("No tables generated.")
