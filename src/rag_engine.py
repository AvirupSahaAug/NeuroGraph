from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import src.config as config
import json

class RAGEngine:
    def __init__(self, graph_manager):
        self.gm = graph_manager
        self.llm = ChatOllama(
            model=config.MODEL_NAME, 
            base_url=config.OLLAMA_BASE_URL
        )

    def extract_syntax_rules(self, user_input):
        """
        Detects if the user is defining SYNTAX RULES or INSTRUCTIONS (singular or plural).
        Can handle cheatsheets or long texts.
        Returns a list of tuples: [(Rule Content, Context), ...] or []
        """
        prompt_text = (
            "You are a Syntax Rule Extractor. Your job is to return JSON data only. DO NOT write Python code.\n"
            "Analyze the input for ANY coding rules, syntax instructions, or style guides.\n"
            "Output format: A JSON list of objects: [{{'rule': '...', 'context': '...'}}]\n"
            "\n"
            "Input: 'Functions must be snake_case.'\n"
            "Output: [{{'rule': 'Functions must be snake_case', 'context': 'Python'}}]\n"
            "\n"
            "Input: 'Use ISO dates. Max line length 100.'\n"
            "Output: [{{'rule': 'Use ISO dates', 'context': 'General'}}, {{'rule': 'Max line length 100', 'context': 'Format'}}]\n"
            "\n"
            "CRITICAL: Return ONLY valid JSON. No Markdown formatting. No explanations.\n"
            "User Input: {input}"
        )
        # Using invoke directly on LLM with just string prompt to bypass template complexity
        try:
            content = response.content.strip()
            
            # Clean up markdown code blocks if the LLM provided them
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
                
            print(f"DEBUG RAW RESPONSE: {content}") # Debugging
            
            # Find JSON list - try multiple techniques
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                # print(f"DEBUG LLM OUTPUT: {json_str}") 
                try:
                    # Naive cleanup for common LLM JSON errors (single quotes)
                    if "'" in json_str and '"' not in json_str:
                         json_str = json_str.replace("'", '"')
                    
                    data = json.loads(json_str)
                    extracted = []
                    
                    # Handle if LLM wrapped it in a dict key like "rules": [...]
                    if isinstance(data, dict):
                        for key in ["rules", "instructions", "data"]:
                            if key in data and isinstance(data[key], list):
                                data = data[key]
                                break

                    if isinstance(data, list):
                        for item in data:
                            try:
                                if isinstance(item, dict):
                                    # Try to find rule content in various keys
                                    rule_content = item.get("rule") or item.get("instruction") or str(item)
                                    context = item.get("context", "General")
                                    extracted.append((rule_content, context))
                                elif isinstance(item, str):
                                    extracted.append((item, "General"))
                            except Exception as inner:
                                print(f"Skipping rule item: {inner}")
                    
                    return extracted
                except:
                    print(f"JSON Parse Error in Rules: {json_str[:50]}...")
            return []
        except Exception as e:
            print(f"Rule Extraction Error: {e}")
            return []

    def generate_reply(self, user_input):
        # 1. Detect & Store New Rules Loop
        new_rules = self.extract_syntax_rules(user_input)
        for rule_text, rule_context in new_rules:
             self.gm.store_syntax_rule(rule_text, rule_context)
        
        # 2. Retrieve Focused Rules Loop
        # We fetch ALL rules to ensure we don't miss anything (as requested "iteratively checks... consistency")
        # In a larger system, we'd limit this.
        known_rules = self.gm.get_focused_rules(user_input)
        
        # 3. Generate Answer with Strict Adherence
        system_prompt = (
            "You are a Strict Syntax Assistant. "
            "Your Primary Goal: Follow the USER DEFINED RULES below to the letter. "
            "If the user asks for code, use the syntax defined in the Rules. "
            "If the Rules say 'Don't do X', then NEVER do X. "
            "Ignore your pre-training if it conflicts with these Rules.\n\n"
            f"=== KNOWN SYNTAX RULES & INSTRUCTIONS ===\n{known_rules}\n\n"
            "If no rule applies, answer normally."
        )

        if new_rules:
            system_prompt += f"\n[Update: I just learned {len(new_rules)} new rules!]\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm
        return chain.invoke({"input": user_input}).content
