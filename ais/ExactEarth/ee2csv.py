import logging
from optparse import OptionParser
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
    'cog' : 'COG'
}

fields = [
    'datetime', 'mmsi', 'latitude', 'longitude', 'true_heading', 'sog', 'cog' 
]

def convert (infile_name, outfile_name):

    with open(infile_name, 'rb') as csvfile:  
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',') 
        csvfile.seek(0)   
        reader = csv.DictReader(csvfile, dialect=dialect) 

        f_out = open(outfile_name, 'w')
        f_out.write (','.join(fields))
        f_out.write ('\n')

        for row in reader:
            out_row = convert_row (row)
            if out_row['mmsi'] and out_row['datetime'] and out_row['latitude'] and out_row['longitude']:
                write_rec = ['%s'%out_row.get(f,'') for f in fields]
                f_out.write (','.join(write_rec))
                f_out.write ('\n')


def convert_row (row_in):
    row_out = {}
    for k,v in field_map.items():
        row_out[k] = row_in.get(v)

    # fix up datetime    
    dt = row_out.get('datetime')
    if dt:
        row_out['datetime'] = "%s-%s-%s %s:%s:%s" % (dt[0:4],dt[4:6],dt[6:8],dt[9:11],dt[11:13],dt[13:15])
    return row_out
        


def main ():
    desc = ""
    
    usage = """%prog [options] INFILE OUTFILE

  INFILE 
    filename containing ExactEarth AIS Data in CSV format
  OUTFILE
    output filename to get standardized CSV
    
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