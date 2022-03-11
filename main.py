import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time

rm = pyvisa.ResourceManager('/opt/keysight/iolibs/libktvisa32.so')

inst_list = rm.list_resources()
print('Instrument list:')
print(inst_list)
index = input('Select instrument by typing index\n')
inst = rm.open_resource(inst_list[int(index)])

print('ID of connected instrument')
print(inst.query('*IDN?'))

channel = int(input('What channel are you using? [1-4]\n'))
inst.write(':CHANnel'+str(channel)+':DISPlay ON')

# I think this gives the maximum number of data points...
inst.write(':WAVeform:POINts:MODE MAX')
# Selecting the chosen channel for data collection
inst.write(':WAVeform:SOURce CHANnel'+str(channel))

# Get waveform preamble
'''
FORMAT: int16 - 0 = BYTE, 1 = WORD, 4 = ASCII.
TYPE: int16 - 0 = NORMAL, 1 = PEAK DETECT, 2 = AVERAGE
POINTS: int32 - number of data points transferred.
COUNT: int32 - 1 and is always 1.
XINCREMENT: float64 - time difference between data points.
XORIGIN: float64 - always the first data point in memory.
XREFERENCE: int32 - specifies the data point associated with x-origin.
YINCREMENT: float32 - voltage diff between data points.
YORIGIN: float32 - value is the voltage at center screen.
YREFERENCE: int32 - specifies the data point where y-origin occurs.
'''
preamble_keys = ['format',
                 'type',
                 'points',
                 'count',
                 'xincrement',
                 'xorigin',
                 'xreference',
                 'yincrement',
                 'yorigin',
                 'yreference']

preamble_data = inst.query(':WAVeform:PREamble?').split(',')
preamble_data[-1] = preamble_data[-1][:-1]
preamble = dict(zip(preamble_keys, preamble_data))
print(preamble)

# Set output format
inst.write(":WAVeform:FORMat WORD") # 16 bit WORD format... or BYTE for 8 bit format
inst.write(":WAVeform:UNSigned 0") # Set signed integer
inst.write(":WAVeform:BYTeorder LSBFirst") # Most computers use Least Significant Bit First

# Set signal duration (maximum 500s)
duration = 10
inst.write(':TIMebase:RANGe '+str(duration))
# Start a single acquisition
inst.write(':SINGle')
time.sleep(duration+1)

# Calculate time values from preamble
times = (np.arange(0,int(preamble['points'])) - int(preamble['xreference']))*float(preamble['xincrement']) + float(preamble['xorigin'])
data = inst.query_binary_values(':WAVeform:SOURce CHANnel'+str(channel)+';DATA?', container=np.array, datatype='h', is_big_endian=False)
# h is signed WORD, H is unsigned WORD

# Transform binary IEEE 488.2 data to actual values
scaled_waveform_data = ((data - int(preamble['yreference'])) * float(preamble['yincrement'])) + float(preamble['yorigin'])

'''
IEEE 488.2 Data types
NR1: Signed integer
NR2: Float with no exponent (not used by HP)
NR3: Float always with exponent
'''

# Plot the data
plt.plot(times, scaled_waveform_data)
plt.show()
