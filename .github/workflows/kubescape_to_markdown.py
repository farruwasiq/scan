import json
import sys

def json_to_markdown_table(json_file):
    """
    Converts Kubescape JSON output to a more user-friendly Markdown format.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        str: A Markdown string representing the formatted output, or an
             empty string if there's an error.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not read or parse JSON file: {e}")
        return ""

    markdown_output = ""

    # 1. Iterate through 'results' to find failed controls.  This is the core logic
    if "results" in data and isinstance(data["results"], list):
        for result in data["results"]:
            if isinstance(result, dict) and "controls" in result and isinstance(result["controls"], list):
                for control in result["controls"]:
                    if control.get("status", {}).get("status") == "failed":
                        # Extract relevant information
                        resource_id = result.get("resourceID", "N/A")
                        namespace, name = extract_namespace_name(resource_id)
                        control_id = control.get("controlID", "N/A")
                        control_name = control.get("name") or control.get("controlName") or "N/A"
                        message = control.get("status", {}).get("info", "N/A")
                        severity = result.get("severity", "N/A")
                        #docs_link = f"https://hub.armosec.io/docs/{control_id.lower()}" #removed hardcoded link
                        docs_link = get_docs_link(control_id)
                        remediation = result.get("remediation", "N/A")

                        # Add a separator for each failed control.
                        markdown_output += "################################################################################\n"
                        # Resource Information
                        markdown_output += f"**Resource ID**: {resource_id}\n"
                        markdown_output += f"**Name**: {name}\n"
                        markdown_output += f"**Namespace**: {namespace}\n\n"

                        # Control Information
                        markdown_output += f"**Control ID**: {control_id}\n"
                        markdown_output += f"**Control Name**: {control_name}\n"
                        markdown_output += f"**Status**: Failed\n" #added status
                        markdown_output += f"**Message**: {message}\n\n" #added message

                        #Add version and kind.
                        apiVersion, kind = extract_version_kind(resource_id)
                        markdown_output += f"**APIVersion**: {apiVersion}\n"
                        markdown_output += f"**Kind**: {kind}\n\n"

                        #Remediation
                        markdown_output += f"**Severity**: {severity}\n"
                        markdown_output += f"**Docs**: {docs_link}\n"
                        markdown_output += f"**Assisted Remediation**: {remediation}\n\n"
    if not markdown_output:
        markdown_output = "No failed controls found.\n"
    return markdown_output
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

    if "ServiceAccount" in resource_id:
        for i, part in enumerate(parts):
            if part == "ServiceAccount":
                if i + 1 < len(parts):
                    namespace = parts[i - 1]
                    name = parts[i + 1]
                break
    elif "RoleBinding" in resource_id:
        for i, part in enumerate(parts):
            if part == "RoleBinding":
                name = parts[i + 1]
                namespace = parts[i - 1]
                break
    elif "Role" in resource_id:
        for i, part in enumerate(parts):
            if part == "Role":
                name = parts[i + 1]
                namespace = parts[i - 1]
                break
    elif "ConfigMap" in resource_id:
        for i, part in enumerate(parts):
            if part == "ConfigMap":
                name = parts[i + 1]
                namespace = parts[i - 1]
                break
    elif "Namespace" in resource_id:
        for i, part in enumerate(parts):
            if part == "Namespace":
                name = parts[i+1]
                namespace = parts[i-1]
                break
    elif "Pod" in resource_id:
        for i, part in enumerate(parts):
            if part == "Pod":
                name = parts[i+1]
                namespace = parts[i-1]
                break
    else:
        if len(parts) > 1:
            namespace = parts[-2]
            name = parts[-1]
        elif len(parts) == 1:
            name = parts[0]

    return namespace, name

def get_docs_link(control_id):
    """
    Returns the documentation link for a given control ID.

    Args:
        control_id (str): The control ID (e.g., "C-0012").

    Returns:
        str: The documentation link, or "N/A" if not found.
    """
    base_url = "https://hub.armosec.io/docs/"
    if control_id:
        return f"{base_url}{control_id.lower()}"
    return "N/A"

def extract_version_kind(resource_id):
    """
    Extracts apiVersion and kind from the resource ID.

    Args:
        resource_id (str): The resource ID.

    Returns:
        tuple: (apiVersion, kind)
    """
    parts = resource_id.split('/')
    apiVersion = "N/A"
    kind = "N/A"
    for part in parts:
        if part.startswith("v1") or part.startswith("apps/"):
            apiVersion = part
        elif part in ["ConfigMap", "ServiceAccount", "Role", "RoleBinding", "Pod","Namespace"]:
            kind = part
    return apiVersion, kind
def format_markdown_table(headers, rows):
    """Formats a list of headers and rows into a Markdown table."""
    if not rows:
        return "No data found for this table."
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
    markdown_output = json_to_markdown_table(json_file)
    if markdown_output:
        print(markdown_output)
    else:
        print("No output generated.")
