import csv
from optparse import OptionParser

desc = ""

usage = """%prog [options] INFILE BASENAME

  INFILE 
    filename containing AIS Data in CSV format
  BASENAME
    Basename for output files

"""
parser = OptionParser(description=desc, usage=usage)

parser.add_option("-f", "--fieldnames",
                      action="store", dest="fieldnames", default=None,
                      help="Field names if not specified in the file")
parser.add_option("-b", "--buckets",
                      action="store", dest="buckets", default='0.25,0.5,1.5',
                      help="Buckets to sort rows in")

(options, args) = parser.parse_args()

infile_name = args[0]
basename = args[1]

fieldnames = options.fieldnames.split(",")

buckets = [float(bucket) for bucket in options.buckets.split(",")] + [None]
bucket_files = {}
bucket_writers = {}
for bucketidx in xrange(0, len(buckets)):
    bucket = buckets[bucketidx]
    if bucketidx == 0:
        lower = ''
    else:
        lower = str(buckets[bucketidx-1])
    if bucket is None:
        upper = ''
    else:
        upper = str(buckets[bucketidx])
    bucket_files[bucket] = open("%s:%s-%s.csv" % (basename, lower, upper), 'a')
    bucket_writers[bucket] = csv.DictWriter(bucket_files[bucket], fieldnames=fieldnames, lineterminator='\n')

with open(infile_name, 'rb') as csvfile:  
    dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',') 
    csvfile.seek(0)   
    reader = csv.DictReader(csvfile, dialect=dialect, fieldnames=fieldnames) 
    for row in reader:
        score = float(row['score'])
        for bucket in buckets:
            if bucket is None or score < bucket:
                bucket_writers[bucket].writerow(row)
                break

for bucketfile in bucket_files.itervalues():
    bucketfile.close()
