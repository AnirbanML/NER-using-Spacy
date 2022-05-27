from fastapi import FastAPI, BackgroundTasks, Request
import time
import json
import os
import namedEntity as ne
from azure.storage.blob import BlockBlobService
import PyPDF2
from datetime import date

app = FastAPI()
PATH = './dump'
ACCOUNT_NAME = "saacedeveastinput"
ACCOUNT_KEY = "RhJlnL3AloZbVZ48ENuRlYPBKCab1Wsoc94mbESIxtAmoI5ep3pxaTYhXgyAmDpvtPMpRbtJfV3A7YKKWSbKlQ==;EndpointSuffix=core.windows.net"
CONTAINER_NAME = "input"
# LOCAL_FILE = r"/.Blob_Pdf/ADR-2022-1311.pdf"  
# referenceNo = "ADR-2022-200000003992/Divorce_Decree_27.pdf"

async def downloadPdfFromBlob(data):
    referenceNo = data['referenceNo']
    block_blob_service = BlockBlobService(account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)
    outputfile = os.path.join('./dump', referenceNo+'_.pdf')
    try:
        for file in block_blob_service.list_blobs(CONTAINER_NAME, referenceNo):
            if(file.name.split('.')[-1] == 'pdf'):
                block_blob_service.get_blob_to_path(CONTAINER_NAME,
                                                    file.name,
                                                    outputfile,
                                                    open_mode='wb')
    except:
        return None
    return outputfile


async def backtask(data):
    print('backtask')
    filename = data['referenceNo']+".txt"
    OUTPATH = './dump/'+str(date.today())
    if os.path.isdir(OUTPATH)==False:
        os.makedirs(OUTPATH)
        
    with open(os.path.join(OUTPATH,filename), 'w') as f:
        f.write(data['ocr'])
    pageNo = data['pageNo']
    inputfile = await downloadPdfFromBlob(data)
    
    outputfile = os.path.join(OUTPATH,data['referenceNo']+'.pdf')
    if inputfile!=None:
        pdfFileObj = open(inputfile, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        pdf_writer = PyPDF2.PdfFileWriter()
        page = pdfReader.getPage(pageNo-1)
        pdf_writer.addPage(page)
        with open(outputfile, 'wb') as pdf_out:
            pdf_writer.write(pdf_out)
        os.remove(inputfile)
        pdfFileObj.close()
    print('end')

@app.post('/NER')
async def main(request: Request, background_tasks: BackgroundTasks):
    '''jsonOutput = """{
                "ORG": null,
                "PERSON": [
                    {
                        "index": [
                            13,
                            27
                        ],
                        "value": "Anirban Sarkar"
                    }
                ]
            }"""
    jsonOutput =  json.loads(jsonOutput)'''
    
    content_type =  request.headers.get('content-type',None)
    if not content_type=='application/json':
        raise Exception("Content-Type should be json")
    else:
        data = await request.json()
        print(data)
        ocr = data["ocr"]
        extractkind= data["extractkind"]
        jsonOutput = ne.getNamedEntity(ocr)
               
        if extractkind=="O" and jsonOutput["ORG"]==None:
            background_tasks.add_task(backtask,data)
        if extractkind=="P" and jsonOutput["PERSON"]==None:
            background_tasks.add_task(backtask,data)
        if extractkind=="OP" and ((jsonOutput["ORG"]==None) or (jsonOutput["PERSON"]==None)):
            background_tasks.add_task(backtask,data)
    return jsonOutput