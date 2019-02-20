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

import struct


# Class representing a message
class Message(object):
    def __init__(self, payload=None, messageId=None, lenghtPrefix=None):
        self.messageId = messageId
        self.payload = payload
        self.lenghtPrefix = lenghtPrefix

    # Serialize a message
    def createMessage(self):
        return struct.pack(">I", int(self.lenghtPrefix)) + struct.pack("b", self.messageId) + self.payload

    # Deserialize a message
    def createFromBytes(self, bytes):
        try:
            self.lenghtPrefix = struct.unpack(">I", bytes[0:4])[0]
            self.messageId = struct.unpack_from("B", bytes[4:5])[0]
            self.payload = bytes[5:self.lenghtPrefix+6]
        except:
            self.lenghtPrefix = 0
            self.messageId = 0
            self.payload = 0
        return Message


# Represent a status message
class Status(Message):
    def __init__(self, id, lenghtPrefix):
        Message.__init__(self, None, id, lenghtPrefix)

    # Serialize a message
    def createMessage(self):
        return struct.pack(">I", int(self.lenghtPrefix)) + struct.pack("b", self.messageId)


# Represent keepAlive message
class KeepAlive(Status):
    def __init__(self):
        Status.__init__(self, None, 0)

    # Serialize a message
    def createMessage(self):
        return struct.pack(">I", int(self.lenghtPrefix))


# Represent the chocke message
class Chocke(Status):
    def __init__(self):
        Status.__init__(self, 0, 1)


# Represent the unchocke message
class Unchocke(Status):
    def __init__(self):
        Status.__init__(self, 1, 1)


# Represent the interested message
class Interested(Status):
    def __init__(self):
        Status.__init__(self, 2, 1)


# Represent the not interested message
class NotInterested(Status):
    def __init__(self):
        Status.__init__(self, 3, 1)


# Represent the bitfield message
class Bitfield(Status):
    def __init__(self):
        Status.__init__(self, 5, 1)


# Represent a message of type request
class Request(Message):
    def __init__(self, index, begin, length):
        Message.__init__(self, None, 6, 13)
        self.index = int(index)
        self.begin = int(begin)
        self.length = int(length)

    # Serialize the payload
    def createPayload(self):
        return struct.pack(">I", self.index) + struct.pack(">I", self.begin) + struct.pack(">I", self.length)

    # Serialize the message
    def createMessage(self):
        return struct.pack(">I", int(self.lenghtPrefix)) + struct.pack("b", self.messageId) + self.createPayload()


# Represent a piece
class Piece(Message):
    def __init__(self, index=0, begin=0, block=0, id=0):
        Message.__init__(self, None, 7, None)
        self.index = int(index)
        self.begin = int(begin)
        self.block = block
        self.id = id

    # Deserialize a piece
    def createFromBytes(self, bytes):
        try:
            self.lenghtPrefix = struct.unpack(">I", bytes[0:4])[0]
            self.id = struct.unpack_from("B", bytes[4:5])[0]
            self.index = struct.unpack("I", bytes[5:9])[0]
            self.begin = struct.unpack("I", bytes[9:13])[0]
            self.block = bytes[13:self.lenghtPrefix+4]
        except:
            self.lenghtPrefix = 0
            self.id = 0
            self.index = 0
            self.begin = 0
            self.block = 0
        return Piece
