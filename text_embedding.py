# importing required modules
from pypdf import PdfReader
import re
import docx
from collections import Counter
import psycopg2
from sentence_transformers import SentenceTransformer
import faiss
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import numpy as np
import os
import shutil
from pydantic import BaseModel  #used for data parsing and data validation
from ollama import chat
from ollama import ChatResponse
from openai import OpenAI

#LLM


#SERVER CREATION :
app=FastAPI()


client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=""  # Get free at https://console.groq.com
)

UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

#For string as a parameter in /query
class QueryRequest(BaseModel):
    query: str 

#Embedding model:
'''
URL for hugging face sentence transformers =
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
'''
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# DB CONNECTION :
conn=psycopg2.connect(
    dbname="OWN_RAG",
    user="postgres",
    password="",
    host="localhost",
    port="5432"
)

cur=conn.cursor()

#Structure aware chunking : 
def isheading(line):
    score = 0
    threshold = 4

    line = line.strip()
    if not line:
        return False

    if len(line) <= 80: score += 1
    if line.endswith(":"): score += 1
    if line.isupper(): score += 2
    if len(line.split()) <= 10: score += 2
    if not line.endswith("."): score += 1
    if line.lower().startswith(("the ", "a ", "an ","and ")): score -= 2

    return score if score >= threshold else False


def extract_text_from_pdf(file_name):
    reader = PdfReader(file_name)

    sections = []
    current_section = None

    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        lines = text.split("\n")

        for line in lines:
            cleanLine = line.strip()
            if not cleanLine:
                continue

            heading_score = isheading(cleanLine)
            if heading_score:
                if current_section:
                    dbQuery="""
                        INSERT INTO chunks
                        (source_name,heading,content,pg_start,pg_end)
                        VALUES(%s,%s,%s,%s,%s)
                        """
                    cur.execute(dbQuery,(current_section["document_name"],current_section["heading"],current_section["content"],current_section["page_start"],current_section["page_end"]))
                    conn.commit()
                    sections.append(current_section)

                current_section = {
                    "heading": cleanLine,
                    "content": "",
                    "document_name": file_name,
                    "page_start": page_no,
                    "page_end": page_no
                }
            else:
                if not current_section:
                    current_section = {
                        "heading": "GENERAL",
                        "content": "",
                        "document_name": file_name,
                        "page_start": page_no,
                        "page_end": page_no
                    }

                current_section["content"] += " " + cleanLine
                current_section["page_end"] = page_no

    if current_section:
        dbQuery="""
        INSERT INTO chunks
        (source_name,heading,content,pg_start,pg_end)
        VALUES(%s,%s,%s,%s,%s)
        """
        cur.execute(dbQuery,(current_section["document_name"],current_section["heading"],current_section["content"],current_section["page_start"],current_section["page_end"]))
        conn.commit()
        sections.append(current_section)

    return sections

def extract_text_from_word(file_name):
    document = docx.Document(file_name)

    sections = []
    current_section = None

    for para_index, para in enumerate(document.paragraphs):
        cleanLine = para.text.strip()
        if not cleanLine:
            continue

        heading_score = isheading(cleanLine)

        if heading_score:
            if current_section:
                dbQuery="""
                    INSERT INTO chunks
                    (source_name,heading,content,pg_start,pg_end)
                    VALUES(%s,%s,%s,%s,%s)
                    """
                cur.execute(dbQuery,(current_section["document_name"],current_section["heading"],current_section["content"],current_section["para_start"],current_section["para_end"]))
                conn.commit()
                sections.append(current_section)

            current_section = {
                "heading": cleanLine,
                "content": "",
                "document_name": file_name,
                "para_start": para_index,
                "para_end": para_index
            }
        else:
            if not current_section:
                current_section = {
                    "heading": "GENERAL",
                    "content": "",
                    "document_name": file_name,
                    "para_start": para_index,
                    "para_end": para_index
                }

            current_section["content"] += " " + cleanLine
            current_section["para_end"] = para_index

    if current_section:
        dbQuery="""
            INSERT INTO chunks
            (source_name,heading,content,pg_start,pg_end)
            VALUES(%s,%s,%s,%s,%s)
            """
        cur.execute(dbQuery,(current_section["document_name"],current_section["heading"],current_section["content"],current_section["para_start"],current_section["para_end"],))
        conn.commit()
        sections.append(current_section)

    return sections

@app.post("/upload")
def file_uploads(file: UploadFile = File(...)):
    filename=os.path.basename(file.filename)
    file_path=os.path.join(UPLOAD_DIRECTORY,filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"Saved {file.filename} to {file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
    

    if file.filename.endswith(".pdf"):
        chunks=extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        chunks=extract_text_from_word(file_path)
    else:
        raise HTTPException(status_code=404,detail="Invalid File Type ! Upload a valid file PDF or Docx")
    
    texts = [
        f"{chunk['heading']}. {chunk['content']}"
        for chunk in chunks
    ]
    embeddings = model.encode(texts,normalize_embeddings=True)
    dimension=embeddings.shape[1]

    if os.path.exists("faissx.faiss"):
        index=faiss.read_index("faissx.faiss")
    else:
        index=faiss.IndexFlatL2(dimension)

    base_chunk_id=index.ntotal
    index.add(embeddings)
    faissFileName="faissx.faiss"
    faiss.write_index(index,faissFileName)
    print(f"Updated index saved to {faissFileName}")
    return{"message":"Vector inserted successfully"}


#Query retrieval :

def fetchChunksFromDB(chunk_id):
    print(chunk_id)
    chunk_id=[i+1 for i in chunk_id]
    print(f"Chunk ID after adding one :\n{chunk_id}")
    query="""
        SELECT heading,content FROM chunks
        WHERE chunk_id=ANY(%s) AND deleted_at IS NULL
    """
    cur.execute(query,(chunk_id,))
    chunks=cur.fetchall()
    if not chunks:
        message={"Message":"No chunks retrieved ! No relevant information is found!"}
        return message
    context=""
    for heading,content in chunks:
        context+=f"\n[SECTION:${heading}]\n{content}\n"
    return context.strip()

def build_prompt(context, user_query):
    return f"""
    You are a helpful technical assistant.
    Answer ONLY using the information provided below.
    If the answer is not present, say "Not found in the document".

    Context:
    {context}

    Question:
    {user_query}

    Answer:
    """.strip()

# def ask_llm(prompt):
#     response: ChatResponse = chat(
#         model="qwen2:1.5b",
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )
#     return response.message.content

def ask_llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # or other Groq models
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.2
    )
    return response.choices[0].message.content

@app.post("/result")
def query_retrieval(req: QueryRequest):
    query=req.query
    embedding = model.encode(query,normalize_embeddings=True)
    embedding = np.array(embedding).astype("float32").reshape(1, -1)

    faiss_file="faissx.faiss"
    if os.path.exists("faissx.faiss"):
        index=faiss.read_index(faiss_file)
    else:
        raise HTTPException(status_code=404,detail="No faiss file !")
        
    top_K=12
    D,I=index.search(embedding,top_K)
    chunk_ids = I[0].tolist()
    context=fetchChunksFromDB(chunk_ids)
    prompt=build_prompt(context,query)
    # ollamaResponse=ollama(prompt)
    LLMResponse=ask_llm(prompt)
    message={
        "Question:":query,"Response:":LLMResponse
    }

    return message


@app.get("/deleteDocuments")
def deleteDocuments(req:QueryRequest):
    docToDelete=req.query
    query="""
        UPDATE chunks SET deleted_at=LOCALTIMESTAMP WHERE source_name=%s
    """
    cur.execute(query,(docToDelete,))
    conn.commit()






