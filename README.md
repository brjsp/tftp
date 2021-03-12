TFTP client and server with RFC7440 support. Written in Python3 as an university project
# Server
Server implements [TFTP](https://tools.ietf.org/html/rfc1350) with [RFC7440](https://tools.ietf.org/html/rfc7440) extensions (windowsize), sends at most 16 blocks at a time. It listens on the port given as a parameter, if no port is given defaults to 69. Server serves files from the current directory — before running you need to `cd` into where you want to serve files from.

Usage: `tftpd.py [port]`

# Client
The client actually only calculates the md5sum of a file rather than downloading it because it was only used for testing and i am a lazy ass. If you have any level of python literacy it should be easy to change it lol.

Usage: `tftp.py server file [port]`

# Known problems
* Client sends the last ACK only when timeout expires. The server may think that the packet got lost and send the end of file again, but in reality the client is simply a jerk.
* Running the server on default port may require root privileges on some operating systems.

# Known non-problems
* This implementation does not include the “[sorcerer's apprentice](https://en.wikipedia.org/wiki/Sorcerer%27s_Apprentice_Syndrome)” bug.
