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
    '''(' bI.', 'B.'),
 (' sI.', 'C.'),
 (' DI.', 'D.'),
 (' epha.', 'F.'),
 (' jI.', 'G.'),
 (' echa.', 'H.'),
 (' ke.', 'K.'),
 (' ela.', 'L.'),
 (' ema.', 'M.'),
 (' em.','M.'),        
 (' ena.', 'N.'),
 (' o.', 'O.'),
 (' pI.', 'P.'),
 (' Ara.', 'R.'),
 (' esa.', 'S.'),
 (' TI.', 'T.'),
 (' yU.', 'U.'),
 (' vI.', 'V.'),
 (' DablyU.', 'W.'),
 (' eksa.', 'X.'),
 (' vAI.', 'Y.'),  
 (' jeDa.', 'Z.'),
 (' kyU.', 'Q.'),    
 (' je.', 'J.'),    
 (' AI.', 'I.'),
 (' I.', 'E.'),
 (' e.', 'A.'),'''
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
def dealWithDOT(name):
    name = muhammadification(name)
    name,dotNM = nameStops(name)
    dots = findOccurrences(name,'.')
    for i,val in enumerate(dotNM):
        if val:
            name = name[:dots[i]]+name[dots[i]+1:]
    return name
def findOccurrences(s, ch):# taken from: https://stackoverflow.com/a/13009866/5345646
    return [i for i, letter in enumerate(s) if letter == ch]
