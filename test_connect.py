import os
from neo4j import GraphDatabase

uri = "neo4j://127.0.0.1:7687"
user = "neo4j"
password = "neo4j"

print(f"Testing connection to {uri}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 'Connection Successful' AS message")
        for record in result:
            print(record["message"])
    driver.close()
except Exception as e:
    print(f"Connection Failed: {e}")
