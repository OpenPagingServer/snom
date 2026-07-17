# SNOM Endpoint Module for Open Paging Server

PopUp Config:

1) Go into the Phone's web configuration interface
2) Navigate to Advanced -> QoS/Security
3) Under HTTP server, set authenthication Scheme to BASIC
4) Set Restrict URI Queries to OFF
5) Set Use Hidden Tags to OFF
6) in OPS add in the HTTP Server's username and password under the phones endpoint
7) add in the phone's IP into OPS

Multicast Config:
1) Create a Multicast group inside of open paging server
2) Login to the phone's web configuration utility
3) Go into Advanced -> SIP/RTP
4) Enable Multicast Support
5) Under Zone 1 add in a name, and add in the multicast address you made in open paging server


## Demo
[![Watch the Video](https://img.youtube.com/vi/F06C0dwH6a8/hqdefault.jpg)](https://youtube.com/shorts/F06C0dwH6a8)
