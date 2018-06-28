#######################################################################################################
import pytesseract as pt
from PIL import Image
from polyglot.text import Text
import subprocess
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from multiprocessing import Pool
import re
import csv
import time
import os
from pathos.multiprocessing import ProcessingPool
           
                
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
	saneEnd: The ending x-coordinate of the line to be checked
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
def tessBox(box_lst):
    """
    The output of cropperBox is a list of Image objects, of boxes. TessBox will require such an input.
    """
    rows = []
    indicesWithErrors = []
    for i,box in enumerate(box_lst):
        boxStart = time.time()
        op = pt.image_to_string(box,lang='hin+eng',config='--psm 6')
        #####################################print(op)
        boxTess = time.time()
        print("box number :"+str(i))
        try:
            res = op.split("\n") 
            name = res[0].split('ः')[1] if len(res[0].split(":"))==1 else res[0].split(":")[1]
            age = re.search('[0-9]+',res[len(res)-1]).group(0)
            intermediate = res[len(res)-1].split(" ")
            gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' 
            opName = transliterate(name,sanscript.DEVANAGARI,sanscript.ITRANS)            
            rows.append([opName,age,gender])
        except:
            indicesWithErrors.append(i)
            print("Had Errors.")
        boxEnd = time.time()
        print("    Box took :"+str(boxTess-boxStart))
    return rows,indicesWithErrors
            
        
        
    
def cropAndOCR(im,rangeTuple,formatType,argv,n_blocks):
    """
    im: The PIL Image object 
    rangeTuple: A tuple describing the range of the pages to be processed. Example (4,7)
    formatType: 'box' or 'list' 
	n_blocks: Number of blocks the box_lst must be divided. 
    argv: if format is "list"
                    [colSize,dimXName,dimYName,inXName,inYName,dimXAge,dimYAge,inXAge,inYAge,dimXGender,dimYGender,inXGender,inYGender]
                        0       1        2        3       4       5       6       7      8         9        10         11        12   
                    colSize: Number of rows,or total number of instances
                    dimX*: Needed width
                    dimY*: Needed height
                    inX*: Starting x co-ordinate of the first instance
                    inY*: Starting y co-ordinate of the first instance
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
        for l in chunks(box_lst,int(len(box_lst)/n_blocks)):
            box_lst_divided.append(l)
        pool = ProcessingPool() 
	# names_lst,boxesWithErrors = tessBox(box_lst)
        results = pool.map(tessBox,box_lst_divided)
        for result in results:
            names_lst+=result[0] 
            boxesWithErrors+=result[1]
        en2 = time.time() 
        print("Time to OCR :"+str(en2-en))
        #boxCleanUp()
    elif (formatType=='list'):
        pass
    genEnd = time.time()
    print("Total time = "+str(genEnd-genStart))
    return names_lst
def mainProcess(pdfFile,rangeTuple,formatType,argv,n_blocks):
    """
	pdfFile: The file to be processed, along with the .pdf 
	rangeTuple: The range of the pages to be processed 
	formatType: 'box' or 'list'
	n_blocks: Number of blocks the box_lst must be divided. 
	argv: if format is "list"
                    [colSize,dimXName,dimYName,inXName,inYName,dimXAge,dimYAge,inXAge,inYAge,dimXGender,dimYGender,inXGender,inYGender]
                        0       1        2        3       4       5       6       7      8         9        10         11        12   
                    colSize: Number of rows,or total number of instances
                    dimX*: Needed width
                    dimY*: Needed height
                    inX*: Starting x co-ordinate of the first instance
                    inY*: Starting y co-ordinate of the first instance
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
    startPage = time.time()
    cmd = 'magick convert -density 300 '+pdfFile+'['+str(rangeTuple[0])+'-'+str(rangeTuple[1])+'] -depth 8 '+'temp.tiff'
    if(os.path.isfile('temp.tiff')):
        os.remove('temp.tiff')
    subprocess.call(cmd)
    endPage = time.time()
    print('Time to create pages :'+str(endPage-startPage)) 
    im = Image.open('temp.tiff')
    im.load()
    names_lst = cropAndOCR(im,(0,rangeTuple[1]-rangeTuple[0]),formatType,argv,n_blocks)
    return names_lst
def chunks(l, n): #Took from :https://stackoverflow.com/a/1751478/5345646
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]	
####################################################################################################################
# The mainProcess now takes one more parameter n_blocks, which gives the number of blocks in which box_lst to be divided. Each such block
# is executed by a process of tessBox. So, I **think** that equalling n_blocks to os.cpu_count() would do better. It was seen that when
# I put n_blocks = 2 , the OCR time was ~88s. For n = 4 (total number of cores in my machine, including the virtual ones), the time
# was 44s. So, it is an important parameter which significantly affects the performance of the function. Moreover, the function
# mainProcess should be inside "if __name__=='__main__':" atleast for windows based machines. 
# im = Image.open('page.tiff')
res = []
if __name__=='__main__':
	res = mainProcess('A001.pdf',(10,10),'box',[10,3,550,200,80,370,780,286.5,305,50,300],os.cpu_count())	
	print(res) 
	
