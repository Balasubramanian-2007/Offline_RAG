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


#SERVER CREATION :
app=FastAPI()

UPLOAD_DIRECTORY = "./uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

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
    password="Bala@2007",
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
    
    embeddings = model.encode(chunks,normalize_embeddings=True)
    index=faiss.IndexFlatL2(384)
    index.add(embeddings)


    print(index)


# extract_text_from_word("D:\Academics Till Now\\3-rd SEM Academics\CN_Lab\CN_lab1_revised.docx")
# chunks=extract_text_from_pdf("documents\\40_a.pdf")
# file_uploads()
