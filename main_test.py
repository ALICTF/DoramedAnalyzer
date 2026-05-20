# main_test.py
import os
from pdf_extractor import PDFReportParser
from analyzer import HealthAnalyzer
import json

def run_test():
    files = [
        ("body_report.pdf", "sample_body.pdf"), 
        ("bp_report.pdf", "sample_bp.pdf")
    ]
    
    extractor = PDFReportParser()
    analyzer = HealthAnalyzer()
    
    final_output = []

    print("--- Starting Extraction & Analysis ---")

    for internal_name, file_path in files:
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            continue
            
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
            
        print(f"\nProcessing: {internal_name}")
        extraction_result = extractor.parse_file(pdf_bytes, internal_name)
        
        if "error" in extraction_result:
            print(f"Extraction Error: {extraction_result['error']}")
            continue
            
        print(f"Type Identified: {extraction_result['type']}")
        
        analysis_result = analyzer.analyze(
            extraction_result['type'], 
            extraction_result['data']
        )
        
        output_item = {
            "file": internal_name,
            "raw_data": extraction_result['data'],
            "analysis": analysis_result
        }
        final_output.append(output_item)

    print("\n--- Final Results (Dictionary) ---")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_test()