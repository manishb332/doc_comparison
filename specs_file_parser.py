import PyPDF2
import pandas as pd

def parse_specs(filetext):
    
    p_text1 = []
    for i in range(0,len(filetext)):
        #print(filetext[i][17:])
        p_text1.append(filetext[i][35:])
    
    for i in range(0,len(p_text1)):
        for j in range(len(p_text1[i])-1,0,-1):
            if p_text1[i][j].strip()!="" and p_text1[i][j-1].strip()!="":
                p_text1[i][j-1] = p_text1[i][j-1] + p_text1[i][j]
                p_text1[i][j] = "rmvths"
    
    from itertools import chain
    p_text2 = list(chain(*p_text1))
    #p_text3 = list(chain.from_iterable(p_text1))
    
    p_text2 = [ele for ele in p_text2 if ele.strip()!='rmvths']
    
    for j in range(len(p_text2)-1,0,-1):
        #print(p_text2[j])
        if p_text2[j].strip()!="" and p_text2[j-1].strip()!="":
            p_text2[j-1] = p_text2[j-1] + p_text2[j]
            p_text2[j] = "rmvths"
    p_text3 = [ele for ele in p_text2 if ele.strip()!='rmvths']
    
    for j in range(len(p_text3)-1,0,-1):
        if p_text3[j].strip()!="" and p_text3[j-1].strip()=="" and p_text3[j-2].strip()!="":
            p_text3[j-1] = "rmvths"
    p_text4 = [ele for ele in p_text3 if ele.strip()!='rmvths']
    
    #Treating 2 gaps only
    for j in range(len(p_text4)-1,0,-1):
        if p_text4[j].strip()!="" and p_text4[j-1].strip()==""  and p_text4[j-2].strip()=="" and p_text4[j-3].strip()!="":
            p_text4[j-1] = "rmvths"
    p_text5 = [ele for ele in p_text4 if ele.strip()!='rmvths']
    
    #Treating 3 gaps only
    for j in range(len(p_text5)-1,0,-1):
        if p_text5[j].strip()!="" and p_text5[j-1].strip()=="" and p_text5[j-2].strip()=="" and p_text5[j-3].strip()=="" and p_text5[j-4].strip()!="":
            p_text5[j-2] = "rmvths"
            #p_text6[j-1] = "rmvths"
    p_text6 = [ele for ele in p_text5 if ele.strip()!='rmvths']
    
    #Treating 4 gaps only
    for j in range(len(p_text6)-1,0,-1):
        if p_text6[j].strip()!="" and p_text6[j-1].strip()=="" and p_text6[j-2].strip()=="" and p_text6[j-3].strip()=="" and p_text6[j-4].strip()=="" and p_text6[j-5].strip()!="":
            p_text6[j-2] = "rmvths"
            p_text6[j-1] = "rmvths"
    p_text7 = [ele for ele in p_text6 if ele.strip()!='rmvths']
    
    #Combining when starts and ends with / and when ends with -
    for i in range(len(p_text7)-1,0,-1):
        if p_text7[i].startswith('/'):
            p_text7[i-1] = p_text7[i-1] + p_text7[i]
            p_text7[i] = "rmvths"
        elif p_text7[i].endswith('/'):
            p_text7[i] = p_text7[i] + p_text7[i+1]
            p_text7[i+1] = "rmvths"
        elif p_text7[i].endswith('-'):
            p_text7[i] = p_text7[i] + p_text7[i+1]
            p_text7[i+1] = "rmvths"
    p_text8 = [ele for ele in p_text7 if ele.strip()!='rmvths']
    
    #Combining edition
    for i in range(0,len(p_text8)):
        if p_text8[i].lower().find('edition')!=-1 and p_text8[i-1].lower().find('edition')!=-1:
            p_text8[i-1]=p_text8[i-1]+p_text8[i]
            p_text8[i]='rmvths'
    p_text9 = [ele for ele in p_text8 if ele.strip()!='rmvths']
    
    
    
    #Check for 3 gaps after Fructose
    
    
    #Hard-coding
    for i in range(0,len(p_text9)):
        if p_text9[i].lower().find('sulfur dioxide')!=-1 and p_text9[i+1].strip()=="":
            p_text9[i+1]='rmvths'
    p_text10 = [ele for ele in p_text9 if ele.strip()!='rmvths']
    
    for i in range(0,len(p_text10)):
        if p_text10[i].lower().find('karl fischer')!=-1:
            p_text10[i+1]='rmvths'
            p_text10[i+4]='rmvths'
    p_text11 = [ele for ele in p_text10 if ele.strip()!='rmvths']
    
    for i in range(0,len(p_text11)):
        if p_text11[i].lower().find('dextrose (glucose')!=-1 and p_text11[i+1].strip()=="":
            p_text11[i+1]='rmvths'
    p_text12 = [ele for ele in p_text11 if ele.strip()!='rmvths']
    
    #print(p_text11)
    substring1 = "Quality Inspection Plan (Official Specification Values)"
    substring2 = "Product Composition / Labeling"
    #print(p_text12)
    if substring1 in p_text12:
        l = p_text12.index(substring1)
        l2 = p_text12.index(substring2)
        x = p_text12[l+2:l2-2]
    
    col_count=0
    for i in range(0,len(x)):
        col_count=col_count+1
        if col_count==6:
            x[i]="*****"+x[i]
            col_count=1
    
    out='|'.join(x)
    out1=out.split("*****")
	
    #print(final_out1)
    #with open('final_output.txt','w') as f:
    #    f.write('\n'.join(out1))
    return out1