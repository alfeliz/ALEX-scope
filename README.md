# ALEX-scope
Python script to extract data from Tektronix scope connected by GPIB

The script is able to create the folder for the data, and store inside the raw data and the transformation made to them. 
Obviously, the Gpib driver must be working before the script can be running.

In Linux, make the file ALEX.py executable and in the same folder were it is placed run in the terminal:

`./ALEX.py`

Files here:
* _**ALEX.py**_,  the python script that makes all the work. Version 1.00
* _**settings.txt**_ a text file were data for the script are read.

To improve on the script:
-  [ ] Save date and time in the web page shot.
-  [ ] Save the settings file for every shot.
-  [x] _Save the Voltage difference and the power for every shot._
