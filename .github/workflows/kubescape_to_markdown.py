import json
import sys
import traceback

def get_kubescape_data(json_file):
    """
    Extracts data from a Kubescape JSON output file, organizing it into a
    more comprehensive structure.

    Args:
        json_file (str): Path to the Kubescape JSON output file.

    Returns:
        dict: A dictionary containing the extracted data, organized
              by top-level categories. Returns an empty dictionary on error.
    """
    data = {}
    try:
        with open(json_file, 'r') as f:
            raw_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        print(traceback.format_exc())
        return {}

    # Top-level data extraction
    data["cluster_api_server_info"] = raw_data.get("clusterAPIServerInfo", {})
    data["cluster_info"] = {
        "cloud_provider": raw_data.get("clusterCloudProvider", ""),
        "name": raw_data.get("clusterName", ""),
    }
    data["report_metadata"] = {
        "customer_guid": raw_data.get("customerGUID", ""),
        "report_guid": raw_data.get("reportGUID", ""),
        "job_id": raw_data.get("jobID", ""),
    }
    data["scan_status"] = raw_data.get("status", "")
    data["frameworks"] = raw_data.get("frameworks", [])
    data["metadata"] = raw_data.get("metadata",{})

    # 1. Summary Details
    data["summary_details"] = {}
    if "summaryDetails" in raw_data and "controls" in raw_data["summaryDetails"]:
        controls = raw_data["summaryDetails"]["controls"]
        for control_id, control_data in controls.items():
            data["summary_details"][control_id] = {
                "name": control_data.get("name") or control_data.get("controlName") or "N/A",
                "status": control_data.get("statusInfo", {}).get("status", "N/A"),
                "sub_status": control_data.get("statusInfo", {}).get("subStatus", "N/A"),
                "compliance_score": control_data.get("complianceScore", "N/A"),
                "score": control_data.get("score", "N/A"),
                "category": control_data.get("category", {}).get("name", "N/A"),
                "category_id": control_data.get("category", {}).get("id", "N/A"),
                "resource_counters": control_data.get("ResourceCounters", {}),
            }

    # 2. Resources
    data["resources"] = []
    if "resources" in raw_data and isinstance(raw_data["resources"], list):
        for resource in raw_data["resources"]:
            if isinstance(resource, dict) and "object" in resource and isinstance(resource["object"], dict):
                data["resources"].append({
                    "resource_id": resource.get("resourceID", "N/A"),
                    "kind": resource["object"].get("kind", "N/A"),
                    "namespace": resource["object"].get("namespace", "N/A"),
                    "name": resource["object"].get("name", "N/A"),
                    "apiVersion": resource["object"].get("apiVersion","N/A")
                })

    # 3. Results
    data["results"] = []
    if "results" in raw_data and isinstance(raw_data["results"], list):
        for result in raw_data["results"]:
            if isinstance(result, dict):
                result_data = {
                    "resource_id": result.get("resourceID", "N/A"),
                    "severity": result.get("severity", "N/A"),
                    "category": result.get("category", "N/A"),
                    "remediation": result.get("remediation", "N/A"),
                    "namespace": result.get("namespace", "N/A"),
                    "name": result.get("name", "N/A"),
                }
                controls_data = result.get("controls", [])
                if isinstance(controls_data, list):
                    result_data["controls"] = []
                    for control in controls_data:
                        result_data["controls"].append({
                            "control_id": control.get("controlID", "N/A"),
                            "name": control.get("name") or control.get("controlName") or "N/A",
                            "status": control.get("status", {}).get("status", "N/A"),
                            "message": control.get("status", {}).get("info", "N/A"),
                        })
                data["results"].append(result_data)

    # 4. Control Reports
    data["control_reports"] = []
    if "controlReports" in raw_data:
        control_reports = raw_data["controlReports"]
        if isinstance(control_reports, list):
            for report in control_reports:
                data["control_reports"].append({
                    "control_id": report.get("controlID", "N/A"),
                    "name": report.get("name", "N/A"),
                    "failed_resources": report.get("failedResources", "N/A"),
                    "total_resources": report.get("totalResources", "N/A"),
                })
        elif isinstance(control_reports, dict):
            for control_id, report_data in control_reports.items():
                data["control_reports"].append({
                    "control_id": control_id,
                    "name": report_data.get("name", "N/A"),
                    "failed_resources": report_data.get("failedResources", "N/A"),
                    "total_resources": report_data.get("totalResources", "N/A"),
                })
    return data


def print_table(title, data, column_order=None, max_width=80):
    """
    Prints a formatted table with a title, handling long values and wrapping.

    Args:
        title (str): The title of the table.
        data (list of dict): The data to print, where each dict represents a row.
        column_order (list, optional): A list of column names in the desired order.
            If None, the columns are ordered as found in the first data item.
        max_width (int, optional): The maximum width of the table.  Longer values
            will be wrapped.
    """
    if not data:
        print(f"\n--- {title} ---")
        print("  No data available.")
        return

    headers = column_order if column_order else list(data[0].keys())
    max_widths = {header: len(header) for header in headers}

    # Calculate maximum column widths
    for row in data:
        for header, value in row.items():
            max_widths[header] = max(max_widths[header], len(str(value)))

    # Adjust column widths for overall table width and wrapping
    available_width = max_width - (len(headers) * 3 + 1)  # Account for padding and separators
    extra_width = sum(max_widths.values()) - available_width
    if extra_width > 0:
        # Prioritize shrinking columns with less important content (e.g., long IDs, messages)
        shrinkable_columns = sorted(headers, key=lambda h: max_widths[h], reverse=True)
        for col in shrinkable_columns:
            if extra_width <= 0:
                break
            shrink_by = min(extra_width // len(shrinkable_columns), max_widths[col] - 10)  # Leave a minimum of 10
            max_widths[col] -= shrink_by
            extra_width -= shrink_by
            if extra_width < 0 :
                break

    # Print table header
    print(f"\n--- {title} ---")
    header_format = " | ".join(f"{{:<{max_widths[header]}}}" for header in headers)
    print(header_format.format(*headers))
    print("-" * (sum(max_widths.values()) + len(headers) * 3 - 1))

    # Print table rows with wrapping
    row_format = " | ".join(f"{{:<{max_widths[header]}}}" for header in headers)
    for row in data:
        values = []
        for header in headers:
            value = str(row[header])
            if len(value) > max_widths[header]:
                # Wrap the value if it exceeds the column width
                wrapped_value = "\n".join(value[i:i + max_widths[header]] for i in range(0, len(value), max_widths[header]))
                values.append(wrapped_value)
            else:
                values.append(value)
        print(row_format.format(*values))

def main(json_file):
    """
    Main function to process the Kubescape JSON file and print tables.

    Args:
        json_file (str): Path to the Kubescape JSON output file.
    """
    data = get_kubescape_data(json_file)
    if not data:
        sys.exit(1)

    # Print tables
    print_table("Cluster API Server Info", [data["cluster_api_server_info"]])
    print_table("Cluster Information", [data["cluster_info"]])
    print_table("Report Metadata", [data["report_metadata"]])
    print(f"\nScan Status: {data['scan_status']}")

    # Print Summary Details
    summary_details_data = list(data["summary_details"].values())
    summary_details_columns = [
        "Control ID", "Name", "Status", "Sub Status", "Compliance Score", "Score",
        "Category", "Category ID", "Resource Counters"
    ]
    print_table("Summary Details", summary_details_data, summary_details_columns)

    # Print Resources
    resources_data = data["resources"]
    resources_columns = ["Resource ID", "Kind", "Namespace", "Name", "apiVersion"]
    print_table("Resources", resources_data, resources_columns)

    # Print Results
    results_data = data["results"]
    results_columns = ["Resource ID", "Severity", "Category", "Remediation", "Namespace", "Name", "Controls"]
    print_table("Results", results_data, results_columns)

    # Print Control Reports
    control_reports_data = data["control_reports"]
    control_reports_columns = ["Control ID", "Control Name", "Failed Resources", "Total Resources"]
    print_table("Control Reports", control_reports_data, control_reports_columns)
    print_table("Frameworks",data["frameworks"])
    print_table("Metadata", [data["metadata"]])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_parser.py <path_to_results.json>")
        sys.exit(1)
    json_file = sys.argv[1]
    main(json_file)

