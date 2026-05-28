import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
def clean_text(text: str) -> str:
    text=text.replace("(cid:127)","")
    lines = text.split("\n")
    lines = [l for l in lines if not (
        len(l.strip()) < 60 and any([
            "constituteproject.org" in l,
            "PDF generated" in l,
            "Norway 1814" in l,
            "Page" in l
        ])
    )]
    return " ".join(lines)

def extract_pages(pdf_path: str) -> list[dict]:
    pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text()
            cleaned = clean_text(raw)
            
            pages.append({
                "page_number": i + 1,
                "text": cleaned
            })

    return pages                                        
def chunk_pages(pages:list[dict])->list[dict]:
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=80,
        separators=["\n\n","\n","."," "]
    )
    chunks=[]
    chunk_index=0
    for page in pages:
        splits=splitter.split_text(page["text"])
        for split in splits:
            chunks.append({
              "chunk_id": f"norway_p{page['page_number']}_c{chunk_index}",
                "source": "constitution.pdf",
                "page_number": page["page_number"],
                "text": split  
            })
            chunk_index+=1
    return chunks
if __name__=="__main__":
    print(chunk_pages(extract_pages("constitution.pdf"))[2])