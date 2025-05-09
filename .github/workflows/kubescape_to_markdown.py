import json
import sys

def json_to_markdown_table(json_file):
    """
    Converts Kubescape JSON output to a Markdown table.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        str: A Markdown table representation of the JSON data.
             Returns an empty string if there's an error or no relevant data.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        return ""

    # Kubescape JSON structure can vary.  We need to find the relevant results.
    results = None
    if isinstance(data, dict):
        if "results" in data:
            results = data["results"]  #  Handle top-level "results"
        elif "controls" in data:
             results = data["controls"] # Handle  "controls"
        elif "frameworkReport" in data and "results" in data["frameworkReport"]:
            results = data["frameworkReport"]["results"]
        elif "frameworkReport" in data and "controlReports" in data["frameworkReport"]:
            results = data["frameworkReport"]["controlReports"]
        elif "controlReports" in data:
            results = data["controlReports"]
    elif isinstance(data, list):
        results = data # hope its a list of results

    if not results:
        print("Error: No results found in JSON data.")
        return ""

    if not isinstance(results, list):
        print("Error: Results is not a list.")
        return ""
        

    # Extract relevant fields and construct the table.
    headers = ["Control Name", "Status", "Severity", "Message"]  # Consistent headers
    rows = []

    for result in results:
        # Handle different possible structures of the result object
        control_name = result.get("name") or result.get("controlName") or "N/A"
        status = result.get("status", "N/A")
        severity = result.get("severity", "N/A")
        message = result.get("message", "N/A")

        if isinstance(message, list):
            message = ", ".join(message)

        rows.append([control_name, status, severity, message])

    if not rows:
        return "No relevant data found to create table."

    # Format the Markdown table
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows:
        table += "| " + " | ".join(row) + " |\n"
    return table
    

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    markdown_table = json_to_markdown_table(json_file)
    print(markdown_table)
