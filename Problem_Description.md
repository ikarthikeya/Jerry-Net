# **Satellite Networking Problem Description**

## **Major Problem:**
The geosynchronous satellites are “fixed” upon a static longitude and latitude relative to earth, so its earth-satellite signal is stable. But for Low Earth Orbit Systems like Starlinks, the distance between satellites to earth is much shorter, which means satellites are moving swiftly at around 27000km/hour relative to earth, and every satellite is having much smaller valid coverage area than geosynchronous one. 

## **Major hypothesis:**
We can hypothesis that the our satellites are moving swiftly relative to earth, and that the relative position between satellites are fixed because they are roughly on the same orbit.

## **Major Challenges:**
So there are two major changes for satellites-to-satellites and satellites-to-earth.
1. **Satellite-to-satellite communication.** Satellites could be seen as formatting a separate subnet. In our use case we are basically using satellites as routers for “wifi connection”. So we don’t care that much about an accurate transmitting from one particular satellite to another. We can simply broadcast information to the whole satellite subnet once interesting event is discovered.  As satellites are far away from each other, we should assume that every satellites only have connections to nearby satellites, we need a “routing table” to update its connection status to other satellites. Because this satellites net is a peer-to-peer net, we can’t store this routing table in a centralized position. Instead, we need to invent a solution that each satellite could maintain its own routing table dynamically, as connection loss could happen more frequently in the space.

2. **Satellite-to-earth and earth-to-satellite communication.** As satellite is moving fast relative to earth, only the satellites with projected longitude and latitude very near to earth base have clear signals that could be received. We could speculate that the signal strength of satellite is a function with parameter longitude and latitude, we need to simulate this signal and make the generation function ourselves. The signal is with higher latency due to satellite height which also need to be simulated. The last issue is the satellite handover. According to the Star-link article mentioned in the requirement, the earth-base should always try to receive/send signals from its nearest satellite and detect which is the nearest in about 15 seconds, then change to the next one. 

## **Possible solution to satellites-to-satellites network**
The effect on networking is that the network transport between satellites will be stable. The model will be very like a subnet on the ground made of several ‘routers’. Wether two routers could be connected on one hop will depend on their physical distance. We can maintain a per satellite dynamic routing table recording the node-number, its current longitude and latitude. We can utilizing some some routing optimization algorithm such as A* search Algorithm and Dijkstra's algorithm

## **Possible solution to satellites-to-earth connection**
First, we need to simulate the movement of satellites and the signal change of satellites due to location change. We can simulate a net connection between earth and satellites with higher-than-usual latency and packet loss rate. Then our transport handling function need to solve 2 problems:
1. It can effectively handle packet loss with a balanced trade-off between data accuracy and  latency, it can effectively reduce the buffer size or any overhead caused by packet loss.
2. It can automatically decide which satellites to connect according its calculation of satellites’ longitude and latitude. It will change its connection to next nearest satellite every time interval of about 15 seconds. The purpose of earth-base is to connect to the satellite subnet for some information that has already be propagated to every note. The gateway of this satellite subnet is constantly changing because of location change and the earth-base need some algorithm to figure it out, the nearest satellite should confirm with its own location that it is indeed the nearest node.

Currently we decide to use UDP protocol with some enhanced feature(like UDP Forward Error Correction) to tackle this problem. In Python socket, using flag “socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM” will create a socket with UDP protocol.

## **Temporary Task splitting intention**
**Daim:** tackle earth-2-earth UDP handling function

**Karthik:** tackle satellite-2-satellite router table maintenance

**Ting:** simulate satellite location change, simulate signal change function and packet loss in UDP transportation.

**Sanjiv:** Define clear use case scenario, propose requirements such as data type/data flag/frequency of event detection & update
