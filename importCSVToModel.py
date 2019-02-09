import os
import django
os.environ['DJANGO_SETTINGS_MODULE']='infer.settings'
django.setup()
from temp.models import VoterDetails
from temp.models import NamePop


import csv
with open('/home/rohit/WORK/dataverse_files/jk_new3.csv','r') as f:
    reader = csv.reader(f)
    lst = []
    for i,row in enumerate(reader):
        print('Adding :'+str(i))
        if(i!=0):
            lst.append(NamePop(
                name = row[0],
                popularity = row[1],
                ssum = row[2],
                yearrange = row[3],
                state = row[4]
                ))
    NamePop.objects.bulk_create(lst)

    
