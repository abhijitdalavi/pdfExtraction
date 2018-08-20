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

def cropperBox(im,rangeTuple,dimX,dimY,inX,inY,addX,addY,rows,cols,saneY,saneStart,saneEnd):
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
        #img = im.load() 
        count = 0 
        for i in range(rows):
            for j in range(cols):
                x = inX+j*addX
                y = inY+i*addY
                crp1 = im.crop((x,y,dimX+x,dimY+y))
                #crp1.save(str(pg)+str(count)+'.tiff')
                crp1.load()
                lst.append(crp1)
                count = count + 1
    return lst
    #magick convert page.tiff[1] -crop 305x200+80+320 boxName1-0.tiff 
def tessBox(box_lst):#,pt,time,re,tranliterate,sanscript):
    """
    The output of cropperBox is a list of Image objects, of boxes.
    """
#    tr = Transliterator(source_lang='hi',target_lang='en')#p
    rows = []
    indicesWithErrors = []
    for i,box in enumerate(box_lst):
        boxStart = time.time()
        op = pt.image_to_string(box,lang='hin+eng',config='--psm 6')
        boxTess = time.time()
        print("box number :"+str(i))
        try:
            res = op.split("\n") 
            name = (res[0].split("ः")[1] if len(res[0].split(":"))==1 else res[0].split(":")[1]).strip()
            age = re.search('[0-9]+',res[len(res)-1]).group(0)
            #print(res[len(res)-1]) #This might be commented out
            intermediate = res[len(res)-1].split(" ")
            gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' #3 for other states, 4 for UK.
            nameCorrect = nameCheck(name,'hin')
            #print(gender) ##
            if not nameCorrect:
                raise Exception('Not hindi')   
            if int(age) not in range(18,111):
                raise Exception('Age incorrect')
            opName = transliterate(name,sanscript.DEVANAGARI,sanscript.ITRANS) 
            rows.append([opName,age,gender])    
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
def cropAndOCR(im,rangeTuple,formatType,argv,n_blocks):
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
    """
    genStart = time.time()
    if(formatType=='box'):
        st = time.time()
        box_lst = cropperBox(im,rangeTuple,argv[2],argv[3],argv[4],argv[5],argv[6],argv[7],argv[0],argv[1],argv[8],argv[9],argv[10])
        en = time.time()
        print("Time for cropping :"+str(en-st))
        names_lst = []
        boxesWithErrors = []
        box_lst_divided = []
	if (len(box_lst)<n_blocks):
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
        #boxCleanUp()
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
def mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks,outputCSV,writeBlockSize):
    startPage = time.time()
    cmd = 'magick convert -density 300 '+pdfFile+'['+str(rangeTuple[0])+'-'+str(rangeTuple[1])+'] -depth 8 '+'temp.tiff' #WINDOWS
    
    if(os.path.isfile('temp.tiff')):
        os.remove('temp.tiff')
    subprocess.call(cmd,shell=True)
    im = Image.open('temp.tiff')
    im.load()
    endPage = time.time()
    print('Time to create pages :'+str(endPage-startPage)) 
    with open(outputCSV,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name','Age','Gender'])
    entries_per_page = 0 
    if(formatType=='box'):
        entries_per_page = argv[0]*argv[1]
    elif(formatType=='list'):
        entries_per_page = argv[0] 
    
    numberOfPages = int(writeBlockSize/entries_per_page) 
    div_lst = divider(rangeTuple[1]-rangeTuple[0],numberOfPages)
    print("div_lst :"+str(div_lst))
    for tup in div_lst: #(0,rangeTuple[1]-rangeTuple[0])
        names_lst = cropAndOCR(im,(tup[0],tup[1]),formatType,argv,n_blocks)
        with open(outputCSV,'a',newline='') as f:
            writer = csv.writer(f)
            writer.writerows(names_lst)
def doItAll(basePDFName,outputCSV,totalPDFs,formatType,argv,n_blocks,writeBlockSize):
    totalNumberLength = len(str(totalPDFs))
    for i in range(totalPDFs):
        zeros = totalNumberLength-len(str(i+1))
        pdfName = basePDFName+'0'*zeros+str(i+1)+'.pdf'
        noOfPages = PdfFileReader(open(pdfName,'rb')).getNumPages()
        mainProcess(pdfName,(0,noOfPages-1),formatType,argv,n_blocks,outputCSV,writeBlockSize)
   #mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks,outputCSV,writeBlockSize): 
    
    
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
		
	
####################################################################################################################

#im = Image.open('out.tiff')
#res = []
if __name__=='__main__':
	#names_lst = mainProcess('w0010001.pdf',(2,3),'box',[10,3,577,215,94,340,746,296,263,94,770],2)
	#print(names_lst)
	#doItAll('w001000','op2.csv',2,'box',[10,3,577,215,94,340,746,296,263,94,770],2) ## for 2 pages: 3.5 minutes per page=3 minutes for OCR+0.5 minutes for page creation by ImageMagick 
	# doItAll('w0010','chandigarh.csv',527,'box',[10,3,577,215,94,340,746,296,263,94,770],2)
    #names_lst = mainProcess('A001.pdf',(10,13),'box',[10,3,550,200,80,370,780,286.5,305,50,300],4)
    #print(names_lst)
    #[10,3,550,200,80,370,780,286.5,305,50,300] for UK
    #names_lst = mainProcess('A001.pdf',(10,19),'box',[10,3,550,200,80,370,780,286.5,305,50,300],4,'op4.csv',40)
