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
    api_version = obj.get('apiVersion', 'N/A')

    # Try to extract metadata from common locations
    metadata = obj.get('metadata', {}) or obj.get('spec', {}).get('template', {}).get('metadata', {})
    name = metadata.get('name', 'N/A')
    namespace = metadata.get('namespace', 'N/A')

    # Extracting the controls linked to this resource
    related_controls = resource.get('controls', [])
    failed_controls = sum(1 for ctrl in related_controls if ctrl.get('status', '') == 'failed')
    action_required = sum(1 for ctrl in related_controls if ctrl.get('status', '') == 'action_required')

    # Resource header
    resource_section = [
        f"###############################################",
        f"**ApiVersion:** {api_version}",
        f"**Kind:** {kind}",
        f"**Name:** {name}",
        f"**Namespace:** {namespace}",
        f"**Controls:** {len(related_controls)} (Failed: {failed_controls}, action required: {action_required})",
        ""
    ]

    # Add control details
    if related_controls:
        resource_section.append("### Resources")
        for ctrl in related_controls:
            control_name = ctrl.get('name', 'N/A')
            severity = ctrl.get('severity', 'N/A')
            docs = ctrl.get('documentation', 'N/A')
            remediation = '\n'.join(ctrl.get('remediation', []))
            fix_paths = ctrl.get('fixPath', [])

            # Format the severity for better visibility
            severity_display = f"**{severity}**"

            resource_section.append(f"- **Severity:** {severity_display}")
            resource_section.append(f"- **Control Name:** {control_name}")
            resource_section.append(f"- **Docs:** {docs}")
            resource_section.append("- **Assisted Remediation:**")
            resource_section.append(f"```\n{remediation if remediation else 'N/A'}\n```")

            # Add fix path table if available
            if fix_paths:
                fix_table = tabulate([[path] for path in fix_paths], headers=["Fix Path"], tablefmt="github")
                resource_section.append("- **Fix Path:**")
                resource_section.append(fix_table)

            # Also include detailed file paths if present
            if 'files' in ctrl:
                file_paths = [f.get('filePath', 'N/A') for f in ctrl['files']]
                file_table = tabulate([[f] for f in file_paths], headers=["File Path"], tablefmt="github")
                resource_section.append("- **Vulnerable Files:**")
                resource_section.append(file_table)

        resource_section.append("")

    resource_blocks.append('\n'.join(resource_section))

# Combine all sections
print("### Controls Summary")
print(controls_table)
print()
print("### Detailed Resources Summary")
print('\n\n'.join(resource_blocks))
