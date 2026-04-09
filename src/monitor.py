import json
import datetime
import src.config as config
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

class DissatisfactionMonitor:
    def __init__(self, graph_manager=None):
        self.llm = ChatOllama(
            model=config.MODEL_NAME, 
            base_url=config.OLLAMA_BASE_URL,
            temperature=0  # Deterministic for classification
        )
        self.gm = graph_manager

    def analyze_interaction(self, user_input, bot_reply, history):
        """
        Check if the user is frustrated based on their LATEST input.
        Returns a detailed breakdown if dissatisfaction is detected.
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a sentiment analyst. Your job is to detect User DISSATISFACTION or FRUSTRATION. "
                       "If detected, analyze the root causes and break them down into separate, granular entities. "
                       "Return ONLY a JSON object with the following structure:\n"
                       "{{\n"
                       "  \"is_dissatisfied\": true/false,\n"
                       "  \"issues\": [\n"
                       "      {{\n"
                       "         \"issue_type\": \"<Convention Enum like HALLUCINATION, IGNORED_INSTRUCTION, WRONG_FORMAT, INCORRECT_FACT, BAD_TONE>\",\n"
                       "         \"description\": \"Specific detail of what went wrong in this exact instance\",\n"
                       "         \"cause\": \"Underlying reason for this specific issue\",\n"
                       "         \"suggested_fix\": \"How the system should have responded to avoid this issue\"\n"
                       "      }}\n"
                       "  ],\n"
                       "  \"detailed_analytics\": {{ \"sentiment_score\": 0-10, \"tone\": \"...\", \"recommendation\": \"...\" }}\n"
                       "}}\n"
                       "Look for cues like 'no', 'wrong', 'bad', 'retry', 'stupid', 'not working', or repetitive corrections. "
                       "If there are multiple reasons for dissatisfaction, create a separate object in the 'issues' array for EACH distinct reason."),
            ("user", "Conversation History:\n{history}\n\nLast Interaction:\nBot: {bot_reply}\nUser: {user_input}\n\nAnalyze:")
        ])
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "history": history, 
                "bot_reply": bot_reply, 
                "user_input": user_input
            })
            
            content = response.content.strip()
            
            # Handle markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Try to find JSON in the response if it includes extra text
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                
                # Replace single quotes with double quotes for valid JSON
                # Be careful, it might break if there are actual single quotes inside strings
                # But Ollama with this prompt usually outputs valid double-quoted JSON anyway.
                import re
                
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    print(f"JSON Parse Error in Monitor: {json_str[:50]}...")
                    return False, None
                
                if result.get("is_dissatisfied"):
                    self.log_dissatisfaction(user_input, bot_reply, result)
                    return True, result
            
            return False, None
            
        except Exception as e:
            print(f"Monitor Error: {e}")
            return False, None

    def log_dissatisfaction(self, user_input, bot_reply, analysis_result):
        # 1. Log to Graph
        if self.gm:
            # Pass the granular analysis to the graph manager
            self.gm.log_mistake_node(user_input, bot_reply, analysis_result)
        else:
             print(f"Error: No GraphManager connected to Monitor. Mistake detected.")

        # 2. Log to Dataset File (the "json based thing" for analytics/training)
        try:
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "user_input": user_input,
                "bot_previous_reply": bot_reply,
                "issues": analysis_result.get("issues", []),  # Granular issues
                "detailed_analytics": analysis_result.get("detailed_analytics", {}),
                "full_analysis_json": analysis_result
            }
            with open(config.DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Error logging to dataset file: {e}")
