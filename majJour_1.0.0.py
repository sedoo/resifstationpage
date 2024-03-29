# -*- coding: UTF-8 -*-

from obspy.clients.fdsn import Client
from obspy.core import UTCDateTime
import subprocess
import os
import sys
import shutil

workingFolder ='.'
sta_id_lst = ['A*,B*,C*,D*,E*,F*,G*,H*,I*,J*,K*,L*,M*', 'N*,O*,P*,Q*,R*,S*,T*,U*,V*,W*,X*,Y*,Z*']
if len(sys.argv)>1:
    workingFolder = sys.argv[1]
    sta_id_lst = sta_id_lst[int(sys.argv[2])]
    jsonOut = sys.argv[3]
   
print("Working folder: %s\nStation list: %s\nJson file out: %s " % (workingFolder, sta_id_lst, jsonOut))

deltaT = 86500
t0 = UTCDateTime()
t1 = t0 - deltaT

# verification de l'arborescence des répertoires et de la présence des fichiers
os.makedirs(workingFolder+"/json", exist_ok=True)

client = Client("RESIF")
liste_Stations = client.get_stations(
    network="FR",
    starttime=t1,
    endtime=t0,
    sta=sta_id_lst,
    channel="HHZ",
    level="channel"
    )

### preparation du fichier json
#ficTmp = workingFolder+"/json/stations_FR.tmp"
#ficJson = workingFolder+"/json/stations_FR.json"
ficJson = workingFolder+"/json/"+jsonOut
json = """{
    "type": "FeatureCollection",
    "features": ["""
f = open(ficJson, 'w')
f.write(json)
f.close()

for sta in liste_Stations[0]:
    #if sta.code=="VILS":
    #    pass
    ### creation des fichiers journaliers
    print("fichier journalier de la station %s" % sta.code)
    #tday0 = UTCDateTime(t0.year, t0.month, t0.day-1)
    tday0 = t0 - 86400
    tday0 = UTCDateTime(tday0.year, tday0.month, tday0.day)
    tday1 = UTCDateTime(t0.year, t0.month, t0.day)
    try:
        ficout = workingFolder+"/jpg/%s_journalier.png" % sta.code
        #st = client.get_waveforms("FR", sta.code, "00", "HHZ", tday0, tday1)
        st = client.get_waveforms("FR", sta.code, "00", "HHZ", t1, t0)
        # creation du jpg
        echelle = sta[0].response.instrument_sensitivity.value*2*10e-7
        st_f = st[0].filter("highpass", freq=0.01, corners=2, zerophase=True)
        st_f.plot(type="dayplot", linewidth="0.5", vertical_scaling_range=echelle, outfile=ficout)
        #st.plot(type="dayplot", outfile=ficout)
        print("===> %s" % ficout)
    except:
        pass

    ### creation des stats
    print("fichier json et histogramme de la station %s" % sta.code)
    try:
        ficstat = workingFolder+"/jpg/%s_stats.jpg" % sta.code
        ficjson = workingFolder+"/json/%s.json" % sta.code
        pythonEnvPath = "../venv/bin/python"
        subprocess.run([pythonEnvPath, "./stat_ws_json.py", sta.code, "-b", ficstat, "-o", ficjson])
        print("===> %s" % ficstat)
        print("===> %s" % ficjson)
    except:
        pass
    
    # ajout de la station à la liste json
    print("ajout de la station %s a la liste json" % sta.code)
    try:
        json = """
            {
                    "type": "Feature",
                    "properties": {
                        "code": "%s",
                        "agence": "%s",
                        "en service depuis le": "%s"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [%s, %s]
                    }
            },""" % (sta.code, sta.operators[0].agencies[0], sta.creation_date, sta.longitude, sta.latitude)
        with open(ficJson, 'a') as f:
            f.write(json)
    except:
        pass


json = """
        {}
    ]
}"""
with open(ficJson, 'a') as f:
    f.write(json)
#shutil.copy2(ficTmp, ficJson)
