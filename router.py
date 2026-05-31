from groq import Groq
from db import search
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"), 
    auth=("neo4j", os.getenv("NEO4J_PASSWORD"))
)
model1="llama-3.3-70b-versatile"
model2="llama-3.1-8b-instant"
model=model1
def run_cypher(query,driver):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]
    
def beautify_text(answer):
    prompt="Make this answer structured and do not add any additional details. Answer: "
    prompt+=answer
    response=client.chat.completions.create(
    model=model,
    messages=[{"role":"user","content":prompt}]
    )
    text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
    return text
def handle_query(user_input,driver,st_model):

    prompt = """Classify the user question into exactly one of: graph, summary, both.

    graph = questions about specific entities, facts, rules, powers, rights, duties, relationships between specific things
    summary = questions asking for overview, explanation, general understanding, broad context
    both = questions needing specific facts AND broader context together

    Return ONLY one word. No punctuation. No explanation.

    Examples:
    "What powers does the King have?" -> graph
    "What is the constitution about?" -> summary
    "Tell me about the King and his role in government" -> both
    ONLY use the node types and relationship types listed above. Do not invent new ones.
    Question: """
    prompt+=user_input
    
    response=client.chat.completions.create(
    model=model,
    messages=[{"role":"user","content":prompt}]
    )
    text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
    try:
        if text=="graph":
            prompt_graph = """Write a Cypher query for Neo4j strictly using only these:
            Node types: Person, Role, Institution, Right, Duty, Article
            Relationship types: HAS_POWER, PART_OF, DEFINED_IN, APPOINTED_BY, RESPONSIBLE_TO, GRANTS, RESTRICTS
            Every node has a 'name' property.
            Use WHERE n.name CONTAINS 'keyword' for name matching, never exact names.
            ONLY use node types and relationship types listed above. Do not invent new ones.
            Return ONLY the Cypher query, no explanation, no backticks, no comments.

            Examples:
            "What articles grant human rights?" -> MATCH (a:Article)-[:GRANTS]->(r:Right) WHERE r.name CONTAINS 'human' RETURN a.name, r.name
            "What powers does the King have?" -> MATCH (p:Person)-[:HAS_POWER]->(r:Role) WHERE p.name CONTAINS 'King' RETURN p.name, r.name
            "Which institutions are part of government?" -> MATCH (i:Institution)-[:PART_OF]->(g:Institution) WHERE g.name CONTAINS 'government' RETURN i.name, g.name
            "What duties are defined in Article 1?" -> MATCH (a:Article)-[:GRANTS]->(d:Duty) WHERE a.name CONTAINS '1' RETURN a.name, d.name
            - Always include the article number where this fact is stated as source_article
            Question: """
            prompt_graph+=user_input
            response=client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt_graph}]
            )
            text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
            return(beautify_text(str(run_cypher(text,driver))))
        elif text=="summary":
            return(beautify_text(str(search(user_input,st_model))))
        else:
            prompt_graph = """Write a Cypher query for Neo4j strictly using only these:
            Node types: Person, Role, Institution, Right, Duty, Article
            Relationship types: HAS_POWER, PART_OF, DEFINED_IN, APPOINTED_BY, RESPONSIBLE_TO, GRANTS, RESTRICTS
            Every node has a 'name' property.
            Use WHERE n.name CONTAINS 'keyword' for name matching, never exact names.
            ONLY use node types and relationship types listed above. Do not invent new ones.
            Return ONLY the Cypher query, no explanation, no backticks, no comments.

            Examples:
            "What articles grant human rights?" -> MATCH (a:Article)-[:GRANTS]->(r:Right) WHERE r.name CONTAINS 'human' RETURN a.name, r.name
            "What powers does the King have?" -> MATCH (p:Person)-[:HAS_POWER]->(r:Role) WHERE p.name CONTAINS 'King' RETURN p.name, r.name
            "Which institutions are part of government?" -> MATCH (i:Institution)-[:PART_OF]->(g:Institution) WHERE g.name CONTAINS 'government' RETURN i.name, g.name
            "What duties are defined in Article 1?" -> MATCH (a:Article)-[:GRANTS]->(d:Duty) WHERE a.name CONTAINS '1' RETURN a.name, d.name
            - Always include the article number where this fact is stated as source_article
            Question: """
            prompt_graph+=user_input
            response=client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt_graph}]
            )
            text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
            return(beautify_text(str(run_cypher(text,driver))+str(search(user_input,st_model))))
    except Exception as e:
        raise RuntimeError(str(e))
