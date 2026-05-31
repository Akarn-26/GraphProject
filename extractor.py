from groq import Groq
from dotenv import load_dotenv
import os
import json
from ingestion import extract_pages,chunk_pages
import time
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
def prompt(chunk_text):
    prompt=f""" 
    You are a knowledge graph extractor. Extract triples from the text below.

    ALLOWED NODE TYPES: Person, Role, Institution, Right, Duty, Article

    ALLOWED RELATIONSHIP TYPES: HAS_POWER, PART_OF, DEFINED_IN, APPOINTED_BY, RESPONSIBLE_TO, GRANTS, RESTRICTS

    RULES:
    - Only use node types and relationship types from the lists above
    - Extract only facts explicitly stated in the text, no assumptions
    - Always include the article number where this fact is stated as source_article
    - Return ONLY a JSON array, no explanation, no extra text

    FORMAT:
    [
        {{"subject": "...", "subject_type": "...", "relation": "...", "object": "...", "object_type": "...", "source_article": "Article X"}}
    ]

    TEXT:
    {chunk_text} """
    return prompt

chunks=chunk_pages(extract_pages("constitution.pdf"))

extracted_list=[]
for chunk in chunks:
    time.sleep(2)
    try:
        response=client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt(chunk["text"])}],
             temperature=0
        )
        text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
    except Exception as e:
        print(f"Error:{e}")
        break

    try:
        extracted_list.append(json.loads(text))
    except:
        print(f"Failed to parse chunk: {chunk['chunk_id']}")
        extracted_list.append([])
with open("triples.txt","w") as f:
    f.write(str(extracted_list))