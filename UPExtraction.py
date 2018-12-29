import cv2
from PIL import Image
import subprocess
import numpy as np
from indic_transliteration import sanscript 
from indic_transliteration.sanscript import transliterate
import re
import csv
import time
import os
import tempfile
from PyPDF2 import PdfFileWriter, PdfFileReader
def dealWithID(ID):
    """
    Returns the ID if it is of the correct format. Otherwise, if only a problem of 0s recognized as Os, then it corrects
    them. Otherwise, return None.
    """
    ID = ''.join(ID.split(" "))
    newID = ID[:3].replace('0','O')+ID[3:].replace('O','0')
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

#(2281, 2755)
def getFirstPageBoxesUP(im):
    """
    Box 0: parl_const
    Box 1: ass_const
    Box 2: Main box
    Box 3: Voting booth name + address
    Box 4: male_electors
    Box 5: female_electors
    Box 6: third_gender_electors
    Box 7: total_electors
    Box 8: part_number
    """
    
    im = im.convert('RGB')
    opencvImage = cv2.cvtColor(np.array(im,dtype=np.uint8), cv2.COLOR_RGB2BGR)
    roi = getMaxContour(opencvImage)
    (h,w) = roi.shape[:2]
    masks = []
    masks.append((0,0,w*0.88,h*0.062)) #the parameter 0.88 and 0.062 were found base on the format of the document
    masks.append((0,h*0.062,w,h*(0.062+0.06)))
    masks.append((w*(1179/2281),h*(1054/2755),w,h*(1054/2755)+h*(810/2755)))
    masks.append((0,h*(1964/2755),w*(1193/2281),h*(2354/2755)))
    masks.append((w*(747/2281),h*(2636/2755),w*(1147/2281),h))
    masks.append((w*(1146/2281),h*(2632/2755),w*(1495/2281),h))
    masks.append((w*(1495/2281),h*(2632/2755),w*(1859/2281),h))
    masks.append((w*(1859/2281),h*(2632/2755),w,h))
    masks.append((w*0.88,0,w,h*0.062))
    boxes = []
    ROI = Image.fromarray(roi)
    for mask in masks:
        boxes.append(ROI.crop((mask[0]+10,mask[1]+10,mask[2]-10,mask[3]-10)))
    
    return boxes
def getOp(boxes):
    opList = []
    for box in boxes:
        # opList.append(pt.image_to_string(box,lang='hin+eng',config='--psm 6'))
        fl = tempfile.mktemp()
        box.save(fl+'.tiff')
        opList.append(subprocess.Popen(['tesseract',fl+'.tiff','stdout','-l','hin+eng','--psm','6'],env={'OMP_THREAD_LIMIT':'1'},stdout=subprocess.PIPE))
    resLst = []
    for res in opList:
        resLst.append(res.communicate()[0].decode('utf-8'))
    return resLst 
def getMaxContour(img):
    imgray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(imgray,127,255,0)
    cv2.bitwise_not(thresh,thresh)
    im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)# will have to do RETR_LIST for finding all the boxes
    max_area = 0
    max_contour = None
    for i,c in enumerate(contours):# Finds the contour with the largest area
        area = cv2.contourArea(c)
        if area>max_area:#Finding the contour with the maximum area
            max_area = area
            max_contour = c
    rect = cv2.boundingRect(max_contour)
    roi = img[rect[1]:rect[1]+rect[3],rect[0]:rect[0]+rect[2]]
    return roi
def getNormalPageBoxes(im,rows,cols):
    im = im.convert('RGB')
    opencvImage = cv2.cvtColor(np.array(im,dtype=np.uint8), cv2.COLOR_RGB2BGR)
    roi = getMaxContour(opencvImage)
    (h,w) = roi.shape[:2]
    boxes = []
    boxL = w/3 
    boxH = h/10 
    ROI = Image.fromarray(roi)
    for r in range(rows):
        for c in range(cols):
            boxes.append(ROI.crop((c*boxL+10,r*boxH+10,c*boxL+boxL-10,r*boxH+boxH-10)))
    return boxes
def specifiedBoxes(boxList,mainBoxCoords,voterIDCoords,numberCoords,pageNumber):
    infoList = []
    for box in boxList:
        infoList.append([box.crop(mainBoxCoords),box.crop(voterIDCoords),box.crop(numberCoords),pageNumber])    
    return infoList

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
mapping = [('bI.', 'B.'), ('sI.', 'C.'), ('DI.', 'D.'),
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
def cropperBox(im,rangeTuple,boxCoord,voterBoxCoord,boxNumberCoord):
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
    boxNumberCoord: [inX,inY,endX,endY]
                      0    1    2   3  
    voterBoxCoord:   [inX,inY,endX,endY]
                        0    1   2   3
    boxCoord : [rows,cols,[inX,inY,endX,endY]]
                  0    1          2   
    """    
    sanePages = [i for i in range(2,rangeTuple[1])]
    print(sanePages)
    lst = []
    s1 = time.time() 
    for pg in sanePages:
        im.seek(pg)
        boxes = getNormalPageBoxes(im,10,2)#Hard coded
        specList = specifiedBoxes(boxes,boxCoord,voterBoxCoord,boxNumberCoord,pg)
        lst = lst + specList
    s2 = time.time()
    print("Took :"+str(s2-s1)+" to create all cropBoxes") 
    return lst
def picEater(boxList):
    resLst = []
    for boxes in boxList:
        lst = []
        fl1 = tempfile.mktemp()
        fl2 = tempfile.mktemp()
        fl3 = tempfile.mktemp()
        boxes[0].save(fl1+'.png')
        boxes[1].save(fl2+'.png')
        boxes[2].save(fl3+'.png')
        lst.append(subprocess.Popen(['tesseract',fl1+'.png','stdout','-l','hin+eng','--psm','6'],env={'OMP_THREAD_LIMIT':'1'},stdout=subprocess.PIPE))
        lst.append(subprocess.Popen(['tesseract',fl2+'.png','stdout','-l','eng','--psm','7'],env={'OMP_THREAD_LIMIT':'1'},stdout=subprocess.PIPE))
        lst.append(subprocess.Popen(['tesseract',fl3+'.png','stdout','-l','eng','--psm','7'],env={'OMP_THREAD_LIMIT':'1'},stdout=subprocess.PIPE))
        resLst.append(lst)
    return resLst
        
    
def tessBox(box_lst):
    """
    box_lst : Input format : A list of lists, with each inner list being of the format:
        0: Main box
        1: voterIDBox
        2: boxNumber 
        3: Pagenumber
    
    """
    rows = []
    st = time.time()
    indicesWithErrors = []
    resLst = picEater(box_lst)
    for i,rex in enumerate(resLst):
        op= rex[0].communicate()[0].decode('utf-8')
        voter_id = rex[1].communicate()[0].decode('utf-8')
        voter_id = dealWithID(voter_id)
        boxNumber = rex[2].communicate()[0].decode('utf-8')
        print("box number :"+str(i))
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
            has_husband = 1 if (res[1].split("ः")[0] if len(res[0].split(":"))==1 else res[1].split(":")[0]).split(" ")[0].strip() == "पति" else 0
            age = re.search('[0-9]+',res[len(res)-1]).group(0)
            if(int(age)<18):
                raise ValueError()
            intermediate = res[len(res)-1].split(" ")
            gender = 'F' if re.match('म',intermediate[len(intermediate)-1])!= None else 'M' #3 for other states, 4 for UK.
            opName = transliterate(name_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            opHusband_or_father = transliterate(husband_or_father_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
            rows.append([opName,age,gender,opHusband_or_father,has_husband,house_number,voter_id,boxNumber,box_lst[i][3],name_regional,husband_or_father_regional])    
        except:
            indicesWithErrors.append(i)
            print("Had Errors.")
    return rows,indicesWithErrors
def cropAndOCR(im,rangeTuple,boxCoord,voterBoxCoord,boxNumberCoord):
    """
    im: The PIL Image object 
    rangeTuple: A tuple describing the range of the pages to be processed. Example (4,7)
    """
    box_lst = cropperBox(im,rangeTuple,boxCoord,voterBoxCoord,boxNumberCoord)
    names_lst = tessBox(box_lst) 
    return names_lst
def extractFirstPage(im):
    """
    im: Image object 
    Return format : main_town,police_station,pin_code,polling_station_name,polling_station_address,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_net,main_town_regional,police_station_regional,polling_station_regional,polling_station_address_regional
    +[mandal,district,part_no,parl_const,ac_const,revenue_division,mandal_regional,district_regional,parl_const_regional,ac_const_regional,panchayat]
    """
    im.seek(0)
    res = getFirstPageBoxesUP(im)
    resAll = getOp(res)
    print('resAll len :'+str(len(resAll)) )
    res2 = resAll[2].split("\n")
    resNoEmp = [i for i in res2 if not i=='']
    print("resNoEmp :"+str(resNoEmp))
    if(resNoEmp[0].strip()[0]=='म'): #Town
        try:
            main_town = (resNoEmp[0].split("ः")[1].strip() if len(resNoEmp[0].split(":"))==1 else resNoEmp[0].split(":")[1]).strip() 
        except:
            main_town = '######'
        try:
            police_station = (resNoEmp[3].split("ः")[1].strip() if len(resNoEmp[3].split(":"))==1 else resNoEmp[3].split(":")[1]).strip()
        except:
            police_station = '######'
        try:
            pin_code = (resNoEmp[7].split("ः")[1].strip() if len(resNoEmp[7].split(":"))==1 else resNoEmp[7].split(":")[1]).strip()
        except:
            pin_code = '######'
        main_town_eng = transliterate(main_town,sanscript.DEVANAGARI,sanscript.ITRANS) 
        police_station_eng = transliterate(police_station,sanscript.DEVANAGARI,sanscript.ITRANS)
        try:
            district_regional = (resNoEmp[5].split("ः")[1].strip() if len(resNoEmp[5].split(":"))==1 else resNoEmp[5].split(":")[1]).strip()
        except:
            district_regional = '######'
        try:
            panchayat_regional = (resNoEmp[1].split("ः")[1].strip() if len(resNoEmp[1].split(":"))==1 else resNoEmp[1].split(":")[1]).strip()
        except:
            panchayat_regional = '######'
        try:
            parl_const_regional = resAll[0].split("-")[1].strip()
        except:
            parl_const_regional = '######'
        try:
            ac_const_regional = resAll[1].split(",")[2].strip()
        except:
            ac_const_regional = '######'
        try:
            temp = resAll[8].split("\n")[1]
            
            part_no = (temp if temp.isdigit() else '#######')
        except:
            part_no = '######'
        ward_regional = 'N/A'
    else:#City
        try:
            main_town = (resNoEmp[0].split("ः")[1].strip() if len(resNoEmp[0].split(":"))==1 else resNoEmp[0].split(":")[1]).strip() 
        except:
            main_town = '######'
        try:
            police_station = (resNoEmp[2].split("ः")[1].strip() if len(resNoEmp[2].split(":"))==1 else resNoEmp[2].split(":")[1]).strip()
        except:
            police_station = '######'
        try:
            pin_code = (resNoEmp[6].split("ः")[1].strip() if len(resNoEmp[6].split(":"))==1 else resNoEmp[6].split(":")[1]).strip()
        except:
            pin_code = '######'
        main_town_eng = transliterate(main_town,sanscript.DEVANAGARI,sanscript.ITRANS) 
        police_station_eng = transliterate(police_station,sanscript.DEVANAGARI,sanscript.ITRANS)
        try:
            district_regional = (resNoEmp[4].split("ः")[1].strip() if len(resNoEmp[4].split(":"))==1 else resNoEmp[4].split(":")[1]).strip()
        except:
            district_regional = '######'
        try:
            ward_regional = (resNoEmp[1].split("ः")[1].strip() if len(resNoEmp[1].split(":"))==1 else resNoEmp[1].split(":")[1]).strip()
        except:
            ward_regional = '######'
        try:
            parl_const_regional = resAll[0].split("-")[1].strip()
        except:
            parl_const_regional = '######'
        try:
            ac_const_regional = resAll[1].split(",")[2].strip()
        except:
            ac_const_regional = '######'
        try:
            temp = resAll[8].split("\n")[1]
            
            part_no = (temp if temp.isdigit() else '#######')
        except:
            part_no = '######'
        panchayat_regional = 'N/A'


    district = transliterate(district_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    panchayat = transliterate(panchayat_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    ward = transliterate(ward_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    parl_const = transliterate(parl_const_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    ac_const = transliterate(ac_const_regional,sanscript.DEVANAGARI,sanscript.ITRANS) 
    addressGoneWell = True
    
    try:
        temp = [i for i in resAll[3].split("\n") if i!='']
        polling_station_name_native = temp[1]
        polling_station_address_native = temp[3]
        polling_station_name = transliterate(temp[1],sanscript.DEVANAGARI,sanscript.ITRANS) 
        polling_station_address = transliterate(temp[3],sanscript.DEVANAGARI,sanscript.ITRANS)
    except:
        addressGoneWell = False
        polling_station_name_native = '######'
        polling_station_address_native = '######'
        polling_station_address = '######'
        polling_station_name = '######'
    
    panchayat = transliterate(panchayat_regional,sanscript.DEVANAGARI,sanscript.ITRANS)
    newList = [district,part_no,parl_const,ac_const,panchayat,ward,panchayat_regional,district_regional,parl_const_regional,ac_const_regional,ward_regional]
    return [main_town_eng,police_station_eng,pin_code,polling_station_name,polling_station_address,resAll[4],resAll[5],resAll[6],resAll[7],main_town,police_station,polling_station_name_native,polling_station_address_native]+newList
#main_town,police_station,pin_code,polling_station_name,polling_station_address,net_electors_male,net_electors_female,net_electors_third_gender,net_electors_net,main_town_regional,police_station_regional,polling_station_regional,polling_station_address_regional  
#[mandal,district,part_no,parl_const,ac_const,revenue_division,mandal_regional,district_regional,parl_const_regional,ac_const_regional,panchayat]
def mainProcess(pdfFile,rangeTuple,outputCSV,boxCoord,voterBoxCoord,boxNumberCoord,bigPDFName):
    """
    addListInfo: [boxLen,boxH,lineWidth,dimX,dimY,box_coord,vid_coord,saneY,saneStart,saneEnd]
                    0      1      2       3    4      5        6        7       8        9
    #def dealWithPage(im,boxLen,boxH,lineWidth,dimX,dimY,pg,box_cord,vid_cord):
    """
    #cmd = 'sudo convert -density 300 '+pdfFile+'['+str(rangeTuple[0])+'-'+str(rangeTuple[1])+'] -depth 8 '+'temp.tiff' #LINUX
    cmd = ['gs','-dBATCH','-dNOPAUSE','-sDEVICE=tiffgray','-dTIFFQ=95','-r300','-g2412x3406','-sOutputFile=temp.tiff',pdfFile]
    if(os.path.isfile('temp.tiff')):
        os.remove('temp.tiff')
    subprocess.run(cmd)
    im = Image.open('temp.tiff')
    im.load()
    fpageInfo = extractFirstPage(im)
    fpageInfo.append(bigPDFName) 
    names_lst = cropAndOCR(im,(rangeTuple[0],rangeTuple[1]),boxCoord,voterBoxCoord,boxNumberCoord)
    new_names_lst = [names_lst[i]+fpageInfo for i in range(len(names_lst))]
    with open(outputCSV,'a',newline='',encoding='UTF-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_names_lst)
    
def nameMakerUP(outer,inner):
    return 'AC'+getGoodNames(outer,3)+'_S24A'+getGoodNames(outer,3)+'P'+getGoodNames(inner,3)+'.pdf'
def getGoodNames(num,length):
    d = len(str(num))
    zeros = length-d
    z = ''
    for _ in range(zeros):
        z = z+'0'
    z = z+str(num)
    return z 
def doItAll(outputCSV,boxCoord,voterBoxCoord,boxNumberCoords):
    for outer in range(1,404):
        for inner in range(1,1000):
            pdfName = nameMakerUP(outer,inner)
            print(pdfName) 
            if(not os.path.isfile(pdfName)):
                print('Does not exist')
                break
            print('Processing pdf :'+pdfName)
            noOfPages = PdfFileReader(open(pdfName,'rb')).getNumPages()
            mainProcess(pdfName,(0,noOfPages-1),outputCSV,boxCoord,voterBoxCoord,boxNumberCoords,pdfName)
       

mainBoxCoords = (10,60,510,280)
voterIDCoords = (510,10,750,70)
numberCoords = (8,8,200,40)
doItAll('mycsv.csv',mainBoxCoords,voterIDCoords,numberCoords) 