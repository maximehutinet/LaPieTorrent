#!/usr/local/bin/python
# @author Maxime Hutinet & Livio Nagy

#    LaPieTorrent : This projet is a simplified version of a BitTorrent client.
#    Copyright (C) 2019  Maxime Hutinet & Livio Nagy

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

import bencode


# Class representing the file
class File(object):
    def __init__(self,file):
        self.file = file
        self.fileName = self.readInfo()['name']
        self.size = self.readInfo()['length']
        self.pieceLength = self.readInfo()['piece length']
        self.myFileDump = self.readFile(self.file)

    # Read a file
    def readFile(self, file):
        myFile = open(file)
        return myFile.read()

    # Decode a bencoded value
    def decodeBencode(self, myFileDump):
        myBencode = bencode.decode_dict(myFileDump, 0)
        return myBencode

    # Get the http link of the tracker
    def getTrackerLink(self):
        myFile = self.readFile(self.file)
        return self.decodeBencode(myFile)[0]['announce']

    # Read the file once decoded
    def readDecodedFile(self):
        myFile = self.readFile(self.file)
        return self.decodeBencode(myFile)

    # Read the info field of the torrent
    def readInfo(self):
        myFile = self.readFile(self.file)
        return self.decodeBencode(myFile)[0]['info']


