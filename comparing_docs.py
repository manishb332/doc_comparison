import pandas as pd
from fuzzywuzzy import fuzz

def compare(specs,comp_doc):
    specs_col=specs.columns
    comp_cols=comp_doc.columns
    l1 = []
    l2 = []
    ind=False
    for idx1, row1 in specs.iterrows():
        ind=False
        ratio=0
        app_list=[]
        conv=""
        for idx, row in comp_doc.iterrows():
            #print(row[0])
            if str(row[0]).find("Hydroxymethylfurfural")!=-1:
                row[0]= "HMF"
            elif str(row[0]).lower().find("sulfur dioxide")!=-1:
                row[0]= "SO2"
            if fuzz.ratio(row[0].lower(),row1[0].lower())>ratio and ((row[0].lower()).find(row1[0].lower())!=-1 or (row1[0].lower()).find(row[0].lower())!=-1):
                if row1["Unit"].lower().strip()!=row["UOM"].lower().strip() and row["UOM"].lower().strip()!="":
                    conv=row1["Unit"]
                ratio=fuzz.ratio((row[0].lower()),row1[0].lower())
                if str(row['Min']).strip()=='' or str(row['Min']).strip()=='-':
                    val=str(row['Max'])
                #print(row['Max'])
                    if conv!="":
                        if conv=="%":
                            val=row['Max'] + "/10000"
                        else:
                            val=row['Max'] + "*10000"
						
                    cond=""
                    if str(row1['Range/Attribute']).strip().find("<=")!=-1:
                        cond=val+">=" + str(row1['Range/Attribute']).replace("<=","").strip()
							
                    #app_list=[row['Property'],cond]
                elif row['Min']!=pd.np.nan:
                    val=str(row['Min'])
                    if conv!="":
                        if conv=="%":
                            val=row['Min'] + "/10000"
                        else:
                            val=row['Min'] + "*10000"
                    cond=""
                    if str(row1['Range/Attribute']).strip().find(">=")!=-1:
                        cond=val+"<=" + str(row1['Range/Attribute']).replace(">=","").strip()
							
                app_list=[row['Property'],cond]
            else:
                l1.append(row[0])			
        if ratio>0:
            ind=True
            #l1.append(row[0])
            l2.append(app_list)
        #else:
            #l1.append(row[0])
            
    #print(l1)
    #s = set(l1)
    #s = list(s)
    df3 = pd.DataFrame(l2, columns=['Property', 'Criteria'])
    #print(l2)
    df3['Within_limits'] = df3.apply(lambda x : eval(x['Criteria']),axis=1)
    s = set(l1) - set(df3['Property'])
    s = list(s)
    s = pd.DataFrame(s, columns=['Property'])
    s['Within_limits'] = "Not Found"
    #print(s)
    df3 = df3.append(s, sort=False)
    df3=df3.sort_values(["Property"])
    #print(df3)
    return df3
