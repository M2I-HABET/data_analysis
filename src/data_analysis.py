# Import Mapping software
import tilemapbase

# Pandas for data analysis
import pandas as pd

#Import needed libraries, mainly numpy, matplotlib and datetime
import math
from math import radians, sin, cos, acos, atan2,sqrt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
import simplekml

# ---------------------------------------
# Default Settings
# ---------------------------------------

# Launch Coordinates in Decimal Degrees
launch_loc = (41.595693, -93.554037)

filename = 'data/lx187a.csv'

# Weather information at alaunch site
weather_temp = 75
weather_wind = 12
weather_clouds = 20
weather_pressure = 29.46

# Radius of the Earth in kilometers
R = 6371.0

#set the DPI for saved graphs/plots
img_dpi = 300

#Flight ID - Example LX-158-C
flight_id = filename

#set the date and time format
date_format = '%m-%d-%Y %H:%M:%S'
launch_date = date(2025, 6, 11)
launch_time = datetime.strptime('6-11-2024 8:47:00',date_format)

har_df = pd.read_csv('data/lx187a.csv')
print(har_df.head())
har_df.columns =['Device','Time', 'Lat', 'Lon', 'Altitude', 'Heading','Speed','PDOP','Pressure','Temp','Humidity']
# Convert data
# Data is stored as integers for efficiency. This "unpacks" that to the proper values
har_df['Lon'] /= 10000000
har_df['Lat'] /= 10000000
har_df['Altitude'] /= 1000
har_df['Temp'] = har_df.Temp / 100
har_df['Humidity'] = har_df.Humidity / 1000
har_df['Pressure'] = har_df.Pressure / 100
har_df['Time'] = pd.to_datetime(launch_date.strftime('%Y-%m-%d ') + har_df['Time'],format='%Y-%m-%d %H:%M:%S')
har_df['Speed'] = har_df.Speed / 10
har_df['PDOP'] = har_df.PDOP / 10
har_df['Heading'] = har_df.Heading / 100000

# First, ensure that your 'Time' column is timezone-aware
har_df['Time'] = pd.to_datetime(har_df['Time']).dt.tz_localize('UTC')

# Now convert from UTC to Central Time
har_df['Time'] = har_df['Time'].dt.tz_convert('America/Chicago')

print(har_df.head())

print('Launch date is:',launch_time.date())
print('Launch time is:',launch_time.time())
time_sec = len(har_df)*3
flight_time = har_df
flight_time = timedelta(seconds=time_sec)
landing_time = har_df['Time'].iloc[-1].tz_convert('UTC')
launch_time = har_df['Time'].iloc[0].tz_convert('UTC')
#launch_time = pd.Timestamp('2025-06-11 13:47:00').tz_localize('UTC')
#set_time = pd.Timestamp('2025-06-11 13:47:00').tz_localize('UTC')
# Calculate the time difference
time_difference = landing_time - launch_time
print('Launch time is:',launch_time)
print('Flight time is:',time_difference)
print('Landing time is:',landing_time)

# Calculate the distance using the Haversine formula

lat1 = radians(launch_loc[0])
lon1 = radians(launch_loc[1])
lat2 = radians(har_df['Lat'].iloc[-1])
lon2 = radians(har_df['Lon'].iloc[-1])
dlon = lon2 - lon1
dlat = lat2 - lat1
a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
c = 2 * atan2(sqrt(a), sqrt(1 - a))
distance = R * c

print('Result: %.2f km' % distance)

print('The maximum temperature recorded inside the payload was',har_df.Temp.max(),'C')
print('The minimum temperature recorded inside the payload was',har_df.Temp.min(),'C')
print('The maximum humidity recorded inside the payload was',har_df.Humidity.max(),'%')
print('The minimum humidity recorded inside the payload was',har_df.Humidity.min(),'%')

print('The maximum dewpoint recorded inside the payload was {:.2f} C'.format(har_df.Temp.max()-((100 - har_df.Humidity.max())/5.0)))
print('The minimum dewpoint recorded inside the payload was {:.2f} C'.format(har_df.Temp.min()-((100 - har_df.Humidity.min())/5.0)))

print('The maximum pressure recorded inside the payload was',har_df.Pressure.max(),'hPa')
print('The minimum pressure recorded inside the payload was',har_df.Pressure.min(),'hPa')