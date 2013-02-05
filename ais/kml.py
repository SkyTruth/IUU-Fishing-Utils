import logging
import re
from string import Template
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta
import sys
import bisect
   
   
MIN_INTERVAL = 60   # minimum interval between placemarks in seconds


time_gap_styles = [
    {
        'range': (0, (3600 * 12)),
        'style': 'trackStyle1'
    },
    {
        'range': ((3600 * 12), (3600 * 48)),
        'style': 'trackStyle2'
    },
    {
        'range': ((3600 * 48), sys.maxint),
        'style': 'trackStyle3'
    },
]



document_kml_template = Template(
"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>$name</name>
	<StyleMap id="vesselStyleMap">
		<Pair>
			<key>normal</key>
			<styleUrl>#normVesselStyle</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#hlightVesselStyle</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="hlightVesselStyle">
		<IconStyle>
            <scale>1.2</scale>  
    		<color>ff006666</color>
			<Icon>
				<href>http://alerts.skytruth.org/markers/vessel_direction.png</href>
			</Icon>
            <hotSpot x="16" y="3" xunits="pixels" yunits="pixels"/>
		</IconStyle>
        <LabelStyle><color>ff999999</color><scale>0.8</scale></LabelStyle>
	</Style>
	<Style id="normVesselStyle">
		<IconStyle>
		  <color>ff009999</color>
		  <Icon><href>http://alerts.skytruth.org/markers/vessel_direction.png</href></Icon>
          <hotSpot x="16" y="3" xunits="pixels" yunits="pixels"/>
		</IconStyle>
        <LabelStyle><scale>0</scale></LabelStyle>
	</Style>
	<StyleMap id="trackStyle1">
		<Pair>
			<key>normal</key>
			<styleUrl>#normTrackStyle1</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#hlightTrackStyle1</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="hlightTrackStyle1">
		<LineStyle>
			<color>ff999999</color>
			<width>2</width>
		</LineStyle>
	</Style>
	<Style id="normTrackStyle1">
		<LineStyle>
			<color>ff999999</color>
			<width>1.2</width>
		</LineStyle>
	</Style>	
	<StyleMap id="trackStyle2">
		<Pair>
			<key>normal</key>
			<styleUrl>#normTrackStyle2</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#hlightTrackStyle2</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="hlightTrackStyle2">
		<LineStyle>
			<color>ff00ffff</color>
			<width>6</width>
		</LineStyle>
	</Style>
	<Style id="normTrackStyle2">
		<LineStyle>
			<color>ff00ffff</color>
			<width>4</width>
		</LineStyle>
	</Style>	
	<StyleMap id="trackStyle3">
		<Pair>
			<key>normal</key>
			<styleUrl>#normTrackStyle3</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#hlightTrackStyle3</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="hlightTrackStyle3">
		<LineStyle>
			<color>ff0000ff</color>
			<width>6</width>
		</LineStyle>
	</Style>
	<Style id="normTrackStyle3">
		<LineStyle>
			<color>ff0000ff</color>
			<width>4</width>
		</LineStyle>
	</Style>		
    $vessels_kml
</Document>
</kml>
"""	)


vessel_kml_template = Template(
"""<Folder>
    <name>$name</name>
<Folder>
    <name>Vessel Tracks</name>
$track_kml
</Folder>

<Folder>
    <name>AIS Points</name>
$placemarks_kml
</Folder>

</Folder>
"""	 )



track_template = Template (
"""	<Placemark>
	<name>$name</name>
	<styleUrl>#$style</styleUrl>
	<LineString>
		<tessellate>1</tessellate>
		<coordinates>
		    $coords
		</coordinates>
	</LineString>
	<TimeSpan><begin>$time_begin</begin><end>$time_end</end></TimeSpan>
 	
</Placemark>""")
	

placemark_template = Template(
"""<Placemark>
    <name>$datetime</name>
    <description>
<table width="300">
    <tr><th align="right">Vessel Name</th><td>$name</td></tr>
    <tr><th align="right">Vessel Type</th><td>$type</td></tr>
    <tr><th align="right">MMSI</th><td>$mmsi</td></tr>
    <tr><th align="right">Length</th><td>$length meters</td></tr>
    <tr><th align="right">Datetime</th><td>$datetime</td></tr>
    <tr><th align="right">True Heading</th><td>$true_heading</td></tr>
    <tr><th align="right">Speed Over Ground</th><td>$sog</td></tr>
    <tr><th align="right">Course Over Ground</th><td>$cog</td></tr>
    <tr><th align="right">Latitude</th><td>$latitude</td></tr>
    <tr><th align="right">Longitude</th><td>$longitude</td></tr>
    <tr><th align="right">Vessel Info</th><td><a href="$marinetraffic_url">marinetraffic.com</a> <a href="$itu_url">ITU</a></td></tr>
</table>    
    </description>    
	<styleUrl>#vesselStyleMap</styleUrl>
    <TimeStamp><when>$timestamp</when></TimeStamp>
    <Point>
        <coordinates>$longitude,$latitude,0</coordinates>
    </Point>
    <Style><IconStyle><heading>$cog</heading><color>$icon_color</color></IconStyle></Style>
</Placemark>""")



class Vessel ():
    def __init__(self, params):
        self.mmsi = params['mmsi']  # This can't be null
        self.name = params.get('name')
        self.vessel_type = params.get('type'),
        self.length = params.get('length'),
        self.url = params.get('url')
        self.marinetraffic_url = params.get('marinetraffic_url')
        self.itu_url = params.get('itu_url')
        self.ais = []
        self.timestamps = []
            
    def add_ais (self, ais):
        idx = 0
        dt = ais['datetime']
        if self.ais:
            # ignore anything that is less than MIN_INTERVAL seconds away from a record we already have in the list
            idx = bisect.bisect (self.timestamps,dt)
            if idx > 0 and abs(interval_total_seconds(dt - self.timestamps[idx-1])) < MIN_INTERVAL:
                return
            if idx < len(self.timestamps) and abs(interval_total_seconds(dt - self.timestamps[idx])) < MIN_INTERVAL:
                return
        self.timestamps.insert (idx, dt)
        self.ais.insert (idx, ais)

def interval_total_seconds(interval):
    return (interval.microseconds + (interval.seconds + interval.days * 24 * 3600) * 10**6) / 10**6

    
def get_vessel_kml (vessel, mmsi):
    params = {'name': vessel.name}
    params['placemarks_kml'] = '\n'.join([get_placemark_kml(ais) for ais  in vessel.ais])
    params['track_kml'] = get_track_kml (vessel)
    return vessel_kml_template.substitute (params)
    

def get_placemark_kml (record):
    params = record
    params['timestamp'] = record['datetime'].strftime ('%Y-%m-%dT%H:%M:%SZ') 
    try:
        c = min(float(record['sog']), 15) * 17
    except:
        c = 0    
        
    params['icon_color'] = 'ff00%02x%02x' % (c, 255-c)
    return  placemark_template.substitute (params)


def get_time_gap_style (dt, last_dt):
    td = interval_total_seconds(dt - last_dt)
    for s in time_gap_styles:
        if td >= s['range'][0] and td < s['range'][1]:
            return s

def get_track_segment_kml (records, style):
    params = {'name': 'Vessel Track'}
    params['coords'] = ' '.join(['%(longitude)s,%(latitude)s,0'%r for r in records])
    params['time_begin'] = records[0]['datetime'].strftime ('%Y-%m-%dT%H:%M:%SZ')
    params['time_end'] = records[-1]['datetime'].strftime ('%Y-%m-%dT%H:%M:%SZ')
    params['style'] = style['style']
    return track_template.substitute(params)
    
def get_track_kml (vessel):
    kml = []
    records = []
    last_dt = vessel.timestamps[0]
    last_style = get_time_gap_style (last_dt, last_dt)
        
    for ais in vessel.ais:
        dt = ais['datetime']
        style = get_time_gap_style (dt, last_dt)
        if style != last_style and records:
            kml.append (get_track_segment_kml(records, last_style))
            records = [records[-1]]
        records.append (ais)
        last_style = style
        last_dt = dt
    
    if records:
        kml.append (get_track_segment_kml(records, last_style))
    
    return '\n'.join (kml)


# rows sorted by mmsi and timestamp and yield Vessel():s
def read_vessels (rows):    

    vessel = None
    last_dt = datetime (2000,1,1)
    for row in rows:
        dt = row.get('datetime')
        mmsi = row.get('mmsi')

        if not mmsi or not dt:
            continue

        if not row.get('name'):
            row['name'] = mmsi
        row['marinetraffic_url'] = 'http://www.marinetraffic.com/ais/shipdetails.aspx?MMSI=%s' % mmsi
        row['itu_url'] = 'http://www.itu.int/cgi-bin/htsh/mars/ship_search.sh?sh_mmsi=%s' % mmsi

        if not vessel or vessel.mmsi != mmsi:
            if vessel:
                yield vessel
            vessel = Vessel(row)

        vessel.add_ais(row)

    if vessel:
        yield vessel
        

def convert (rows, name):
    params = {'name': name}

    params['vessels_kml'] = '\n'.join([
            get_vessel_kml(vessel, vessel.mmsi)
            for vessel in read_vessels (rows)])

    return document_kml_template.substitute (params)
