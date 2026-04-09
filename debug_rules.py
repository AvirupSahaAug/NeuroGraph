from src.rag_engine import RAGEngine
from src.graph_manager import GraphManager

# Mock GraphManager to avoid needing real Neo4j for this quick test if we wanted
# But we have real Neo4j, so let's just use it but print instead of checking DB manually endlessly
class MockGM:
    def store_syntax_rule(self, rule, context):
        print(f"MOCK STORE: {rule} | {context}")
    def get_focused_rules(self, query):
        return ""
    def add_knowledge(self, a,b,c): pass
    def get_context(self, a): return ""
    def add_instruction(self, i): pass
    def get_all_instructions(self): return ""
    def wipe_db(self): pass

# Test the extraction logic
rag = RAGEngine(MockGM())

test_input = """
Here are the rules for writing python code in this project:
1. Always use snake_case for functions.
2. Use Google docstrings.
3. Max line length is 80 chars.
"""

print(f"Testing input: {test_input}")
rules = rag.extract_syntax_rules(test_input)
print(f"Extracted rules: {rules}")
