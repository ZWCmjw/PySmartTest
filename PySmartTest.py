from __future__ import print_function
from smartcard.scard import *
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.Exceptions import CardRequestTimeoutException
from smartcard.System import readers
from smartcard.util import *

import sys,os
import codecs
from tkinter import *
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import  askopenfilename
# from smartcard.util import toHexString
# from smartcard.util import toBytes
# from smartcard.util import HexListToBinString
import win32api

from Crypto.Cipher import DES


# define the apdus used in this script
GET_RESPONSE = [0X00, 0XC0, 00, 00]
SELECT = [0x00, 0xA4, 0x00, 0x0C, 0x02]
READ = [0x00,0xB0,0x00,0x00]
VERIFY = [0x00,0x20,0x00,0x01,0x08]


global  readerlist
global  readernum
global  connection
global  apdulist
global  coldflag
global  filename 
filename = "new"
global  filelist 
filelist = []
global  filelistnum
filelistnum = []
global  filelistcnt

def cur_file_dir():
	#获取脚本路径
	path = sys.path[0]
	#判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
	if os.path.isdir(path):
		return path
	elif os.path.isfile(path):
		return os.path.dirname(path)

def donothing():
    filewin = Toplevel(root)
    button = Button(filewin, text="Do nothing button")
    button.pack()

def markfile(num,fileline):
	global  filelist
	global  filelistnum 	
	file = fileline.upper()
	
	res = file.find("RESET") 
	if res !=  -1:
		n = file.find("CARD") 
		n += 4 
		start = str(num) + "." + str(res)
		end = str(num) + "." + str(n)
		textpad.tag_add("fun", start, end)

	res = fileline.find("//") 
	if res !=  -1:
		n = len(fileline)
		start = str(num) + "." + str(res)
		end = str(num) + "." + str(n)
		textpad.tag_add("annotation", start, end)
		apdu = file[0:res].replace(" ","").replace("	","").replace("\n","").replace("\r","")
		if apdu  != "":
			filelist.append(str(apdu))
			filelistnum.append(num)
	else:
		apdu = file.replace(" ","").replace("	","").replace("\n","").replace("\r","")
		if apdu  != "":
			filelist.append(str(apdu))
			filelistnum.append(num)

	res = file.find("MAIN:") 
	if res !=  -1:
		n = len(fileline)
		start = str(num) + "." + str(res)
		end = str(num) + "." + str(n)
		textpad.tag_add("main", start, end)

	res = file.find("END") 
	if res !=  -1:
		n = len(fileline)
		start = str(num) + "." + str(res)
		end = str(num) + "." + str(n)
		textpad.tag_add("main", start, end)

	textpad.tag_config("main", foreground="blue")
	textpad.tag_config("fun", foreground="purple")
	textpad.tag_config("annotation", foreground="green")

def Displaytext(file):
	global filelist	
	global  filelistcnt
	filelistcnt =0	
	textpad.delete(1.0,END)
	filelist = []
	with codecs.open(file, 'r', 'gbk') as handle:
		cnt = 0
		for i in handle:
			cnt +=1			
			textpad.insert(INSERT, i.strip('\n')  )
			markfile(cnt,i)
			textpad.insert(INSERT, "\n")
		handle.close()

def openfile():	
	global filename
	filename = askopenfilename(defaultextension = '.txt')
	if filename == '':
		filename = None
	else:
		root.title('RongCard:'+os.path.basename(filename))
		Displaytext(filename)

def newonefile():
	global filename	
	root.title('Unnamed file')
	filename = "new"
	textpad.delete(1.0,END)
	textpad.focus() 

def savefile():
	file = textpad.get("0.0", "end")
	if filename != "new":
		with codecs.open(filename, 'w', 'gbk') as handle:
			handle.write(file)
		handle.close()	
		Displaytext(filename)		
	else:
		saveasfile()



#另存为
def saveasfile():
	f =  asksaveasfilename(initialfile= 'Unnamed file.txt', defaultextension='.txt')
	global filename
	filename = f
	file = textpad.get("0.0", "end")
	with codecs.open(filename, 'w', 'gbk') as handle:
		handle.write(file)
	handle.close()
	Displaytext(filename)	
	root.title('FileName:'+os.path.basename(f))

def savelog():
	global filename
	path = os.path.dirname(filename)
	name = os.path.basename(filename)
	file = textlog.get("0.0", END)
	log = str (path + "/"+ name.split(".")[0] + ".log")
	with codecs.open(log, 'w', 'gbk') as handle:
		handle.write(file)
	handle.close()

def seelog():
	global filename
	path = os.path.dirname(filename)
	name = os.path.basename(filename)
	log = str (path + "/"+ name.split(".")[0] + ".log")
	win32api.ShellExecute(0,'open','notepad.exe',log,None,1)



def closefile():
	textpad.delete("0.0", "end")
	root.title('RongCard')

def showerror(errortitle,errormessage):
	messagebox.showinfo(title=errortitle,message=errormessage)


def getreader():
	global  readerlist
	readerlist = readers()		
	numberChosen['values'] = tuple(readerlist)

def connect():
	pass

def disconnect():
	connection.disconnect()

def warmreset():
	temp = readerlist
	length = len(temp)
	for i in range(length):
		temp[i] = str(temp[i])
	global  readernum
	readernum = temp.index(numberChosen.get())

	global  connection
	connection = readers()[readernum].createConnection()
	try:
		connection.connect(disposition= SCARD_RESET_CARD)
		Display_Data.set(toHexString(connection.getATR()).replace(' ',''))
	except :
		showerror("Error","Not connected to the IC card!Please connect card reader or insert IC card again!")


def coldreset():
	global  connection
	connection = readers()[readernum].createConnection()	
	try:
		connection.disconnect()
		connection.connect(disposition= SCARD_UNPOWER_CARD )
		Display_Data.set(toHexString(connection.getATR()).replace(' ',''))
	except :
		showerror("Error","Not connected to the IC card!Please connect card reader or insert IC card again!")

def RunsendAPDU(apdu):
	global  connection
	data, sw1, sw2 =connection.transmit(toBytes(apdu))
	
	if Get0xC0.get() == 1:
		sw = [sw1,sw2]
		if sw1 == 0x9F:			
			apdu = 'A0C00000'+toHexString(sw)[3:5]
			data, sw1, sw2 = connection.transmit(toBytes(apdu))			
		if sw1 == 0x61:
			cla = apdu[1:2]
			dic = {'0':"00",'1':"01",'2':"02",'3':"03"}
			try:
				apdu = dic[cla] + 'C00000' + toHexString(sw)[3:5]
				data, sw1, sw2 = connection.transmit(toBytes(apdu))			
			except :
				showerror("Error","Check CLA")
		if sw1 == 0x6C:	
			apdu = apdu[:-2] + toHexString(sw)[3:5]
			try:
				data, sw1, sw2 = connection.transmit(toBytes(apdu))	
			except :
				showerror("Error","Check LE")

	datastr = toHexString(data).replace(' ','')
	sw = [sw1,sw2]
	sw = toHexString(sw).replace(' ','')
	return datastr,sw

def sendAPDU():
	try:
		apdu = Get_APDU.get().replace(' ','')
		datastr , sw = RunsendAPDU(apdu)
		Display_Data.set(datastr+sw)

		if apdulist.count(apdu) == 0:
			apdulist.reverse()
			apdulist.append(apdu)
			apdulist.reverse()
			if len(apdulist) > 20:
				apdulist.pop()

		APDUChosen['values'] = tuple(apdulist)  
	except :
		Data_ent.set("Send failed!")


def apdulog(inputapdu):
	if inputapdu == "MAIN:" or  inputapdu == "END" :
		textlog.insert(INSERT,inputapdu+"\r\n")
	else:
		if inputapdu  == "RESETSMARTCARD":
			warmreset()			
			textlog.insert(INSERT,"Reset SmartCard" + "\r\n")
		else:							
			apdu = 	inputapdu.split(';')
			apdulen = len(apdu)
			try:
				data,sw = RunsendAPDU(apdu[0])
				textlog.insert(INSERT,"==============================================" "\r\n")
				textlog.insert(INSERT,"APDU:" + apdu[0]+ "\r\n")
				if data == "":
					data = "not receive data"

				if apdulen >= 2:
					if apdu[1][0:3] == "SW=":
						if sw in apdu[1]:													
							textlog.insert(INSERT,"Expect  SW:" + apdu[1][3:]+"\r\n"+ "Receive SW:" + sw+"\r\n")
						else:
							textlog.insert(INSERT,"Expect  SW:" + apdu[1][3:]+"\r\n"+ "Receive SW:" + sw +"\r\n")								
							stop()
							showerror("ERROR", "SW ERROR!")
							return False
					elif apdu[1][0:3] == "DE=":							
						if data in apdu[1]:
							textlog.insert(INSERT,"Expect  DE:" + apdu[1][3:]+"\r\n"+ "Receive DE:" + data+"\r\n")
						else:
							textlog.insert(INSERT,"Expect  DE:" + apdu[1][3:]+"\r\n"+ "Receive DE:" + data+"\r\n")	
							stop()
							showerror("ERROR", "DE ERROR!")
							return False			
					if apdu[2][0:3] == "SW=":
						if sw in apdu[2]:
							textlog.insert(INSERT,"Expect  SW:" + apdu[2][3:]+"\r\n"+ "Receive SW:" + sw+"\r\n")
						else:
							textlog.insert(INSERT,"Expect  SW:" + apdu[2][3:]+"\r\n"+ "Receive SW:" + sw+"\r\n")
							stop()
							showerror("ERROR", "SW ERROR!")
							return False
					elif apdu[2][0:3] == "DE=":
						if data in apdu[2]:
							textlog.insert(INSERT,"Expect  DE:" + apdu[2][3:]+"\r\n"+ "Receive DE:" + data+"\r\n")
						else:
							textlog.insert(INSERT,"Expect  DE:" + apdu[2][3:]+"\r\n"+ "Receive DE:" + data+"\r\n")
							stop()
							showerror("ERROR", "DE ERROR!")
							return False
				else:
					textlog.insert(INSERT,"Expect  SW:" +"\r\n"+ "Receive SW:" +"\r\n")
					textlog.insert(INSERT,"Expect  DE:" +"\r\n"+ "Receive DE:" +"\r\n")

				textlog.see(END)
			except:
				return False


def single_step():
	global filelist
	global filelistnum
	global  filelistcnt

	try:
		if filelistcnt == 0:
			textlog.delete(1.0,END)

		if filelistcnt >= len(filelistnum):
			filelistcnt= 0
			textpad.tag_remove("step", 0.0, END)
		else:
			start0 = str(filelistnum[filelistcnt]) +".0"
			end0 = str(filelistnum[filelistcnt]+1) +".0"
			textpad.tag_add("step", start0, end0)
			textpad.tag_config("step", background="LightGray")

			apdulog(filelist[filelistcnt])

			filelistcnt += 1
	except:
		pass

def run():
	global filelist
	global filelistnum
	try:
		textlog.delete("0.0", "end")

		for s in filelist:
			if apdulog(s) == False:
				break
	except:
		pass


def stop():
	global filelistcnt
	global filelistnum
	filelistcnt = 	len(filelistnum) +1
	# single_step()


def new(event):
	newonefile()
def open(event):
	openfile()
def save(event):
	savefile()
def saveas(event):
	saveasfile()
def close(event):
	closefile()

def cut():
    textpad.event_generate('<<Cut>>')

def copy():
    textpad.event_generate('<<Copy>>')

def paste():
    textpad.event_generate('<<Paste>>')

def redo():
    textpad.event_generate('<<Redo>>')

def undo():
    textpad.event_generate('<<Undo>>')

def selectAll():
    textpad.tag_add('sel','1.0',END)

def author():
    pass
    # showinfo('作者信息','本软件由飞不起来完成')
def about():
    pass
    # showinfo('版权信息.copyright','版权融卡')

def menubarfun():
	filemenu = Menu(menubar)
	filemenu.add_command(label = '新建', command=newonefile, accelerator ='ctrl + n')
	filemenu.add_command(label = '打开', command=openfile,  accelerator ='ctrl + o')
	filemenu.add_command(label = '保存', command=savefile,  accelerator ='ctrl + s')
	filemenu.add_command(label = '另存为',command=saveasfile,accelerator ='ctrl + Shift + s')	
	filemenu.add_command(label = '关闭', command=closefile, accelerator ='ctrl + w')
	menubar.add_cascade(label = '文件',menu = filemenu)	
	editmenu = Menu(menubar)
	editmenu.add_command(label = '撤销',accelerator = 'ctrl + z')
	editmenu.add_command(label = '重做',accelerator = 'ctrl + y')
	editmenu.add_command(label = '复制',accelerator = 'ctrl + c')
	editmenu.add_command(label = '剪切',accelerator = 'ctrl + x')
	editmenu.add_command(label = '粘贴',accelerator = 'ctrl + v')
	editmenu.add_command(label = '查找',accelerator = 'ctrl + F')
	editmenu.add_command(label = '全选',accelerator = 'ctrl + A')
	menubar.add_cascade(label = '编辑',menu = editmenu)
	aboutmenu = Menu(menubar)
	aboutmenu.add_command(label = '作者',command = author)
	aboutmenu.add_command(label = '版权',command = about)
	menubar.add_cascade(label = '关于',menu = aboutmenu)	






root = Tk()
root.title('PySmartTest')
menubar = Menu(root)
menubarfun()
frame = Frame(root)
# frame.pack(padx=8, pady=8, ipadx=4)
frame.pack(pady=8, ipadx=4)


button_reader = Button(frame, text="读卡器", command=getreader,relief= GROOVE)



readers_Display = StringVar()
numberChosen = ttk.Combobox(frame, textvariable=readers_Display)
numberChosen['values'] = ("选择读卡器")  
numberChosen.current(0)

# button_connect = Button(frame, text="复位",command=connect,relief= GROOVE)
button_disconnect = Button(frame, text="断开",command=disconnect,relief= GROOVE)
button_warmreset = Button(frame, text="复位", command=warmreset,relief= GROOVE)
button_coldreset = Button(frame, text="冷复位", command=coldreset,relief= GROOVE)

button_go = Button(frame, text="单步",command=single_step,relief= GROOVE)
button_run = Button(frame, text="运行",command=run,relief= GROOVE)
button_stop = Button(frame, text="停止", command=stop,relief= GROOVE)
button_savelog = Button(frame, text="保存log", command=savelog,relief= GROOVE)
button_seelog = Button(frame, text="查看log", command=seelog,relief= GROOVE)


button_reader.grid(row=0, column=0,  sticky='ew')
numberChosen.grid(row=0, column=1, sticky='ew', columnspan=8)
# button_connect.grid(row=0, column=9,  sticky='ew')
button_disconnect.grid(row=0, column=9,  sticky='ew')
button_warmreset.grid(row=0, column=10, sticky='ew')
button_coldreset.grid(row=0, column=11, sticky='ew')


Get0xC0 = IntVar()    
check0xC0 = Checkbutton(frame, text="自动获取响应", variable=Get0xC0)    
check0xC0.deselect()
check0xC0.grid( row=0, column=12,sticky='ew')



APDU_lab = Label(frame, text="APDU:")
Get_APDU = StringVar()
global apdulist
apdulist = []
APDUChosen = ttk.Combobox(frame, width=24, textvariable=Get_APDU)
APDUChosen['values'] = tuple(apdulist)  
APDUChosen.focus() 
# APDUChosen.current(0)
button_send = Button(frame, text="发送", command=sendAPDU,relief= GROOVE)
Display_Data = StringVar()
Data_ent = Entry(frame, textvariable=Display_Data, relief=GROOVE)

APDU_lab.grid(row=2, column=0,   sticky='ew')
APDUChosen.grid(row=2, column=1, sticky='ew', columnspan=8)
button_send.grid(row=2, column=9,sticky='ew')
Data_ent.grid(row=2, column=10, sticky='ew', columnspan=10)


button_go.grid(row=3, column=1,  sticky='ew')
button_run.grid(row=3, column=2,  sticky='ew')
button_stop.grid(row=3, column=3, sticky='ew')
button_savelog.grid(row=3, column=4, sticky='ew')
button_seelog.grid(row=3, column=5, sticky='ew')



textpadW = 100 # 设置文本框的长度
textpadH = 30 # 设置文本框的高度
textpad = scrolledtext.ScrolledText(frame, width=textpadW, height=textpadH,tabs = 16,relief= SUNKEN)
textpad.grid(row=4,column=1, columnspan=19) 

textlogW = 100
textlogH = 15
textlog = scrolledtext.ScrolledText(frame, width=textlogW, height=textlogH, tabs=16, relief=SUNKEN)
textlog.grid(row=5, column=1, columnspan=19)





root.config(menu=menubar)
root.update_idletasks()
x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2
y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2
root.geometry("+%d+%d" % (x,y))
# root.resizable(False, False)   #禁止修改窗口大小
root.maxsize(800, 700)
path = cur_file_dir()
try:
    root.iconbitmap(path + '\ico\card.ico')
except:
    pass
# root.wm_attributes('-topmost',1)
root.attributes("-alpha",1)
root.bind_all("<Control-n>", new)
root.bind_all("<Control-o>", open)
root.bind_all("<Control-s>", save)
root.bind_all("<Control-S>", saveas)
root.bind_all("<Control-w>", close)

root.mainloop()