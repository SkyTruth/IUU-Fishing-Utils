import psycopg2
import paramiko
import sys
import ee
import contextlib
from settings import settings


with contextlib.closing(psycopg2.connect(**settings['db'])) as conn:
    with contextlib.closing(conn.cursor()) as cur:

        cur.execute("select * from downloaded_exactearth");
        oldfiles = set(row[0] for row in cur.fetchall())

        with contextlib.closing(paramiko.Transport((settings['sftp']['host'], settings['sftp']['port']))) as transport:
            transport.connect(username=settings['sftp']['username'], password=settings['sftp']['password'])
            with contextlib.closing(paramiko.SFTPClient.from_transport(transport)) as sftp:

                for sourcedir in ("SAISData", "SAISData/old"):
                    for filename in sftp.listdir(sourcedir):
                        if filename.endswith('.complete'):

                            filename = filename[:-len(".complete")]
                            filepath = sourcedir + "/" + filename + ".csv"

                            if filename in oldfiles:
                                print filepath + " (OLD)"
                            else:
                                print filepath

                                try:
                                    with contextlib.closing(sftp.file(filepath)) as file:

                                        cur.execute("begin")
                                        try:

                                            for row in ee.convert(file):
                                                print "    %(datetime)s: %(mmsi)s" % row
                                                try:
                                                    cur.execute("insert into ais (datetime, mmsi, latitude, longitude, true_heading, sog, cog) values (%(datetime)s, %(mmsi)s, %(latitude)s, %(longitude)s, %(true_heading)s, %(sog)s, %(cog)s)", row)
                                                except:
                                                    print row
                                                    raise
                                            cur.execute("insert into downloaded_exactearth (filename) values (%(filename)s)", {'filename': filename})

                                        except Exception, e:
                                            print "    Error loading file " + str(e)
                                            cur.execute("rollback")
                                        else:
                                            cur.execute("commit")

                                except Exception, e:
                                    print "    Unable to open file " + str(e)
