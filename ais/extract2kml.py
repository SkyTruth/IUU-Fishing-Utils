import psycopg2
import sys
import kml
import contextlib
from settings import settings

files = []
args = {}
for arg in sys.argv[1:]:
    if arg.startswith("--"):
        arg = arg[2:]
        if '=' in arg:
            arg = arg.split("=", 1)
            args[arg[0]] = arg[1]
        else:
            args[arg] = True
    files.append(arg)


def dictreader(cur):
    for row in cur:
        yield dict(zip([col[0] for col in cur.description], row))


if 'help' in args:
    print """Usage: extract2kml.py
    --timemin=2012-01-20 14:30:47 GMT+2
    --timemax=2013-01-20 14:30:47 GMT+2
    --latmin=53.47
    --latmax=54.47
    --lonmin=10.24
    --lonmax=11.24
    --mmsi=319063000
"""
else:

    with contextlib.closing(psycopg2.connect(**settings['db'])) as conn:
        with contextlib.closing(conn.cursor()) as cur:

            where = ['true']
            if 'timemax' in args:
                where.append("datetime <= %(timemax)s")
            if 'timemin' in args:
                where.append("datetime >= %(timemin)s")
            if 'latmin' in args:
                where.append("latitude <= %(latmin)s")
            if 'latmax' in args:
                where.append("latitude >= %(latmax)s")
            if 'lonmin' in args:
                where.append("lonitude <= %(lonmin)s")
            if 'lonmax' in args:
                where.append("lonitude >= %(lonmax)s")
            if 'mmsi' in args:
                where.append("ais.mmsi = %(mmsi)s")
                
            cur.execute("select datetime, ais.mmsi as mmsi, latitude, longitude, true_heading, sog, cog, location, name, type, length, url from ais left join vessel on ais.mmsi = vessel.mmsi where " + " and ".join(where) + " order by ais.mmsi, datetime", args);
            
            print kml.convert(dictreader(cur), args.get('name', 'extract2kml'))

