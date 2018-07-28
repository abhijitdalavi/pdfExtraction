#@numba.jit
def nameStops(name):
    dots = findOccurrences(name,'.')
    dotNM = [True]*len(dots)
    if '.' in name:
        for mp in mapping:
            if mp[0] in name:
                idx = name.find(mp[0])
                if(idx==0 or name[idx-1]==' ' or name[idx-1]=='.'):
                    name = name.replace(mp[0],mp[1])
                    for i,dt in enumerate(dots):
                        if idx<dt:
                            dotNM[i] = False 
                            break
                
            if mp[0].title() in name:
                idx = name.find(mp[0].title())
                if(idx==0 or name[idx-1]==' ' or name[idx-1]=='.'):
                    name = name.replace(mp[0].title(),mp[1])
                    for i,dt in enumerate(dots):
                        if idx<dt:
                            dotNM[i] = False 
                            break
    return name,dotNM             
mapping = [('bI.', 'B.'),
 ('sI.', 'C.'),
 ('DI.', 'D.'),
 ('epha.', 'F.'),
 ('jI.', 'G.'),
 ('echa.', 'H.'),
 ('ke.', 'K.'),
 ('ela.', 'L.'),
 ('ema.', 'M.'),
 ('em.','M.'),        
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
 ('ai.','A'),
           
           
 ('bI ', 'B. '),
 ('sI ', 'C. '),
 ('DI ', 'D. '),
 ('epha ', 'F. '),
 ('jI ', 'G. '),
 ('echa ', 'H. '),
 ('ke ', 'K. '),
 ('ela ', 'L. '),
 ('ema ', 'M. '),
 ('em ', 'M. '),
 ('ena ', 'N. '),
 ('o ', 'O. '),
 ('pI ', 'P. '),
 ('Ara ', 'R. '),
 ('esa ', 'S. '),
 ('TI ', 'T. '),
 ('yU ', 'U. '),
 ('vI ', 'V. '),
 ('DablyU ', 'W. '),
 ('eksa ', 'X. '),
 ('vAI ', 'Y. '),
 ('jeDa ', 'Z. '),
 ('kyU ', 'Q. '),
 ('je ', 'J. '),
 ('AI ', 'I. '),
 ('I ', 'E. '),
 ('e ', 'A. ')
          
          ]    
#@numba.jit
def muhammadification(name):
    mohds = ['mo.', 'moha.', 'mohamada.', 'mohammada.']
    for i in mohds:
        if i in name:
            idx = name.find(i)
            if(idx+len(i)<len(name) and name[idx+len(i)]!=' '):
                name = name.replace(i,'Muhammad ')
            else:
                name = name.replace(i,'Muhammad')
    return name
#@numba.jit
def dealWithDOT(name):
    name = muhammadification(name)
    name,dotNM = nameStops(name)
    dots = findOccurrences(name,'.')
    for i,val in enumerate(dotNM):
        if val:
            name = name[:dots[i]]+name[dots[i]+1:]
    return name
#@numba.jit
def findOccurrences(s, ch):# taken from: https://stackoverflow.com/a/13009866/5345646
    return [i for i, letter in enumerate(s) if letter == ch]
#@numba.jit
def dealWithTilde(name):
    if '~' in name:
        name = name.replace('j~n','gy')
    return name 
#@numba.jit
def dealWithChandra(name):
    if 'ॉ' in name:
        name = name.replace('ॉ','u')
    return name
#@numba.jit
def dealWithZWJ(name):
    if '\u200d' in name:
        name = name.replace('\u200d','')
    return name
#@numba.jit
def dealWithNuqta(name):
    if '़' in name:
        name = name.replace('़','')
    return name
#@numba.jit
def dealWithAnudatta(name):
    if '॒' in name:
        name = name.replace('a'+chr(2386),'')
    return name
#@numba.jit
def dealWithZWNJ(name):
    if '\u200d' in name:
        name = name.replace('\u200d','')
    return name  
#@numba.jit

def nameMagic(df):
    names = np.copy(df['Name'].values)
    delLst,col = nameMagicCol(names)
    dfNew = df.copy(deep=True)
    dfNew['Name'] = col
    #print(':::: '+str(len(dfNew)))
    #print(str(delLst))
    dfNew = dfNew.drop(dfNew.index[delLst]) #Why is this not working?
    #print(':::: '+str(len(dfNew)))
    dfNew = dfNew.reset_index(drop=True)
    return dfNew
# 42s no-numba   
# numpy 1.54 s
def tester(name):
    
    name = dealWithDOT(name)
    name = dealWithZWJ(name)
    #print('Name after ZWJ:'+name)
    name = dealWithChandra(name)
    name = dealWithNuqta(name)
    name = dealWithZWNJ(name)
    name = dealWithAnudatta(name)
    name = dealWithTilde(name)
    noSpaces = name.replace(' ','') 
    noSpaces = noSpaces.replace('.','')
    return name 
def nameMagicCol(col):
    delLst = []
    for i in range(len(col)):
        name = col[i]
        name = dealWithDOT(name)
        name = dealWithZWJ(name)
        #print('Name after ZWJ:'+name)
        name = dealWithChandra(name)
        name = dealWithNuqta(name)
        name = dealWithZWNJ(name)
        name = dealWithAnudatta(name)
        name = dealWithTilde(name)
        noSpaces = name.replace(' ','') 
        noSpaces = noSpaces.replace('.','')
        #print('noSpaces :'+noSpaces)
        if not noSpaces.isalpha():
            delLst.append(i)
            print('removing '+str(i))
        else:
            col[i] = name   
    return delLst,col           

    
