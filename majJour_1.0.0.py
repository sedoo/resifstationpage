# -*- coding: UTF-8 -*-

from obspy.clients.fdsn import Client
from obspy.core import UTCDateTime
import subprocess
import os
import sys

workingFolder ='.'
if len(sys.argv)>1:
    workingFolder = sys.argv[1]
   
print("Working folder: "+workingFolder)

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
#    sta="LABF",
    format="text",
    )

for sta in liste_Stations[0]:

    ### creation des fichiers journaliers
    print("fichier journalier de la station %s" % sta.code)
    tday0 = UTCDateTime(t0.year, t0.month, t0.day-1)
    tday1 = UTCDateTime(t0.year, t0.month, t0.day)
    try:
        ficout = workingFolder+"/jpg/%s_journalier.png" % sta.code
        st = client.get_waveforms("FR", sta.code, "00", "HHZ", tday0, tday1)
        st.plot(type="dayplot", outfile=ficout)
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
