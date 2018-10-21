import imageio
import re
import time
import pandas as pd
import numpy as np
from wordcloud import WordCloud,STOPWORDS
from os import path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import io

from PIL import ImageFont
from PIL import ImageDraw 
def fileMaker(df):
    names = np.copy(df['Name'].values)
    ages = np.copy(df['Age'].values)
    with open('1911-1915.txt','wb') as f1, open('1916-1920.txt','wb') as f2, open('1921-1925.txt','wb') as f3,open('1926-1930.txt','wb') as f4,open('1931-1935.txt','wb') as f5,open('1936-1940.txt','wb') as f6,open('1941-1945.txt','wb') as f7,open('1946-1950.txt','wb') as f8,open('1951-1955.txt','wb') as f9,open('1956-1960.txt','wb') as f10,open('1961-1965.txt','wb') as f11,open('1966-1970.txt','wb') as f12,open('1971-1975.txt','wb') as f13,open('1976-1980.txt','wb') as f14,open('1981-1985.txt','wb') as f15,open('1986-1990.txt','wb') as f16,open('1991-1995.txt','wb') as f17,open('1996-1999.txt','wb') as f18:
        for i in range(0,len(names)):
            age = ages[i]
            name = names[i].split(" ")[0]
            if age in range(18,22):
                f18.write((name+'\n').encode('utf-8'))
            elif age in range(22,27):
                f17.write((name+'\n').encode('utf-8'))
            elif age in range(27,32):
                f16.write((name+'\n').encode('utf-8'))
            elif age in range(32,37):
                f15.write((name+'\n').encode('utf-8'))
            elif age in range(37,42):
                f14.write((name+'\n').encode('utf-8'))
            elif age in range(42,47):
                f13.write((name+'\n').encode('utf-8'))
            elif age in range(47,52):
                f12.write((name+'\n').encode('utf-8'))
            elif age in range(52,57):
                f11.write((name+'\n').encode('utf-8'))
            elif age in range(57,62):
                f10.write((name+'\n').encode('utf-8'))
            elif age in range(62,67):
                f9.write((name+'\n').encode('utf-8'))
            elif age in range(67,72):
                f8.write((name+'\n').encode('utf-8'))
            elif age in range(72,77):
                f7.write((name+'\n').encode('utf-8'))
            elif age in range(77,82):
                f6.write((name+'\n').encode('utf-8'))
            elif age in range(82,87):
                f5.write((name+'\n').encode('utf-8'))
            elif age in range(87,92):
                f4.write((name+'\n').encode('utf-8'))
            elif age in range(92,97):
                f3.write((name+'\n').encode('utf-8'))
            elif age in range(97,102):
                f2.write((name+'\n').encode('utf-8'))
            elif age in range(102,106):
                f1.write((name+'\n').encode('utf-8'))
def wordCloudMaker(lst,mask):
    for fname in lst:
        d = path.dirname('__file__')
        fileBaseName = fname.split(".")[0]
        txt = io.open(fname,mode='r',encoding='utf-8')
        chandi_mask = np.array(Image.open(path.join(d,mask)))
        stopwords = set(STOPWORDS)
        stopwords.add("said")
        wc = WordCloud(background_color="white", max_words=2000, mask=chandi_mask,stopwords=stopwords)
        wc.generate(txt.read())
        wc.to_file(path.join(d,fileBaseName+".png"))
        img = Image.open(fileBaseName+".png")
        draw = ImageDraw.Draw(img)
        # font = ImageFont.truetype(<font-file>, <font-size>)
        font = ImageFont.truetype("RotisSansSerifStd.otf", 40)
        # draw.text((x, y),"Sample Text",(r,g,b))
        draw.text((200, 250),fileBaseName,(0,0,0),font=font)
        img.save(fileBaseName+'.jpg')

def nameLst():
    texts = "open('1911-1915.txt','wb') as f1, open('1916-1920.txt','wb') as f2, open('1921-1925.txt','wb') as f3,open('1926-1930.txt','wb') as f4,open('1931-1935.txt','wb') as f5,open('1936-1940.txt','wb') as f6,open('1941-1945.txt','wb') as f7,open('1946-1950.txt','wb') as f8,open('1951-1955.txt','wb') as f9,open('1956-1960.txt','wb') as f10,open('1961-1965.txt','wb') as f11,open('1966-1970.txt','wb') as f12,open('1971-1975.txt','wb') as f13,open('1976-1980.txt','wb') as f14,open('1981-1985.txt','wb') as f15,open('1986-1990.txt','wb') as f16,open('1991-1995.txt','wb') as f17,open('1996-1999.txt','wb') as f18"
    lst = []
    texts = texts.split(',')
    for i,text in enumerate(texts):
        if (i%2==0):
            spl = text.split("'")
            lst.append(spl[1])
    return lst   
def imgLstMaker(lst):
    imglst = []
    for fname in lst:
        imglst.append(fname.split(".")[0]+'.jpg')
    return imglst

def gifMaker(imgLst,gifName):
    images = []
    for filename in imgLst:
        images.append(imageio.imread(filename))
    imageio.mimsave(gifName, images,duration=1.5)
    
def upperGIFMaker(df,mask,gifName):
    start = time.time()
    fileMaker(df)
    lst = nameLst()
    wordCloudMaker(lst,mask)
    imgLst = imgLstMaker(lst)
    gifMaker(imgLst,gifName)
    end = time.time()
    print("Took :"+str(end-start))
     