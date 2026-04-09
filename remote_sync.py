import requests
import json
import src.config as config
import os

def send_to_big_model(data_payload, custom_prompt):
    """
    Sends the generated JSON dataset and a custom prompt to a larger model 
    (like Gemini Pro) for advanced analysis, summarization, or validation.
    """
    
    # Check if API Key is configured
    if config.GEMINI_API_KEY == "YOUR_API_KEY_HERE" or not config.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set in src/config.py")
        return None

    # Construct the full URL
    url = f"{config.GEMINI_API_URL}{config.GEMINI_API_KEY}"
    
    # Prepare the prompt with the JSON data
    full_prompt = (
        f"{custom_prompt}\n\n"
        f"Input Data (JSON):\n"
        f"{json.dumps(data_payload, indent=2)}"
    )

    # Standard Gemini Pro Request Body
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ]
    }

    headers = {'Content-Type': 'application/json'}

    try:
        print(f"Sending request to Gemini Pro ({len(full_prompt)} chars)...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            # Extract text response from Gemini's specific JSON structure
            try:
                bot_message = result['candidates'][0]['content']['parts'][0]['text']
                return bot_message
            except (KeyError, IndexError):
                print("Error: Could not parse text from Gemini response structure.")
                return result
        else:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def sync_dataset_for_analysis(file_path="sft_dataset.jsonl", prompt="Analyze the following fine-tuning records and suggest improvements for instruction clarity:"):
    """
    Reads the last N lines of a dataset and sends it for analysis.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        # Read last 10 records to avoid context window spill for very large datasets
        lines = f.readlines()
        for line in lines[-10:]:
            records.append(json.loads(line))
    
    analysis = send_to_big_model(records, prompt)
    if analysis:
        print("\n--- Model Analysis ---\n")
        print(analysis)
        print("\n----------------------")

if __name__ == "__main__":
    # Example usage
    # Ensure you set your API Key in config.py first!
    sync_dataset_for_analysis()
