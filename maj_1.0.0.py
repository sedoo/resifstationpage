# -*- coding: UTF-8 -*-
import matplotlib
matplotlib.use("Agg")
import xml.etree.ElementTree as ET
from obspy import read_inventory
from obspy.geodetics import locations2degrees
from obspy.core import UTCDateTime
from obspy.taup import TauPyModel
from obspy.clients.fdsn import Client
from obspy.signal.trigger import classic_sta_lta, plot_trigger
import math
from copy import deepcopy
import sys
import os

workingFolder ='.'

if len(sys.argv)>1:
    workingFolder = sys.argv[1]
   
print("Working folder: "+workingFolder)

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')


def _pretty_print(current, parent=None, index=-1, depth=0):
    '''
    Affichage elegant de donnees
    '''    
    for i, node in enumerate(current):
        _pretty_print(node, current, i, depth + 1)
    if parent is not None:
        if index == 0:
            parent.text = '\n' + ('\t' * depth)
        else:
            parent[index - 1].tail = '\n' + ('\t' * depth)
        if index == len(parent) - 1:
            current.tail = '\n' + ('\t' * (depth - 1))


class Station:
    '''
        Station.id[XXXX] ===> query
        Station.id[XXXX].code ===> code de la station
        Station.id[XXXX].evts ===> liste des balises evt (evenements) retenues pour cette station
                                   objets quakeml
        Station.id[XXXX].xml = balise de la station dans le fichier xml
        Station.id[XXXX].result ===> True/false definie si la stations est selectionnee pour l'evenement
        Station.id[XXXX].dflag ===> local/region/nation/europe/tele/vtele definie le type de seisme
        Station.id[XXXX].mflag ===> definition du poid de la magnitude
        Station.id[XXXX].duree ===> duree du signal a extraire en fonction du poid de la magnitude et du type d'evt
        Station.id[XXXX].tP ===> temps d'arrivee de l'onde P
        Station.id[XXXX].st ===> signal miniseed
        Station.id[XXXX].distance ===> distance de la station (°)
        
    '''

    def __init__(self, xml, liste_Stations):

        lStations = {}

        #for sta in liste_Stations[0]:
        for sta in liste_Stations:
            print("%s %s %s %s" % (sta.code, sta.latitude, sta.longitude, sta.elevation))
            lStations[sta.code] = sta
            lStations[sta.code].evts = ''

        '''
        station = xml.getElementsByTagName('station')
        for sta in station:
            code = sta.getAttribute('id')
            if code in lStations:
                #lStations[code].evts = sta.childNodes
                lStations[code].evts = sta.getElementsByTagName('evt')
        '''
        for sta in xml.findall('station'):
            code = sta.get('id')
            if code in lStations:
                lStations[code].evts = sta.findall('evt')
                lStations[code].xml = sta

        self.id = lStations

    def zone_evt(self, evt, station):
        '''
        definie la zone de l'evenement par rapport à la position de la station
        '''

        for key, value in self.id.items():
            #distance = locations2degrees(latEvt, lonEvt, value.latitude, value.longitude)
            distance = locations2degrees(evt.origins[0].latitude, evt.origins[0].longitude, station.latitude, station.longitude)
            #Station.id[key].distance = distance

            # calcule le temp d'arrivée de l'onde P
            model = TauPyModel(model="iasp91")
            arrival = model.get_travel_times(source_depth_in_km=abs(evt.origins[0].depth/1000), distance_in_degree=distance)
            tP = UTCDateTime(evt.origins[0].time) + arrival[0].time
            #print("time:%s prof:%s distance:%s tP:%s deltaP:%s dflag:%s mflag=%s" % (evt.origins[0].time, evt.origins[0].depth, distance, tP, arrival[0].time, dflag, mflag))
            print("time:%s prof:%s distance:%s tP:%s deltaP:%s" % (evt.origins[0].time, evt.origins[0].depth, distance, tP, arrival[0].time))

            # localisation de la zone
            if distance <= 1:
                dflag = "local"
            elif distance <= 2:
                dflag = "region"
            elif distance <= 7:
                dflag = "nation"
            elif distance <= 20:
                dflag = "europe"
            elif distance <= 100:
                dflag = "tele"
            else:
                dflag = "vtele"

            # definition du poid de la magnitude
            if evt.magnitudes[0].mag <= 1.5:
                mflag = 0
            elif evt.magnitudes[0].mag <= 3:
                mflag = 1
            elif evt.magnitudes[0].mag <= 3.5:
                mflag = 2
            elif evt.magnitudes[0].mag <= 4:
                mflag = 3
            elif evt.magnitudes[0].mag <= 4.5:
                mflag = 4
            elif evt.magnitudes[0].mag <= 5:
                mflag = 5
            elif evt.magnitudes[0].mag <= 5.5:
                mflag = 6
            elif evt.magnitudes[0].mag <= 6:
                mflag = 7
            elif evt.magnitudes[0].mag <= 6.5:
                mflag = 8
            else:
                mflag = 9

            result = "true"
            # calcule la duree du signal qui nous interresse
            if dflag == "local" and mflag == 0:
                result = "false"
                duree = "0"
                #return
            if dflag == "local" and mflag <= 2:
                duree = "60"
            if dflag == "local" and mflag == 3:
                duree = "90"
            if dflag == "local" and mflag == 4:
                duree = "120"
            if dflag == "local" and mflag == 5:
                duree = "150"
            if dflag == "local" and mflag == 6:
                duree = "240"
            if dflag == "local" and mflag > 6:
                duree = "300"
            if dflag == "region" and mflag <= 1:
                result = "false"
                duree = "0"
                #return
            if dflag == "region" and mflag == 2:
                duree = "90"
            if dflag == "region" and mflag == 3:
                duree = "120"
            if dflag == "region" and mflag == 4:
                duree = "180"
            if dflag == "region" and mflag == 5:
                duree = "240"
            if dflag == "region" and mflag > 5:
                duree = "300"
            if dflag == "nation" and mflag <= 2:
                result = "false"
                duree = "0"
                #return
            if dflag == "nation" and mflag <= 4:
                duree = "180"
            if dflag == "nation" and mflag == 5:
                duree = "300"
            if dflag == "nation" and mflag > 5:
                duree = "480"
            if dflag == "europe" and mflag <= 5:
                result = "false"
                duree = "0"
                #return
            if dflag == "tele" and mflag <= 6:
                result = "false"
                duree = "0"
                #return
            if dflag == "vtele" and mflag <= 6:
                result = "false"
                duree = "0"
                #return

            dfactor = 20 / math.sqrt(distance)
            dtRaP = distance / 0.0315 - arrival[0].time

            if dflag == "europe" or dflag == "tele" or dflag == "vtele":
                duree = dfactor * arrival[0].time
            if dflag == "europe" and mflag < 6 or dflag == "tele" and mflag < 7 or dflag == "vtele" and mflag < 8:
                duree = 0.7 * duree

            #return dflag, mflag, duree, arrival[0].time
            return dflag, mflag, duree, tP, distance, result

    def comp_magnitude(self, evt):
        '''
        compare la magnitude de l'evenement actuel avec celle de l'evenement affiché
        '''
        for key, value in self.id.items():
            #self.id[key].result = "true"
            loc = self.zone_evt(evt, value)
            self.id[key].result = loc[5]

            if self.id[key].result == "false":
                print("stop")
                continue

            if loc[0] is "local" or loc[0] is "region" or loc[0] is "nation":
                #t_lastEvt = UTCDateTime(self.id[key].evts[1].getAttribute('date'))
                t_lastEvt = UTCDateTime(self.id[key].evts[0].get('date'))
            else:
                #t_lastEvt = UTCDateTime(self.id[key].evts[3].getAttribute('date'))
                t_lastEvt = UTCDateTime(self.id[key].evts[1].get('date'))

            deltaT = evt.origins[0].time - t_lastEvt

            if deltaT > 0:
                dMag = -0.7 * deltaT / 86400 - 0.5
            else:
                dMag = -0.7 * deltaT / 3600 - 0.5
            print("%s %s %s distance=%s" % (key, deltaT, dMag, loc[4]))

            '''
            if evt.magnitudes[0].mag > dMag and evt.magnitudes[0].mag <=  loc[4]:
                self.id[key].result = "true"
            else:
                self.id[key].result = "false"
            '''
            #if evt.magnitudes[0].mag <= dMag or evt.magnitudes[0].mag <= loc[4]:
            if evt.magnitudes[0].mag <= dMag:
                print("%s <= %s || %s <= %s" % (evt.magnitudes[0].mag, dMag, evt.magnitudes[0].mag, loc[4]))
                self.id[key].result = "false"

            if loc[0] == "europe" and evt.magnitudes[0].mag <= 4 or loc[0] == "tele" and evt.magnitudes[0].mag <= 5.5 or loc[0] == "vtele" and evt.magnitudes[0].mag <= 6:
                self.id[key].result = "false"

            self.id[key].dflag = loc[0]
            self.id[key].mflag = loc[1]
            self.id[key].duree = loc[2]
            self.id[key].tP = loc[3]
            self.id[key].distance = loc[4]

    def comp_signal(self, evt):
        '''
        visualise le rapport sta/lta
        '''
        for key, value in self.id.items():
            if self.id[key].result == "false":
                print("stop")
                continue
            print(self.id[key].tP)
            t0 = UTCDateTime(self.id[key].tP) - int(self.id[key].duree) / 5 
            t1 = UTCDateTime(self.id[key].tP) + int(self.id[key].duree)
            print('st = client.get_waveforms("FR", "%s", "00", "HHZ", "%s", "%s")' % (key, t0, t1))
            try:
                #st = client.get_waveforms("FR", key, "00", "H?Z", t0, t1)
                st = client.get_waveforms("FR", key, "00", "HHZ", t0, t1)
                st_data = deepcopy(st)
            except Exception as err:
                print('Pas de data\n%s' % err)
                self.id[key].result = "false"
                continue
            #st_f = st[0].filter("highpass", freq=2, corners=2, zerophase=True)
            tr = st[0].copy()
            st_f = tr.filter("highpass", freq=0.2, corners=2, zerophase=True)
            df = st[0].stats.sampling_rate
            cft = classic_sta_lta(st_f, int(df / 2), int(df * 5))
            #plot_trigger(st_f, cft, 7, 4)
            print(max(cft))

            #if max(cft) >= 7:
            if max(cft) >= 6:
                self.id[key].result = "true"
                #self.id[key].st = st[0]
                self.id[key].st = st_data[0]
                #self.id[key].evts[1].new = evt
            else:
                self.id[key].result = "false"

    def cree_jpg (self, evt):

        for key, value in self.id.items():
            if self.id[key].result == "false":
                print("stop")
                continue
            t0 = UTCDateTime(self.id[key].tP) - int(self.id[key].duree) / 5
            t1 = UTCDateTime(self.id[key].tP) + int(self.id[key].duree)
            print("%s creation jpg st.plot(starttime=%s, endtime=%s, outfile='%s/jpg/%s_trace_%s.jpg'" % (key, t0, t1, workingFolder, key, self.id[key].dflag))
            if self.id[key].distance <= 10:
                st_f = self.id[key].st.filter("highpass", freq=2, corners=2, zerophase=True)
                st_f.plot(starttime=t0+5, endtime=t1, outfile="%s/jpg/%s_trace_%s.jpg" % (workingFolder, key, self.id[key].dflag), linewidth="0.3")
            else:
                self.id[key].st.plot(starttime=t0, endtime=t1, outfile="%s/jpg/%s_trace_%s.jpg" % (workingFolder, key, self.id[key].dflag), linewidth="0.3")

            
    def modif_xml (self, evt, xml):

        for key, value in self.id.items():
            if self.id[key].result == "false":
                print("stop")
                continue
            print("%s modifie xml" % key)

            n = 0
            if self.id[key].dflag in ["local", "region", "nation"]:
                print ("local")
                n = 0
            else:
                print ("tele")
                n = 1

            #print(self.id[key].xml.attrib)
            #self.id[key].xml.nodeChild[n].attrib[date] = evt.origins[0].time

            # generation dateTxt (YYYY/MM/JJ HH:MN)
            dateObspy = UTCDateTime(evt.origins[0].time)
            dateTxt = "%s/%s/%s %s:%s:%s" % (dateObspy.year, dateObspy.month, dateObspy.day, dateObspy.hour, dateObspy.minute, dateObspy.second)
            print("%s/%s/%s %s:%s:%s" % (dateObspy.year, dateObspy.month, dateObspy.day, dateObspy.hour, dateObspy.minute, dateObspy.second))

            element = self.id[key].xml.findall('evt')
            element[n].set('date', str(evt.origins[0].time))
            element[n].set('dateTxt', str(dateTxt))
            element[n].set('lat', str(evt.origins[0].latitude))
            element[n].set('lon', str(evt.origins[0].longitude))
            element[n].set('mag', str(evt.magnitudes[0].mag))
            element[n].set('dist', str(self.id[key].distance))
            element[n].find('trace').text = "%s_trace_%s.jpg" % (key, self.id[key].dflag)
            #element[n].find('trace').text = "./jpg/%s.%s.jpg" % (evt.origins[0].time, key)
            #print("XML : %s " % ET.tostring(self.id[key].xml.findall('evt')[n]))


deltaT = 86500
#deltaT = 3600
t0 = UTCDateTime()
#t0 = UTCDateTime("2022-11-10T00:00:00")
t1 = t0 - deltaT
#t1 = UTCDateTime("2022-09-19T18:00:00")

stationsXML = workingFolder+'/stations_FR.xml'

# verification de l'arborescence des répertoires et de la présence des fichiers
os.makedirs(workingFolder+"/jpg", exist_ok=True)
if os.path.exists(stationsXML):
    pass
else:
    file = open(stationsXML, "w")
    file.write("<stations></stations>")
    file.close()

# liste les evts vus par le reseau RESIF
client = Client("http://ws.resif.fr")
liste_RESIF = client.get_events(
    starttime=t1,
    endtime=t0,
    minmagnitude=1,
    eventtype="earthquake,induced or triggered event",
    #limit=10,
    )
# liste les evts inventoriés dans IRIS
#client = Client("http://service.iris.edu")
client = Client("IRIS")
try:
    liste_IRIS = client.get_events(
        starttime=t1,
        endtime=t0,
        minmagnitude=5,
        )
    liste_Evt = liste_RESIF + liste_IRIS
except:
    liste_Evt = liste_RESIF
    pass


# inventorie les stations RESIF
#client = Client("http://ws.resif.fr")
client = Client("RESIF")
liste_Stations = client.get_stations(
    network="FR",
    starttime=t1,
    endtime=t0,
    #sta="DOU",
    format="text",
    )

# préparation du fichier stationsXML (création d'un noeud par station contenant, en plus des renseignements sur la station, les derniers evts à afficher pour cette station
list_in_xml = {}
xml_ID = []
xml = ET.parse(stationsXML)
stations = xml.getroot()

for sta in stations:
    list_in_xml[sta.attrib['id']] = sta
    xml_ID.append(sta.attrib['id'])

for sta in liste_Stations[0]:
    if sta.code not in xml_ID:
        print("===> %s %s %s" % (sta.code, sta.latitude, sta.longitude))
        newSta = ET.SubElement(stations, 'station')
        newSta.attrib = {
            'id': sta.code,
            'lat': str(sta.latitude),
            'lon': str(sta.longitude),
        }
        
        newEvt = ET.SubElement(newSta, 'evt')
        newEvt.attrib = {
            'class': 'local',
            'lat': '0',
            'lon': '0',
            'mag': '0',
            'date': '2000-01-01T00:00:00',
        }

        newTrace = ET.SubElement(newEvt, 'trace')
        
        newEvt = ET.SubElement(newSta, 'evt')
        newEvt.attrib = {
            'class': 'tele',
            'lat': '0',
            'lon': '0',
            'mag': '0',
            'date': '2000-01-01T00:00:00',
        }

        newTrace = ET.SubElement(newEvt, 'trace')

# initialise l'objet station
station = Station(xml, liste_Stations[0])
#print(station.id['ATE'].evts)



for evt in liste_Evt:
    print("####################################################### %s %s %s %s ####################################################" % (evt.origins[0].time, evt.origins[0].latitude, evt.origins[0].longitude, evt.origins[0].depth))
    ##print(evt.magnitudes[0].mag)
    try:
        station.comp_magnitude(evt)
        station.comp_signal(evt)
        station.cree_jpg(evt)
        station.modif_xml(evt, xml)
    except:
        print("erreur pour l'evt evt.origins[0].time")
        pass

#station.trace_journaliere()

_pretty_print(stations)
print(ET.tostring(stations))

with open(stationsXML, 'wb') as f:
    xml.write(f, encoding='utf-8')
