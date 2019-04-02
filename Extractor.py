def extractor(pdf):
    import camelot
    import pandas as pd
    file=pdf
    if pdf=="TATE AND LYLE LAFAYETTE 17438FRU CRYSTALLINE FRUCTOSE 9.26.18.pdf":
        tables=camelot.read_pdf(file, pages='2,3')
        cols=["Property", "Test Method(s)", "Target", "Min", "Max", "Supplier Test Frequency","Required on COA"]
        tab1=tables[3].df
        tab2=tables[5].df
        tab=pd.concat([tab1,tab2])
        tab=tab.reset_index(drop=True)        
        tab.columns=cols
        cols2=["Property","Min","Max"]
        tab=tab.filter(cols2)#[tab.columns.isin(cols2)]
        tab["UOM"]=["%" if x.find("%")!=-1 else "ppm" for x in tab["Property"]]
        return(tab)
    elif pdf=="R000260130.pdf":
        tables=camelot.read_pdf(file, pages='2',split_text=True)
        tab=tables[0].df
        tab.columns=["Var"]
        
        Property=[]
        Min=[]
        Max=[]
        UOM=[]

        for i in tab["Var"][1:]:
            vals=i.split('\n')
            #print(vals)
            Property.append(vals[0])
            try:
                float(vals[2])
                Min.append(vals[2])
            except:
                Min.append("")

            Max.append(vals[4])
            UOM.append(vals[5])

        check=pd.DataFrame({'Property':Property,'Min':Min,'Max':Max,'UOM':UOM})
        check.iloc[2][0]=check.iloc[2][0]+" Dioxide (SO2)"
        #tab["Property"]=Property
        #tab["Min"]=Min
        #tab["Max"]=Max
        #tab["UOM"]=UOM
        #del tab["Var"]
        #tab.iloc[2][0]=tab.iloc[2][0]+" Dioxide (SO2)"
        #tab = pd.DataFrame(check)
        return(check)
    elif pdf=="SP-0085; Rev_ J - Fructose Crystalline  Bag  - 15009.pdf":
        tables=camelot.read_pdf(file, pages='3')
        tab=tables[0].df
        tab.columns=list(tab.iloc[10])
        tab=tab.iloc[11:20]
        tab=tab.reset_index(drop=True)
        del tab["Analysis Method"]
        
        Maximum=[]
        Minimum=[]
        UOM=[]
        for i in tab["Acceptance Criteria"]:
            if i.find("Maximum")!=-1:
                Maximum.append(i.split(" ")[0])
                Minimum.append("")
            else:
                Maximum.append("")
                Minimum.append(i.split(" ")[0])
            if i.split(" ")[0].find("%")!=-1:
                UOM.append("%")
            else:
                UOM.append("ppm")
        tab["Max"]=Maximum
        tab["Min"]=Minimum
        tab["UOM"]=UOM
        tab["Max"]=[x.replace("%","") for x in tab["Max"]]
        tab["Min"]=[x.replace("%","") for x in tab["Min"]]
        del tab["Acceptance Criteria"]
        return(tab)
    elif pdf=="10197805_01203.pdf":
        tables2=camelot.read_pdf(file, pages='4')
        tab=tables2[1].df
        vals=tab.iloc[2][0].split("\n")+tab.iloc[4][0].split("\n")
        vals=[x for x in vals if x!=" "]
        vals2=[x for x in vals if vals.index(x)%2==0]
        vals3=[x for x in vals if vals.index(x)%2!=0]

        tab=pd.DataFrame({"Property":vals2,"Test":vals3})
        tab["Test"]=[x.replace("%","") for x in tab["Test"]]

        Minimum=[]
        Maximum=[]

        for i in tab["Test"]:
            if i.find("<=")!=-1:
                Maximum.append(i.replace("<=",""))
                Minimum.append("")
            else:
                Minimum.append(i.replace(">=",""))
                Maximum.append("")

        tab["Min"]=Minimum
        tab["Max"]=Maximum
        del tab["Test"]
        tab["UOM"]="%"
        return(tab)
