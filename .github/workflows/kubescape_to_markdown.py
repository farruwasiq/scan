import json
from tabulate import tabulate
import sys

# Load the JSON file passed as an argument
if len(sys.argv) < 2:
    print("Usage: python kubescape_to_markdown.py <results.json>")
    sys.exit(1)

json_file = sys.argv[1]

with open(json_file, 'r') as file:
    data = json.load(file)

# Extract control summaries
controls = data.get('summaryDetails', {}).get('controls', {})

control_rows = []
for control_id, control in controls.items():
    control_rows.append([
        control_id,
        control.get('name', 'N/A'),
        control.get('status', 'N/A'),
        control.get('score', 'N/A'),
        control.get('complianceScore', 'N/A'),
        control.get('ResourceCounters', {}).get('passedResources', 0),
        control.get('ResourceCounters', {}).get('failedResources', 0),
        control.get('ResourceCounters', {}).get('skippedResources', 0),
        control.get('ResourceCounters', {}).get('excludedResources', 0),
    ])

# Generate the controls table
controls_table = tabulate(
    control_rows,
    headers=["Control ID", "Name", "Status", "Score", "Compliance Score", "Passed", "Failed", "Skipped", "Excluded"],
    tablefmt="github"
)

# Extract detailed resource summaries
resources = data.get('resources', [])

resource_blocks = []
for resource in resources:
    obj = resource.get('object', {})
    kind = obj.get('kind', 'N/A')
    name = obj.get('name', 'N/A')
    namespace = obj.get('namespace', 'N/A')
    api_version = obj.get('apiVersion', 'N/A')

    # Extracting the controls linked to this resource
    related_controls = resource.get('controls', [])
    resource_section = [f"### Resource: {kind} - {name} (Namespace: {namespace})"]
    resource_section.append(f"ApiVersion: {api_version}")
    resource_section.append(f"Kind: {kind}")
    resource_section.append(f"Name: {name}")
    resource_section.append(f"Namespace: {namespace}\n")

    # Add control details
    for ctrl in related_controls:
        control_name = ctrl.get('name', 'N/A')
        severity = ctrl.get('severity', 'N/A')
        docs = ctrl.get('documentation', 'N/A')
        remediation = '\n'.join(ctrl.get('remediation', []))

        resource_section.append(f"Severity: **{severity}**")
        resource_section.append(f"Control Name: {control_name}")
        resource_section.append(f"Docs: {docs}")
        resource_section.append(f"Assisted Remediation:\n{remediation if remediation else 'N/A'}\n")

    resource_blocks.append('\n'.join(resource_section))

# Combine all sections
print("### Controls Summary")
print(controls_table)
print()
print("### Detailed Resources Summary")
print('\n\n'.join(resource_blocks))
