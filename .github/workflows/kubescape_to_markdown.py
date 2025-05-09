import json
import sys

def json_to_markdown_table(json_file):
    """
    Converts Kubescape JSON output to a user-friendly Markdown format,
    grouping information by resource and control.

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
    resource_data = {}

    # 1. Process the results to group by resource
    if "results" in data and isinstance(data["results"], list):
        for result in data["results"]:
            if isinstance(result, dict):
                resource_id = result.get("resourceID", "N/A")
                namespace, name = extract_namespace_name(resource_id)  # Extract namespace and name
                apiVersion, kind = extract_version_kind(resource_id)
                controls_data = result.get("controls", [])
                if isinstance(controls_data, list):
                    resource_data[resource_id] = {
                        "apiVersion": apiVersion,
                        "kind": kind,
                        "name": name,
                        "namespace": namespace,
                        "controls": []
                    }
                    for control in controls_data:
                        control_id = control.get("controlID", "N/A")
                        control_name = control.get("name") or control.get("controlName") or "N/A"
                        status_info = control.get("status", {})
                        status = status_info.get("status", "N/A")
                        message = status_info.get("info", "N/A")
                        severity = result.get("severity", "N/A")
                        docs_link = get_docs_link(control_id)
                        remediation = control.get("remediation", "N/A") # change from result.get to control.get
                        if status == "failed":  # Only process failed controls
                            resource_data[resource_id]["controls"].append({
                                "control_id": control_id,
                                "control_name": control_name,
                                "status": status,
                                "message": message,
                                "severity": severity,
                                "docs_link": docs_link,
                                "remediation": remediation
                            })

    # 2. Generate Markdown output
    for resource_id, resource_info in resource_data.items():
        if resource_info["controls"]:  # Only generate output if there are failed controls
            markdown_output += "################################################################################\n"
            markdown_output += f"ApiVersion: {resource_info['apiVersion']}\n"
            markdown_output += f"Kind: {resource_info['kind']}\n"
            markdown_output += f"Name: {resource_info['name']}\n"
            markdown_output += f"Namespace: {resource_info['namespace']}\n\n"
            markdown_output += f"Controls: {len(resource_info['controls'])} (Failed: {len(resource_info['controls'])}, action required: 0)\n\n"  # Added "action required"

            markdown_output += "┌" + "─" * 105 + "┐\n"
            markdown_output += "│" + " " * 52 + "Resources" + " " * 53 + "│\n"
            markdown_output += "├" + "─" * 105 + "┤\n"

            for control in resource_info["controls"]:
                markdown_output += "│" + " " * 21 + f"Severity : {control['severity']}" + " " * (84 - len(f"Severity : {control['severity']}")) + "│\n"
                markdown_output += "│" + " " * 21 + f"Control Name : {control['control_name']}" + " " * (84 - len(f"Control Name : {control['control_name']}")) + "│\n"
                markdown_output += "│" + " " * 21 + f"Docs : {control['docs_link']}" + " " * (84 - len(f"Docs : {control['docs_link']}")) + "│\n"
                markdown_output += "│" + " " * 21 + "Assisted Remediation : " + (84 - len("Assisted Remediation : ")) + "│\n"
                remediation_lines = control['remediation'].splitlines()
                for line in remediation_lines:
                    markdown_output += "│" + " " * 23 + f"{line}" + " " * (82 - len(f"{line}")) + "│\n"
                markdown_output += "└" + "─" * 105 + "┘\n"
    if not markdown_output.strip():
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
        elif part in ["ConfigMap", "ServiceAccount", "Role", "RoleBinding", "Pod","Namespace","Deployment"]:
            kind = part
    return apiVersion, kind



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python kubescape_to_markdown.py <path_to_results.json>")
        sys.exit(1)

    json_file = sys.argv[1]
    markdown_output = json_to_markdown_table(json_file)
    if markdown_output:
        print(markdown_output)
    else:
        print("No tables generated.")

