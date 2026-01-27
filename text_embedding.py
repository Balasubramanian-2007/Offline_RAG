# importing required modules
from pypdf import PdfReader
import re
import docx

#Structure aware chunking : 

def isheading(line):
    score=0
    threshold=4
    if len(line)<=80:score+=1
    if line.endswith(":"):score+=1
    if line.isupper():score+=2
    if len(line.split())<=10:score+=2
    if not line.endswith("."):score+=1
    if line.lower().startswith(("the ", "a ", "an ")):score -= 2

    if score>=threshold:
        return score
    else:
        return False


# x=isheading("COMPLETE RESEARCH ANALYSIS: Best LLM for Offline Technical  Document Retrieval")
# print(f"x:{x}")
# y=isheading("the research actually says:")
# print(f"y:{y}")


def extract_text_from_pdf(file_name):
    reader = PdfReader(file_name)
    words=[]

    heading_found=False

    for page in reader.pages:
        text=page.extract_text()
        if not text:
            continue

        sections={}
        lines=text.split('\n')

        sections["heading"]=""
        sections["content"]=""
        sections["document_name"]=file_name

        previousHeadingScore=2

        for eachLine in lines:
            cleanLine=eachLine.strip()
            check_heading=isheading(cleanLine)
            if( check_heading and check_heading>previousHeadingScore):
                if sections["heading"]!="":
                    sections["content"]+=f"{sections['heading']}"

                sections["heading"]=cleanLine
                previousHeadingScore=check_heading
            else:
                sections["content"]+=f"  {cleanLine}"

        if(len(sections["heading"])<=1):
            sections["heading"]+="None"

        words.append(sections)
    #this is for checking the heading identification parameter :
    # for i in words:
    #     print("Chunk : ")
    #     print(i)
    #     print("\n")
    #     print("\n")

def extract_text_from_word(file_name):
    # bullet_pattern = re.compile(r"^\s*[\*\-\•\d\.]+\s+")
    document=docx.Document(file_name)
    words=[]

    for page in document.paragraphs:
        if not page.text:
            continue
        lines=page.text.split('\n')
        sections={}
        sections["heading"]=""
        sections["content"]=""
        sections["document_name"]=file_name

        previousHeadingScore=1
        for eachLine in lines:
            cleanLine=eachLine.strip()
            check_heading=isheading(cleanLine)
            if( check_heading and check_heading>previousHeadingScore):
                if sections["heading"]!="":
                    sections["content"]+=f"{sections['heading']}"

                sections["heading"]=cleanLine
                previousHeadingScore=check_heading
            else:
                sections["content"]+=f"  {cleanLine}"

        if(len(sections["heading"])<=1):
            sections["heading"]+="None"

        words.append(sections)
    # for i in words:
    #     print("Chunk : ")
    #     print(i)
    #     print("\n")
    #     print("\n")

# extract_text_from_word("D:\ACTIMATE.docx")
# extract_text_from_pdf("D:\Downloads\RESEARCH-BACKED LLM Analysis for Offline Technical Document Retrieval - converted.pdf")