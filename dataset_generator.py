import json
import os

# Default paths based on current directory structure
DATASET_FILE = "dissatisfaction_dataset.jsonl"
SFT_OUTPUT_FILE = "sft_dataset.jsonl"
DPO_OUTPUT_FILE = "dpo_dataset.jsonl"

def generate_requirements(input_file=DATASET_FILE, sft_file=SFT_OUTPUT_FILE, dpo_file=DPO_OUTPUT_FILE):
    """
    Reads the dissatisfaction dataset containing granular issues.
    Transforms each issue into SFT (Chat ML) and DPO (Preference) formats 
    suitable for fine-tuning.
    """
    stats = {"sft": 0, "dpo": 0, "skipped": 0}
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Ensure you have logged some feedback.")
        return stats

    sft_data = []
    dpo_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                user_input = data.get("user_input", "")
                bot_previous_reply = data.get("bot_previous_reply", "")
                issues = data.get("issues", [])
                
                if not issues and "reason" in data:
                    issues = [{
                        "issue_type": "LEGACY_FEEDBACK",
                        "description": data.get("reason", ""),
                        "cause": "Unknown",
                        "suggested_fix": data.get("fine_tuning_prompt", "")
                    }]
                
                if issues:
                    for issue in issues:
                        suggested_fix = issue.get("suggested_fix", "")
                        
                        if not suggested_fix or not user_input:
                            stats["skipped"] += 1
                            continue
                            
                        # 1. SFT Format (Chat ML: messages array)
                        # Helps the model learn *how* to answer correctly given the prompt
                        sft_entry = {
                            "messages": [
                                {
                                    "role": "system", 
                                    "content": "You are a Strict Syntax Assistant. Follow user rules meticulously."
                                },
                                {
                                    "role": "user", 
                                    "content": user_input
                                },
                                {
                                    "role": "assistant", 
                                    "content": suggested_fix
                                }
                            ]
                        }
                        sft_data.append(sft_entry)
                        
                        # 2. DPO Format (Prompt, Chosen, Rejected)
                        # Helps the model align by contrasting good behavior vs bad behavior
                        dpo_entry = {
                            "prompt": f"System: You are a Strict Syntax Assistant. Follow user rules meticulously.\n\nUser: {user_input}",
                            "chosen": suggested_fix,
                            "rejected": bot_previous_reply
                        }
                        dpo_data.append(dpo_entry)
                        
            except json.JSONDecodeError:
                stats["skipped"] += 1
            except Exception as e:
                print(f"Error processing entry: {e}")
                stats["skipped"] += 1
                
    # Write SFT requirements to output file
    if sft_data:
        with open(sft_file, 'w', encoding='utf-8') as f:
            for req in sft_data:
                f.write(json.dumps(req) + "\n")
        stats["sft"] = len(sft_data)
                
    # Write DPO requirements to output file
    if dpo_data:
        with open(dpo_file, 'w', encoding='utf-8') as f:
            for req in dpo_data:
                f.write(json.dumps(req) + "\n")
        stats["dpo"] = len(dpo_data)
            
    print(f"Generated {stats['sft']} SFT entries and {stats['dpo']} DPO entries.")
    if stats['skipped'] > 0:
        print(f"Skipped {stats['skipped']} invalid entries.")
        
    return stats

if __name__ == "__main__":
    generate_requirements()
