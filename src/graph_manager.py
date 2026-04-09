from neo4j import GraphDatabase
import src.config as config

class GraphManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            config.NEO4J_URI, 
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def get_focused_rules(self, query):
        """
        Retrieves ALL syntax rules and instructions.
        Ideally we would use vector search here, but for now retrieving everything is safer 
        to ensure we don't miss any 'loop' instructions.
        """
        cypher = """
        MATCH (r:SyntaxRule)
        RETURN r.rule, r.context
        ORDER BY r.created_at ASC
        """
        results = self.query(cypher)
        rules = []
        for row in results:
             rules.append(f"RULE [Context: {row['r.context']}]: {row['r.rule']}")
        return "\n".join(rules)
    
    def store_syntax_rule(self, rule_text, context="General"):
        """
        Stores a specific syntax rule or instruction in the graph.
        """
        cypher = """
        CREATE (r:SyntaxRule {rule: $rule, context: $context, created_at: timestamp()})
        """
        self.query(cypher, {"rule": rule_text, "context": context})
        print(f"Syntax Rule Saved: {rule_text}")

    def log_mistake_node(self, user_input, bot_reply, analysis_data):
        """
        Logs a mistake directly into the graph.
        Supports detailed analysis dictionary with a list of issues.
        """
        import json
        
        # Default empty values
        analytics_json = "{}"
        issues = []

        if isinstance(analysis_data, dict):
            issues = analysis_data.get("issues", [])
            analytics_json = json.dumps(analysis_data.get("detailed_analytics", {}))

        # We create a Mistake node. 
        # Then, for each issue in the issues list, we create an Issue node and link it.
        # Issue nodes capture the specific granular entity (type, description, cause, fix).
        
        cypher_safe = """
        CREATE (m:Mistake {
            user_input: $u,
            bot_reply: $b,
            timestamp: timestamp()
        })
        WITH m
        
        UNWIND $issues as issue_data
        CREATE (i:Issue {
            issue_type: issue_data.issue_type,
            description: issue_data.description,
            cause: issue_data.cause,
            suggested_fix: issue_data.suggested_fix,
            created_at: timestamp()
        })
        CREATE (m)-[:HAS_ISSUE]->(i)
        
        WITH m, i, issue_data
        MERGE (c:Cause {description: issue_data.cause})
        CREATE (i)-[:STEMS_FROM]->(c)
        
        WITH DISTINCT m
        CREATE (a:DetailedAnalytics {
            data: $analytics,
            created_at: timestamp()
        })
        CREATE (m)-[:HAS_ANALYTICS]->(a)
        """

        try:
            self.query(cypher_safe, {
                "u": user_input, 
                "b": bot_reply, 
                "issues": issues,
                "analytics": analytics_json
            })
            print(f"Mistake Logged in Graph with {len(issues)} granular issues.")
        except Exception as e:
            print(f"Failed to log to graph: {e}")

    def add_instruction(self, instruction_text):
        """
        Stores a persistent instruction for the bot.
        """
        cypher = """
        CREATE (i:Instruction {content: $text, created_at: timestamp()})
        """
        self.query(cypher, {"text": instruction_text})
        print(f"Instruction Saved: {instruction_text}")

    def get_all_instructions(self):
        """
        Retrieves all stored instructions ordered by creation time.
        """
        cypher = """
        MATCH (i:Instruction)
        RETURN i.content
        ORDER BY i.created_at ASC
        """
        results = self.query(cypher)
        if not results:
            return ""
        
        return "\n".join([f"- {r['i.content']}" for r in results])

    def wipe_db(self):
        self.query("MATCH (n) DETACH DELETE n")
