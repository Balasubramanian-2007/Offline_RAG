# importing required modules
from pypdf import PdfReader
import re
import docx

#Structure aware chunking : 

def extract_text_from_pdf(file_name):
    bullet_pattern = re.compile(r"^\s*[\*\-\•\d\.]+\s+")
    reader = PdfReader(file_name)
    words=[]
    page_no=1
    for page in reader.pages:
        text=page.extract_text()
        if not text:
            continue
        lines=text.split('\n')
        sections={}
        sections["heading"]=""
        sections["content"]=""
        sections["page_no"]=page_no
        for eachLine in lines:
            cleanLine=eachLine.strip()
            if not cleanLine:
                continue
            if len(cleanLine)<80 and cleanLine.isupper() :
                sections["heading"]+=" "+cleanLine
            elif bullet_pattern.match(cleanLine):
                sections["content"]+=" "+cleanLine
            else:
                sections["content"]+=" "+cleanLine
        words.append(sections)
        page_no+=1
    print(words)

def extract_text_from_word(file_name):
    bullet_pattern = re.compile(r"^\s*[\*\-\•\d\.]+\s+")
    document=docx.Document(file_name)
    words=[]
    page_number=1
    for page in document.paragraphs:
        # total+=page.text
        if not page.text:
            continue
        lines=page.text.split('\n')
        sections={}
        sections["heading"]=""
        sections["content"]=""
        sections["page_no"]=page_number
        for eachLine in lines:
            cleanLine=eachLine.strip()
            if not cleanLine:
                continue
            if len(cleanLine)<80 and cleanLine.isupper() :
                sections["heading"]+=" "+cleanLine
            elif bullet_pattern.match(cleanLine):
                sections["content"]+=" "+cleanLine
            else:
                sections["content"]+=" "+cleanLine
        words.append(sections)
        page_number+=1
    print(words)

extract_text_from_word("D:\ACTIMATE.docx")
extract_text_from_pdf("D:\Downloads\RESEARCH-BACKED LLM Analysis for Offline Technical Document Retrieval - converted.pdf")