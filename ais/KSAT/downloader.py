import psycopg2
import paramiko
import sys
import nmea
import contextlib
from settings import settings
import datetime

with contextlib.closing(psycopg2.connect(**settings['db'])) as conn:
    with contextlib.closing(conn.cursor()) as cur:

        cur.execute("select * from downloaded where src='KSAT'");
        oldfiles = set(row[0] for row in cur.fetchall())

        with contextlib.closing(paramiko.Transport((settings['sftp']['host'], settings['sftp']['port']))) as transport:
            transport.connect(username=settings['sftp']['username'], password=settings['sftp']['password'])
            with contextlib.closing(paramiko.SFTPClient.from_transport(transport)) as sftp:

                sourcedir = "WWW/AIS"

                for filename in sftp.listdir(sourcedir):
                    if filename.endswith('.nmea'):

                        filename = filename[:-len(".nmea")]
                        filepath = sourcedir + "/" + filename + ".nmea"

                        if filename in oldfiles:
                            print filepath + " (OLD)"
                        else:
                            print filepath

                            try:
                                with contextlib.closing(sftp.file(filepath)) as file:

                                    cur.execute("begin")
                                    try:

                                        for row in nmea.convert(file):
                                            # Why doesn't gpsdecode do scaling???
                                            if 'lon' in row: row['lon'] = row['lon'] / 600000.0 # A AIS unit is 1/10000th of a minute (1/60th of a degree)
                                            if 'lat' in row: row['lat'] = row['lat'] / 600000.0
                                            if 'C' in row:
                                                row['C'] = datetime.datetime.fromtimestamp(int(row['C']))
                                            else:
                                                row['C'] = None
                                            if 'S' in row:
                                                row['S'] = 'KSAT-' + row['S']
                                            else:
                                                row['S'] = 'KSAT'
                                            #print row
                                            #print "    %(C)s: %(mmsi)s" % row
                                            if row.get('type', None) in (1, 2, 3): # position reports
                                                try:
                                                    cur.execute("insert into ais (datetime, mmsi, latitude, longitude, true_heading, sog, cog, src) values (%(C)s, %(mmsi)s, %(lat)s, %(lon)s, %(heading)s, %(speed)s, %(course)s, %(S)s)", row)
                                                except:
                                                    print row
                                                    raise
                                            if row.get('name', None) is not None and row.get('shiptype', None) is not None:
                                                row['url'] = 'http://www.marinetraffic.com/ais/shipdetails.aspx?MMSI=' + row['mmsi']
                                                try:
                                                    cur.execute("insert into vessel (mmsi, name, type, length, url) select %(mmsi)s, %(shipname)s, %(shiptype)s, %(to_bow)s, %(url)s where %(mmsi)s not in (select mmsi from vessel)", row)
                                                except:
                                                    print row
                                                    raise
                                        cur.execute("insert into downloaded (src, filename) values ('KSAT', %(filename)s)", {'filename': filename})

                                    except Exception, e:
                                        raise
                                        print "    Error loading file " + str(e)
                                        cur.execute("rollback")
                                    else:
                                        cur.execute("commit")

                            except Exception, e:
                                raise
                                print "    Unable to open file " + str(e)
