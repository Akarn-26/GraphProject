from groq import Groq
import json
from ingestion import extract_pages,chunk_pages
import time

def prompt(chunk_text):
    prompt=f""" 
    You are a knowledge graph extractor. Extract triples from the text below.

    ALLOWED NODE TYPES: Person, Role, Institution, Right, Duty, Article

    ALLOWED RELATIONSHIP TYPES: HAS_POWER, PART_OF, DEFINED_IN, APPOINTED_BY, RESPONSIBLE_TO, GRANTS, RESTRICTS

    RULES:
    - Only use node types and relationship types from the lists above
    - Extract only facts explicitly stated in the text, no assumptions
    - Return ONLY a JSON array, no explanation, no extra text

    FORMAT:
    [
        {{"subject": "...", "subject_type": "...", "relation": "...", "object": "...", "object_type": "..."}}
    ]

    TEXT:
    {chunk_text} """
    return prompt

client=Groq(api_key="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")
chunks=chunk_pages(extract_pages("constitution.pdf"))

extracted_list=[]
for chunk in chunks:
    time.sleep(2)
    response=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt(chunk["text"])}]
    )
    text=response.choices[0].message.content.replace("```json","").replace("```","").strip()
    try:
        extracted_list.append(json.loads(text))
    except:
        print(f"Failed to parse chunk: {chunk['chunk_id']}")
        extracted_list.append([])
with open("triples.txt","w") as f:
    f.write(str(extracted_list))