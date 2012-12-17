import logging
from optparse import OptionParser
import re
from string import Template
import csv
from dateutil.parser import parse as parse_date
from datetime import datetime, timedelta
import sys
   
   
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
$track_kml
$placemarks_kml
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
    <tr><th align="right">Vessel Name</th><td></td></tr>
    <tr><th align="right">MMSI</th><td>$MMSI</td></tr>
    <tr><th align="right">Datetime</th><td>$datetime</td></tr>
    <tr><th align="right">True Heading</th><td>$true_heading</td></tr>
    <tr><th align="right">Speed Over Ground</th><td>$sog</td></tr>
    <tr><th align="right">Course Over Ground</th><td>$cog</td></tr>
    <tr><th align="right">Latitude</th><td>$latitude</td></tr>
    <tr><th align="right">Longitude</th><td>$longitude</td></tr>
    <tr><th align="right"></th><td><a href="">More Info</a></td></tr>
</table>    
    </description>    
	<styleUrl>#vesselStyleMap</styleUrl>
    <TimeStamp><when>$timestamp</when></TimeStamp>
    <Point>
        <coordinates>$longitude,$latitude,0</coordinates>
    </Point>
    <Style><IconStyle><heading>$cog</heading><color>$icon_color</color></IconStyle></Style>
</Placemark>""")


def convert (infile_name, outfile_name):
    vessels = read_csv (infile_name)
    
    params = {'name': outfile_name}
    params['vessels_kml'] = '\n'.join([get_vessel_kml(vessel, mmsi) for mmsi,vessel in vessels.items()])
    document_kml = document_kml_template.substitute (params)
    with open (outfile_name, 'wb') as kml_file:
        kml_file.write (document_kml)    
    
def get_vessel_kml (vessel, mmsi):
    keys = sorted(vessel.iterkeys())
    params = {'name': mmsi}
    params['placemarks_kml'] = '\n'.join([get_placemark_kml(vessel[k]) for k in keys])
    params['track_kml'] = get_track_kml (vessel)
    return vessel_kml_template.substitute (params)
    

def get_placemark_kml (record):
    params = record
    params['timestamp'] = record['datetime'].strftime ('%Y-%m-%dT%H:%M:%SZ') 
    c = min(float(record['sog']), 15) * 17
    params['icon_color'] = 'ff00%02x%02x' % (c, 255-c)
    return  placemark_template.substitute (params)


def get_time_gap_style (dt, last_dt):
    td = (dt - last_dt).total_seconds()
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
    keys = sorted(vessel.iterkeys())
    
    kml = []
    records = []
    last_dt = keys[0]
    last_style = get_time_gap_style (last_dt, last_dt)
        
    for dt in keys:
        style = get_time_gap_style (dt, last_dt)
        if style != last_style and records:
            kml.append (get_track_segment_kml(records, last_style))
            records = [records[-1]]
        records.append (vessel[dt])
        last_style = style
        last_dt = dt
    
    if records:
        kml.append (get_track_segment_kml(records, last_style))
    
    return '\n'.join (kml)
    
# load csv file into a dict keyed by MMSI, and then by timestamp
def read_csv (infile_name):    
    vessels = {}
    
    with open(infile_name, 'rb') as csvfile:  
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',') 
        csvfile.seek(0)   
        reader = csv.DictReader(csvfile, dialect=dialect) 

        last_dt = datetime (2000,1,1)
        for row in reader:
            dt = row.get('datetime')
            mmsi = row.get('MMSI')
            if mmsi and dt:
                if not vessels.get(mmsi):
                    vessels[mmsi] = {}
                dt = parse_date(dt, fuzzy=1)
                row['datetime'] = dt
                if abs((dt-last_dt).total_seconds()) > MIN_INTERVAL:
                    vessels[mmsi][dt] = row   
                    last_dt = dt
                    
    return vessels
        
     



def main ():
    desc = ""
    
    usage = """%prog [options] INFILE OUTFILE

  INFILE 
    filename containing AIS Data in CSV format
  OUTFILE
    output filename to get kml output
    
"""
    parser = OptionParser(description=desc, usage=usage)

    parser.set_defaults(loglevel=logging.INFO)
    parser.add_option("-q", "--quiet",
                          action="store_const", dest="loglevel", const=logging.ERROR, 
                          help="Only output error messages")
    parser.add_option("-v", "--verbose",
                          action="store_const", dest="loglevel", const=logging.DEBUG, 
                          help="Output debugging information")

    (options, args) = parser.parse_args()
    
    if len(args) < 2:
        parser.error("Not enough arguments.")
    elif len(args) > 2:
        parser.error("Too many arguments.")
        

    logging.basicConfig(format='%(levelname)s: %(message)s', level=options.loglevel)

    infile_name = args[0]
    outfile_name = args[1]
    
    print '%s => %s' % (infile_name, outfile_name)
    
    convert (infile_name, outfile_name)
    

if __name__ == "__main__":
    main ()
