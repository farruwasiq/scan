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
            tables["SUMMARY_DETAILS"] = {  # Changed key name to uppercase
                "controls": {}
            }
            controls = data["summaryDetails"]["controls"]
            for control_id, control_data in controls.items():
                tables["SUMMARY_DETAILS"]["controls"][control_id] = {  # Consistent key name
                    "name": control_data.get("name") or control_data.get("controlName") or "N/A",
                    "status": control_data.get("statusInfo", {}).get("status", "N/A"),
                    "complianceScore": control_data.get("complianceScore", "N/A"),
                }
    except Exception as e:
        print(f"Error processing Summary Details: {e}")
        print(traceback.format_exc())

    # 2. Resources Table
    try:
        if "resources" in data and isinstance(data["resources"], list):
            tables["RESOURCES"] = []  # Changed key name to uppercase
            for resource in data["resources"]:
                if isinstance(resource, dict) and "object" in resource and isinstance(resource["object"], dict):
                    tables["RESOURCES"].append({  # Consistent key name
                        "resourceID": resource.get("resourceID", "N/A"),
                        "kind": resource["object"].get("kind", "N/A"),
                        "namespace": resource["object"].get("namespace", "N/A"),
                        "name": resource["object"].get("name", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Resources: {e}")
        print(traceback.format_exc())

    # 3. Frameworks Table
    try:
        if "frameworks" in data and isinstance(data["frameworks"], list):
            tables["FRAMEWORKS"] = []  # Changed key name to uppercase
            for framework in data["frameworks"]:
                if isinstance(framework, dict):
                    tables["FRAMEWORKS"].append({  # Consistent key name
                        "name": framework.get("name", "N/A"),
                        "status": framework.get("status", "N/A"),
                        "complianceScore": framework.get("complianceScore", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Frameworks: {e}")
        print(traceback.format_exc())

    # 4. Results Table
    try:
        if "results" in data:
            tables["RESULTS"] = []  # Changed key name to uppercase
            results = data["results"]
            if isinstance(results, list):
                for result in results:
                    if isinstance(result, dict):
                        resource_id = result.get("resourceID", "N/A")
                        controls_data = result.get("controls", [])
                        if isinstance(controls_data, list):
                            for control_data in controls_data:
                                tables["RESULTS"].append({  # Consistent key name
                                    "resourceID": resource_id,
                                    "controlID": control_data.get("controlID", "N/A"),
                                    "controlName": control_data.get("name") or control_data.get("controlName") or "N/A",
                                    "status": control_data.get("status", {}).get("status", "N/A"),
                                    "message": control_data.get("status", {}).get("info", "N/A"),
                                    "severity": result.get("severity", "N/A"),
                                    "category": result.get("category", "N/A"),
                                    "remediation": result.get("remediation", "N/A"),
                                    "namespace": result.get("namespace", "N/A"),
                                    "name": result.get("name", "N/A")
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
            tables["CONTROLREPORTS"] = []  # Changed key name to uppercase
            control_reports = data["controlReports"]
            if isinstance(control_reports, list):
                for report in control_reports:
                    tables["CONTROLREPORTS"].append({  # Consistent key name
                        "controlID": report.get("controlID", "N/A"),
                        "controlName": report.get("name", "N/A"),
                        "failedResources": report.get("failedResources", "N/A"),
                        "totalResources": report.get("totalResources", "N/A"),
                    })
            elif isinstance(control_reports, dict):
                for control_id, report_data in control_reports.items():
                    tables["CONTROLREPORTS"].append({  # Consistent key name
                        "controlID": control_id,
                        "controlName": report_data.get("name", "N/A"),
                        "failedResources": report_data.get("failedResources", "N/A"),
                        "totalResources": report_data.get("totalResources", "N/A"),
                    })
    except Exception as e:
        print(f"Error processing Control Reports: {e}")
        print(traceback.format_exc())

    return tables
def print_tables(tables):
    """
    Prints the extracted tables in a format that resembles the original
    JSON structure.

    Args:
        tables (dict): A dictionary containing the extracted data.
    """
    if not tables:
        print("No data to display.")
        return

    # Print each table separately
    for table_name, table_data in tables.items():
        print(f"\n--- {table_name} ---")  # Keep table name as is
        print(json.dumps(table_data, indent=4))  # Use json.dumps for formatted output

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_tables.py <path_to_results.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    tables = get_kubescape_tables(json_file)
    print_tables(tables)
