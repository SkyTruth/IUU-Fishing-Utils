import bitstring

def nmea_checksum(str):
    checksum = 0
    for char in str:
        checksum = checksum ^ ord(char)
    return "%02X" % checksum


def encode_avidm(payload, payloadpad, fragments = 1, fragmentid = 1, msgid = '', channel = "B"):
    msg = "AIVDM,%s,%s,%s,%s,%s,%s" % (fragments, fragmentid, msgid, channel, payload, payloadpad)
    return "!" + msg + "*" + nmea_checksum(msg)


def avidm_payload_bits(bits6):
    if bits6 >= 40:
        ascii = bits6 - 40 + 96
    else:
        ascii = bits6 + 48
    return chr(ascii)

def payload_armour(payload):
    res = ""

    while payload.pos + 6 < payload.len:
        res += avidm_payload_bits(payload.read("uint:6"))
    
    extralen = payload.len - payload.pos
    if extralen > 0:
        extra = payload.read("uint:%s" % extralen) << 6 - extralen
        res += avidm_payload_bits(extra)

    return (6 - extralen) % 6, res
    

class AvidmMessage(object):
    TYPES = {
        "Position Report Class A": 1,
        "Position Report Class A (Assigned schedule)": 2,
        "Position Report Class A (Response to interrogation)": 3,
        "Base Station Report": 4,
        "Static and Voyage Related Data": 5,
        "Binary Addressed Message": 6,
        "Binary Acknowledge": 7,
        "Binary Broadcast Message": 8,
        "Standard SAR Aircraft Position Report": 9,
        "UTC and Date Inquiry": 10,
        "UTC and Date Response": 11,
        "Addressed Safety Related Message": 12,
        "Safety Related Acknowledgement": 13,
        "Safety Related Broadcast Message": 14,
        "Interrogation": 15,
        "Assignment Mode Command": 16,
        "DGNSS Binary Broadcast Message": 17,
        "Standard Class B CS Position Report": 18,
        "Extended Class B Equipment Position Report": 19,
        "Data Link Management": 20,
        "Aid-to-Navigation Report": 21,
        "Channel Management": 22,
        "Group Assignment Command": 23,
        "Static Data Report": 24,
        "Single Slot Binary Message,": 25,
        "Multiple Slot Binary Message With Communications State": 26,
        "Position Report For Long-Range Applications": 27
    }
    type = 0

    fields = [("type", "uint", 6)]

    def encode(self, msgid = '', channel = "B"):
        msg = bitstring.BitStream()

        for field in self.fields:
            name = field[0]
            type = field[1]

            value = getattr(self, name)

            if hasattr(self, type + "_convert"):
                value = getattr(self, type + "_convert")(value, *field[2:])
            else:
                args = {}
                args[type] = value
                args["length"] = field[2]
                value = bitstring.Bits(**args)
            msg.append(value)

        pad, payload = payload_armour(msg)
        return encode_avidm(payload, pad, 1, 1, msgid, channel)

    STRING6_ASCII = {"@": 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9, "J": 10, "K": 11, "L": 12, "M": 13, "N": 14, "O": 15, "P": 16, "Q": 17, "R": 18, "S": 19, "T": 20, "U": 21, "V": 22, "W": 23, "X": 24, "Y": 25, "Z": 26, "[": 27, "\\": 28, "]": 29, "^": 30, "_": 31, " ": 32, "!": 33, "\"": 34, "#": 35, "$": 36, "%": 37, "&": 38, "'": 39, "(": 40, ")": 41, "*": 42, "+": 43, ",": 44, "-": 45, ".": 46, "/": 47, "0": 48, "1": 49, "2": 50, "3": 51, "4": 52, "5": 53, "6": 54, "7": 55, "8": 56, "9": 56, ":": 58, ";": 59, "<": 60, "=": 61, ">": 62, "?": 63}

    def string6_convert(self, value):
        msg = bitstring.BitStream()
        for char in value:
            msg.append(bitstring.Bits(uint=self.STRING6_ASCII[char], length=6))
        return msg


class AvidmAddressedSafetyRelatedMessage(AvidmMessage):
    fields = AvidmMessage.fields + [
        ("repeat", "uint", 2),
        ("mmsi", "uint", 30),
        ("seqno", "uint", 2),
        ("dest_mmsi", "uint", 30),
        ("retransmit", "uint", 1),
        ("spare1", "uint", 1),
        ("text", "string6")
        ]
    type = 12
    repeat = 3
    mmsi = 0
    seqno = 0
    dest_mmsi = 0
    retransmit = 0
    spare1 = 0
    text = ''
