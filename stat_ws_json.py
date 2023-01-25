#!/usr/bin/env python3
"""
:author:
    Helene Jund (helene.jund@unistra.fr)
    Marc Grunberg (marc.grunberg@unistra.fr)

:copyright:
    Helene Jund (helene.jund@unistra.fr)

:license:
    The Beerware License
    (https://tldrlegal.com/license/beerware-license)

Usage:
    stats_ws.py <station_code> [-r <radius>] [-d <delta>] [-e <end>] \
[-o <output_file>] [-s <fdsn>] [-w <event>] [-b <image_file>] 

Options:
    -h --help             Show this screen.
    -r <radius>           Distance around the station in degres [default: 1.2].
    -d <delta>            Delta time in the past in days [default: 7].
    -e <end>              End time in obspy.core.UTCDateTime format, NOW by default.
    -o <output_file>      Set output json file.
    -s <fdsn>             Set base url of fdsn response server [default: http://ws.resif.fr/].
    -w <event>            Set base url of event webservice server [default: https://api.franceseisme.fr/fdsnws/event/1/].
    -b <image_file>       Show and set the bar graph image
    
"""
import matplotlib
matplotlib.use('Agg')
from docopt import docopt
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
from geojson import Feature, Point, dump, FeatureCollection

if __name__ == '__main__':

    args = docopt(__doc__, version='stat_ws 1.0')
    # Uncomment for debug
    # print(args)

    if args['-e'] is None:
        t0 = UTCDateTime()
    else:
        t0 = UTCDateTime(args['-e'])
    delta_s = int(args['-d']) *24 * 60 * 60
    t1 = t0 - delta_s

    # Recupération des coordonnées gps de la station via le web service de resif
    data = Client(base_url=args['-s'])
    inv = data.get_stations(station=args['<station_code>'],starttime=t1, endtime=t0)
    latitude = inv[0][0].latitude
    longitude = inv[0][0].longitude

    max_radius = args['-r']  # degres

    fdsn_debug = False
    ws_event_url = args['-w']

    # récupération de tous les seismes autour de la station sur un rayon <radius> et sur une durée <delta> 
    client = Client(debug=fdsn_debug, service_mappings={"event": ws_event_url})
    try:
        cat = client.get_events(
              starttime=t1,
              endtime=t0,
              latitude=latitude,
              longitude=longitude,
              maxradius=max_radius,
              eventtype='earthquake',
              includeallorigins=False,
              includearrivals=True,
              )
    except Exception as err:
        print(err)
        cat = []
    
    list_date = []
    list_eve = []
    list_map = []


    # récupération des seismes où la station à été utilisé
    for event in cat:
        event_id = str(event.resource_id).split("/")[-1]
        orig = event.preferred_origin()
        magnitude = event.preferred_magnitude()
        for arrival in orig.arrivals: 
            if arrival.time_weight:
                pick = next(
                (p for p in event.picks if p.resource_id == arrival.pick_id), None
                )  
                if pick:
                    try:
                        if pick.waveform_id.station_code == args['<station_code>'] and event_id != list_eve[-1][0]:
                            detail_eve = str(event.event_descriptions[0]).split("'")[-2].replace("Earthquake of magnitude","Seisme de magnitude").replace("near of","proche de")
                            time_eve = str(orig.time).split(".")[0]
                            detail_eve_time = "%s %s" % (time_eve,detail_eve)
                            url_eve_renass = "https://renass.unistra.fr/fr/evenements/%s/" % (event_id)
                            mag = "%.1f" % (magnitude.mag)
                            my_point = Point((orig.longitude,orig.latitude))
                            point_map = Feature(geometry=my_point,properties={"url":url_eve_renass, "description":detail_eve_time},sort_keys=True)
                            list_map.append(point_map)
                            list_eve.append([event_id, url_eve_renass, detail_eve, orig.time, orig.latitude, orig.longitude, mag])
                            list_date.append(pick.time)
                    except:
                        if pick.waveform_id.station_code == args['<station_code>']:
                            detail_eve = str(event.event_descriptions[0]).split("'")[-2].replace("Earthquake of magnitude","Seisme de magnitude").replace("near of","proche de")
                            time_eve = str(orig.time).split(".")[0]
                            detail_eve_time = "%s %s" % (time_eve,detail_eve)
                            url_eve_renass = "https://renass.unistra.fr/fr/evenements/%s/" % (event_id)
                            mag = "%.1f" % (magnitude.mag)
                            my_point = Point((orig.longitude,orig.latitude))
                            point_map = Feature(geometry=my_point,properties={"url":url_eve_renass, "description":detail_eve_time},sort_keys=True)
                            list_map.append(point_map)
                            list_eve.append([event_id, url_eve_renass, detail_eve, orig.time, orig.latitude, orig.longitude, mag])
                            list_date.append(pick.time)
#    print(list_eve)   
    data_map = FeatureCollection(list_map)

    if args['-o']:
        with open(args['-o'], "w") as outfile:
            dump(data_map, outfile)

    if args['-b']:
        import matplotlib.pyplot as plt
        day1 = t1
        date = []
        event = []
        date.append(day1.date)
        nb_event = 0

        for selection in list_eve:
            day = selection[3]
            if day.date == date[-1]:
                nb_event += 1
            else:
                event.append(nb_event)
                nb_event = 1
                date.append(day.date)
        event.append(nb_event)
        if date[-1] != t0.date:
            date.append(t0.date)
            event.append(int(0))


#        ax = plt.subplot(1,1,1)
        ax = plt.subplot()
        ax.bar(date, event)
        for label in ax.get_xticklabels():
            label.set_rotation(20)
#            label.set_horizontalalignment('right')
#        ax.xaxis_date()
#        plt.show()
        plt.savefig(args['-b'])
