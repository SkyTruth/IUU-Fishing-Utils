import subprocess
import json
import threading
import tempfile
import contextlib
import avidmencode
import bitstring


def convert(f):
    print "Converting"
    # Use a temporary file to not make paramiko unhappy...
    with contextlib.closing(tempfile.TemporaryFile()) as tmpf:
        for line in f:
            if line.startswith("\\"):
                line = line[1:]
                header, nmea = line.split("\\", 1)
                header = header.split("*")[0] # remove junk?

                msg = avidmencode.AvidmAddressedSafetyRelatedMessage()
                msg.text = header.upper()
                tmpf.write(msg.encode() + "\n")
                line = nmea
            tmpf.write(line)
        tmpf.seek(0)

        gpsdecode = subprocess.Popen(["gpsdecode"], stdin=tmpf, stdout=subprocess.PIPE)

        header = None
        for line in gpsdecode.stdout:
            line = json.loads(line)
            if line.get('class', '') == 'AIS' and line.get('type', '') == 12 and line.get('mmsi', '') == 0:
                header = dict(item.split(":") for item in line['text'].split(","))
            else:
                if header:
                    line.update(header)
                    header = None
                yield line
