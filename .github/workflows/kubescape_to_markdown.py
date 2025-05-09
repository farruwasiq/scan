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

# Extract resource summaries
resources = data.get('resources', [])

resource_rows = []
for resource in resources:
    resource_id = resource.get('resourceID', 'N/A')
    kind = resource.get('object', {}).get('kind', 'N/A')
    name = resource.get('object', {}).get('name', 'N/A')
    namespace = resource.get('object', {}).get('namespace', 'N/A')
    resource_rows.append([resource_id, kind, name, namespace])

# Generate the resources table
resources_table = tabulate(
    resource_rows,
    headers=["Resource ID", "Kind", "Name", "Namespace"],
    tablefmt="github"
)

# Print the tables
print("### Controls Summary")
print(controls_table)
print()
print("### Resources Summary")
print(resources_table)
