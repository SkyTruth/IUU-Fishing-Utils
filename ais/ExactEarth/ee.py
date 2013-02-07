import logging
import re
import csv

# map of field names: {'output file field' : 'input file field'}
field_map = {
    'datetime': 'Time',
    'mmsi': 'MMSI',
    'latitude' : 'Latitude',
    'longitude' : 'Longitude',
    'true_heading' : 'Heading',
    'sog' : 'SOG',
    'cog' : 'COG',
    'name': 'Vessel_Name',
    'type': 'Ship_Type',
    'length': 'Dimension_to_Bow',
}

fields = field_map.keys()

def convert (csvfile):
    dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',') 
    csvfile.seek(0)   
    reader = csv.DictReader(csvfile, dialect=dialect) 

    for row in reader:
        out_row = convert_row (row)
        if out_row['mmsi'] and out_row['datetime'] and out_row['latitude'] and out_row['longitude']:
            yield out_row


def convert_row (row_in):
    row_out = {}
    for k,v in field_map.items():
        new_v = row_in.get(v,'')
        if new_v == 'None' or new_v == '':
            new_v = None
        row_out[k] = new_v

    # fix up datetime    
    dt = row_out.get('datetime')
    if dt:
        row_out['datetime'] = "%s-%s-%s %s:%s:%s" % (dt[0:4],dt[4:6],dt[6:8],dt[9:11],dt[11:13],dt[13:15])
        
    return row_out
