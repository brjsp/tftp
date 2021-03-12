#!/usr/bin/python3
import collections,os,socket,struct,sys,threading
pwd=os.getcwdb()
def servefile(addr,name,bloks=1):
	if(bloks>16):
		bloks=16
	#print(bloks)
	if os.path.isabs(name):
		name=None
	else:
		name=os.path.abspath(name)
	bufs=collections.deque(maxlen=bloks)
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sck:
		sck.settimeout(.2)
		if(not name or os.path.commonpath((pwd,name))!=pwd):#Escaping the current directory
			sck.sendto(b'\0\5\0\2\0',addr)#Access denied
			return
		try:
			file=open(name,'rb')
		except OSError:
			sck.sendto(b'\0\5\0\1\0',addr)#File not found
		fail=0
		if(bloks>1):
			oack=b'\0\6windowsize\0'+str(bloks).encode()+b'\0'#rfc 2437 optional acknowledgment
			while True:
				try:
					sck.sendto(oack,addr)		
					reply,addr1=sck.recvfrom(8)
				except socket.timeout:
					fail+=1
					if(fail>=16):
						raise
					continue
				if addr==addr1 and reply==b'\0\4\0\0':
					break
		blok=1#Początek bufora
		eof=False
		for i in range(bloks):
			bufs.append(b'\0\3'+struct.pack('>H',blok+i)+file.read(512))
			if(len(bufs[-1])<4+512):
				eof=True
				break
		with file:
			while bufs:
				fail=1
				while fail:
					try:
						#print(hex(blok))
						for buf in bufs:
							#print(' ',hex(struct.unpack('>H',buf[2:4])[0]),end='')
							sck.sendto(buf,addr)	
						while True:	#Ignorować nieoczekiwane odpowiedzi, żeby uniknąć https://en.wikipedia.org/wiki/Sorcerer%27s_Apprentice_Syndrome
							reply,addr1=sck.recvfrom(8)
							if addr==addr1 and len(reply)==4 and reply[:2]==b'\0\4':
								nextblok=(struct.unpack('>H',reply[2:])[0]+1)%65536
								if blok < nextblok <= blok+bloks or blok < nextblok+65536 <= blok+bloks:
									fail=0
									break
					except socket.timeout:
						#print('timeout')
						fail+=1
						if(fail>=16):
							raise
						continue
				nextblok=(struct.unpack('>H',reply[2:])[0]+1)%65536
				ii=(blok+bloks)%65536
				while blok != nextblok:
					if eof:
						try:
							bufs.popleft()
						except IndexError:
							pass
					else:
						bufs.append(b'\0\3'+struct.pack('>H',ii)+file.read(512))
						if(len(bufs[-1])<4+512):
							eof=True
					blok+=1
					blok%=65536
					ii+=1
					ii%=65536
try:
	port=int(sys.argv[1])
except:
	port=69
sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0',port))
while True:
	d, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
	#print(d)
	if d[:2] == b'\0\1':
		bloks=1
		d=d[2:].split(b'\0')
		if len(d)%2 ==1 and not d[-1]:
			for optname,optvalue in zip(*[iter(d[2:-1])]*2):#Iterate over optins two at a time:
				#print(optname,optvalue)
				if optname==b'windowsize':
					try:
						bloks=int(optvalue)
					except ValueError:
						continue
		if bloks>=1 and bloks<=65535:
			threading.Thread(target=servefile,args=(addr,d[0],bloks)).start()
	del d,addr,bloks