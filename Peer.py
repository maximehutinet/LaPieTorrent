#!/usr/local/bin/python
# @author Maxime Hutinet & Livio Nagy

#   LaPieTorrent : This projet is a simplified version of a BitTorrent client.
#   Copyright (C) 2019  Maxime Hutinet & Livio Nagy

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import hashlib
import socket
from Message import *


# Class representing a peer
class Peer(object):
    def __init__(self, infoHash, pieceLength, ip, port, outputFileMm):
        self.ip = ip
        self.port = int(port)
        self.pstr = "BitTorrent protocol"
        self.pstrLen = len(self.pstr)
        self.reserved = 0
        self.infoHash = infoHash
        self.peerID = None
        self.version = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.pieceLength = pieceLength
        self.socket.settimeout(10)
        self.bitField = ""
        self.outputFileMm = outputFileMm

    # Create the SHA1 of a data
    def makeSHA1(self, data):
        sha1 = hashlib.sha1(data)
        hash = sha1.digest()
        return hash

    # Create the handshake which will be sent to the peer
    def createHandshake(self, sourcePeerId):
        return struct.pack("b", self.pstrLen) + self.pstr + struct.pack("q",
                                                                        self.reserved) + self.infoHash + sourcePeerId

    # Send the handshake to a peer, check its and send interested
    def connect(self, sourcePeerId):
        print "-----------------------------------------------------------------------\n" \
              "Sending handshake to peer IP: {}, on port {}".format(self.ip, self.port)

        try:
            self.socket.connect((self.ip, self.port))
            self.socket.send(self.createHandshake(sourcePeerId))
            data = self.socket.recv(1024)
            remotePstrLen = struct.unpack("b", data[0:1])[0]
            remotePstr = struct.unpack("%ds" % remotePstrLen, data[1:remotePstrLen + 1])[0]
            remoteInfoHash = struct.unpack("%ds" % 20, data[remotePstrLen + 9:remotePstrLen + 29])[0]
            self.peerID = struct.unpack("%ds" % 20, data[remotePstrLen + 29:remotePstrLen + 49])[0]
            self.version = self.peerID[1:6]

        except:
            print "-----------------------------------------------------------------------\n" \
                  "Connection to peer {} failed".format(self.ip)
            return

        print "Remote Protocol: " + str(remotePstr)

        if remoteInfoHash != self.infoHash:
            print "Uhoh, something is wrong with this little peer, handshake mismatch! Peer: {}".format(self.ip)
        else:
            print "The infohash matches, we can trust this peer! Peer: {}".format(self.ip)

            try:
                bitfield = self.socket.recv(1024)
                bitfieldMessage = Message()
                bitfieldMessage.createFromBytes(bitfield)
                if bitfieldMessage.messageId != 5:
                    return False

                for i in range(len(bitfieldMessage.payload)):
                    self.bitField += format(ord(bitfieldMessage.payload[i]), 'b')

                interestedMessage = Interested()
                self.socket.send(interestedMessage.createMessage())

                unchocke = self.socket.recv(1024)
                unchockeMessage = Unchocke()
                unchockeMessage.createFromBytes(unchocke)
                if unchockeMessage.messageId != 1:
                    return False
            except socket.timeout:
                return False
            return True

    # Request a block to a peer
    def request(self, index, sha1):
        data = b''
        offset = 0
        piece = Piece()

        if self.bitField[index] == "1":
            while len(data) < self.pieceLength:
                request = Request(index, offset, 16384)
                self.socket.send(request.createMessage())

                try:
                    piece.createFromBytes(self.socket.recv(16384 + 79))
                    while len(piece.block) < 16384:
                        piece.block += self.socket.recv(16384)

                except:
                    print "Waiting for piece for too long. Peer: {}".format(self.ip)
                    return False

                data += piece.block
                offset = offset + piece.lenghtPrefix - 9

            dataSha1 = self.makeSHA1(data)
            if dataSha1 == sha1:
                self.outputFileMm.seek(index)
                self.outputFileMm.write(bytes(data))
                return True
            else:
                print "This peer tried to trick me, the sha1 of the piece doesn't match!"
                return False
        else:
            print "BitField missmatch, alla prossima!"
            return False
