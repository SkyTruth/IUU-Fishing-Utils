#svs2kml.py

import logging
from optparse import OptionParser
import re
import pprint
from string import Template
import csv


document_kml_template = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>$kml_file_name</name>
	<StyleMap id="pointStyleMap">
		<Pair>
			<key>normal</key>
			<styleUrl>#normPointStyle</styleUrl>
		</Pair>
		<Pair>
			<key>highlight</key>
			<styleUrl>#hlightPointStyle</styleUrl>
		</Pair>
	</StyleMap>
	<Style id="hlightPointStyle">
		<IconStyle>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png</href>
			</Icon>
		</IconStyle>
	</Style>
	<Style id="normPointStyle">
		<IconStyle>
			<Icon>
				<href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
			</Icon>
		</IconStyle>
	</Style>
	$folder_kml
</Document>
</kml>
	
"""	

folder_kml_template = """
	<Folder>
		<name>$name</name>
		$placemark_kml
    </Folder>
		
"""		

placemark_kml_template = """
			<Placemark>
				<name>$name</name>
				<styleUrl>#pointStyleMap</styleUrl>
				<Style id="inline">
					<IconStyle>
						<color>$color</color>
						<colorMode>normal</colorMode>
						<Icon>
							<href>http://maps.google.com/mapfiles/kml/shapes/target.png</href>
						</Icon>
					</IconStyle>
					<LineStyle>
						<color>$color</color>
						<colorMode>normal</colorMode>
					</LineStyle>
					<PolyStyle>
						<color>$color</color>
						<colorMode>normal</colorMode>
					</PolyStyle>
				</Style>
				<Point>
					<coordinates>$longitude,$latitude,0</coordinates>
				</Point>
			</Placemark>
"""

folder_name_map = {
    '/com/oceani/seaview3/images/symbols/yellowFin1.gif' : {'name': 'Yellow Fin', 'color': 'ff02fed0'},
    '/com/oceani/seaview3/images/symbols/swordFish1.gif' : {'name': 'Swordfish', 'color': 'fffd6a00'},
    'default' : {'name': 'Unknown', 'color': 'ffffffff'}
}
    
def read_svs (svs_file_name):
    content = {}
    with open(svs_file_name, 'rb') as svs_file:
        rdr = csv.reader(svs_file, delimiter=';')
        for row in rdr:
            folder = folder_name_map.get(row[3]) or folder_name_map.get('default')
            f = folder['name']
            if not content.get(f):
                content[f] = []
            content[f].append ({'longitude': row[1], 'latitude': row[2], 'name': folder['name'], 'color': folder['color']})
    return content            


def write_kml (kml_file_name, content):
    placemark_template = Template (placemark_kml_template)
    folder_template = Template (folder_kml_template)
    document_template = Template (document_kml_template)
#     pprint.pprint (content)   
    folder_kml = []
    for name, targets in content.items():
        placemark_kml = '\n'.join([placemark_template.substitute (target) for target in targets])
        folder_kml.append(folder_template.substitute({'name':name,'placemark_kml': placemark_kml}))
        
    document_kml = document_template.substitute({'kml_file_name': kml_file_name, 'folder_kml': '\n'.join(folder_kml)})
        
    with open (kml_file_name, 'wb') as kml_file:
        kml_file.write (document_kml)
    
         

def convert_kml (svs_file_name, kml_file_name):
    
    content = read_svs(svs_file_name)

    write_kml (kml_file_name, content)
        




def main ():
    desc = "Convert a SeaView symbol file (*.svs) containing fishing forcast targets into a KML file"
    
    usage = """%prog [options] INFILE OUTFILE

  INFILE 
    SeaView symbol file
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
    
    convert_kml (infile_name, outfile_name)
    

if __name__ == "__main__":
    main ()
