import pandas as pd
import numpy
from time import time
import csv
import gc
import os
def make_popularity_csv(csvName,state,yearrange):
    df = pd.read_csv(csvName)
    names = df['elector_name'].values
    nameDict = {}
    for name in names:
        for part in name.split(" "):
            nameDict[part] = nameDict.get(part,0)+1 
    sortedNames = sorted(nameDict.items(),key = lambda x:x[1],reverse=True)
    nameDict = {}
    gc.collect()
    total = 0 
    for tup in sortedNames:
        total += int(tup[1])
    namesWithSuffixArray = []
    for tup in sortedNames:
        namesWithSuffixArray.append([tup[0],tup[1],total,yearrange,state])
        total -= int(tup[1])
    
    
    with open(csvName.split(".")[0]+'_popularity.csv','w',newline='',encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name','Popularity','Suffix Sum','Year Range','State'])
        writer.writerows(namesWithSuffixArray)
    
import csv
def divideAccordingToBirthYear(CSV):
    mydict = {}
    with open(CSV,'r',newline='',encoding='UTF-8') as F:
        reader = csv.reader(F)
        for i,row in enumerate(reader):
            if(i!=0):
                age = int(row[7])

                currYear= int(row[12])
                birthYear = currYear-age
                fileno = 0
                if(float(birthYear)%5==0):
                    fileno = int((birthYear-1900)/5)
                else:
                    fileno = int((birthYear-1900)/5)+1 
                print('age '+str(age)+' fileno :'+str(fileno)+' currYear :'+str(currYear))
                if fileno in mydict:
                    mydict[fileno].append(row)
                else :
                    mydict[fileno] = [row]
    return mydict
def noToFile(fileno):
    return str(1900+(fileno*5))+"_"+str(1900+fileno*5+4)+".csv"
def dictToFiles(mydict,state):
    for key in mydict.keys():
        filename = noToFile(key)
        with open(filename,'w',newline='',encoding='UTF-8') as f:
            writer = csv.writer(f)
            writer.writerow(['global_number','number','voter_id', 'elector_name','father_or_husband_name','has_husband','house_no',
                             'age','sex','ac_name','parl_constituency','part_no','year','state','filename','main_town',
                             'police_station','mandal','revenue_division','district','pin_code','polling_station_name',
                             'polling_station_address','net_electors_male','net_electors_female','net_electors_third_gender',
                             'net_electors_total','change'])
            writer.writerows(mydict[key]) 
        make_popularity_csv(filename,state,filename.split(".")[0])
            
def csvYearWisePopularity(CSV,opCSVName,state):
    mydict = divideAccordingToBirthYear(CSV)
    dictToFiles(mydict,state)
    dfLst = []
    for key in mydict.keys():
        dfLst.append(pd.read_csv(noToFile(key).split(".")[0]+'_popularity.csv'))
    make_popularity_csv(CSV,'jk','all')
    dfLst.append(pd.read_csv(CSV.split(".")[0]+'_popularity.csv'))
    cc = pd.concat(dfLst)
    cc.to_csv(opCSVName,index=False)
    for key in mydict.keys(): #Deletion of temporary files
        filename1 = noToFile(key)
        filename2 = noToFile(key).split(".")[0]+'_popularity.csv'
        if(os.path.isfile(filename1)):
            os.remove(filename1)
        if(os.path.isfile(filename2)):
            os.remove(filename2)
            

    
    
