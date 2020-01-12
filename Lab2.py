import socket
import struct
import sys
import random

LenQuery = 0
def DNSQueryTypeA(domain):
    randomId = random.randint(1, 65535)
    FLAGS = 0; QDCOUNT = 1; ANCOUNT = 0; NSCOUNT = 0; ARCOUNT = 0
    data = struct.pack("!H", randomId)
    data += struct.pack("!H", FLAGS)  
    data += struct.pack("!H", QDCOUNT)
    data += struct.pack("!HHH", ANCOUNT, NSCOUNT, ARCOUNT) 
    query = b''
    for label in domain.strip().split('.'):
        query += struct.pack('!B', len(label))
        query = b"".join([query,  str.encode(label.lower())])
    query += b'\x00'
    data += query
    global LenQuery
    LenQuery = len(query)
    q_type = 1
    q_class = 1
    data += struct.pack('!HH', q_type, q_class)
    data = struct.pack('!H', len(data) ) + data
    return data

Offset = 0 
def Decode(response):
    RCODE = struct.unpack('!H', response[2:4] )[0] & 0b00001111
    if RCODE != 0:
        print('Ошибка, rcode = ' + str(RCODE))
        sys.exit(-1)

    anwser_rrs = struct.unpack('!H', response[6:8] )[0]
    print('Найдено %d записи: ' % anwser_rrs)
    global LenQuery, OFFSET
    OFFSET = 12 + LenQuery + 4
    while OFFSET < len(response):
        name_offset = response[OFFSET: OFFSET + 2]
        name_offset = struct.unpack('!H', name_offset)[0]
        if name_offset > 0b1100000000000000:
            name = GetName(response, name_offset - 0b1100000000000000, True)
        else:
            name = GetName(response, OFFSET)
        OFFSET += 8
        data_length = struct.unpack('!H', response[OFFSET: OFFSET+2] )[0]
        if data_length == 4:
            ip = [str(num) for num in struct.unpack('!BBBB', response[OFFSET+2: OFFSET+6] ) ]
            print('.'.join(ip))
        OFFSET += 2 + data_length

def GetName(response, name_offset, is_pointer=False):
    global OFFSET
    labels = []
    while True:
        num = struct.unpack('B', bytes([response[name_offset]]))[0]
        if num == 0 or num > 128: break
        labels.append( response[name_offset + 1: name_offset + 1 + num] )
        name_offset += 1 + num
        if not is_pointer: OFFSET += 1 + num
    name = '.'.join(str(labels))
    OFFSET += 2
    return name

def Main(hostname, dnsIP):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect( (dnsIP, 53) )
    data = DNSQueryTypeA(hostname)
    s.send(data)
    s.settimeout(2.0)
    response = s.recv(4096)
    res_len = struct.unpack('!H', response[:2])[0]
    while len(response) < res_len:
        response += s.recv(4096)
    s.close()
    Decode(response[2:])

if __name__ == '__main__':
    Main(sys.argv[1], sys.argv[2])
