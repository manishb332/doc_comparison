import json
import pickle
import pandas as pd
import PyPDF2
import camelot
import os
import io
from specs_file_parser import parse_specs
from company_doc_parser import parse_doc
from comparing_docs import compare
from Extractor import *
from bottle import get, post,run, request, response, static_file,BaseRequest
from azure.storage.blob import BlockBlobService
from gremlin_python.driver import client, serializer
from fuzzywuzzy import fuzz

BaseRequest.MEMFILE_MAX = 1024*1024*1024 

global block_blob_service;
global client;

def convert_to_html(df):
    style="width:100%;"
    html="<table id='result_tab' border=1 style='"+style+"'><thead><tr><th>"+"</th><th>".join(df.columns)+"</th></tr></thead>"
    for idx,row in df.iterrows():
        html=html+"<tr><td>"+"</td><td>".join(row)+"</td></tr>"
    html=html+"</table>"
    return html


def transform_output(out_param,out_file,type):
    if type=="P":
        cols=['Parameter','Company','Min','Max','UOM']
    elif type=="C":
        cols=['Company','Parameter','Min','Max','UOM']
    out_df=pd.DataFrame(columns=cols)
    for i in range(0,len(out_param)):
        if type=="P":
            p_name=out_param[i][0]
            p_attr=out_param[i][1].split("##sep##parameter##sep##")
            p_attr=["".join(p).split("##sep##") for p in p_attr]
            
            p_comp=out_file[i][1].split("##sep##filename##sep##")
            p_comp=["".join(p).split("##sep##") for p in p_comp]
            
            for i in range(0,len(p_attr)):
                p_comp[i]=[p for p in p_comp[i] if p.strip()!="filename"]
                #print(p_comp[i])
                comp='<a href="'+p_comp[i][2]+'">'+p_comp[i][0]+'</a>'     
                if len(p_attr[i])==2:    
                    print(p_attr[i])
                    if p_attr[i][1].find(">=")!=-1:
                        min=p_attr[i][1].replace(">=","").strip()
                        max=""
                    elif p_attr[i][1].find("<=")!=-1:
                        max=p_attr[i][1].replace("<=","").strip()
                        min=""
            
                    if str(p_attr[i][1]).find(".")==-1 or int(str(p_attr[i][1]).split(".")[0].replace(">=","").replace("<=","").strip())>0:
                        unit="%"
                    else:
                        unit="ppm"
                elif len(p_attr[i])==3:
                    min=p_attr[i][0]
                    max=p_attr[i][1]
                    unit=p_attr[i][2]
                else:
                    raise ValueError
                p_attr[i]=[p_name,comp,min,max,unit]
                out_df.loc[len(out_df)]=p_attr[i]
        elif type=="C":
            p_attr=out_param[i][1].split("##sep##parameter##sep##")
            p_attr=["".join(p).split("##sep##") for p in p_attr]
            p_comp=out_file[i][1].split("##sep##filename##sep##")
            p_comp=["".join(p).split("##sep##") for p in p_comp]
            p_comp=[p for p in p_comp[0] if p.strip()!="filename"]
            comp='<a href="'+p_comp[2]+'">'+p_comp[0]+'</a>'           
            for i in range(0,len(p_attr)):
                p_attr[i]=[p for p in p_attr[i] if p.strip()!="parameter"]
                #print(p_attr[i])
                p_name=p_attr[i][0]				
                if len(p_attr[i])==2:    
                    if p_attr[i][1].find(">=")!=-1:
                        min=p_attr[i][1].replace(">=","").strip()
                        max=""
                    elif p_attr[i][1].find("<=")!=-1:
                        max=p_attr[i][1].replace("<=","").strip()
                        min=""
            
                    if str(p_attr[i][1]).find(".")==-1 or int(str(p_attr[i][1]).split(".")[0].replace(">=","").replace("<=","").strip())>0:
                        unit="%"
                    else:
                        unit="ppm"
                elif len(p_attr[i])==4:
                    min=p_attr[i][1]
                    max=p_attr[i][2]
                    unit=p_attr[i][3]
                else:
                    raise ValueError
                p_attr[i]=[comp,p_name,min,max,unit]
                out_df.loc[len(out_df)]=p_attr[i]
    if len(out_df['Company'].unique())==1:
	    out_df=out_df.drop(['Company'], axis=1)
    return convert_to_html(out_df)
	
def find_param_match(text):
    param_list=["MOISTURE","DENSITY","SCREEN ON US#20","SCREEN ON US#30","SCREEN ON US#40","SCREEN ON US#60","SCREEN THRU US#100","COLOR, RBU","DEXTROSE", "FRUCTOSE",  "ODOR",  "FLAVOR",  "BACTERIA TOTAL",  "OSMOPHILIC MOLD",  "OSMOPHILIC YEAST",  "SO2",  "HMF",  "ASH",  "CHLORIDE",  "ARSENIC",  "SULFATE",  "HEAVY METALS",  "LEAD"]
    
    max_ratio=0
    ind=0
    for i in range(0,len(param_list)):
        if str(text).find("Hydroxymethylfurfural")!=-1:
            text= "HMF"
        elif str(text).lower().find("sulfur dioxide")!=-1:
            text= "SO2"
    	
        ratio=fuzz.ratio(text.lower(),param_list[i].lower())
        if ratio>max_ratio:
            max_ratio=ratio
            ind=i
    
    if max_ratio>0:
        return param_list[ind].lower()
    else:
        return text.lower()
    

def create_graph(filename,file_url,data):
    global client
    #print(filename)
    if(filename=="Krystar 300 Crystalline Spec.pdf"):
        label_text="Tate and Lyle"
        type="S"
    elif(filename=="10197805_01203.pdf"):
        label_text="CSM Bakery Solutions"
        type="R"
    elif(filename=="R000260130.pdf"):
        label_text="Kellogg\'s"
        type="R"
    elif(filename=="SP-0085; Rev_ J - Fructose Crystalline  Bag  - 15009.pdf"):
        label_text="Post"
        type="R"
    else:
        label_text="Pepsico"
        type="R"

    client.submit('g.addV("filename").property("label_text","' + str(label_text) + '").property("file_type","' + str(type) +'").property("id","' + str(filename) + '").property("paramName","' + str(filename) + '").property("url","'+str(file_url)+'")').all().result()
    columns=data.columns
    for index, row in data.iterrows():
        row=row.tolist()
        query="g.addV('parameter').property('paramName','"+str(row[0])+"')"
        for i in range(1,len(columns)):
            if isinstance(row[i],str):
                query=query+".property('"+columns[i]+"','"+str(row[i]).lower()+"')"
            else:
                query=query+".property('"+columns[i]+"',"+str(row[i])+")"
        query=query+".property('mappedParam','"+find_param_match(row[0])+"')"
        callback=client.submit(query).all().result()
        callback = client.submit("g.V().has('paramName','" + str(filename) + "').addE('contains').to(g.V().has('paramName','" + str(row[0]) + "'))").all().result()

def save_to_blob(filename):
    global block_blob_service
    blob_list=[blob.name for blob in block_blob_service.list_blobs(container_name)]
    flag="exists"
    if filename not in blob_list:
        flag="new"
        block_blob_service.create_blob_from_path(container_name,filename,os.path.join(os.getcwd(),"temp",filename))
        blob_source_url = block_blob_service.make_blob_url(container_name, filename)
        os.remove(os.path.join(os.getcwd(),"temp",filename))
    else:
        blob_source_url = block_blob_service.make_blob_url(container_name, filename)
    return blob_source_url,flag

@get("/")
def get_index():
    return static_file("homepage.html", root="static")
	
@post("/specs/<filename>")
def get_specs(filename):
    print("Parsing Specification Document......")
    p_text=[]
    file_url=""
    file_type=""
    with io.BytesIO(request.body.read()) as open_pdf_file:
        with open(os.path.join("temp",filename),"wb") as file:
            file.write(open_pdf_file.read())
        file_url,file_type=save_to_blob(filename)
        if file_type=="new":
            read_pdf = PyPDF2.PdfFileReader(open_pdf_file)
            number_of_pages = read_pdf.getNumPages()
            global specs
            for i in range(0,number_of_pages):
                pg4 = read_pdf.getPage(i) 
                p = pg4.extractText()
                p = p.splitlines()
                p_text.append(p)
    if file_type=="new":
        out1=parse_specs(p_text)
        final_out=[]
        for ele in out1:
            final_out.append(ele[0:len(ele)-1].split("|"))
        specs=pd.DataFrame(final_out[1:],columns=final_out[0])	
        create_graph(filename,file_url,specs)
    return 'File Uploaded to the below path : <br>&nbsp;&nbsp;&nbsp;<a href="'+file_url.replace(" ","%20")+'">'+file_url.replace(" ","%20")+'</a>'

@post("/check/<filename>")
def get_doc(filename):
    print("Parsing Company Document.....")
    with io.BytesIO(request.body.read()) as open_pdf_file:
        with open(os.path.join("temp",filename),"wb") as file:
            file.write(open_pdf_file.read())
    file_url,file_type=save_to_blob(filename)
    if file_type=="new":
        global comp_doc
        comp_doc=extractor(filename)
        create_graph(filename,file_url,comp_doc)
    return 'File Uploaded to the below path : <br>&nbsp;&nbsp;&nbsp;<a href="'+file_url.replace(" ","%20")+'">'+file_url.replace(" ","%20")+'</a>'

@get("/search")
def analyze():
    print("Searching in GraphDB")
    
    text = request.query['q'].lower()
    comp_list = ["Tate and Lyle", "CSM Bakery Solutions", "Kellogg's", "Post", "Pepsico"]
    param_list=["MOISTURE","DENSITY","SCREEN ON US#20","SCREEN ON US#30","SCREEN ON US#40","SCREEN ON US#60","SCREEN THRU US#100","COLOR, RBU","DEXTROSE", "FRUCTOSE",  "ODOR",  "FLAVOR",  "BACTERIA TOTAL",  "OSMOPHILIC MOLD",  "OSMOPHILIC YEAST",  "SO2",  "HMF",  "ASH",  "CHLORIDE",  "ARSENIC",  "SULFATE",  "HEAVY METALS",  "LEAD"]
	
    searched_company=[c for c in comp_list if text.find(c.lower())!=-1 ]
    searched_param=[p for p in param_list if text.find(p.lower())!=-1 ]
	
    if len(searched_param)>0 and len(searched_company)==0:
        callback_param=[]
        callback_file=[]
        for param in searched_param:
            callback_param.append([param,"##sep##".join(client.submit('g.V().has("mappedParam","'+ param.lower() +'").values("label","Range/Attribute","Min","Max","UOM")').all().result())])
            callback_file.append([param,"##sep##".join(client.submit('g.V().has("mappedParam","'+ param.lower() +'").inE().outV().values("label","label_text","file_type","url")').all().result())])
        response="Here is the output to your query :<br> " + transform_output(callback_param,callback_file,"P")
		
    elif len(searched_param)==0 and len(searched_company)>0:
        callback_param=[]
        callback_file=[]
        for param in searched_company:
            callback_param.append([param,"##sep##".join(client.submit('g.V().has("label_text","'+ param +'").outE().inV().values("label","paramName","Range/Attribute","Min","Max","UOM")').all().result())])
            callback_file.append([param,"##sep##".join(client.submit('g.V().has("label_text","'+ param +'").values("label","label_text","file_type","url")').all().result())])
        response=transform_output(callback_param,callback_file,"C")
        if len(searched_company)==1:
            text="Here are the results from <a href='" + callback_file[0][1].split("##sep##")[3] + "'>"+searched_company[0]+"</a> document :<br>"
        else:
            text="Here is the output to your query :<br>"
        response=text+response	
    elif len(searched_param)>0 and len(searched_company)>0:
        pass
    else:
	    response="Sorry.Couldn't understand your query!!!!!"
	
    return response
	
if __name__ == "__main__":
    
    #for BLOB storage
    block_blob_service = BlockBlobService(account_name='aiblob003', account_key='fgzupeMhtpA56k3F4G4ny0mIS3jD4LAU5KeLIz44svymnlMUXk0mnbqSXS+NdNvnAwLbTL4gWJZ/b+tKROJvdw==')
    container_name ='blobcontainer'

    #for GraphDB
    global client	
    client = client.Client('wss://aicosmos2.gremlin.cosmosdb.azure.com:443','g', 
        username="/dbs/doc_compare/colls/docs", 
        password="o3dprlg6hDXxcSsKQRcge8ySqHzjHuwXEYwJ8FUp8oZHsPE0GBbsVHZIgZ48d642jTHEkhOt2C71agXv8vLtSg==",
        message_serializer=serializer.GraphSONSerializersV2d0()
    )
    run(host="0.0.0.0",port=8080)
