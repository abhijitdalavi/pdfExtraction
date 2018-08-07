# Remove writing from doItAll and add to mainProcess
# Have a list of tuples, with 33 pages. Run cropAndOCR multiple times
# For each time cropAndOCR is run, write to the csv file.
# Decide the number of pages per tuple by using rows (if formatType=='list') and rows*cols for boxes.
# 
###################################################################################
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
from PyPDF2 import PdfFileReader 

           
                
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
#pagesWithErrors = doItAll('A0230005.pdf','pages',[(2,3)],"list",["name","age","gender"],'op2.csv',[45,460,62.44,520,410,80,62.44,1660,410,160,62.44,1480,410])
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
#120,312--350,312 
#1050x62.44+690+472.44
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
def getPartNumber(im,coord,pg):#This function belongs inside the cropperBox function
    im.seek(pg)
    crp = im.crop(coord)
    op =  pt.image_to_string(crp,lang='hin+eng',config='--psm 6')
    return '' if re.search('[0-9]+',op)==None else re.search('[0-9]+',op).group(0)
def cropperBox(im,rangeTuple,dimX,dimY,inX,inY,addX,addY,rows,cols,saneY,saneStart,saneEnd,partCoord,dimX2,dimY2,inX2,inY2):#5 new arguments
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
    """
    #im = Image.open(file)
    print(im.n_frames)
    #im.load()
    sanePages = sane(im,rangeTuple,saneY,saneStart,saneEnd)
    
    print(sanePages)
    lst = []
    for pg in sanePages:
        im.seek(pg)
        # im = im.load()
        part_number = getPartNumber(im,partCoord,pg)
        #img = im.load() 
        #Can do part cropping exactly here. A function, that takes in the page, and the coordinates of the part,
        # and returns the part number of the part.
        count = 0 
        for i in range(rows):
            for j in range(cols):
                x = inX+j*addX
                y = inY+i*addY
                x2 = inX2+j*addX
                y2 = inY2+i*addY
                crp1 = im.crop((x,y,dimX+x,dimY+y))
                crp2 = im.crop((x2,y2,dimX2+x2,dimY2+y2))
                
                # crp1.save(str(pg)+str(count)+'.tiff')
                # crp2.save(str(pg)+str(count)+'VID.tiff')
                #crp2.load()
                lst.append((crp1,crp2,pg,i*cols+j,part_number))
                count = count + 1
    return lst# pic of the form Box,pic of voter id,page number, box number, part number
    #magick convert page.tiff[1] -crop 305x200+80+320 boxName1-0.tiff 
    """husband_or_father_regional = res[1].split(":")[1].strip()
house_number = res[2].split(":")[1]
#intermediate = op.split("पति") if len(op.split("पति"))!=1 else op.split("पिता")
has_husband = 1 if husband_or_father_regional=="पति" else 0"""
def tessBox(box_lst):#,pt,time,re,tranliterate,sanscript):
    """
    The output of cropperBox is a list of Image objects, of boxes.
    """
#    tr = Transliterator(source_lang='hi',target_lang='en')#p
    rows = []
    indicesWithErrors = []
    for i,box in enumerate(box_lst):
        boxStart = time.time()
        op = pt.image_to_string(box[0],lang='hin+eng',config='--psm 6')
        voter_id = pt.image_to_string(box[1],lang='eng',config='--psm 6')
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
            if(re.match('[0-9/]+',house_number)==None):
                house_number='' 
            else:
                house_number=re.match('[0-9/]+',house_number).group(0)
            #WHAT ABOUT THAT.
            has_husband = 1 if (res[1].split("ः")[0] if len(res[0].split(":"))==1 else res[1].split(":")[0]).strip() == "पति" else 0
            age = re.search('[0-9]+',res[len(res)-1]).group(0)
            #print(res[len(res)-1]) #This might be commented out
            intermediate = res[len(res)-1].split(" ")
            gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' #3 for other states, 4 for UK.
            nameCorrect = nameCheck(name_regional,'hin')
                #print(gender) ##
            if not nameCorrect:
                raise Exception('Not hindi')   
            if int(age) not in range(18,111):
                raise Exception('Age incorrect')
            opName = transliterate(name_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            opHusband_or_father = transliterate(husband_or_father_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            rows.append([opName,age,gender,opHusband_or_father,has_husband,house_number,voter_id,box[2],box[3],box[4],name_regional,husband_or_father_regional])    
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
def cropAndOCR(im,rangeTuple,formatType,argv,n_blocks,argv2):
    #Add more parameters for cropperBox' procedures
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
    """
    genStart = time.time()
    if(formatType=='box'):
        st = time.time()
        box_lst = cropperBox(im,rangeTuple,argv[2],argv[3],argv[4],argv[5],argv[6],argv[7],argv[0],argv[1],argv[8],argv[9],argv[10],argv2[0],argv2[1],argv2[2],argv2[3],argv2[4])
        #THis needs changing
        en = time.time()
        print("Time for cropping :"+str(en-st))
        names_lst = []
        boxesWithErrors = []
        box_lst_divided = []
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
    """
    im.seek(0)
    resAll = dealWithFirstPage(im,coords)
    res2 = resAll[0].split("\n")
    resNoEmp = [i for i in res2 if not i=='']
    main_town = (resNoEmp[0].split("ः")[1].strip() if len(resNoEmp[0].split(":"))==1 else resNoEmp[0].split(":")[1]).strip()
    police_station = (resNoEmp[5].split("ः")[1].strip() if len(resNoEmp[5].split(":"))==1 else resNoEmp[5].split(":")[1]).strip()
    pin_code = (resNoEmp[8].split("ः")[1].strip() if len(resNoEmp[8].split(":"))==1 else resNoEmp[8].split(":")[1]).strip()
    main_town_eng = transliterate(main_town,sanscript.DEVANAGARI,sanscript.ITRANS) 
    police_station_eng = transliterate(police_station,sanscript.DEVANAGARI,sanscript.ITRANS)  
    polling_station_name = transliterate(resAll[1],sanscript.DEVANAGARI,sanscript.ITRANS) 
    polling_station_address = transliterate(resAll[2],sanscript.DEVANAGARI,sanscript.ITRANS) 
    return [main_town_eng,police_station_eng,pin_code,polling_station_name,polling_station_address,resAll[3],resAll[4],resAll[5],resAll[6],main_town,police_station,resAll[1],resAll[2]]
   
def mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks,outputCSV,writeBlockSize,firstPageCoords,argv2,pdfNumber):
    startPage = time.time()
    cmd = 'magick convert -density 300 '+pdfFile+'['+str(rangeTuple[0])+'-'+str(rangeTuple[1])+'] -depth 8 '+'temp.tiff' #WINDOWS
    if(os.path.isfile('temp.tiff')):
        os.remove('temp.tiff')
    subprocess.call(cmd,shell=True)
    im = Image.open('temp.tiff')
    im.load()
    fpageInfo = extractFirstPage(im,firstPageCoords)
    fpageInfo.append(pdfNumber) ;
    endPage = time.time()
    print('Time to create pages :'+str(endPage-startPage)) 
    with open(outputCSV,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name','Age','Gender','Husband_or_father_name','has_husband','house_number','voter_id','page_number','box_number','part_number','name_regional','husband_or_father_regional','main_town','police_station','pin_code','polling_station_name','polling_station_address','net_electors_male','net_electors_female','net_electors_third_gender','net_electors_total','main_town_hindi','police_station_hindi','polling_station_hindi','polling_station_address_hindi','pdf_number'])
    entries_per_page = 0 
    if(formatType=='box'):
        entries_per_page = argv[0]*argv[1]
    elif(formatType=='list'):
        entries_per_page = argv[0] 
    
    numberOfPages = int(writeBlockSize/entries_per_page) 
    div_lst = divider(rangeTuple[1]-rangeTuple[0],numberOfPages)
    print("div_lst :"+str(div_lst))
    for tup in div_lst: #(0,rangeTuple[1]-rangeTuple[0])
        names_lst = cropAndOCR(im,(tup[0],tup[1]),formatType,argv,n_blocks,argv2)# Add the values of fpageInfo
        new_names_lst = [names_lst[i]+fpageInfo for i in range(len(names_lst))]
        with open(outputCSV,'a',newline='',encoding='UTF-8') as f:
            writer = csv.writer(f)
            writer.writerows(new_names_lst)
def doItAll(basePDFName,outputCSV,totalPDFs,formatType,argv,n_blocks,writeBlockSize,firstPageCoords,argv2):
    totalNumberLength = len(str(totalPDFs))
    for i in range(totalPDFs):
        zeros = totalNumberLength-len(str(i+1))
        pdfName = basePDFName+'0'*zeros+str(i+1)+'.pdf'
        noOfPages = PdfFileReader(open(pdfName,'rb')).getNumPages()
        mainProcess(pdfName,(0,noOfPages-1),formatType,argv,n_blocks,outputCSV,writeBlockSize,firstPageCoords,argv2,i)
  
    
    
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
    #names_lst = mainProcess('w0010001.pdf',(2,3),'box',[10,3,577,215,94,340,746,296,263,94,770],2)
    #print(names_lst)
    #doItAll('w001000','op2.csv',2,'box',[10,3,577,215,94,340,746,296,263,94,770],2) ## for 2 pages: 3.5 minutes per page=3 minutes for OCR+0.5 minutes for page creation by ImageMagick 
    partCoord = (90,180,2330,250)
    firstPageCoords = [(1500,1663,2280,2320),(720,2440,1630,2580),(720,2600,1630,2770),(1250,3070,1480,3160),(1500,3070,1750,3160),(1770,3070,1980,3160),(2000,3060,2290,3160)]
    #mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks,outputCSV,writeBlockSize,firstPageCoords,argv2):
    # mainProcess("w0010001.pdf",(0,3),'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,'final.csv',100,firstPageCoords,[partCoord,300,50,290,280])
    doItAll('w001000','doitallop.csv',2,'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,100,firstPageCoords,[partCoord,300,50,290,280],)
    # doItAll('w001000','op2.csv',1,'box',[10,3,577,215,94,332,750,297.5,263,94,770],4,1000,firstPageCoords,[partCoord,300,50,290,280]) ## for 2 pages: 3.5 minutes per page=3 minutes for OCR+0.5 minutes for page creation by ImageMagick 
   
