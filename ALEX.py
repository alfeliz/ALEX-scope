#!/usr/bin/env python
#Test python
#coding: latin-1
#Version 2.20

import os #File management
import numpy as np #Numerical work in Python. Yeah!!!
import matplotlib.pyplot as plt
# (http://stackoverflow.com/questions/710551/import-module-or-from-module-import)
import time #timing handling
from scipy.optimize import leastsq

import tektronik as teky #function names are different enough to do not overlap.


############################################################################################################################
###############################
###PROGRAM:
###############################
#To do:
#2)DONE Think if to save the preamble file, and how to save it.
#3)Impose closing of files.
############################################################################################################################

ms = 1e-3

sleeptime = 30*ms

addr01 = 2 #Gpib address of scope 01, A.K.A. "ALL"

addr02 = 1 #Gpib address of scope 02, A.K.A. "DETAIL"

addr03 = 11 #Gpib address of scope 03, A.K.A "LECROY"

###############################
#Open and read SETUP file:
###############################
with open("./settings.txt","r") as sett: #Open file with settings called "settings.txt" in this folder.
	text_list = list(sett) #Store the data in a list, each element a line of the file.
	ste_list = [line for line in text_list if not "#" in line]




###############################
#Extracting shot name and 
#characteristics:
###############################
shot_name = [line_name for line_name in ste_list if "shotname" in line_name] #Choose the list lines (items) with "shot" on them.
shot_name = (" ".join(shot_name)).split() #Split the list with by the spaces.
shot_name.pop(0) #To remove the indication of shot name and leave the name only

shot_wire = [line_wire for line_wire in ste_list if "wire" in line_wire]#Choose the list lines (items) with "wire" on them.
#(One of the is the wire info)
shot_wire =(" ".join(shot_wire)).split() #Split the list with the lines with the word "wire" by the spaces.

#Choosing the position of the beginning of comments in the SETTINGS.TXT file:
for i in range(0,len(ste_list)): #Comments go from the first line with "wire" to the end of the file.
	if "wire" in ste_list[i]:
		pos = i+1
		
shot_comments = ste_list[pos:-1]

for i in range(0,len(shot_comments)): #Remove in each line string the "retorno de carro"
	shot_comments[i] = shot_comments[i].translate(None,"\n")

shot_comments = "<p>".join(shot_comments) #Make a single string of the list ready for HTML use.

#Choose the list lines (items) with "olts" on them. (Voltage value in ALEX)
shot_voltage = [line_volt for line_volt in ste_list if "olts" in line_volt][0].translate(None,"\n")

#Extract the "shot number" or equivalent in ALEX:
if shot_name[0].startswith("ALEX"):
	shot_number = shot_name[0][4:]
else:
	print("Problems with the shot name: ",shot_name)

#Make a boolean to save or not treated data:
shot_raw = [line_raw for line_raw in ste_list if "storeboolean" in line_raw][0].translate(None,"\n")
# Decide if work with data or not, and anything but the treatment
if "RAW" in shot_raw:
	verbose = False
	type_work = shot_raw.translate(None,"storebooelan").translate(None,"RAW").translate(None,"\t")
else:
	verbose = True
	type_work = shot_raw.translate(None,"storebooelan").translate(None,"\t")




###############################	
#Folder structure:
###############################
#Star with the shot main folder check:
if os.path.isdir("./"+str(shot_name[0])+"-elec"):
	print("Shot folder already created. Changing the name to {!s}-elec-01".format(shot_name[0]))
	shot_name[0] = shot_name[0]+"elec_01"	
	
#Making the folder structure for the shot:

actual_folder = os.getcwd()
#Strings data for making the folders:
initial_folder = os.path.join(actual_folder,str(shot_name[0])+"-elec")
raw_folder = os.path.join(initial_folder,shot_number+"_RAW")
worked_folder = os.path.join(initial_folder,shot_number+"_WORKED")

#Maiking the folders:
os.mkdir(initial_folder)
os.mkdir(raw_folder) #Raw data folder
if verbose:
	os.mkdir(worked_folder)




###############################	
#Channels info from the scopes:
###############################
	
#Scopes go by order in the SETTINGS.TXT file:
scopes_lines =[position_line for position_line,line in enumerate(ste_list) if "scop." in line]

#Finding the scope names (Modifiy that for diff. devices):
scopes_names =[]
for i in scopes_lines:
	scopes_names.append(ste_list[i].translate(None,"scop.\n").strip())

#Save in chan_list the scope, channels avaliable and devices in each channel:
chan_posi = [i for i,x in enumerate(ste_list) if "CH" in x and "ns" not in ste_list[i] ]

chan_list = []

#Make the channels list for the scopes:
#In the number of scopes, choose the channels for each scope.
for lines in range(len(scopes_lines)):
	if lines < len(scopes_lines)-1:
		channels_scope =[i for i in chan_posi if  i > scopes_lines[lines] and i < scopes_lines[lines+1]]
		#Lines with channels info are between scope number lines..
		for j in channels_scope: #Adding to the channels list the info.
			chan_list.append(scopes_names[lines])
			chan_list.append(ste_list[j])	
			chan_list.append(ste_list[j+1])
	else:
		channels_scope = [i for i in chan_posi if  i > scopes_lines[lines] ] #Lines with channels info.
		for j in channels_scope: #Adding to the channels list the info.
			chan_list.append(scopes_names[lines])
			chan_list.append(ste_list[j])	
			chan_list.append(ste_list[j+1])
		
#Dividing it in three tuples in the list:
chan_list = [chan_list[i:i+3] for i in range(0, len(chan_list), 3)]




#################################################	
#Channels data saving and taking:
#################################################
#For each channel, convert the data and store 
#for sure the original signals and perhaps the converted ones:

saved_ALL, saved_DETAIL, saved_LECROY = False, False, False

data = {} #DICTIONARY WITH DATA

for i in range(0,len(chan_list)):
	if chan_list[i][0] == "ALL":
		print "\nScope ALL"
		CH_curve, CH_error, CH_preamble = teky.takechan(chan_list[i][1][:-1],sleeptime,addr01) #Real command, man.
		if saved_ALL==False:
			print "Start reading the ALL screen. This takes a while..."
			raw_data = teky.readTekScreen(addr01,sleeptime)
			#Go to the raw shot folder:
			os.chdir(initial_folder)
			fid = open(chan_list[i][0]+'-Picture.bmp', 'wb')
			fid.write(raw_data)
			fid.close()
			print 'Done with ALL picture'
			saved_ALL = True
	elif chan_list[i][0] =="DETAIL":
		print "\nScope DETAIL"
		CH_curve, CH_error, CH_preamble = teky.takechan(chan_list[i][1][:-1],sleeptime,addr02) #Real command, man.
		if saved_DETAIL == False:
			print "Start reading the DETAIL screen. This takes a while..."
			raw_data = teky.readTekScreen(addr02, sleeptime)
			#Go to the general shot folder:
			os.chdir(initial_folder)
			fid = open(chan_list[i][0]+'-Picture.bmp', 'wb')
			fid.write(raw_data)
			fid.close()
			print 'Done with DETAIL picture'
			saved_DETAIL = True
	elif chan_list[i][0] =="LECROY":
		print "\nScope LECROY"
		CH_curve, CH_error, CH_preamble = teky.takechan(chan_list[i][1][:-1],sleeptime,addr03) #Real command, man.
		if saved_LECROY == False:
			print "Start reading the LECROY screen. This takes a while..."
			raw_data = teky.readLECScreen(addr03, sleeptime)
			#Go to the general shot folder:
			os.chdir(initial_folder)
			fid = open(chan_list[i][0]+'-Picture.bmp', 'wb')
			fid.write(raw_data)
			fid.close()
			print 'Done with LECROY picture'
			saved_LECROY = True
	filename = chan_list[i][0] + "_"+ chan_list[i][1][:-1] + ".csv"
	os.chdir(raw_folder) #Raw data folder.
	teky.chansave(filename,CH_curve)
	print("Saving raw scope file...{!s}".format(filename))
	
	if verbose:
		signal = teky.transf(CH_curve, chan_list[i][2]) #It stores the data in the third element of the list.
		
		if chan_list[i][0] == "ALL": #We will store general data from the first scope only.
			if "2Rog" in chan_list[i][2]: #Current signal
				vec = []
				data["current"] = signal[0]
				for x in range(0,len(CH_curve)):
					vec.append(float(CH_curve[x][1])*9360000000.00)
				#~ print vec
				data["der_curr"] = vec
				#~ print "type der_curr: ", type(data["der_curr"])

			elif "2Res" in chan_list[i][2]: #voltage beginning signal
				data["volt_in"] = signal[0]
			elif "3Res" in chan_list[i][2]: #voltage end signal
				data["volt_out"] = signal[0]
			elif "Phot" in chan_list[i][2]: #Photodiode
				data["Phot"] = signal[0]

		filename = chan_list[i][0]+ "_" + chan_list[i][2][1:6] + ".csv"
		os.chdir(worked_folder)
		teky.chansave(filename, signal[0]) #Because I know that then is the first list were info is.
		print("Saving parameter file...{!s}".format(filename))
		os.chdir(initial_folder) #Go to shot folder.

		



#################################################	
# Parameters working:
#################################################

if verbose:
	if type_work == "ELEC": #electrical signals treatment
		print "GENERAL ELECTRIC TREATMENT OF DATA"
		volt = []
		time = []
		current = []
		photodiode =[]
		power = []
		if data.has_key("current"):
			for i in range(0,len(data["current"])):
				time.append(float(data["current"][i][0]))
				current.append(float(data["current"][i][1]))
		if data.has_key("volt_in") and data.has_key("volt_out"):
			for i in range(0,len(data["volt_in"])):
				volt.append(float(data["volt_out"][i][1]-data["volt_in"][i][1]))
		elif data.has_key("volt_out"):
			for i in range(0,len(data["volt_out"])):
				volt.append(float(data["volt_out"][i][1]))	
		if data.has_key("Phot"):
			for i in range(0,len(data["Phot"])):
				photodiode.append(float(data["Phot"][i][1]))			
		for i in range(0,len(volt)):
			power.append(float(volt[i]*current[i])/1e3) #KiloWatts

		#Voltage, current and photodiode:
		fig_02, ax3 = plt.subplots()
		ax3.plot(time,volt,"g", time,current,"b")
		ax3.set_ylabel("Volts, Current")
		ax3.legend(["Volts(V)","Current(A)"])
		ax3.set_title(str(shot_name[0])+" light")
		ax4 = ax3.twinx()
		ax4.plot(time, photodiode,"k")
		ax4.set_ylabel("Phot. (A.U.)", color="k")
		# Make the y-axis label and tick labels match the line color.
		for tl in ax4.get_yticklabels():
			tl.set_color('k')
		ax4.legend(["Phot.(A.U.)"], loc=3)
		ax3.figure.savefig(str(shot_name[0])+"-light.png",dpi=300)

	elif type_work == "CALI":
		print "ALEX CALIBRATION TREATMENT OF DATA"
		volt = []
		V2Res = []
		time = []
		current = []
		der_curr = []
		curr_not_align = []
		if data.has_key("current"):
			for i in range(0,len(data["current"])):
				time.append(float(data["current"][i][0]))
				curr_not_align.append(float(data["current"][i][1]))
		if data.has_key("der_curr"):
			for i in range(0,len(data["der_curr"])):
				der_curr.append(float(data["der_curr"][i]))
		if data.has_key("volt_in"):
			for i in range(0,len(data["volt_in"])):
				V2Res.append(float(data["volt_in"][i][1]))
		if data.has_key("volt_in") and data.has_key("volt_out"):
			for i in range(0,len(data["volt_in"])):
				volt.append(float(data["volt_out"][i][1]-data["volt_in"][i][1]))
		elif data.has_key("volt_out"):
			for i in range(0,len(data["volt_out"])):
				volt.append(float(data["volt_out"][i][1]))	
		#Shot name for the output file
		#shot_name = str(raw_input("Disparo? "))

		#Current problem persists in the alignment. No clear reason for it.
		#curr_not_alig = inte.cumtrapz(der_curr, time, initial=0) #Not correctly aligned!!!

		#Placing current rightly:
		pol = np.polyfit(time,curr_not_align,1)
		current = curr_not_align - np.polyval(pol,time) + pol[1]

		###
		#Finding ALEX support parameters by adjusting the voltage to the ideal circuit
		###
		#We make a stack of the current and its derivative vectors to have a matrix of data to adjust
		x = np.vstack([current, der_curr]).T
		#Using just Numpy to solve the problem, not sklearn:
		#Linear adjust of Voltage to the current amd its derivative. 
		#The parameters are R and L, after simple transformations
		#np.linalg.lstsq  returns a list with:
		# parameters_results[0], sum of residues[1], rank of matrix x[2], singular values of x[4]
		#First with the data from 2Res divider, R and L are the addition of the support and earth values
		sum_par = np.linalg.lstsq(x, np.array(V2Res))[0] #Support and earth values.
		#Now with data from 3Res divider, R and L are the support values only.
		x2 = np.vstack([current, der_curr]).T
		par = np.linalg.lstsq(x2, np.array(volt), rcond=1e-2)[0] #Support values.

		###
		#Finding ALEX L and R, the other part of the circuit by
		#defining the functions to fit C+B*exp(-alpha*(x-x0))*cos(omega*(x-x0)),
		#which is the current derivative. Also possible to use this to adjust the Rogowsky.
		###
		#Initial guess for parameters:
		#Meaning of the vector, check a few lines down its transformation: 
		# guess_par[0] ---> Baseline for the current derivative.
		# guess_par[1] ---> Multiplication factor for the exponential oscillatory decay
		# guess_par[2] ---> Decay contant of exponential.
		# guess_par[3] ---> Timing of current initial respect the scope zero time.
		# guess_par[4] ---> Frequency of the oscillation.
		#REMEMBER THAT EVERYTHING HERE HAS UNITS. IN HERE SI UNITS
		guess_par_cir = [np.mean(der_curr[0:10]), abs(max(der_curr))*0.1, 1e-3/(abs(time[0]-time[1])), 1.67e-6, 1.74e6]
		#Function of derivative current (direct channel signal):
		func = lambda t,par_cir:par_cir[0] + par_cir[1]*np.exp(-par_cir[2]*(t-par_cir[3]))*np.cos(par_cir[4]*(t-par_cir[3]))
		#Function to optimize (function minus der_curr[current derivative]):
		optimize = lambda par_cir: func(time[400:],par_cir) - der_curr[400:]
		#Optimization with leastsq function:
		adj_par_cir = leastsq(optimize, guess_par_cir)[0]
		#Calculation of derivative current values from the adjustment
		adjusted =[]
		for i in time[400:]:
			adjusted.append(func(i,adj_par_cir))
		#Statistical Error(high because of a problem with the end part of the current)
		err_vec =[]
		for i in range(len(time[400:])):
			err_vec.append((der_curr[i]-adjusted[i])**2)
		error = np.sqrt(sum(err_vec)/len(time[400:]))
		#Making sense of the parameters related with R and L of the circuit:
		#Inductance of the circuit
		Cir_Inductance = 1 / ( 2.2e-6 * ( adj_par_cir[4]**2 + adj_par_cir[3]**2) ) #Henri
		#The value of ALPHA(adj_par[3]) is almost zero...
		#Resistance of the circuit
		Cir_Resistance = 2 * adj_par_cir[2] * Cir_Inductance #Ohmns

		###
		# Storing the obtained parameters in a text file
		###
		with open(str(shot_name[0])+"-cali.txt","w") as save_file:
			save_file.write("Calibration values for "+str(shot_name[0])+"(S.I. Units)\n\n")
			save_file.write("Support results:\n")
			save_file.write("R_sop\t\tL_sop:\n")
			save_file.write("{:0.3e}".format(par[0])+"\t\t"+"{:0.3e}".format(par[1])+"\n")
			save_file.write("Earth pole results:\n")
			save_file.write("R_tie\t\tL_tie:\n")
			save_file.write("{:0.3e}".format(sum_par[0]-par[0])+"\t\t"+"{:0.3e}".format(sum_par[1]-par[1])+"\n")
			save_file.write("\nCircuit Results:\n")
			save_file.write("R_cir\t\tL_cir:\n")
			save_file.write("{:0.3e}".format(Cir_Resistance)+"\t\t"+"{:0.3e}".format(Cir_Inductance)+"\n")

		###
		# Saving a graph with the adjustment
		###
		plt.plot(time,der_curr,"r",  time[400:], adjusted, "k")
		plt.legend(["Current derivative", "Adjusted"])
		plt.title("ALEX calibration with shot "+str(shot_name[0]))
		plt.ylabel("A/s")
		plt.xlabel("Seconds")
		plt.savefig(str(shot_name[0])+"-cir-adj.png", bbox_inches='tight')




	
#################################################	
#HTML construction:
#################################################	

#HTML text strings:
html_01 = """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <meta content="text/html;charset=ISO-8859-1" http-equiv="Content-Type">
"""

html_02 = "    <title>"+str(shot_name[0])+"</title>"+"""
  </head>
  <body>
"""

html_04 = "<h1>"+str(shot_name[0])+"</h1>\n"

html_05 = "<p><b>Material:</b>	"+str(shot_wire[0])+"	<b>Diameter:</b>	"+str(shot_wire[1])+"	<b>Length:</b>	"+str(shot_wire[2])+"	<b>Initial voltage:</b>	"+str(shot_voltage)+"</p>\n"

html_06 = "<p><b>Comments:</b></p>\n"

html_07 = "<p>"+str(shot_comments)+"</p>\n"

if verbose:
	if type_work =="ELEC": #electrical signals treatment
		html_08 = '<img src="./'+str(shot_name[0])+'-light.png" border="3" height="500" width="500">\n'
	elif type_work =="CALI": #ALEX calibration
		html_08 = '<img src="./'+str(shot_name[0])+'-cir-adj.png" border="3" height="500" width="500">\n'+'<p>Calibration file exists.</p>\n'
	elif type_work == "OTHER": #Other treatment of signals.
		html_08 = '<img src="./'+"WHATEVER IT COMES HERE"+'-light.png" border="3" height="500" width="500">\n'
else:
	html_08 = '<p>No signals treatment in this shot. Just raw data.</p> \n'	

if saved_ALL == True:
	html_09 = '<p>ALL scope:</p><p><img src="./'+'ALL-Picture.bmp" border="3" height="250" width="250"></p>\n'
else:
	html_09 = '<p> No image saved from ALL scope.</p> \n'

if saved_DETAIL == True:
	html_10 = '<p>DETAIL scope:</p><p><img src="./'+'DETAIL-Picture.bmp" border="3" height="250" width="250"></p>\n'
else:
	html_10 = '<p> No image saved from scope DETAIL.</p> \n' 

if saved_LECROY == True:
	html_11 = '<p>LECROY scope:</p><p><img src="./'+'LECROY-Picture.bmp" border="3" height="250" width="250"></p>\n'
else:
	html_11 = '<p> No image saved from scope LECROY.</p> \n' 


html_21 = '\n <h3>Scopes wiring.</h3>\n'

#All channles info in one list:
channels_info = [item for sublist in chan_list for item in sublist]
channels_info = " <p>".join(channels_info)
html_22 = "<p>"+str(channels_info)+"</p>\n"

html_99 = "</body> </html>"


html_total = html_01+html_02+html_04+html_05+html_06+html_07+html_08+html_09+html_10+html_11+html_21+html_22+html_99



#Writing of web page:
os.chdir(initial_folder)
with open(str(shot_name[0])+".html","w") as htfile:
	htfile.write(html_total)	
	htfile.close()
