#!/usr/bin/python3
# Student name and No.:Abhinav Joshi 3035203857
# Development platform:Ubuntu 14.04 LTS
# Python version:3.4.3
# Version:1


from tkinter import *
import sys
import socket
import threading
import time


#
# Global variables
#
start=0							#check if keppalive should be started
sockfd = socket.socket()		#socket to rooomserver
sockfwd = socket.socket()		#socket to forward connection
Uname=""					#Username
isgp=0							#Is in group
roomname=""					#Room name
PORTl=0							#Port used for listening
gpmt={}							#dict storing all information on peers
msgID=0							#message id of user	
WList = []						#socket list
cthread = []					#thread list
gLock = threading.Lock()
all_thread_running = True		#used for stopping threads
error=False
fwd=0							#used to check if forward connection
IPu="127.0.0.1"					#user IP
lis=0							#check if listen should be started

#
# Main functions
#

def printpeers():
	global gpmt
	for x in gpmt.keys():
		a,b,c,d,e=gpmt[x]
		if not (a==Uname):
			CmdWin.insert(1.0,"\n"+a+"\n")
	CmdWin.insert(1.0,"\nPeers in group:\n")
#Decodes join message from server and puts into gpmt(all peer data storage)
def gpdecode(msg):
	global gpmt,fwd,msgID,myhs
	print("Message Join request from server",str(msg))
	bck={}
	
	x=str(msg).split(':')
	i=0
	
	myhs=sdbm_hash(Uname+IPu+str(PORTl))
	for index in range(2,len(x)-2,3):
		hs=sdbm_hash(x[index]+x[index+1]+x[index+2])
		if(hs in gpmt.keys()):
			a,b,c,d,e=gpmt[hs]
			bck[hs]=[x[index],x[index+1],x[index+2],d,e]
			
		else:
			bck[hs]=[x[index],x[index+1],x[index+2],0,0]
		
		
		if(hs==myhs):
			a,b,c,d,e=bck[hs]
			bck[hs]=a,b,c,d,msgID
	
	gpmt=bck

#Decodes message from peers
def msgdecode(msg,ck):
	
	print("\n<-------------msg recv frm some----------->\n",str(msg))
	global gpmt
	x=str(msg).split(':')
	y=""

	if(int(x[2]) in gpmt.keys() ):
		a,b,c,d,e=gpmt[int(x[2])]
		print(gpmt[int(x[2])])
		print(x)
		if(int(x[4])==e+1 or e==0):
			if(roomname==x[1]):
				for index in range(6,len(x)-2):
					y=y+x[index]+":"
				y=y[:-1]
				y="["+x[3]+"] "+y
				e=int(x[4])
				gpmt[int(x[2])]=a,b,c,d,e
				MsgWin.insert(1.0,"\n"+y)
			else:
				y="f"
		else:
			y="f"
	elif(ck==0):
		roomser("j2")
		msgdecode(msg,1)
	else:
		y="f"
	

	return y

#trys forward connection with peers
def connect2p():
	global gpmt,fwd,msgID,IPu,PORTl,Uname,sockfwd,lis,all_thread_running
	if(lis==1):
		print("\nRetrying for forward connection:")
		time.sleep(10)
	ret=[]
	my=sdbm_hash(Uname+IPu+str(PORTl))
	
	
	for h in gpmt:
		ret.append(h)

	ret.sort()
	#print(ret)
	#print(my)
	
	ind=ret.index(my)
	start=(ind+1)%len(ret)
	
	while (ret[start]!=my and fwd==0):
		a,b,c,d,e=gpmt[ret[start]]
		print(gpmt[ret[start]])
		if(d>0):
			start=(start+1)%len(ret)
		else:
			try:
				
				x,y,a,b,e=gpmt[ret[start]]
				print("IP connect2p:",y,a)
				sockfwd.connect((y,int(a)))
				msg="P:"+roomname+":"+Uname+":"+IPu+":"+str(PORTl)+":"+str(msgID)+"::\r\n"
				#"S:msgID::\r\n"
				sockfwd.send(msg.encode("ascii"))
				rmsg = sockfwd.recv(500)	
				if(rmsg[0:1] == b"S"):
					CmdWin.insert(1.0,"\nConnecting to peers\n")
					print("CONNECTING fwd suscess:--> ",rmsg)
					fwd=1
					x=str(rmsg).split(':')
					e=int(x[1])
					x,y,a,b,e=gpmt[ret[start]]
				else:
					CmdWin.insert(1.0, "\nError joining ")
					break
			
			except socket.error as emsg:
				print("Socket bind error: ", emsg)
				start=(start+1)%len(ret)
	if(lis==1 and fwd==0):
		if(all_thread_running):
			connect2p()
		
	
#listening thread function listens on port given by user
def listen():
	global gpmt, WList,cthread,all_thread_running
	sockl = socket.socket()

	sockl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	try:
		sockl.bind(('', PORTl))
	except socket.error as emsg:
		print("Socket bind error: ", emsg)
		sys.exit(1)

	sockl.listen(5)

	sockl.settimeout(1.0)
	ex=0
	while all_thread_running:
		
		try:
			newfd, caddr = sockl.accept()
		except socket.timeout:
			if(all_thread_running):
				
				continue
			else:
				break
		if(ex==0):
			print("A new backwardlink has arrived. It is at:", caddr)
			cname = caddr[0]+':'+str(caddr[1])
			thd = threading.Thread(name=cname, target= client_thd, args=(newfd,))
			thd.start()

			cthread.append(thd)
			
			gLock.acquire()
			
			WList.append(newfd)
			gLock.release()


	
	
	

#Thread to handle connected peers (reciveing messages)
def client_thd(sock):
	global WList,fwd, all_thread_running, gLock,msgID,gpmt,sockfwd,cthread

	change=0
	myName = threading.currentThread().name
	if(fwd==1):
		if(sock==sockfwd):
			change=1
	sock.settimeout(1.0)

	while (all_thread_running):
		try:
			rmsg = sock.recv(500)
		except socket.timeout:
			if(all_thread_running):
				continue
			else:
				break

		except socket.error as emsg:
			print("[%s] Socket error: %s" % (myName, emsg))
			continue

		# if has message arrived, do the following
		if rmsg:
			
			if(rmsg[0:1] == b"P"):
				roomser("j2")
				prt=str(myName).split(':')
				x=str(rmsg).split(':')
				print("\npeer connecting",x[3],x[4])
				hs=sdbm_hash(x[2]+x[3]+x[4])
				if(gpmt[hs]):
					mg="S:"+str(msgID)+"::\r\n"
					a,b,c,d,e=gpmt[hs]
					gpmt[hs]=a,b,c,int(prt[1]),e
					sock.send(mg.encode("ascii"))
					print("connected to backwardlink:",gpmt[hs])
				else:
					print("connection unscussefull wrong connect")
					break
			elif(rmsg[0:1] == b"T"):
				print("recieved text")
				m=msgdecode(rmsg,0)
				if(m!="f"):
					#print(m)
					
					fwdmsg(rmsg,sock)

			else:
				print("[%s] The client connection is broken!!" % myName)
				if(change==1):
					fwd=0
				gLock.acquire()
				WList.remove(sock)
				gLock.release()
				
				break

	if(change==1):
		fwd=0
	gLock.acquire()
	try:
		WList.remove(sock)
	except:
		pass
	gLock.release()

	print("[%s] Thread termination" % myName)
	return



def sdbm_hash(instr):
	hash = 0
	for c in instr:
		hash = int(ord(c)) + (hash << 6) + (hash << 16) - hash
	return hash & 0xffffffffffffffff


#Keepalive procedure every 20 sec wakes up and gets new JOIN list from roomserver
def keepalive():
	global all_thread_running
	while(all_thread_running):
		roomser("j2")
		for i in range(20):
			if(all_thread_running):
				time.sleep(1)
			else:
				break
#Mannages Request to and from roomserver
def roomser(arg):
	global IPu, PORTl , roomname ,Uname, sockfd,isgp,lis,fwd

	try:
	
		if(arg=="l"):
			arg=""
			msg = "L::\r\n"
			sockfd.send(msg.encode("ascii"))
			rmsg = sockfd.recv(500)
			print("List msg:"+str(rmsg))
			if(rmsg == b'G::\r\n'):
				CmdWin.insert(1.0, "\nNo groups Available.\nMake new")
			elif(rmsg == b"F:error message::\r\n"):
				CmdWin.insert(1.0, "\nError gp")
			else:
				x=str(rmsg).split(':')
				for index in range(1,len(x)-2):
					CmdWin.insert(1.0,"\n"+x[index]+"\n")
				CmdWin.insert(1.0,"\nHere are the active chatrooms:\n")
		
		elif(arg=="j1"):
			arg=""
			msg = "J:"+roomname+":"+Uname+":"+IPu+":"+str(PORTl)+"::\r\n"
			print(msg)
			sockfd.send(msg.encode("ascii"))
			rmsg = sockfd.recv(500)	
			if(rmsg[0:1] == b"F"):
				CmdWin.insert(1.0, "\nError joining")
				print("join:--> ",rmsg)
			elif(rmsg[0:1]==b"M"):
				CmdWin.insert(1.0,"\nEntering Chat...")
				isgp=1
				gpdecode(rmsg)
				printpeers()
				connect2p()
				if(lis==0):
					thd = threading.Thread(name="listen", target= listen, args=())
					cthread.append(thd)
					thd.start()
					lis=1
				if(fwd==1):
					thd2= threading.Thread(name="client_thd", target= client_thd, args=(sockfwd,))
					cthread.append(thd2)
					thd2.start()
				
				if(fwd==0):
					print("Error no forward connection\nRetrying in 5..")
					thd3= threading.Thread(name="connect2p", target= connect2p, args=())
					cthread.append(thd3)
					thd3.start()
	

		elif(arg=="j2"):
			arg=""
			msg = "J:"+roomname+":"+Uname+":"+IPu+":"+str(PORTl)+"::\r\n"
			print(msg)
			sockfd.send(msg.encode("ascii"))
			rmsg = sockfd.recv(500)	
			if(rmsg[0:1] == b"F"):
				CmdWin.insert(1.0, "\nError joining")
				print("Join error ")
			else:
				gpdecode(rmsg)
				
			
		

			
	except socket.error as emsg:
		print("Socket error: ", emsg)
	




#Function to send message to all 
def sendmsg(m):
	global roomname,Uname,fwd,msgID

	msgID=msgID+1
	myhs=sdbm_hash(Uname+IPu+str(PORTl))
	msg="T"+":"+roomname+":"+str(myhs)+":"+Uname+":"+str(msgID)+":"+str(len(m))+":"+m+"::\r\n"
	MsgWin.insert(1.0,"\n"+"["+Uname+"] "+m)

	try:
		for so in WList:
			so.send(msg.encode("ascii"))
			#print("printing i",i)
		
		if(fwd==1):
			sockfwd.send(msg.encode("ascii"))
			print("fwd send")
	
	except socket.error as emsg:
		print("Socket error: ", emsg)
	
#Function to forward messages to all but origin and message owner
def fwdmsg(m,sock):
	global gpmt,WList, sockfwd
	msg=str(m,"utf-8")
	x=str(msg).split(':')
	print(gpmt)
	a,ip,prt,d,e=gpmt[int(x[2])]
	
	try:
		for so in WList:
			print("\ncon1")
			if(so!=sock):
				xx,yy=so.getpeername()
				print("\ncon2",xx,yy)
				if not (xx==ip and yy==int(d)):
					so.send(msg.encode("ascii"))
				elif(d==0):
					so.send(msg.encode("ascii"))
				print("fwd to-->>>>>>>",xx,yy)
		
		
		
		if(fwd==1):
			if(sockfwd!=sock):
				print("\nsockfwd cond1")
				xx,yy=sockfwd.getpeername()
				print(xx,yy)		
				print("printing sockfwd",xx,yy)
				if not (xx==ip and yy==int(prt)):
					sockfwd.send(msg.encode("ascii"))
					print("sockfwd->>>>>>>>>",xx,yy)
	
	except socket.error as emsg:
		print("Socket error: ", emsg)
#
# Functions to handle user input
#
# Event handlers on click of buttons
#

def do_User():
	global Uname, arg,isgp
	CmdWin.insert(1.0, "\nPress User")
	if (isgp==0):
		x=userentry.get()
		if(len(x)>0):
			outstr = "\n[User] username: "+x
			Uname=userentry.get()
			CmdWin.insert(1.0, outstr)
			userentry.delete(0, END)
		else:
			outstr = "\nPlease Enter a Username"+x
			CmdWin.insert(1.0, outstr)
			
	else:
		
		CmdWin.insert(1.0, "User in Group please Exit before changing name")
		userentry.delete(0, END)
	

def do_List():
	global arg
	CmdWin.insert(1.0, "\nPress List")
	roomser("l")
	time.sleep(0.05)
	win.update()
	
	
	

def do_Join():
	global roomname, start,cthread
	CmdWin.insert(1.0, "\nPress JOIN")
	roomname=userentry.get()
	if(len(roomname)>0):
		if(len(Uname)>0):
			userentry.delete(0, END)
			roomser("j1")
			if(start==0):
				thd = threading.Thread(name="room", target= keepalive, args=())
				cthread.append(thd)
				thd.start()
				start=1
	else:
		CmdWin.insert(1.0, "\nPlease write Roomname")
	
	time.sleep(0.05)
	win.update()
	

def do_Send():
	x=userentry.get()
	if(len(x)>0):
		if(isgp==1):
			if(x!=""):
				sendmsg(x)
		CmdWin.insert(1.0, "\nPress Send")
		userentry.delete(0, END)
		time.sleep(0.05)
		win.update()

def do_Quit():
	global WList,sockfd,sockfwd,cthread,all_thread_running,gLock
	CmdWin.insert(1.0, "\nPress Quit")
	all_thread_running = False
	print("\nAlive:",threading.activeCount())
	gLock.acquire()
	for so in WList:
		so.close()
	gLock.release()

	sockfwd.close()
	sockfd.close()
	for t in cthread:
		print(t,"is Alive:",t.is_alive())
		t.join()
	for t in cthread:
		print(t,"is Alive:",t.is_alive())
	
	print("All threads terminated. ByeBye")
	

	

	


	sys.exit(1)



#
# Set up of Basic UI
#
win = Tk()
win.title("MyP2PChat")

#Top Frame for Message display
topframe = Frame(win, relief=RAISED, borderwidth=1)
topframe.pack(fill=BOTH, expand=True)
topscroll = Scrollbar(topframe)
MsgWin = Text(topframe, height='15', padx=5, pady=5, fg="red", exportselection=0, insertofftime=0)
MsgWin.pack(side=LEFT, fill=BOTH, expand=True)
topscroll.pack(side=RIGHT, fill=Y, expand=True)
MsgWin.config(yscrollcommand=topscroll.set)
topscroll.config(command=MsgWin.yview)

#Top Middle Frame for buttons
topmidframe = Frame(win, relief=RAISED, borderwidth=1)
topmidframe.pack(fill=X, expand=True)
Butt01 = Button(topmidframe, width='8', relief=RAISED, text="User", command=do_User)
Butt01.pack(side=LEFT, padx=8, pady=8);
Butt02 = Button(topmidframe, width='8', relief=RAISED, text="List", command=do_List)
Butt02.pack(side=LEFT, padx=8, pady=8);
Butt03 = Button(topmidframe, width='8', relief=RAISED, text="Join", command=do_Join)
Butt03.pack(side=LEFT, padx=8, pady=8);
Butt04 = Button(topmidframe, width='8', relief=RAISED, text="Send", command=do_Send)
Butt04.pack(side=LEFT, padx=8, pady=8);
Butt05 = Button(topmidframe, width='8', relief=RAISED, text="Quit", command=do_Quit)
Butt05.pack(side=LEFT, padx=8, pady=8);

#Lower Middle Frame for User input
lowmidframe = Frame(win, relief=RAISED, borderwidth=1)
lowmidframe.pack(fill=X, expand=True)
userentry = Entry(lowmidframe, fg="blue")
userentry.pack(fill=X, padx=4, pady=4, expand=True)

#Bottom Frame for displaying action info
bottframe = Frame(win, relief=RAISED, borderwidth=1)
bottframe.pack(fill=BOTH, expand=True)
bottscroll = Scrollbar(bottframe)
CmdWin = Text(bottframe, height='15', padx=5, pady=5, exportselection=0, insertofftime=0)
CmdWin.pack(side=LEFT, fill=BOTH, expand=True)
bottscroll.pack(side=RIGHT, fill=Y, expand=True)
CmdWin.config(yscrollcommand=bottscroll.set)
bottscroll.config(command=CmdWin.yview)

def main():
	global IPu, PORTu ,PORTl
	#s="M:13631095706086584736:Abhi:127.0.0.1:5555:Tony:147.8.175.180:50012:Fay:147.8.175.181:50011:James:147.8.147.190:50010::\r\n"
	#gpdecode(s)
	if len(sys.argv) != 4:
		print("P2PChat.py <server address> <server port no.> <my port no.>")
		sys.exit(2)

	PORTl=int(sys.argv[3])
	x=True
	while(x):
		try:
			x=False
			sockfd.connect((sys.argv[1], int(sys.argv[2])))
			IPu, PORTu=sockfd.getsockname()
			print("The connection with roomserver at ", sockfd.getpeername(),"has_been_established")
		except socket.error as emsg:
			print("Socket error: ", emsg)
			print("Retrying to connect in 5 sec: ")
			time.sleep(5)
			x=True
	win.mainloop()




if __name__ == "__main__":
	main()

