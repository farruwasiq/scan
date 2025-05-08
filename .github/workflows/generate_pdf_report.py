import json
from fpdf import FPDF
import sys

def generate_pdf(json_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        pdf.cell(200, 10, txt="Kubescape Scan Report", ln=1, align="C")
        pdf.ln(5)

        if 'results' in data:
            for result in data['results']:
                resource_info = f"Resource: {result.get('kind', 'N/A')} - {result.get('name', 'N/A')} (Namespace: {result.get('namespace', 'N/A')})"
                pdf.cell(200, 10, txt=resource_info, ln=1)

                if 'failedControlsDetails' in result and result['failedControlsDetails']:
                    pdf.cell(200, 10, txt="  Failed Controls:", ln=1)
                    for control in result['failedControlsDetails']:
                        pdf.cell(200, 8, txt=f"    - Severity: {control.get('severity', 'N/A')}", ln=1)
                        pdf.cell(200, 8, txt=f"      Control Name: {control.get('controlName', 'N/A')}", ln=1)
                        pdf.cell(200, 8, txt=f"      Docs: {control.get('docsUrl', 'N/A')}", ln=1)
                        pdf.cell(200, 8, txt=f"      Remediation: {control.get('remediation', 'N/A')}", ln=1)
                        pdf.ln(2)
                else:
                    pdf.cell(200, 8, txt="  No failed controls for this resource.", ln=1)
                pdf.ln(5)
        else:
            pdf.cell(200, 10, txt="No scan results found in JSON.", ln=1)

        pdf.output(pdf_file, "F")

    except FileNotFoundError:
        pdf.cell(200, 10, txt=f"Error: JSON file '{json_file}' not found.", ln=1)
        pdf.output(pdf_file, "F")
    except json.JSONDecodeError:
        pdf.cell(200, 10, txt=f"Error: Could not decode JSON from '{json_file}'.", ln=1)
        pdf.output(pdf_file, "F")
    except Exception as e:
        pdf.cell(200, 10, txt=f"An error occurred: {e}", ln=1)
        pdf.output(pdf_file, "F")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        json_input_file = sys.argv[1]
        pdf_output_file = sys.argv[2]
        generate_pdf(json_input_file, pdf_output_file)
    else:
        print("Usage: python generate_pdf_report.py <input_json_file> <output_pdf_file>")