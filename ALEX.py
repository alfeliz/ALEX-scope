#!/usr/bin/env python
#Test python
#coding: latin-1
#Version 1.05
#TO DO:
#Function TRANSF needs to take into account the posibility of an unknown trasnformation.
#DONE Think if the word "wire" should be the indicator of comments

import os #File management
import csv #To make the nice CSV output.
import numpy as np #Numerical work in Python. Yeah!!!
import scipy.integrate as inte #Numerical integration. YOU NEED TO INSTALL THE SCIPY PACKAGE.
import matplotlib.pyplot as plt
from Gpib import * #Gpib module import everything. there is no overlap.
# (http://stackoverflow.com/questions/710551/import-module-or-from-module-import)
import time #timing handling


###############################
###FUNCTIONS:
###############################

#From: https://www.peterbe.com/plog/uniqifiers-benchmark
def rem_repeat(seq, idfun=None): 
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result
   
#Defining a function to save the channels info:
def chansave(channel,chandata):
	if not os.path.isfile(channel):	#When the file does not exists.
		with open(channel, 'w') as arch:
			writer = csv.writer(arch, delimiter="\t", quotechar=" ")
			#4 decimals:
			writer.writerows(map(lambda t: ("%.4e" % t[0], "%.4e" % t[1]), chandata))
			#~ writer.writerows(chandata)
	else: #the file exists:
		with open("01-"+channel, 'w') as arch:
			writer = csv.writer(arch, delimiter="\t", quotechar=" ")
			#4 decimals:
			writer.writerows(map(lambda t: ("%.4e" % float(t[0]), "%.4e" % float(t[1])), chandata))
	return[0]   
   
def transf(signal, device): 
	time = []
	volts = []
	for x in range(0,len(signal)):
		time.append(signal[x][0])
		volts.append(signal[x][1])
	time = np.array(time)
	volts = np.array(volts)

	if "2Rog" in device:
		#Multiplying to obtain the A/s:
		der_curr = volts*8000000000.00 #Rogowsky gives current derivative. Updated value
		current = inte.cumtrapz(der_curr, time, initial=0)
		result = zip(time,current)
	elif "2Res" in device:
		volt_div2 = 1359*volts #Updated value for second time
		result = zip(time,volt_div2)
	elif "3Res" in device:
		volt_div3 = 2400*volts #Updated value for second time
		result = zip(time,volt_div3)
	elif "Phot" in device:
		#Normalizing to 1:
		phot = volts/max(volts)
		result = zip(time,phot)
	elif "Dumb" in device: #"No device" attached to the scope.
		result = zip(time,volts)
	return[result]


def takechan(channel,sleeptime,addr):
	#sleeptime = 0.030
	#addr = 3 #Gpib address of the scope
	scope = Gpib(0,addr)
	
	scope.write("HEADER OFF") #Don't give headers of data with the data.
	time.sleep(sleeptime)
	scope.write("DATA:WIDTH 1")
	time.sleep(sleeptime)
	scope.write("DATA:ENCDG ASCII") #1 byte for voltage data and ASCII format.
	time.sleep(sleeptime)
	
	selectchan = "SELECT:"+channel+" ON"
	datachan = "DATA:SOURCE "+channel

	#SELECTING CHANNEL 1:
	scope.write(selectchan) #Set the channel to show, if was not it will not record the data...
	time.sleep(sleeptime)

	scope.write(datachan) #Set the channel source to Channel datachan.
	time.sleep(sleeptime)

	scope.write("DATA:SOURCE?") #Ask for data.
	time.sleep(sleeptime)
	CHAN = scope.read(3)

	#CHANNEL ASIGNMENT CHECKING
	if CHAN != channel: #DO NOT FORGET THE : IN THE IF...
		print("Error: Channel not correctly assigned.")
		print(CHAN, datachan)
		raise SystemExit #Go out. all wrong.

	#WAVEFORM PREAMBLE (ALL INFO OVER DATA)
	scope.write("WFMPRE?")
	time.sleep(sleeptime)
	preamble = scope.read(256)
	preamble = preamble.split(";")

	#USE OF PREAMBLE INFO. PUTTING THEM IN NICE VARIABLES.
	points = int(preamble[5])
	ymult = float(preamble[12])
	yzero = float(preamble[13])
	yoff = float(preamble[14]) #Not measured, but stablished. Let's remove it...
	
	#WAVEFORM VOLTS/DIV SCALE:
	text = channel + ":SCALE?"
	scope.write(text)
	time.sleep(sleeptime)
	Volt = float(scope.read())

	print("Reading data from channel {!s}...".format(CHAN))

	#WAVEFORM DATA: (FINALLY)
	scope.write("CURVE?")
	time.sleep(sleeptime)
	tmp_curve = scope.read(16384) #Why 16384? Looks like it's related wit the SEC/DIV settings.
	print("Reading finished...")

	#Waveform transformation into real volts:
	tmp_curve = tmp_curve.split(",") #First, splitting the bytes. Why now "," and before ";"? Ask Textronik...

	CH_curve = [] #EMPTY NOW... LET'S FILL IT!!!
	for x in tmp_curve[len(tmp_curve)-points:-1]:
		CH_curve.append(0)

	#CREATING TIME VECTOR:
	t =[]
	scope.write("WFMPRE:XINCR?")
	time.sleep(sleeptime)
	sweep=float(scope.read())
	for n in range(len(CH_curve)):
		t.append(int(n)*sweep)
		
	CH_curve = zip(t,CH_curve)
	CH_error = ymult/Volt
		
	return(CH_curve, CH_error, preamble)












############################################################################################################################
###############################
###PROGRAM:
###############################
#To do:
#1)DONE (not necesary, info is saved in the HTMLfile) Save the setting file
#2)DONE Think if to save the preamble file, and how to save it.
#3)Impose closing of files.
############################################################################################################################

ms = 1e-3

sleeptime = 30*ms

addr01 = 2 #Gpib address of scope 01, A.K.A. "ALL"

addr02 = 1 #Gpib address of scope 02, A.K.A. "DETAIL"


with open("./settings.txt","r") as sett: #Open file with settings called "settings.txt" in this folder.
	ste_list = list(sett)



###############################
#Extracting shot name and 
#characteristics:
###############################
shot_name = [name for name in ste_list if "shot" in name] #Choose the list items with "shot" on them.
shot_name = (" ".join(shot_name)).split() #Look for the shot name

shot_wire = [wire for wire in ste_list if "wire" in wire]
shot_wire =(" ".join(shot_wire)).split()

for i in range(0,len(ste_list)): #Comments start BEFORE the line with the word wire in
	if "wire" in ste_list[i]:
		pos = i+1
shot_comments = ste_list[pos:-1]
shot_comments = rem_repeat(shot_comments)
shot_comments.remove("\n")
shot_comments = "".join(shot_comments)
shot_comments = [x for x in shot_comments if "\n" not in x]
shot_comments = "".join(shot_comments)


shot_voltage = ste_list[-1]



if shot_name[1].startswith("ALEX"):
	shot_number = shot_name[1][4:]
else:
	print("Problems with the shot name: ",shot_name[1])

if os.path.isdir("./"+str(shot_name[1])):
	print("Shot folder already created.\nChanging the name to ",shot_name[1]+"_01")
	shot_name[1] = shot_name[1]+"_01"

#Making the folder structure for the shot:
os.mkdir("./"+str(shot_name[1])) #Main folder
os.mkdir("./"+str(shot_name[1])+"/"+shot_number+"_RAW") #Raw data folder
os.mkdir("./"+str(shot_name[1])+"/"+shot_number+"_WORKED") #Trandformed data folder

initial_folder = os.getcwd()
raw_folder = os.path.join(initial_folder,str(shot_name[1])+"/"+shot_number+"_RAW")
worked_folder = os.path.join(initial_folder,str(shot_name[1])+"/"+shot_number+"_WORKED")


###############################	
#Channels info:
###############################
	
#Scopes go by order:
scopes_positions =[i for i,x in enumerate(ste_list) if "SCOPE" in x]
#Finding the scope names:
scopes_names =[]
for i in scopes_positions:
	scopes_names.append(ste_list[i])

scopes_names = ("\t".join(scopes_names)).split()
scopes_names = rem_repeat(scopes_names)
scopes_names.remove("SCOPE")



#Svae in chan_list the scope, channels avaliable and devices in each channel:
chan_posi = [i for i,x in enumerate(ste_list) if "CH" in x]
chan_list = []
for i in chan_posi:#!/usr/bin/env python
	if "ns" not in ste_list[i]:
		#If you want to consider more scopes, modify this IF loop
		if i< scopes_positions[1]: #We are in the first scope. 
			chan_list.append(scopes_names[0])
			chan_list.append(ste_list[i])	
			chan_list.append(ste_list[i+1])
		else:
			chan_list.append(scopes_names[1])  #Second scope name
			chan_list.append(ste_list[i])	
			chan_list.append(ste_list[i+1])			

#Dividing it in three tuples:
chan_list = [chan_list[i:i+3] for i in range(0, len(chan_list), 3)]



#################################################	
#Channels data saving and taking:
#################################################
#For each channel, convert the data and stored the converted and original signals:
data = [] #Initialing this list as such.
n = 0 #To save the picture just one time
m = 0 #To save the picture just one time
for i in range(0,len(chan_list)):
	##############################3
	##########
	#Change the line for something that takes into account the scope, like the if 
	#~ #CH1_curve, CH1_err = takechan(chan_list[i][1][:-1],sleeptime,scope) #Real command, man.
	if chan_list[i][0] == "ALL":
		print("Scope ALL")
		CH_curve, CH_error, CH_preamble = takechan(chan_list[i][1][:-1],sleeptime,addr01) #Real command, man.
		if n==0:
			scope = Gpib(0,addr01)
			print "Start reading the screen. This takes a while..."
			scope.write('HARDCOPY START')
			time.sleep(sleeptime)
			raw_data = scope.read(80000)
			#Go to the raw shot folder:
			os.chdir(os.path.join(initial_folder,str(shot_name[1])))
			fid = open(chan_list[i][0]+'-Picture.bmp', 'wb')
			fid.write(raw_data)
			fid.close()
			print 'Done with ALL'
		n = n +1
	else:
		print("Scope DETAIL")
		CH_curve, CH_error, CH_preamble = takechan(chan_list[i][1][:-1],sleeptime,addr02) #Real command, man.
		if m==0:
			scope = Gpib(0,addr02)
			print "Start reading the screen. This takes a while..."
			scope.write('HARDCOPY START')
			time.sleep(sleeptime)
			raw_data = scope.read(80000)
			#Go to the general shot folder:
			os.chdir(os.path.join(initial_folder,str(shot_name[1])))
			fid = open(chan_list[i][0]+'-Picture.bmp', 'wb')
			fid.write(raw_data)
			fid.close()
			print 'Done with DETAIL'
		m = m +1

	filename = chan_list[i][0] + "_"+ chan_list[i][1][:-1] + ".csv"
	os.chdir(raw_folder) #Raw data folder.
	chansave(filename,CH_curve)
	print("Saving raw scope file...{!s}".format(filename))
	
	
	#~ if chan_list[i][0] == "DETAIL":
		#~ print("CH_curve",CH_curve)

	signal = transf(CH_curve, chan_list[i][2]) #Signal is a list of list
	
	#~ print(signal[0])

	if chan_list[i][0] == "ALL": #We will store general data from the first scope only.
		if "2Rog" in chan_list[i][2]: #Current signal
			data.append(["current", signal])
		elif "2Res" in chan_list[i][2]: #voltage beginning signal
			data.append(["volt_in", signal])
		elif "3Res" in chan_list[i][2]: #voltage end signal
			data.append(["volt_out", signal])
		elif "Phot" in chan_list[i][2]: #Photodiode
			data.append(["Phot", signal])
			
	
	filename = chan_list[i][0]+ "_" + chan_list[i][2][1:6] + ".csv"
	os.chdir(worked_folder)
	if any(isinstance(el, list) for el in signal): #Then signal is a list of lists:
		chansave(filename, signal[0]) #Because I know that then is the first list were info is.
	else:
		chansave(filename, signal) #Just a normal list.
		print("Normal list")
	os.chdir(os.path.join(initial_folder,str(shot_name[1]))) #Come to the Shot folder


foo1 = [] #Not to be used
foo2 = [] #Not to be used
foo3 = []
foo4 = []
#Separating data in lists:
for i in range(0, len(data)):
	if data[i][0] == "current":
		foo1 = list(data[i][1])
	elif  data[i][0] == "volt_in":
		foo2 = list(data[i][1])
	elif  data[i][0] == "volt_out":
		foo3 = list(data[i][1])
	elif  data[i][0] == "Phot":
		foo4 = list(data[i][1])

volt = []
time = []
current = []
photodiode =[]
power = []
for i in range(0,len(foo2[0])):
	time.append(float(foo2[0][i][0]))
	try:
		volt.append(float(foo2[0][i][1]-foo3[0][i][1]))
	except:
		volt.append(float(foo2[0][i][1]))
		
	try:
		current.append(float(foo1[0][i][1]))
	except IndexError:
		current.append(0)
		
	try:
		photodiode.append(float(foo4[0][i][1]))
	except IndexError:
		photodiode.append(0)


for i in range(0,len(volt)):
	power.append(float(volt[i]*current[i])/1e3) #KiloWatts



#Data plotted:
#Voltage, current and elec. power:
fig_01, ax1 = plt.subplots()
ax1.plot(time,volt,"g", time,current,"b")
ax1.set_ylabel("Volts, Current")
ax1.legend(["Volts(V)","Current(A)"])
ax1.set_title(str(shot_name[1])+" electrical")
ax2 = ax1.twinx()
ax2.plot(time, power,"r")
ax2.set_ylabel("Power(W)", color="r")
# Make the y-axis label and tick labels match the line color.
for tl in ax2.get_yticklabels():
    tl.set_color('r')
ax2.legend(["Power(KW)"], loc=3)
ax1.figure.savefig(str(shot_name[1])+"-elec.png",dpi=300)

#Voltage, current and photodiode:
fig_02, ax3 = plt.subplots()
ax3.plot(time,volt,"g", time,current,"b")
ax3.set_ylabel("Volts, Current")
ax3.legend(["Volts(V)","Current(A)"])
ax3.set_title(str(shot_name[1])+" light")
ax4 = ax3.twinx()
ax4.plot(time, photodiode,"k")
ax4.set_ylabel("Phot. (A.U.)", color="k")
# Make the y-axis label and tick labels match the line color.
for tl in ax4.get_yticklabels():
    tl.set_color('k')
ax4.legend(["Phot.(A.U.)"], loc=3)
ax3.figure.savefig(str(shot_name[1])+"-light.png",dpi=300)

	
#################################################	
#HTML construction:
#################################################	

#Folder situation:
os.chdir(os.path.join(initial_folder,str(shot_name[1])))

direction = str(os.path.join(initial_folder,str(shot_name[1]))  )

html_01 = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <meta content="text/html;charset=ISO-8859-1" http-equiv="Content-Type">
"""

html_02 = "    <title>"+str(shot_name[1])+"</title>"+"""
  </head>
  <body>
"""

html_04 = "<h1>"+str(shot_name[1])+"</h1>"

html_05 = "<p><b>Material:</b>	"+str(shot_wire[0])+"	<b>Diameter:</b>	"+str(shot_wire[1])+"	<b>Length:</b>	"+str(shot_wire[2])+"	<b>Initial voltage:</b>	"+str(shot_voltage)+"</p>"

html_06 = "<p><b>Comments:</b></p>"

html_07 = "<p>"+str(shot_comments)+"</p>"

html_08 = '<img src="./'+str(shot_name[1])+'-light.png" border="3" height="500" width="500">'
 
html_09 = '<img src="./'+str(shot_name[1])+'-elec.png" border="3" height="500" width="500">'

html_10 = '<img src="./'+'ALL-Picture.bmp" border="3" height="500" width="500">'

html_11 = '<img src="./'+'DETAIL-Picture.bmp" border="3" height="500" width="500">'

html_12 = '<h3>Scopes wiring.</h3>'

html_14 = "<p>" +str(item for sublist in chan_list for item in sublist)+"<p>"
#html_14 = "<p>"+str(chan_list)+"</p>"

html_99 = "</body> </html>"


html_total = html_01+html_02+html_04+html_05+html_06+html_07+html_08+html_09+html_10+html_11+html_12+html_14+html_99



#Writing of web page:
os.chdir(os.path.join(initial_folder,str(shot_name[1])))
with open(str(shot_name[1])+".html","w") as htfile:
	htfile.write(html_total)	
	htfile.close()
