import logging
from optparse import OptionParser
import re
import ais


    

def convert_spacequest (infile_name, outfile_name):
    fields = [
        'datetime', 'mmsi', 'latitude', 'longitude', 'true_heading', 'sog', 'cog' 
        ]
        
    f_in = open(infile_name, 'r')
    f_out = open(outfile_name, 'w')
    f_out.write (','.join(fields))
    f_out.write ('\n')
    
    for line in f_in:
        full_rec = convert_spacequest_record (line)
        write_rec = ['%s'%full_rec.get(f,'') for f in fields]
        f_out.write (','.join(write_rec))
        f_out.write ('\n')
        
def convert_spacequest_record (line):
    fields = line.rstrip().split('|')
    rec = {
        'datetime' : fields[0],
        'MMSI' : fields[1],
        'latitude' : fields[2],
        'longitude' : fields[3],
        }
    rec.update (parse_ais(fields[4]))
    return rec


uscg_ais_nmea_regex_str = r'''^!(?P<talker>AI)(?P<string_type>VD[MO])
,(?P<total>\d?)
,(?P<sen_num>\d?)
,(?P<seq_id>[0-9]?)
,(?P<chan>[AB])
,(?P<body>[;:=@a-zA-Z0-9<>\?\'\`]*)
,(?P<fill_bits>\d)\*(?P<checksum>[0-9A-F][0-9A-F])
(
  (,S(?P<slot>\d*))
  | (,s(?P<s_rssi>\d*))
  | (,d(?P<signal_strength>[-0-9]*))
  | (,t(?P<t_recver_hhmmss>(?P<t_hour>\d\d)(?P<t_min>\d\d)(?P<t_sec>\d\d.\d*)))
  | (,T(?P<time_of_arrival>[^,]*))
  | (,x(?P<x_station_counter>[0-9]*))
  | (,(?P<station>(?P<station_type>[rbB])[a-zA-Z0-9_]*))
)*
'''

uscg_ais_nmea_regex = re.compile(uscg_ais_nmea_regex_str,  re.VERBOSE)


def parse_ais (ais_str):
    if 'AIVDM' not in ais_str:
        raise 'Missing AIVDM header'

    result = uscg_ais_nmea_regex.search(ais_str).groupdict()
    if not result:
        raise 'Not well formed'
        
    return ais.decode(result['body'], 0)
        

def main ():
    desc = ""
    
    usage = """%prog [options] INFILE OUTFILE

  INFILE 
    filename containing AIS data
  OUTFILE
    output filename to get csv output
    
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
    
    convert_spacequest (infile_name, outfile_name)
    

if __name__ == "__main__":
    main ()
