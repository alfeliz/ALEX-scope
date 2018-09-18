
import os #Folder and files managment
import csv #To make the nice CSV output.
import re #Regular expresions use.
import numpy as np #Numerical work in Python. Yeah!!!
import scipy.integrate as inte #Numerical integration. YOU NEED TO INSTALL THE SCIPY PACKAGE.
#~ import matplotlib.pyplot as plt
import Gpib #Gpib module import everything. there is no overlap.
# (http://stackoverflow.com/questions/710551/import-module-or-from-module-import)
import time #timing handling




###############################
###FUNCTIONS:
###############################

#To remove similar values in a chain:
#From: https://www.peterbe.com/plog/uniqifiers-benchmark
#~ def rem_repeat(seq, idfun=None): 
   #~ # order preserving
   #~ if idfun is None:
       #~ def idfun(x): return x
   #~ seen = {}
   #~ result = []
   #~ for item in seq:
       #~ marker = idfun(item)
       #~ # in old Python versions:
       #~ # if seen.has_key(marker)
       #~ # but in new ones:
       #~ if marker in seen: continue
       #~ seen[marker] = 1
       #~ result.append(item)
   #~ return result
   
#Defining a function to save the channels info:
def chansave(channel,chandata):
	if not os.path.isfile(channel):	#When the file does not exists.
		with open(channel, 'w') as arch:
			writer = csv.writer(arch, delimiter="\t", quotechar=" ")
			#8 decimals:
			writer.writerows(map(lambda t: ("%.8e" % t[0], "%.8e" % t[1]), chandata))
			#~ writer.writerows(chandata)
	else: #the file exists:
		with open("01-"+channel, 'w') as arch:
			writer = csv.writer(arch, delimiter="\t", quotechar=" ")
			#8 decimals:
			writer.writerows(map(lambda t: ("%.8e" % float(t[0]), "%.8e" % float(t[1])), chandata))
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
		der_curr = volts*12820000000.00 #Rogowsky gives current derivative. Updated value for third time
		result = np.column_stack((time,der_curr))
	elif "2Res" in device:
		volt_div2 = 1359*volts #Updated value for second time
		result = np.column_stack((time,volt_div2))
	elif "3Res" in device:
		volt_div3 = 2400*volts #Updated value for second time
		result = np.column_stack((time,volt_div3))
	elif "Phot" in device:
		#Normalizing to 1:
		phot = volts/max(volts)
		result = np.column_stack((time,phot))
	elif "Curr" in device:
		curr_time = volts * 139000
		result = np.column_stack((time,curr_time))
	elif "None" in device: #"No device" attached to the scope.
		result = np.column_stack((time,volts))

	return[result]


def takechan(channel,sleeptime,addr):
	#sleeptime = 0.030
	#addr = 3 #Gpib address of the scope
	scope = Gpib.Gpib(0,addr)
	
	scope.write("*IDN?") #Identify the scope
	time.sleep(sleeptime)
	scope_type = scope.read(3)
	
	if scope_type == "TEK": #tektronik scopes
		scope.write("HEADER OFF") #Don't give headers of data with the data.
		time.sleep(sleeptime)
		scope.write("DATA:WIDTH 1")
		time.sleep(sleeptime)
		scope.write("DATA:ENCDG ASCII") #1 byte for voltage data and ASCII format.
		time.sleep(sleeptime)
		
		selectchan = "SELECT:"+channel+" ON"
		datachan = "DATA:SOURCE "+channel

		#SELECTING CHANNEL:
		scope.write(selectchan) #Set the channel to show, if was not it will not record the data...
		time.sleep(sleeptime)

		scope.write(datachan) #Set the channel source to Channel datachan.
		time.sleep(sleeptime)

		#CHANNEL ASIGNMENT CHECKING
		scope.write("DATA:SOURCE?") #Ask for data channel source.
		time.sleep(sleeptime)
		CHAN = scope.read(3)
		if CHAN != channel:
			print("Error: Channel not correctly assigned.")
			print(CHAN, datachan)
			raise SystemExit #Go out. all wrong.

		#WAVEFORM PREAMBLE (ALL INFO OVER DATA)
		scope.write("WFMPRE?")
		time.sleep(sleeptime)
		preamble = scope.read(256).split(";")
		#preamble = preamble.split(";")

		#USE OF PREAMBLE INFO. PUT INFO IN NICE VARIABLES.
		points = int(preamble[5])
		ymult = float(preamble[12])
		yzero = float(preamble[13])
		yoff = int(float(preamble[14])) #Not measured, but stablished. Let's remove it...
		#WAVEFORM VOLTS/DIV SCALE:
		text = channel + ":SCALE?"
		scope.write(text)
		time.sleep(sleeptime)
		Volt = float(scope.read())

		print("Reading data from channel {!s}...".format(CHAN))

		#WAVEFORM DATA: (FINALLY)
		scope.write("CURVE?")
		time.sleep(sleeptime)
		curve = scope.read(16000).split(",")
		if curve[len(curve)-1] == "": #Avoiding strange numbers...
			curve[len(curve)-1] = "0"
		print("Reading finished...")

		#Waveform transformation into real volts:
			#The rounding to 2 ciphers is important to avoid the use of 
			#garbage bits apperaing in the digitazing process from the computer.
			# As now no integration is necessary, 10 cyphers are used.
		CH_curve = [round((int(x) - yoff)*ymult,10) for x in curve] 

		#CREATING TIME VECTOR:
		t =[]
		scope.write("WFMPRE:XINCR?")
		time.sleep(sleeptime)
		sweep=float(scope.read())
		for n in range(len(CH_curve)):
			t.append(float(n)*sweep)
			
		CH_curve = zip(t,CH_curve)
		CH_error = ymult/Volt
	else: #Lecroy scope. Its label is shit.
		scope.write('DTFORM ASCII') #ASCII format for the data.	
		time.sleep(sleeptime)
		scope.write('WAVESRC '+channel) #Selecting channel for waveform download.
		time.sleep(sleeptime)		
		scope.write('DTINF?') #reading information of the scope and waveform setup.
		time.sleep(sleeptime)
		preamble =  scope.read(550).split(",")
		#Determining the number of points to be read in the waveform(Memory Length)		
		points = preamble[23][16:] #text, not number!!!!
		#Determining the time division:
		t_sweep = ( convlecroytime(preamble[20][11:])/float(points) )*10
		#Passing them to the scope:
		scope.write('DTPOINTS '+points)
		time.sleep(sleeptime)
		#Determining the scaling and offset of the channel:
		if channel == 'CH1':
			CH_scale = convlecroyscale(preamble[4][12:]) #This is a number
			CH_offset =convlecroyscale(preamble[5][9:])
		elif channel == 'CH2':
			CH_scale = convlecroyscale(preamble[8][12:])
			CH_offset =convlecroyscale(preamble[9][9:])
		elif channel == 'CH3':
			CH_scale = convlecroyscale(preamble[12][12:])
			CH_offset =convlecroyscale(preamble[13][9:])
		elif channel == 'CH4':
			CH_scale = convlecroyscale(preamble[16][12:])
			CH_offset =convlecroyscale(preamble[17][9:])
		print("Reading data from channel {!s}...".format(channel))
		scope.write('DTWAVE?')
		time.sleep(sleeptime)
		wave_ascii =  scope.read(8*int(points)).split(",") #It reads bites transformed in BYTES...
		wave_number = [float(number) for number in wave_ascii]
		volts = [ round(  ( ((float(number) / 256 / 32 ) * CH_scale ) - CH_offset ),12) for number in wave_ascii]
		#Making the time vector:
		t =[] #It's a list
		for i in range(len(volts)):
			t.append(float(i)*t_sweep)
		CH_curve = zip(t,volts) #List of tuples.
		CH_error = CH_scale 
	return(CH_curve, CH_error, preamble)
	
def readTekScreen(adrr,sleeptime):
	scope = Gpib.Gpib(0,adrr)
	scope.write('HARDCOPY START')
	time.sleep(sleeptime)
	raw_data = scope.read(80000) #Minimun number to obtain the full picture
	return raw_data
	
def readLECScreen(adrr,sleeptime):
	scope = Gpib.Gpib(0,adrr)
	scope.write('TSCRN? BMP')
	time.sleep(sleeptime)
	raw_data = scope.read(330000) #Minimun number to obtain the full picture
	return raw_data[10:] #It is necessary to remove the first byte, as it is no data.
	
def convlecroyscale(scale_text):
	value = float(re.findall(r'[+-]?[0-9.]+',scale_text)[0]) #Hopefully the scale in volts
	if re.findall(r'[V-mV]+',scale_text)[0] == 'mV':
		value = value * 1e-3
	return value

def convlecroytime(scale_time):
	value = float(re.findall(r'[+-]?[0-9.]+',scale_time)[0]) #time scale number
	if re.findall(r'[s,ms,us,ns]+',scale_time)[0] == 'ms':
		value = value * 1e-3
	elif re.findall(r'[s,ms,us,ns]+',scale_time)[0] == 'us':
		value = value * 1e-6
	elif re.findall(r'[s,ms,us,ns]+',scale_time)[0] == 'ns':
		value = value * 1e-9		
	return value
