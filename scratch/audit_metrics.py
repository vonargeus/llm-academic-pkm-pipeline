import json
import os

def audit_details():
    results_dir = r"c:\Users\jubam\Desktop\Bsc_Project\data\results"
    
    # 1. RQ1 CV report
    with open(os.path.join(results_dir, "cv_report.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
        print("\n=== RQ1 Link-Expanded CV Aggregated Metrics ===")
        print(data.get("aggregated_out_of_fold", {}))
        
    # 2. RQ2 Metadata and Strict Topics
    with open(os.path.join(results_dir, "rq2_results.json"), 'r', encoding='utf-8') as f:
        data = json.load(f)
        print("\n=== RQ2 Group A Bibliographic Metadata Metrics ===")
        meta = data.get("Group_A_Bibliographic", {})
        print({k: v for k, v in meta.items() if not isinstance(v, list)})
        
        print("\n=== RQ2 Group B Semantic Strict Topics ===")
        semantic = data.get("Group_B_Semantic", {})
        # print only top level strict metrics
        print({k: v for k, v in semantic.items() if k not in ["per_paper", "B2_supplementary"]})

if __name__ == '__main__':
    audit_details()
