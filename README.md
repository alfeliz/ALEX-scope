# ALEX-scope
Python script to extract data and transform them following intructions, plus store both raw and transformed data, from Tektronix and LeCroy scopes connected by GPIB

The script is able to create the folder for the data, and store inside the raw data and the transformation made to them. 
Obviously, the Gpib driver must be working before the script can be running.

In Linux, make the file ALEX.py executable, and in the same folder were it is placed run in the terminal:

`./ALEX.py`

Files here:
* _**ALEX.py**_,  the python script that makes all the work. Version 2.20
* _**settings.txt**_ a text file were data for the script are read. Now admits comments starting by '#'
* _**tektronik.py**_ the module where all the functions to handle the scopes and data transformation are stored/placed.

To improve on the script:
-  [ ] Save date and time in the web page shot.
-  [x] _Save the settings file for every shot._ (Not the settings file, but the info there is saved in the HTML file).
-  [x] _Save the Voltage difference and the power for every shot._
