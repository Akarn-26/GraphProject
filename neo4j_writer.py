from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
import ast
load_dotenv()
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=("neo4j", os.getenv("NEO4J_PASSWORD")))

def write_triple(session, triple):
    source = triple.get('source_article', 'unknown')
    query = f"""
    MERGE (a:{triple['subject_type']} {{name: "{triple['subject']}"}})
    MERGE (b:{triple['object_type']} {{name: "{triple['object']}"}})
    MERGE (a)-[:{triple['relation']}]->(b)
    MERGE (a)-[:{triple['relation']} {{source_article: "{source}"}}]->(b)
    """
    session.run(query)

with open("triples.txt", "r", encoding="utf-8") as f:
    data = ast.literal_eval(f.read())
all_triples=[triple for chunk in data for triple in chunk]
with driver.session() as session:
    for triple in all_triples:
        write_triple(session, triple)
driver.close()
print("done")