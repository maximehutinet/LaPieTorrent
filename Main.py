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

import mmap
import time
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep
from File import File
from Tracker import Tracker
from Peer import Peer
from threading import Thread
import logging
import os

PORT_NUMBER = 6882
FILE = "Torrent/debian-9.5.0-amd64-xfce-CD-1.iso.torrent"
THREADS = 30

# Try to remove the current version of logs.csv
try:
    os.remove('logs.csv')
    print("Deleted an old version of logs.csv !")
except OSError:
    print("A new version of logs.csv will be created !")

# Write header to log file
with open('logs.csv', 'a') as file_obj:
    file_obj.write('DATE,IP,PORT,PEER VERSION,SPEED,AVAILABLE PIECES\n')

# Setting for the logs
logging.basicConfig(filename='logs.csv', level=logging.INFO, format='%(asctime)s%(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S')


myFile = File(FILE)
print(myFile.readDecodedFile())

# Create the output file with zeros, placeholder
outputFile = open(myFile.fileName, "w+b")
outputFile.write("\0" * myFile.size)
outputFileMm = mmap.mmap(outputFile.fileno(), 0)


# Test the different peer in order to add the one that are alive to a list which we can take from
def testPeers(myTracker):
    global alivePeers
    while myTracker.peers:
        peerData = myTracker.peers.pop()
        myPeer = Peer(myTracker.infoHash, myFile.pieceLength, peerData[0], peerData[1], outputFileMm)
        if myPeer.connect(myTracker.peerID):
            alivePeers.append(myPeer)


print("Filename : {}".format(myFile.fileName))
print("File Size : {}".format(myFile.size))
print("Tracker link : {}".format(myFile.getTrackerLink()))
print("Info : {}".format(myFile.readInfo()))

myTracker = Tracker(myFile, PORT_NUMBER)
alivePeers = []
print(myTracker.peers)
thread = Thread(target=myTracker.maintainPeerArray)
thread.start()
thread_test = Thread(target=testPeers, args=[myTracker])
thread_test.start()

print "-----------------------------------------------------------------------\n" \
      "Found {} alive peers.".format(len(alivePeers))

# Create an array to subdivide tasks for the threads
offsetArray = []
currentIndex = 0
for piece in range(myTracker.piecesNb):
    offsetArray.append(currentIndex)
    currentIndex += 1


# Retrieve pieces that a pear has
def getPieceNumber(pieceLength, bitfield):
    pieceArray = []
    count = 0
    for element in bitfield:
        if element is "1":
            pieceArray.append(count)
        count += pieceLength
    myString = '-'.join(str(element) for element in pieceArray)
    return myString


# Get blocks from a peer, used by the threads
def getData(index):
    print "-----------------------------------------------------------------------\n" \
          "Entering threat for index: {}".format(index)
    # If the file is downloaded, the threads should exit
    while myTracker.active:
        # If the peer stack is empty, wait for it to be populated
        while len(alivePeers) == 0:
            sleep(2)
        # We try to pop a peer from the list, if it doesn't work we try again
        try:
            activePeer = alivePeers.pop()
            timeStart = time.time()
            if activePeer.request(index, myTracker.pieces[index]):
                timeElapsed = time.time() - timeStart
                logging.info(',%s,%s,%s,%s,%s', activePeer.ip, activePeer.port, activePeer.version,
                             (activePeer.pieceLength / 1000) / timeElapsed, getPieceNumber(activePeer.pieceLength, activePeer.bitField))
                alivePeers.append(activePeer)
                return True
            else:
                getData(index)
        except IndexError:
            getData(index)


# Create a pool of thread of a given size and map it to the index array
pool = ThreadPool(THREADS)
test = pool.map(getData, offsetArray)

# Close the thread pool once they are finished with their job
pool.close()
pool.join()

# Kill all peer search jobs (threads)
myTracker.active = False

# Flush the open file to the disk
outputFileMm.flush()
thread.join()
thread_test.join()
