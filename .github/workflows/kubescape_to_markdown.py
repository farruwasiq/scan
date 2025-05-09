import json
import sys
import traceback

def get_kubescape_tables(json_file):
    """
    Extracts data from a Kubescape JSON output file, maintaining the
    original table structure as much as possible.

    Args:
        json_file (str): Path to the Kubescape JSON output file.

    Returns:
        dict: A dictionary containing the extracted data, organized
              by table name.  Returns an empty dictionary on error.
    """
    tables = {}
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        print(traceback.format_exc())
        return {}

    # 1. Summary Details Table
    try:
        if "summaryDetails" in data and "controls" in data["summaryDetails"]:
            tables["SUMMARY_DETAILS"] = []
            controls = data["summaryDetails"]["controls"]
            for control_id, control_data in controls.items():
                tables["SUMMARY_DETAILS"].append({
                    "Control ID": control_id,
                    "Name": control_data.get("name") or control_data.get("controlName") or "N/A",
                    "Status": control_data.get("statusInfo", {}).get("status", "N/A"),
                    "Compliance Score": control_data.get("complianceScore", "N/A"),
                })
    except Exception as e:
        print(f"Error processing Summary Details: {e}")
        print(traceback.format_exc())

    # 2. Resources Table
    try:
        if "resources" in data and isinstance(data["resources"], list):
            tables["RESOURCES"] = []
            for resource in data["resources"]:
                if isinstance(resource, dict) and "object" in resource and isinstance(resource["object"], dict):
                    tables["RESOURCES"].append({
                        "Resource ID": resource.get("resourceID", "N/A"),
                        "Kind": resource["object"].get("kind", "N/A"),
                        "Namespace": resource["object"].get("namespace", "N/A"),
                        "Name": resource["object"].get("name", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Resources: {e}")
        print(traceback.format_exc())

    # 3. Frameworks Table
    try:
        if "frameworks" in data and isinstance(data["frameworks"], list):
            tables["FRAMEWORKS"] = []
            for framework in data["frameworks"]:
                if isinstance(framework, dict):
                    tables["FRAMEWORKS"].append({
                        "Name": framework.get("name", "N/A"),
                        "Status": framework.get("status", "N/A"),
                        "Compliance Score": framework.get("complianceScore", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Frameworks: {e}")
        print(traceback.format_exc())

    # 4. Results Table
    try:
        if "results" in data:
            tables["RESULTS"] = []
            results = data["results"]
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict):
                        resource_id = result.get("resourceID", "N/A")
                        controls_data = result.get("controls", [])
                        if isinstance(controls_data, list):
                            for control_data in controls_data:
                                tables["RESULTS"].append({
                                    "Resource ID": resource_id,
                                    "Control ID": control_data.get("controlID", "N/A"),
                                    "Control Name": control_data.get("name") or control_data.get("controlName") or "N/A",
                                    "Status": control_data.get("status", {}).get("status", "N/A"),
                                    "Message": control_data.get("status", {}).get("info", "N/A"),
                                    "Severity": result.get("severity", "N/A"),
                                    "Category": result.get("category", "N/A"),
                                    "Remediation": result.get("remediation", "N/A"),
                                    "Namespace": result.get("namespace", "N/A"),
                                    "Name": result.get("name", "N/A")
                                })
                        else:
                            print(f"Warning: 'controls' is not a list for resourceID: {resource_id}, skipping")
                    else:
                        print(f"Unexpected result item type: {type(result)}, skipping")
            else:
                print(f"Unexpected results type: {type(results)}, skipping")
    except Exception as e:
        print(f"Error processing Results: {e}")
        print(traceback.format_exc())

    # 5. Control Reports Table
    try:
        if "controlReports" in data:
            tables["CONTROLREPORTS"] = []
            control_reports = data["controlReports"]
            if isinstance(control_reports, list):
                for report in control_reports:
                    tables["CONTROLREPORTS"].append({
                        "Control ID": report.get("controlID", "N/A"),
                        "Control Name": report.get("name", "N/A"),
                        "Failed Resources": report.get("failedResources", "N/A"),
                        "Total Resources": report.get("totalResources", "N/A"),
                    })
            elif isinstance(control_reports, dict):
                for control_id, report_data in control_reports.items():
                    tables["CONTROLREPORTS"].append({
                        "Control ID": control_id,
                        "Control Name": report_data.get("name", "N/A"),
                        "Failed Resources": report_data.get("failedResources", "N/A"),
                        "Total Resources": report_data.get("totalResources", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Control Reports: {e}")
        print(traceback.format_exc())

    return tables

def print_tables(tables):
    """
    Prints the extracted tables in a user-friendly format.

    Args:
        tables (dict): A dictionary containing the extracted data.
    """
    if not tables:
        print("No data to display.")
        return

    for table_name, table_data in tables.items():
        print(f"\n--- {table_name} ---")  # Print table name

        if not table_data:
            print("  No data available.")
            continue

        # Determine maximum column widths
        headers = list(table_data[0].keys())
        max_widths = {header: len(header) for header in headers}
        for row in table_data:
            for header, value in row.items():
                max_widths[header] = max(max_widths[header], len(str(value)))

        # Print table header
        header_format = " | ".join(f"{{:<{max_widths[header]}}}" for header in headers)
        print(header_format.format(*headers))
        print("-" * (sum(max_widths.values()) + len(headers) * 3 - 1))  # Separator line

        # Print table rows
        row_format = " | ".join(f"{{:<{max_widths[header]}}}" for header in headers)
        for row in table_data:
            values = [str(row[header]) for header in headers]
            print(row_format.format(*values))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_tables.py <path_to_results.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    tables = get_kubescape_tables(json_file)
    print_tables(tables)
