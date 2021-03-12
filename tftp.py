#!/usr/bin/python3
import collections,hashlib,socket,struct,sys
host = socket.gethostbyname(sys.argv[1]) # 35.156.81.40 149.156.75.213
try:
	port = int(sys.argv[3])
except:
	port=69
filename = sys.argv[2].encode()
#172.27.255.213 35.156.81.40 149.156.75.213
#a.txt b.txt a b c d e
mdsum=hashlib.md5()
printout=mdsum.update #Zmienić żeby wypisywać na stdout
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
	sock.settimeout(.2)
	last_mess=b'\0\1'+filename+b'\0octet\0windowsize\x0016\0'
	fail=0
	while True:
		try:
			sock.sendto(last_mess,(host,port))		
			reply,addr=sock.recvfrom(1024)
		except socket.timeout:
			fail+=1
			if fail>=16:
				raise socket.error
			continue
		if addr[0]==host:
			if reply[:4]==b'\0\3\0\1':
				port=addr[1]
				rfc7440=False
				break
			elif reply[:13]==b'\0\6windowsize\0':
				port=addr[1]
				bloks=int(reply[13:-1])
				if bloks<2 or bloks>16:
					raise socket.error
				rfc7440=True
				break
	#print(reply)
	if not rfc7440:
		blok=0
		while True:
			blok+=1
			blok%=65536
			printout(reply[4:])
			if len(reply)<4+512:
				break
			fail=0
			last_mess=b'\0\4'+struct.pack('>H',blok)
			while True:
				try:
					sock.sendto(last_mess,(host,port))		
					reply,addr=sock.recvfrom(1024)
				except socket.timeout:
					fail+=1
					if fail>=16:
						raise
					continue
				if addr==(host,port) and reply[:4]==b'\0\3'+struct.pack('>H',(blok+1)%65536):
					break
		last_mess=b'\0\4'+struct.pack('>H',blok)
		sock.sendto(last_mess,(host,port))		#final ACK
	else: #rfc7440
		bufs=collections.deque([None] * bloks,bloks)
		blok=0
		fail=0
		while True:
			while bufs[0] is not None:
				printout(bufs[0])
				blok+=1
				blok%=65536
				if len(bufs[0])<512:
					sock.sendto(b'\0\4'+struct.pack('>H',blok),(host,port)) #final ACK
					break
				bufs.append(None)
			else:
				#print(hex(blok))
				try:
					sock.sendto(b'\0\4'+struct.pack('>H',blok),(host,port))
					rem2=bloks*2#Gdyby serwer wysyłał pakiety szybciej niż my je przetwarzamy to mogą zalegać, tak chcemy je szybciej pretworzyć
					rem=bufs.count(None)#Nie zliczamy dubli, zliczamy tylko tyle ile nam brakuje
					while rem and rem2:
						addr=None
						while not ( addr==(host,port) and reply[:2]==b'\0\3' ):
							reply,addr=sock.recvfrom(1024)
						rem2-=1
						newblok=struct.unpack('>H',reply[2:4])[0]
						#print(' ',hex(newblok),end='',flush=True)
						if(blok < newblok <= blok+bloks) and bufs[newblok-blok-1] is None:
							fail=0
							rem-=1
							bufs[newblok-blok-1]=reply[4:]
						elif(blok < newblok+65536 <= blok+bloks) and bufs[newblok+65536-blok-1] is None:
							fail=0
							rem-=1
							bufs[newblok+65536-blok-1]=reply[4:]

				except socket.timeout:
					#print('timeout')
					fail+=1
					if fail>=16:
						raise
				continue
			break
print(mdsum.hexdigest())