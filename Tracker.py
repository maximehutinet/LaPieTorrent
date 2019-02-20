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
import time
import urllib
import bencode
import random
import requests
import socket
import struct
import string


# Class representing the tracker
class Tracker(object):
    def __init__(self, myFile, port):
        self.myFile = myFile
        self.infoHash = self.createInfoHash()  # 20-byte SHA1 hash value.
        self.peerID = self.createRandom() # Contain the 20-byte self-designated ID of the peer
        self.port = str(port)  # The port number that the peer is listening to for incoming connections from other peers
        self.uploaded = str(0)  # Total amount of bytes that the peer has uploaded in the swarm
        self.downloaded = str(0)  # Total amount of bytes that the peer has downloaded in the swarm
        self.left = self.getQtyLeft()  # Total amount of bytes that the peer needs
        self.compact = str(1)
        self.event = "started"
        self.ip = None  # OPTIONAL value, and if present should indicate the true address of the peer
        self.numwant = None  # OPTIONAL value, indicate the number of peers wanted from the tracker
        self.link = myFile.getTrackerLink()  # The URL link of the tracker
        self.URLtoSend = self.createSendURL()
        self.peers = self.request()
        self.peerArray = []
        self.piecesNb = self.getPiecesNb()
        self.pieces = self.getPiecesArray()
        self.active = True

    # Create a semi random PeerID
    def createRandom(self):
        peerID = "LaPieTorrent"
        for i in range(8):
            peerID += random.choice(string.ascii_uppercase + string.digits)
        return peerID

    # Create the SHA1 of a data
    def makeSHA1(self, data):
        sha1 = hashlib.sha1(data)
        hash = sha1.digest()
        return hash

    # Create an URL with the right format
    def urlEncode(self, data):
        myUrl = urllib.quote_plus(data)
        return myUrl

    # Decode a bencoded value
    def decodeBencode(self, myFileDump):
        myBencode = bencode.decode_dict(myFileDump, 0)
        return myBencode

    # Bencode a dictionnary
    def bencodeDict(self, data):
        myData = []
        bencode.encode_dict(data, myData)
        myData = "".join(myData)
        return myData

    # Create a SHA1 of the info field
    def createInfoHash(self):
        myDict = {}
        myDict = self.myFile.readInfo()
        sha1 = self.makeSHA1(self.bencodeDict(myDict))
        return sha1

    # Bencode a value
    def bencodeValue(self, number):
        return bencode.bencode(number)

    # Decode a bencoded value
    def decodeBencodeValue(self, number):
        return bencode.bdecode(number)

    # Change the downloaded value
    def changeDownloadedValue(self, value):
        self.downloaded = str(value)

    # Get the amount that has been downloaded
    def getDownloadedValue(self):
        return self.downloaded

    # Return the quantity left to download
    def getQtyLeft(self):
        value = self.myFile.size - int(self.downloaded)
        return str(value)

    # Update the quantity left to download
    def updateQtyLeft(self):
        self.getQtyLeft()

    # Get the number of pieces into which the file is split
    def getPiecesNb(self):
        return int(self.myFile.size // self.myFile.readInfo()['piece length'])

    # Return an array of the sha1 of the pieces
    def getPiecesArray(self):
        array = []
        index = 0
        for piece in range(self.piecesNb):
            array.append(self.myFile.readInfo()['pieces'][index:index+20])
            index += 20
        return array

    # Create the URL to send to the tracker
    def createSendURL(self):
        encodedPeerID = self.urlEncode(self.peerID)
        infoHash = self.urlEncode(self.infoHash)
        self.URLtoSend = self.link + '?' \
                         + "info_hash=" + infoHash + "&" \
                         + "peer_id=" + encodedPeerID + "&" \
                         + "port=" + self.port + "&" \
                         + "uploaded=" + self.uploaded + "&" \
                         + "downloaded=" + self.downloaded + "&" \
                         + "left=" + self.left + "&" \
                         + "event=" + self.event + "&" \
                         + "compact=" + self.compact
        return self.URLtoSend

    # Contact the tracker, deserialize the peers and return a list composed of their ip and port
    def request(self):
        print "-----------------------------------------------------------------------\n" \
              "Contacting tracker with URL: {}".format(self.URLtoSend)
        response = requests.get(self.URLtoSend)
        response = bencode.bdecode(response.content)
        peersNb = int((len(response['peers']) / 8) / 6)
        print('Peers number: %i' % peersNb)

        peers = []
        y = 0
        for x in range(0, peersNb):
            address = response['peers'][y:y + 4]
            ip = response['peers'][y + 4:y + 6]
            peers.extend({(socket.inet_ntoa(address), int(struct.unpack('>H', ip)[0]))})
            y = y + 6
        return peers

    # Add the peer to a list which can then by tested in order to keep the peer that are alive
    def maintainPeerArray(self):
        while(self.active):
            self.peerArray.append(self.request())
            for element in self.peerArray:
                for peer in element:
                    if peer not in self.peers:
                        self.peers.append(peer)

            time.sleep(15)
