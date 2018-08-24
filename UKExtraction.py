import pytesseract as pt
from PIL import Image
#from polyglot.text import Text
import subprocess
from indic_transliteration import sanscript 
from indic_transliteration.sanscript import transliterate
#from multiprocessing import Pool
import multiprocessing
import re
import csv
import time
import os
from pathos.multiprocessing import ProcessingPool
from PyPDF2 import PdfFileWriter, PdfFileReader
def dealWithHouses(house):
    """
    Checks if there is a "ling" part inside the name. If yes, then returns the part that is before it. Then
    transliterates the result. Then converts to normal english.
    """
    house = house.split("लिंग")[0]
    ophouse = transliterate(house,sanscript.DEVANAGARI,sanscript.ITRANS)            
    for i in mapping:
        ophouse = ophouse.replace(i[0],i[1])
    ophouse  = saneHouse(ophouse.strip())
    return ophouse
def saneHouse(house):
    allowed = ['\\','/',':','-',' ']
    for c in house:
        if(not (c.isalpha() or c.isdigit() or c in allowed)):
            return '#####'+house
    return house  
mapping = [('bI.', 'B.'),
 ('sI.', 'C.'),
 ('DI.', 'D.'),
 ('epha.', 'F.'),
 ('jI.', 'G.'),
 ('echa.', 'H.'),
 ('ke.', 'K.'),
 ('ela.', 'L.'),
 ('ema.', 'M.'),
 ('em.', 'M.'),
 ('ena.', 'N.'),
 ('o.', 'O.'),
 ('pI.', 'P.'),
 ('Ara.', 'R.'),
 ('esa.', 'S.'),
 ('TI.', 'T.'),
 ('yU.', 'U.'),
 ('vI.', 'V.'),
 ('DablyU.', 'W.'),
 ('eksa.', 'X.'),
 ('vAI.', 'Y.'),
 ('jeDa.', 'Z.'),
 ('kyU.', 'Q.'),
 ('je.', 'J.'),
 ('AI.', 'I.'),
 ('I.', 'E.'),
 ('e.', 'A.'),
 ('ai.', 'A'),
 ('bI', 'B.'),
 ('sI', 'C.'),
 ('DI', 'D.'),
 ('epha', 'F.'),
 ('jI', 'G.'),
 ('echa', 'H.'),
 ('ke', 'K.'),
 ('ela', 'L.'),
 ('ema', 'M.'),
 ('em', 'M.'),
 ('ena', 'N.'),
 ('o', 'O.'),
 ('pI', 'P.'),
 ('Ara', 'R.'),
 ('esa', 'S.'),
 ('TI', 'T.'),
 ('yU', 'U.'),
 ('vI', 'V.'),
 ('DablyU', 'W.'),
 ('eksa', 'X.'),
 ('vAI', 'Y.'),
 ('jeDa', 'Z.'),
 ('kyU', 'Q.'),
 ('je', 'J.'),
 ('AI', 'I.'),
 ('I', 'E.'),
 ('e', 'A.')]           
           
def dealWithID(ID):
    """
    Returns the ID if it is of the correct format. Otherwise, if only a problem of 0s recognized as Os, then it corrects
    them. Otherwise, return None.
    """
    newID = ID[:3]+ID[3:].replace('O','0')
    #print(newID)
    if not goodID(ID):
        if goodID(newID):
            return newID
        elif(len(newID)==11 and newID[3]=='0' and newID[4]=='0'):
            noOID = newID[:3]+newID[4:]
            if goodID(noOID):
                return noOID
            else:
                return '#####'+ID
        else:
            return '#####'+ID
    return ID
def goodID(ID):
    l = len(ID) 
    if(l!=10):
        return False
    else:
        for c in range(3):
            if not ID[c].isalpha():
                return False
        for c in range(3,10):
            if not ID[c].isdigit():
                return False
    return True                
def sane(im,rangeTuple,y,start,end):
    """
    The input is not a file on disk, but a file in memory that has already been opened by Image.open('path')
    Checks whether there is a black line of length (end-start) at the height y in a grayscale image.
    """
    #im = Image.open(pageImage)
    print(im.n_frames)
    lst = []
    for pg in range(rangeTuple[0],rangeTuple[1]+1):
        acc = True 
        im.seek(pg)
        pix = im.load()
        for i in range(start,end):
            if(pix[i,y][0]!=0 or pix[i,y][1]!=255):
                acc = False 
                break
        if(acc):
            lst.append(pg)
    return lst
def cropperList(im,rangeTuple,rows,inX,inY,dimX,dimY,saneY,saneStart,saneEnd):
    """
    im: The PIL Image object
    rangeTuple: The range of pages to be processed 
    rows : Number of rows of boxes
                    inX: The x coordinate of the starting row
                    inY:The y-coordinate of the starting row
                    dimX: The length of the row
                    dimY: The height of the row
                    saneY : To check a black line at height saneY
                    saneStart : Line starts from saneStart x-coordinate
                    saneEnd : Line ends at saneEnd x-coordinate
    """
    sanePages = sane(im,rangeTuple,saneY,saneStart,saneEnd)
    lst = []
    for pg in sanePages:
        im.seek(pg)
        count = 0 
        for i in range(rows):
            y = inY+i*dimY
            crp1 = im.crop((inX,y,dimX+inX,dimY+y))
            crp1.load()
            #crp1.save(str(count)+".tiff")
            lst.append(crp1)
            count+=1
    return lst
def tessList(name_lst):
    rows = []
    indicesWithErrors = []
    for i,row in enumerate(name_lst):
        tessStart = time.time()
        op = pt.image_to_string(row,lang='hin+eng',config='--psm 7')
        tessEnd = time.time()
        print("row number :"+str(i))
        try:
            intermediate = op.split("पति") if len(op.split("पति"))!=1 else op.split("पिता")
            #print(str(intermediate))
            res = intermediate[1].strip().split(" ")
            #print(str(res))
            name = intermediate[0].strip()
            #print("name :"+name)
            gender = 'F' if re.match('म',res[len(res)-2])!=None else 'M'
            #print("gender :"+gender)
            age = res[len(res)-1]
            nameCorrect = nameCheck(name,'hin')
            if not nameCorrect:
                raise Exception('Not hindi') 
            if int(age) not in range(18,111):
                raise Exception('Age incorrect')
            opname = transliterate(name,sanscript.DEVANAGARI,sanscript.ITRANS)            
            rows.append([opname,age,gender])
        except:
            indicesWithErrors.append(i)
            print("Had errors.")
        print("Took time :"+str(tessEnd-tessStart))
    return rows,indicesWithErrors
def getPartNumber(im,coord,pg):
    im.seek(pg)
    crp = im.crop(coord)
    op =  pt.image_to_string(crp,lang='hin+eng',config='--psm 6')
    return '' if re.search('[0-9]+',op)==None else re.search('[0-9]+',op).group(0)
    
def cropperBox(im,rangeTuple,boxCoord,voterBoxCoord,boxNumberCoord,basePages):
    """
    im: Inputs an Image object
    rangeTuple: The range of pages to be checked, in a tuple format, example :(2,5)
    dimX: length of the box in pixels
    dimY: height of the box in pixels
    inX: The x-coordinate of the first box
    inY: The y-coordinate of the first box
    addX: Number of pixels to add to the current x-coordinate to get the next box' x-coordinate
    addY: Number of pixels to add to the current y-coordinate to get the next box' y-coordinate
    rows: Number of rows of boxes in the file.
    cols: Number of cols in the file.
    saneY: The height of the line to be checked
    saneStart: The starting x-coordinate of the line to be checked
    : The ending x-coordinate of the line to be checked
    boxNumberCoord: [dimX.dimY,inX,inY]
                      0    1    2   3  
    voterBoxCoord:   [dimX,dimY,inX,inY]
                        0    1   2   3
    boxCoord : [rows,cols,dimX,dimY,inX,inY,addX,addY,saneY,saneStart,saneEnd]
                       0    1    2    3    4   5   6    7     8      9         10
    basePages
    """
    #im = Image.open(file)
    print(im.n_frames)
    #im.load()
    sanePages = sane(im,rangeTuple,boxCoord[8],boxCoord[9],boxCoord[10])
    
    print(sanePages)
    lst = []
    s1 = time.time() 
    for pg in sanePages:
        im.seek(pg)
        count = 0 
        for i in range(boxCoord[0]):
            for j in range(boxCoord[1]):
                x = boxCoord[4]+j*boxCoord[6] 
                y = boxCoord[5]+i*boxCoord[7]
                x2 = voterBoxCoord[2]+j*boxCoord[6]
                y2 = voterBoxCoord[3]+i*boxCoord[7]
                x3 = boxNumberCoord[2]+j*boxCoord[6]
                y3 = boxNumberCoord[3]+i*boxCoord[7]
                crp1 = im.crop((x,y,boxCoord[2]+x,boxCoord[3]+y))
                crp2 = im.crop((x2,y2,voterBoxCoord[0]+x2,voterBoxCoord[1]+y2))
                crp3 = im.crop((x3,y3,boxNumberCoord[0]+x3,boxNumberCoord[1]+y3))
                crp3.save('boxN'+str(count)+'.tiff')
                box_number = pt.image_to_string(crp3,lang='eng',config='--psm 7').strip()
                if(box_number.split(" ")[0]!='#'):
                    lst.append((crp1,crp2,pg+basePages,box_number))
                count = count + 1
    s2 = time.time()
    print("Took :"+str(s2-s1)+" to create all cropBoxes") ;
    return lst
def tessBox(box_lst):#,pt,time,re,transliterate,sanscript):
    """
    box_lst : Input format : A list of lists, with each inner list being of the format:
        crp1: Cropped image of core box for each entry
        crp2: Cropped image of voter ID
        number: page number
        crp3: box_number
        
    The output of cropperBox is a list of Image objects, of boxes.
    """
    rows = []
    indicesWithErrors = []
    for i,box in enumerate(box_lst):
        boxStart = time.time()
        op = pt.image_to_string(box[0],lang='hin+eng',config='--psm 6')
        voter_id = pt.image_to_string(box[1],lang='eng',config='--psm 7')
        # box_number= pt.image_to_string(box[3],lang='eng',config='--psm 7')
        voter_id = dealWithID(voter_id)
        # voter_id = ''
        boxTess = time.time()
        print("box number :"+str(i))
        # try:
        # res = op.split("\n") 
        # res = [i for i in res if not i=='']
        # name_regional = (res[0].split("ः")[1] if len(res[0].split(":"))==1 else res[0].split(":")[1]).strip()
        # husband_or_father_regional = (res[1].split("ः")[1] if len(res[0].split(":"))==1 else res[1].split(":")[1]).strip()
        # house_number = ''
        # if(len(res[2].split(":"))>1):
            # house_number = res[2].split(":")[1].strip()
        # elif(len(res[2].split("ः"))>1):
            # house_number = res[2].split("ः")[1].strip()
        # if(re.match('[0-9/]+',house_number)==None):
            # house_number='' 
        # else:
            # house_number=re.match('[0-9/]+',house_number).group(0)
        
        # has_husband = 1 if (res[1].split("ः")[0] if len(res[0].split(":"))==1 else res[1].split(":")[0]).strip() == "पति" else 0
        # age = re.search('[0-9]+',res[len(res)-1]).group(0)
        
        # intermediate = res[len(res)-1].split(" ")
        # gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' #3 for other states, 4 for UK.
        # nameCorrect = nameCheck(name_regional,'hin')
        
        # if not nameCorrect:
            # raise Exception('Not hindi')   
        # if int(age) not in range(18,111):
            # raise Exception('Age incorrect')
        # opName = transliterate(name_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
        # opHusband_or_father = transliterate(husband_or_father_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
        # rows.append([opName,age,gender,opHusband_or_father,has_husband,house_number,voter_id,box[2],box[3],box[4],name_regional,husband_or_father_regional])    
        #
        try:
            res = op.split("\n") 
            res = [i for i in res if not i=='']
            name_regional = (res[0].split("ः")[1] if len(res[0].split(":"))==1 else res[0].split(":")[1]).strip()
            husband_or_father_regional = (res[1].split("ः")[1] if len(res[0].split(":"))==1 else res[1].split(":")[1]).strip()
            house_number = ''
            if(len(res[2].split(":"))>1):
                house_number = res[2].split(":")[1].strip()
            elif(len(res[2].split("ः"))>1):
                house_number = res[2].split("ः")[1].strip()
            house_number = dealWithHouses(house_number)
            
                # house_number=re.match('[0-9/]+',house_number).group(0)
            has_husband = 1 if (res[1].split("ः")[0] if len(res[0].split(":"))==1 else res[1].split(":")[0]).split(" ")[0].strip() == "पति" else 0
            age = re.search('[0-9]+',res[len(res)-1]).group(0)
            intermediate = res[len(res)-1].split(" ")
            gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' #3 for other states, 4 for UK.
            nameCorrect = nameCheck(name_regional,'hin')
            if not nameCorrect:
                raise Exception('Not hindi')   
            if int(age) not in range(18,111):
                raise Exception('Age incorrect')
            opName = transliterate(name_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            opHusband_or_father = transliterate(husband_or_father_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            rows.append([opName,age,gender,opHusband_or_father,has_husband,house_number,voter_id,box[2],box[3],name_regional,husband_or_father_regional])    
        except:
            indicesWithErrors.append(i)
            print("Had Errors.")
        boxEnd = time.time()
        print("    Box took :"+str(boxTess-boxStart))
    return rows,indicesWithErrors
def langRange(lang):
    if lang=='hin':
        return (2304,2431)
    elif lang=='guj':
        return (2688,2815)
    elif lang=='ori':
        return (2816,2943)
    elif lang=='gur':
        return (2560,2687)
    elif lang=='tam':
        return (2944,3071)
    elif lang=='tel':
        return (3072,3199)
    elif lang=='kan':
        return (3200,3327)
    elif lang=='mal':
        return (3328,3455)
def nameCheck(name,lang):
    div = name.strip().split(' ')
    tup = langRange(lang)
    for word in div:
        if ord(word[0]) not in range(tup[0],tup[1]+1):
            return False
    return True  
def cropAndOCR(im,rangeTuple,formatType,boxCoord,voterBoxCoord,boxNumberCoord,n_blocks,basePages):
    """
    im: The PIL Image object 
    rangeTuple: A tuple describing the range of the pages to be processed. Example (4,7)
    formatType: 'box' or 'list' 
	n_blocks: Number of blocks the box_lst must be divided. Basically number of concurrent processes.
    argv: if format is "list"
                    [rows,inX,inY,dimX,dimY,saneY,saneStart,saneEnd]
					rows : Number of rows of boxes
					inX: The x coordinate of the starting row
					inY:The y-coordinate of the starting row
					dimX: The length of the row
					dimY: The height of the row
					saneY : To check a black line at height saneY
                    saneStart : Line starts from saneStart x-coordinate
                    saneEnd : Line ends at saneEnd x-coordinate
                    if format is "box"
                    [rows,cols,dimX,dimY,inX,inY,addX,addY,saneY,saneStart,saneEnd]
                      0    1    2    3    4   5   6    7     8      9         10
                    rows : Number of rows of boxes
                    cols : Number of columns of boxes
                    dimX : width of the box (Excluding the non-needed stuff)
                    dimY : Height of the box 
                    inX : Starting x co-ordinate of the first instance
                    inY : Starting y co-ordinate of the first instance
                    addX : Addition in x-coordinate to reach the next box in the row
                    addY : Addition in y-coordinate to reach the next box in the column
                    saneY : To check a black line at height saneY
                    saneStart : Line starts from saneStart x-coordinate
                    saneEnd : Line ends at saneEnd x-coordinate
    n_blocks: Maximum number of names to keep in buffer at a time
    argv2: Additional arguments needed by cropperBox:
        partCoords: a size-4 tuple describing the dimensions of the block of the page that contains the part number
        dimX2: x-dimension for voter ID
        dimY2: y-dimension for Voter ID
        inX2: starting x-coordinate for Voter ID
        inY2: starting y-coordinate for Voter ID
        dimX3: x-dimension for box number
        dimY3: y-dimension for box number
        inX3 : starting x-coordinate for box number
        inY3 : starting y-coordinate for box number
    """
    genStart = time.time()
    if(formatType=='box'):
        st = time.time()
        box_lst = cropperBox(im,rangeTuple,boxCoord,voterBoxCoord,boxNumberCoord,basePages)
        en = time.time()
        print("Time for cropping :"+str(en-st))
        names_lst = []
        boxesWithErrors = []
        box_lst_divided = []
        if(len(box_lst)<n_blocks):
            box_lst_divided.append(box_lst)
        else:
            for l in chunks(box_lst,int(len(box_lst)/n_blocks)):
                box_lst_divided.append(l)
        pool = ProcessingPool()     
        results = pool.map(tessBox,box_lst_divided)
        for result in results:
            names_lst+=result[0] 
            boxesWithErrors+=result[1]
        en2 = time.time() 
        print("Time to OCR :"+str(en2-en))
    elif (formatType=='list'):
        st = time.time()
        row_lst = cropperList(im,rangeTuple,argv[0],argv[1],argv[2],argv[3],argv[4],argv[5],argv[6],argv[7])
        en = time.time()
        print("Time for cropping :"+str(en-st))
        names_lst = []
        boxesWithErrors = []
        row_lst_divided = []
        for l in chunks(row_lst,int(len(row_lst)/n_blocks)):
            row_lst_divided.append(l)
        pool = ProcessingPool()
        results = pool.map(tessList,row_lst_divided)
        for result in results:
            names_lst+=result[0]
            boxesWithErrors+=result[1]
        en2 = time.time()
        print("Time to OCR :"+str(en2-en))
    genEnd = time.time()
    print("Total time = "+str(genEnd-genStart))
    return names_lst
def dealWithFirstPage(im,coords):
    """
    im: Image object 
    coords: List of size-4 tuples. Order: Box-1 containing mandal name, pin code etc.
                                          Box-2 polling station name
                                          Box-3 polling station address
                                          Box-4 net electors male
                                          Box-5 net electors female
                                          Box-6 net electors third gender
                                          Box-7 total electors
    """
    crpLst = []    
    for c in coords:
        crpLst.append(im.crop(c))
    resAll = []
    for i in crpLst:
        resAll.append(pt.image_to_string(i,lang='hin+eng',config='--psm 6'))
    return resAll
def extractFirstPage(im,coords):
    """
    im: Image object 
    coords: List of size-4 tuples. Order: Box-1 containing mandal name, pin code etc.
                                          Box-2 polling station name
                                          Box-3 polling station address
                                          Box-4 net electors male
                                          Box-5 net electors female
                                          Box-6 net electors third gender
                                          Box-7 total electors
                                          Box-8 parliamentary constituency
                                          Box-9 Ac.. Constituency
                                          Box-10 Part Number
    Return format : main_town,police_station,pin_code,polling_station_name,polling_station_address,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_net,main_town_regional,police_station_regional,polling_station_regional,polling_station_address_regional
    +[mandal,district,part_no,parl_const,ac_const,revenue_division,mandal_regional,district_regional,parl_const_regional,ac_const_regional,revenue_division_regional]
    """
    im.seek(0)
    resAll = dealWithFirstPage(im,coords)
    res2 = resAll[0].split("\n")
    resNoEmp = [i for i in res2 if not i=='']
    main_town = (resNoEmp[0].split("ः")[1].strip() if len(resNoEmp[0].split(":"))==1 else resNoEmp[0].split(":")[1]).strip()
    police_station = (resNoEmp[4].split("ः")[1].strip() if len(resNoEmp[4].split(":"))==1 else resNoEmp[4].split(":")[1]).strip()
    pin_code = (resNoEmp[7].split("ः")[1].strip() if len(resNoEmp[7].split(":"))==1 else resNoEmp[7].split(":")[1]).strip()
    main_town_eng = transliterate(main_town,sanscript.DEVANAGARI,sanscript.ITRANS) 
    police_station_eng = transliterate(police_station,sanscript.DEVANAGARI,sanscript.ITRANS)
    mandal_regional = (resNoEmp[5].split("ः")[1].strip() if len(resNoEmp[5].split(":"))==1 else resNoEmp[5].split(":")[1]).strip()
    district_regional = (resNoEmp[6].split("ः")[1].strip() if len(resNoEmp[6].split(":"))==1 else resNoEmp[6].split(":")[1]).strip()
    revenue_division_regional = (resNoEmp[2].split("ः")[1].strip() if len(resNoEmp[2].split(":"))==1 else resNoEmp[2].split(":")[1]).strip()
    parl_const_regional = resAll[7].split("-")[1].strip()
    ac_const_regional = resAll[8].split(",")[1].strip()
    part_no = resAll[9] 
    district = transliterate(district_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    mandal = transliterate(mandal_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    parl_const = transliterate(parl_const_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    ac_const = transliterate(ac_const_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    polling_station_name = transliterate(resAll[1],sanscript.DEVANAGARI,sanscript.ITRANS) 
    polling_station_address = transliterate(resAll[2],sanscript.DEVANAGARI,sanscript.ITRANS)
    revenue_division = transliterate(revenue_division_regional,sanscript.DEVANAGARI,sanscript.ITRANS)
    newList = [mandal,district,part_no,parl_const,ac_const,revenue_division,mandal_regional,district_regional,parl_const_regional,ac_const_regional,revenue_division_regional]
    return [main_town_eng,police_station_eng,pin_code,polling_station_name,polling_station_address,resAll[3],resAll[4],resAll[5],resAll[6],main_town,police_station,resAll[1],resAll[2]]+newList
       
def mainProcess(pdfFile,rangeTuple,formatType,n_blocks,outputCSV,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,internalBoxNumberCoord,externalBoxNumberCoord,addListInfo,bigPDFName,basePages):
    """
    addListInfo: [boxLen,boxH,lineWidth,dimX,dimY,box_coord,vid_coord,saneY,saneStart,saneEnd]
                    0      1      2       3    4      5        6        7       8        9
    #def dealWithPage(im,boxLen,boxH,lineWidth,dimX,dimY,pg,box_cord,vid_cord):
    """
    try:
        startPage = time.time()
        cmd = 'magick convert -density 300 '+pdfFile+'['+str(rangeTuple[0])+'-'+str(rangeTuple[1])+'] -depth 8 '+'temp.tiff' #WINDOWS
        if(os.path.isfile('temp.tiff')):
            os.remove('temp.tiff')
        subprocess.call(cmd,shell=True)
        im = Image.open('temp.tiff')
        im.load()
        fp1 = time.time()
        
        fpageInfo = extractFirstPage(im,firstPageCoords)
        fp2 = time.time()
        print("First page took :"+str(fp2-fp1))
        
        fpageInfo.append(bigPDFName) ;
        endPage = time.time()
        print('Time to create pages :'+str(endPage-startPage)) 
        entries_per_page = 0 
        if(formatType=='box'):
            entries_per_page = boxCoord[0]*boxCoord[1]
        elif(formatType=='list'):
            entries_per_page = argv[0] 
        numberOfPages = int(writeBlockSize/entries_per_page) 
        div_lst = divider(rangeTuple[1]-rangeTuple[0],numberOfPages)
        print("div_lst :"+str(div_lst))
        for tup in div_lst:
        #def cropAndOCR(im,rangeTuple,formatType,boxCoord,voterBoxCoord,boxNumberCoord,n_blocks,basePages)
            names_lst = cropAndOCR(im,(tup[0],tup[1]),formatType,boxCoord,voterBoxCoord,externalBoxNumberCoord,n_blocks,basePages)# Add the values of fpageInfo
            wrt0 = time.time()
            new_names_lst = [names_lst[i]+fpageInfo for i in range(len(names_lst))]
            wrt1 = time.time()
            print("THE LOOP TOOK AWAY :"+str(wrt1-wrt0)) 
            with open(outputCSV,'a',newline='',encoding='UTF-8') as f:
                writer = csv.writer(f)
                writer.writerows(new_names_lst)
            wrt2 = time.time()
            print("Took :"+str(wrt2-wrt1)+" for writing.")
        addListPages = sane(im,rangeTuple,addListInfo[7],addListInfo[8],addListInfo[9])
        #def dealWithPage(im,boxLen,boxH,lineWidth,dimX,dimY,pg,box_cord,vid_cord):
       #addListInfo: [boxLen,boxH,lineWidth,dimX,dimY,box_coord,vid_coord,saneY,saneStart,saneEnd]
       #                0      1      2       3    4      5        6        7       8        9
        bxes = []
        for pg in range(addListPages[0],rangeTuple[1]+1):
        #def dealWithPage(im,boxLen,boxH,lineWidth,dimX,dimY,pg,box_cord,vid_cord,boxNumber_coord,basePages):
            bxes+=dealWithPage(im,addListInfo[0],addListInfo[1],addListInfo[2],addListInfo[3],addListInfo[4],pg,addListInfo[5],addListInfo[6],internalBoxNumberCoord,basePages)
        box_lst_divided = []
        names_lst = []
        boxesWithErrors = []
        if(len(bxes)<n_blocks):
            box_lst_divided.append(bxes)
        else:
            for l in chunks(bxes,int(len(bxes)/n_blocks)):
                box_lst_divided.append(l)
        pool = ProcessingPool()     
        results = pool.map(tessBox,box_lst_divided)
        for result in results:
            names_lst+=result[0] 
            boxesWithErrors+=result[1]
        new_names_lst = [names_lst[i]+fpageInfo for i in range(len(names_lst))]
        with open(outputCSV,'a',newline='',encoding='UTF-8') as f:
            writer = csv.writer(f)
            writer.writerows(new_names_lst)
        wrt2 = time.time()
        print("Took :"+str(wrt2-wrt1)+" for writing.")
        end = time.time()
        print("mainProcess took :"+str(end-startPage))
    except:
        print("Error in "+pdfFile+" of :"+bigPDFName) 
def doItAll(basePDFName,outputCSV,startPDF,totalPDFs,formatType,n_blocks,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,internalBoxNumberCoord,externalBoxNumberCoord,addListInfo,bigPDFName):
    totalNumberLength = len(str(totalPDFs))
    
    start = time.time()
    basePages = 0 
    for i in range(startPDF-1,totalPDFs):
        zeros = totalNumberLength-len(str(i+1))
        pdfName = basePDFName+'0'*zeros+str(i+1)+'.pdf'
        noOfPages = PdfFileReader(open(pdfName,'rb')).getNumPages()
        #mainProcess(pdfFile,rangeTuple,formatType,n_blocks,outputCSV,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,boxNumberCoord,addListInfo,bigPDFName,basePages):
        mainProcess(pdfName,(0,noOfPages-1),formatType,n_blocks,outputCSV,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,internalBoxNumberCoord,externalBoxNumberCoord,addListInfo,bigPDFName,basePages)
        basePages+=noOfPages
    end= time.time()
    print("doItAll took:"+str(end-start)) 
def searchHorizontalLines(im,length,dimX,dimY,pg):
    """
    im: PIL image object of the file
    length: Length of box
    dimX: Width of the page
    dimY: Height of the page
    pg: Page number of the page to take under consideration
    """
    im.seek(pg)
    pix = im.load()
    line = False
    linez = []
    start = (0,0) 
    end = (0,0) 
    for i in range(0,dimY):
        for j in range(0,dimX):
            if(line):
                if(pix[j,i][0]!=0 or pix[j,i][1]!=255):
                    line = False
                    end = (j-1,i)
                    if(end[0]-start[0]>(length-10) and end[0]-start[0]<(length+10)):
                        linez.append([start,end])
            else:
                if(pix[j,i][0]==0 or pix[j,i][1]==255):
                    start = (j,i)
                    line = True 
    return linez
def grouping(hor,width):
    """
    Groups similar lines together.
    hor: List of lines in the format [[(start_x,start_y),(end_x,end_y)],...]
    width: What width can a line have. Takes all the lines inside this list into a group
    Returns: A list of groups. Each group is a list of lines. Each line has the format [(start_x,start_y),(end_x,end_y)]
    """
    horSet = set()
    for i in hor:
        horSet.add((i[0],i[1]))
    group = []
    count = 0 
    for i in hor:
        if (i[0],i[1]) in horSet:
            print("Visiting :"+str(i))
            for j in hor:
                if (j[0],j[1]) in horSet:
                    if(i[0][0]==j[0][0] and i[1][0]==j[1][0] and abs(j[0][1]-i[0][1])<width and abs(j[1][1]-i[1][1])<width):
                        if(len(group)<=count):
                            group.append([j])
                        else:
                            group[count].append(j)
                        horSet.remove((j[0],j[1]))
            count+=1
    return group
def boxing(groupList,boxHeight):
    """
    Given a groupList, it makes a list of coordinates of boxes that have a boxHeight height+-5
    """
    boxCoord = []
    groupSet = set()
    for i in range(len(groupList)):
        groupSet.add(i)
    for i,g in enumerate(groupList):
        if i in groupSet:
            print("On :"+str(i))
            for j,g1 in enumerate(groupList):
                if j in groupSet:
                    print("    Checking :"+str(j))
                    if(g[0][0][0]==g1[0][0][0] and g[0][1][0]==g1[0][1][0] and abs(g[len(g)-1][0][1]-g1[0][0][1])>=boxHeight-5 and abs(g[len(g)-1][0][1]-g1[0][0][1])<boxHeight+5):
                        groupSet.remove(j)
                        print("        removing :"+str(j))
                        boxCoord.append((g[0][0][0]+4,min(g[len(g)-1][0][1],g1[0][0][1])+1,g[0][1][0]-4,max(g[len(g)-1][0][1],g1[0][0][1])-1))
                        break
            groupSet.remove(i)
    return boxCoord
def dealWithPage(im,boxLen,boxH,lineWidth,dimX,dimY,pg,box_cord,vid_cord,boxNumber_coord,basePages):
    """
    im: PIL image object
    boxLen: box' length
    boxH: box' height
    lineWidth: What is the width of a normal line, in pixels
    dimX: Length of the page in pixels
    dimY: Height of the page in pixels
    pg: Page number of the page under consideration
    
    Returns: A list of PIL images, that are supposed to be the boxes in the page.
    
    """
    lines = searchHorizontalLines(im,boxLen,dimX,dimY,pg)
    groups = grouping(lines,lineWidth)
    boxes = boxing(groups,boxH)
    bxes = []
    for i in boxes:
        bxes.append(im.crop(i))
    tripleBoxLst = boxToBoxes(bxes,box_cord,vid_cord,basePages+pg,boxNumber_coord)
    return tripleBoxLst
    
def boxToBoxes(box_lst,box_cord,vid_cord,pg,boxNumber_cord):
    new_box_lst = []
    for i in box_lst:
        crp1 = i.crop(box_cord)
        crp2 = i.crop(vid_cord)
        crp3 = i.crop(boxNumber_cord)
        box_number = pt.image_to_string(crp3,lang='eng',config='--psm 7').strip()
        if(len(box_number.split(" "))==1):
            new_box_lst.append([crp1,crp2,pg,box_number])
        elif(box_number.split(" ")[0]=='#'):
            box_number = box_number.split(" ")[1]
            new_box_lst.append([crp1,crp2,pg,box_number])
    return new_box_lst
def dealWithAdditionLists(im,boxLen,boxH,lineWidth,dimX,dimY,box_cord,vid_cord,boxNumber_cord,fromPage,toPage):
    bxes = []
    for pg in range(fromPage,toPage+1):
        lines = searchHorizontalLines(im,boxLen,dimX,dimY,pg)
        groups = grouping(lines,lineWidth)
        boxes = boxing(groups,boxH)
        for i in boxes:
            bxes.append(im.crop(i))
    tripleBoxLst = boxToBoxes(bxes,box_cord,vid_cord,boxNumber_cord)
    return tripleBoxLst 
#[opName,age,gender,opHusband_or_father,has_husband,house_number,voter_id,box[2],box[3],name_regional,husband_or_father_regional])            
 #doItAll(basePDFName,outputCSV,totalPDFs,formatType,n_blocks,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,boxNumberCoord,bigPDFName):                                                                                                                                                                   # """main_town,police_station,pin_code,polling_station_name,polling_station_address,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_net,main_town_regional,police_station_regional,polling_station_regional,polling_station_address_regional +[mandal,district,part_no,parl_const,ac_const,revenue_division,mandal_regional,district_regional,parl_const_regional,ac_const_regional,revenue_division_regional]"""            
def doItAllUpper(bigPDFBaseName,outputCSV,tempPDFName,totalPDFs,formatType,n_blocks,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,internalBoxNumberCoord,externalBoxNumberCoord,addListInfo):
    """
    bigPDFBaseName: base name of the Big PDFs
    ouputCSV: The output CSV 
    tempPDFName: base name of the temporary small PDFs thus built
    totalPDFs: Total number of big PDFs
    formatType: "Box" or "list"
    n_blocks: Number of parallel processes
    writeBlockSize: Size of buffer
    firstPageCoords:List of size-4 tuples. Order: Box-1 containing mandal name, pin code etc.(inX,inY,outX,outY)
                                          Box-2 polling station name
                                          Box-3 polling station address
                                          Box-4 net electors male
                                          Box-5 net electors female
                                          Box-6 net electors third gender
                                          Box-7 total electors
                                          Box-8 parliamentary constituency
                                          Box-9 Ac.. Constituency
                                          Box-10 Part Number
    boxCoord: Coords for the boxes of normal pages
    voterBoxCoord: Coords for the voter ID format :[dimX,dimY,inX,inY]
    internalBoxNumberCoord: Coords for the box Numbers inside additional Lists boxes: [inX,inY,outX,outY]
    externalBoxNumberCoord: Coords for the box numbers inside a normal page: [dimX,dimY,inX,inY]
    addListInfo: [boxLen,boxH,lineWidth,dimX,dimY,box_coord,vid_coord,saneY,saneStart,saneEnd]
    
    """
    totalNumberLength = len(str(totalPDFs))
    with open(outputCSV,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name','Age','Gender','Husband_or_father_name','has_husband','house_number','voter_id','page_number','box_number','name_regional','husband_or_father_regional','main_town','police_station','pin_code','polling_station_name','polling_station_address','net_electors_male','net_electors_female','net_electors_third_gender','net_electors_total','main_town_regional','police_station_regional','polling_station_regional','polling_station_address_regional','mandal','district','part_no','parl_const','ac_const','revenue_division','mandal_regional','district_regional','parl_const_regional','ac_const_regional','revenue_division_regional','bigPDFName'])
    for i in range(totalPDFs):
        zeros = totalNumberLength-len(str(i+1))
        pdfName = bigPDFBaseName+'0'*zeros+str(i+1)+'.pdf'
        # noOfPages = PdfFileReader(open(pdfName,'rb')).getNumPages()
        pdfs = splitAccordingToBookmarks(pdfName,tempPDFName)
        doItAll(tempPDFName,outputCSV,1,pdfs,formatType,n_blocks,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,internalBoxNumberCoord,externalBoxNumberCoord,addListInfo,pdfName)            


def _setup_page_id_to_num(pdf, pages=None, _result=None, _num_pages=None):
    if _result is None:
        _result = {}
    if pages is None:
        _num_pages = []
        pages = pdf.trailer["/Root"].getObject()["/Pages"].getObject()
    t = pages["/Type"]
    if t == "/Pages":
        for page in pages["/Kids"]:
            _result[page.idnum] = len(_num_pages)
            _setup_page_id_to_num(pdf, page.getObject(), _result, _num_pages)
    elif t == "/Page":
        _num_pages.append(1)
    return _result
def splitAccordingToBookmarks(PDF,basePDFName):
    with open(PDF,'rb') as f:
        p = PdfFileReader(f)
        pg_id_num_map = _setup_page_id_to_num(p)
        o = p.getOutlines()
        # type(o[0])
        splitPages = [pg_id_num_map[o[i].page.idnum] for i in range(len(o))]
        bookmarkSet = set(splitPages)
        output = PdfFileWriter()
        count = 0 
        for i in range(p.numPages):
            if(i in bookmarkSet):
                print('Found '+str(i)+' in s')
                with open(str(basePDFName)+str(count)+".pdf","wb") as f2:
                    output.write(f2)
                count+=1
                output = PdfFileWriter()    
                output.addPage(p.getPage(i))
            else:
                print('Just added '+str(i)+' to o/p')
                output.addPage(p.getPage(i))
        with open(str(basePDFName)+str(count)+".pdf","wb") as f2:
            output.write(f2)
        return len(o) ;
            
def chunks(l, n): #Took from :https://stackoverflow.com/a/1751478/5345646
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def divider(upLimit,size):
    tupleList = []
    lim = int(upLimit/size)
    for i in range(lim):
        tupleList.append((i*size,(i+1)*size-1))
    if (lim!=upLimit/size):
        tupleList.append((size*lim,upLimit-1)) ;
    return tupleList
# Chandigarh: [10,3,577,215,94,340,746,296,263,94,770]
# Uttarakhand: [10,3,550,200,80,370,780,286.5,305,50,300]
# MP: [10,3,480,210,123,400,749,300,325,118,130]
# HP: [48,690,365,1050,60.05,300,120,300]
# Haryana:
# UP: [10,3,455,210,90,320,770,300,245,75,300]

if __name__=='__main__':
    #doItAll('w001000','op2.csv',2,'box',[10,3,577,215,94,340,746,296,263,94,770],2) ## for 2 pages: 3.5 minutes per page=3 minutes for OCR+0.5 minutes for page creation by ImageMagick 
    # partCoord = (90,180,2330,250)
    # firstPageCoords = [(1500,1663,2280,2320),(720,2440,1630,2580),(720,2600,1630,2770),(1250,3070,1480,3160),(1500,3070,1750,3160),(1770,3070,1980,3160),(2000,3060,2290,3160)]
    #mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks,outputCSV,writeBlockSize,firstPageCoords,argv2):
    # mainProcess("w0010001.pdf",(0,3),'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,'checkHouses3.csv',100,firstPageCoords,[partCoord,300,50,290,280],0)
    # doItAll('w001000','checkAgain.csv',2,'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,100,firstPageCoords,[partCoord,300,50,290,280])
    firstPageCoordsUK = [(1303,1224,2371,2267),(580,2360,1260,2480),(600,2520,1240,2700),(860,3060,1220,3160),(1260,3060,1580,3160),(1600,3060,1940,3160),(1960,3060,2360,3160),(1000,220,2100,340),(1000,400,2100,500),(2160,260,2360,360)]
    boxCoordUK =  [10,3,590,220,60,360,780,286.5,305,50,300]
    voterBoxCoordUK = [503,40,320,310]
    internalBoxNumberCoordUK= [70,30,290,70]
    externalBoxNumberCoordUK = [210,40,80,310]
    box_coordUK = (30,80,550,280)
    voterID_coordUK = (310,20,730,70)
    addListInfoUK = [740,300,4,2479,3504,box_coordUK,voterID_coordUK,72,100,800]
    #addListInfo: [boxLen,boxH,lineWidth,dimX,dimY,box_coord,vid_coord,saneY,saneStart,saneEnd]
    doItAllUpper("A00","op6.csv","temp",2,"box",4,50,firstPageCoordsUK,boxCoordUK,voterBoxCoordUK,internalBoxNumberCoordUK,externalBoxNumberCoordUK,addListInfoUK)
    # doItAll('w001000','op2.csv',1,'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,1000,firstPageCoords,[partCoord,300,50,290,280]) ## for 2 pages: 3.5 minutes per page=3 minutes for OCR+0.5 minutes for page creation by ImageMagick 
    #def doItAllUpper(bigPDFbaseName,tempPDFName,totalPDFs,formatType,n_blocks,writeBlockSize,firstPageCoords,boxCoord,voterBoxCoord,boxNumberCoord,addListInfo):
