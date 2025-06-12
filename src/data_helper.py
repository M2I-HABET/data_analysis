'''
Data Helper Module
This module contains several helper functions
for parsing, computing and graphing data generated.
'''
import numpy as np
import math
import matplotlib.pyplot as plt
import pytest
import simplekml
# Import Mapping software
import tilemapbase
# Import FirParse that can read and parse FIT Data
from fitparse import FitFile

#=============== DEFINES ============
img_dpi = 300 # Set's our image resolution, higher is better but takes more time to generate
#G_EARTH = 9806.65 # -9.80665 m/s2
G_EARTH = 1 # -9.80665 m/s2

#============Calculators=============
# Find the Distance
def find_dist(launch_loc: list,df):
    '''Find the distance between GPS coordinates

    Parameters
    ----------
    launch_loc : Pandas DataFrame
        :lat1: Starting Latitude
        :lat2: Ending Latitude
        :lon1: Starting Longitude
        :lon1: Ending Longitude

    Returns
    -------
    distance (float) : distance between two coordinates in km

    Examples
    --------
    
    '''
     # approximate radius of earth in km
    R = 6373.0
    lat1 = math.radians(launch_loc[0])
    lon1 = math.radians(launch_loc[1])
    lat2 = math.radians(df.Lat.iloc[-1])
    lon2 = math.radians(df.Lon.iloc[-1])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def pressure_to_altitude(pressure_hPa):
    '''
    Convert pressure (in hPa) to altitude (in meters) using the barometric formula.
    
    Parameters:
    pressure_hPa (float): Pressure in hectopascals (hPa)
    
    Returns:
    float: Altitude in meters
    '''
    # Constants for the barometric formula
    sea_level_pressure = 1021  # Pressure at sea level in hPa
    temperature_lapse_rate = 0.0065  # Temperature lapse rate in K/m
    sea_level_temperature = 297  # Temperature at sea level in Kelvin
    gas_constant = 8.3144598  # Universal gas constant in J/(mol·K)
    molar_mass = 0.0289644  # Molar mass of Earth's air in kg/mol
    gravity = 9.80665  # Acceleration due to gravity in m/s^2

    # Barometric formula
    altitude = (sea_level_temperature / temperature_lapse_rate) * (
        1 - (pressure_hPa / sea_level_pressure) ** (1 / ((gravity * molar_mass) / (gas_constant * temperature_lapse_rate)))
    )
    
    return altitude

def print_minmax(device_id: str,df):
    '''Print out the min/max values from the GPS
    and other sensor data we have collected

    Parameters
    ----------
    decvice_id: Used to help ID different data sources such as HAR or BERT
    :df: Pandas Dataframe that has the data

    Returns
    -------
    nothing, data is printed out

    Examples
    --------
    
    '''
    print('The maximum temperature recorded inside {} was {:.2f} C'.format(device_id,df.Temp.max()))
    print('The minimum temperature recorded inside {} was {:.2f} C'.format(device_id,df.Temp.min()))
    print('The maximum humidity recorded inside {} was {:.2f} %'.format(device_id,df.Humidity.max()))
    print('The minimum humidity recorded inside {} was {:.2f} %'.format(device_id,df.Humidity.min()))
    print('The maximum dewpoint recorded inside {} was {:.2f} C'.format(device_id,df.Temp.max()-((100 - df.Humidity.max())/5.0)))
    print('The minimum dewpoint recorded inside {} was {:.2f} C'.format(device_id,df.Temp.min()-((100 - df.Humidity.min())/5.0)))
    print('The maximum pressure recorded inside {} was {:.2f} hPa'.format(device_id,df.Pressure.max()))
    print('The minimum pressure recorded inside {} was {:.2f} hPa'.format(device_id,df.Pressure.min()))
    print('The maximum altitude obtained is',df.Altitude.max(),'m, or',(df.Altitude.max()*3.2808),'ft')
    return 

# Process FIT Data
def process_fitdata(fn: str):
    '''Read in and process data stored in the FIT format

    Parameters
    ----------
    fn: Filename that has the .fit file

    Returns
    -------
    lat,lon,altitude,airspeed,heading,timestamp

    Examples
    --------
    
    '''
    fitfile = FitFile(fn)
    fitfile.parse()
    gps_records = list(fitfile.get_messages(name='gps_metadata'))
    gyro = list(fitfile.get_messages(name='gyroscope_data'))
    accel = list(fitfile.get_messages(name='accelerometer_data'))
    mag = list(fitfile.get_messages(name='magnetometer_data'))
    # Extract data from parsed data
    lat_semi=[]
    lon_semi=[]
    altitude=[]
    timestamp=[]
    airspeed=[]
    heading=[]
    lat = []
    lon = []
    gyro_x = []
    gyro_y = []
    gyro_z = []
    for item in gps_records:
        for field in item:
            if field.name == 'position_lat':
                lat_semi.append(field.value)
            if field.name == 'position_long':
                lon_semi.append(field.value)
            if field.name == 'enhanced_altitude':
                altitude.append(field.value)
            if field.name == 'timestamp':
                timestamp.append(field.value)
            if field.name == 'enhanced_speed':
                airspeed.append(field.value)
            if field.name == 'heading':
                heading.append(field.value)
    lat = [(180/2**31)* x for x in lat_semi]
    lon = [(180/2**31)* x for x in lon_semi]
    altitude = [3.28 * x for x in altitude]
    airspeed = [1.944 * x for x in airspeed]
    # Convert the list from strings to float values
    heading = [float(i) for i in heading]

    return(lat,lon,altitude,airspeed,heading,timestamp)

def make_kml(flight_id: str,df):
    '''Produce a KML file that can be imported in other programs
    like Google Earth or Google maps

    Parameters
    ----------
    :flight_id: Flight ID information
    :df: Pandas Dataframe that has our GPS data

    Returns
    -------
    nothing, KML file is produced

    Examples
    --------
    
    '''
    
    kml = simplekml.Kml()
    linestring = kml.newlinestring(name=flight_id)
    df.apply(lambda X: linestring.coords.addcoordinates([( X['Lon'],X['Lat'],X['Altitude'])]) ,axis=1)
    linestring.altitudemode = simplekml.AltitudeMode.relativetoground
    linestring.extrude = 1
    linestring.linestyle.color = simplekml.Color.green
    linestring.linestyle.width = 5
    linestring.polystyle.color = simplekml.Color.orange
    #Saving
    kml.save('KML/{}_flight.kml'.format(flight_id))

# ==============================================
# Process IMU Data
# ==============================================

def process_yaw(df, pitch: float, roll: float):
    '''Process the IMU data stored in HAR/BERT
    and calculate the Yaw from the data with magnetometer
    corrections

    Parameters
    ----------
    :df: Pandas Dataframe that has IMU data
    :pitch: Pitch array
    :roll: Roll array

    Returns
    -------
    Returns the Yaw data

    Examples
    --------
    
    '''

    B = 53380.4/1000 # uT
    I = 68 * 0.0174533
    corr_x,corr_y,corr_z = calculate_mag_correction(df)
    mx = df.values[:,13] - corr_x
    my = df.values[:,14] - corr_y
    mz = df.values[:,15] - corr_z
    # Tilt compensation for the magnetometer
    Xh = mx * np.cos(pitch) + mz * np.sin(pitch)
    Yh = mx * np.sin(roll) * np.sin(pitch) + my * np.cos(roll) - mz * np.sin(roll) * np.cos(pitch)
    # yaw = np.arctan2(np.cos(pitch) * mz*np.sin(roll)-my*np.cos(roll),mx + B * np.sin(I)*np.sin(roll))
    yaw = np.arctan2(-Yh, Xh)
    
    return yaw

def calculate_mag_correction(df):
    '''Calculate a correction to the data using magnetometer data

    Parameters
    ----------
    :df: Pandas Dataframe that has IMU data

    Returns
    -------
    Corrected data with Mag corrections

    Examples
    --------
    
    '''
    mx = df.values[:,13] 
    my = df.values[:,14]
    mz = df.values[:,15]
    corr_x = (mx.min() + mx.max())/2
    corr_y = (my.min() + my.max())/2
    corr_z = (mz.min() + mz.max())/2
    return corr_x,corr_y,corr_z

def integrate_gyro(g: float,ts: int):
    '''Integrate our Gyro data

    Parameters
    ----------
    :g: Gyro data
    :ts: time series

    Returns
    -------
    Integrated Gyro data

    Examples
    --------
    
    '''
    
    t0 = ts[0]
    result = np.zeros(g.shape[0])
    for i in range(1,g.shape[0]):
        dt=(ts[i]-t0)/1000.0
        result[i]=result[i-1]+g[i]*dt
        t0 = ts[i]
    return result

def process_gyro(df):
    '''Process Gyro data

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas Dataframe that has Alt,Temp and Pressure data

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    
    ts = df.values[:,0]
    gx = df.values[:,10] 
    gy = df.values[:,11] 
    gz = df.values[:,12] 
    t = np.arange(gx.shape[0])    
    gxi = integrate_gyro(gx,ts)
    gyi = integrate_gyro(gy,ts)
    gzi = integrate_gyro(gz,ts)
    return gxi,gyi,gzi

def process_pitch_roll(df):
    '''Process the IMU data to generate pitch and roll data

    Parameters
    ----------
    :df: Pandas Dataframe that has Alt,Temp and Pressure data

    Returns
    -------
    Pitch and Roll data

    Examples
    --------
    
    '''
    ax = df.values[:,7] 
    ay = df.values[:,8] 
    az = df.values[:,9] 

    #ax=np.clip(ax,-G_EARTH,G_EARTH)
    #ay=np.clip(ay,-G_EARTH,G_EARTH)
    #az=np.clip(az,-G_EARTH,G_EARTH)
    pitch = np.arctan2(ax,np.sqrt(ay**2 + az**2))
    roll = np.arctan2(-ay,az)
    #pitch = np.arcsin(-ax/-G_EARTH)
    #roll = np.arctan2(ay,az)
    return pitch, roll

#============Plot Functions==========

def plot_data(flight_id: str,device_id: str,df,sensor: str,units: str):
    '''Plot specified data

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: list containing altitude information
    :sensor: Specify the sensor data to plot
    :units: Units the data is in, for example C, or m, or hPa

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    hab_id = device_id + '-' + flight_id
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    df[sensor].plot(title='{} {} Plot'.format(hab_id,sensor),ylabel='{} in {}'.format(sensor,units),xlabel='Time in seconds')
    plt.savefig('Plots/temp_plot.pdf',bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/{}_{}_plot.png'.format(flight_id,sensor),bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig


def plot_altvs(flight_id: str, device_id: str, df, df_column1: str, df_column2: str='Altitude'):
    '''Altitude vs other data

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas Dataframe that has Alt, Temp, and Pressure data

    Returns
    -------
    returns fig, used mostly for testing
    '''
    
    hab_id = device_id + '-' + flight_id
    fig, ax = plt.subplots(figsize=(20, 10), dpi=img_dpi)  # Create figure and axis properly
    
    df.plot(ax=ax, title=f'{hab_id} {df_column1} vs {df_column2} Plot',
            xlabel=df_column1, ylabel=df_column2, x=df_column1, y=df_column2)

    plt.savefig(f'Plots/{flight_id}_{df_column1}vs{df_column2}_plot.png',
                bbox_inches='tight', dpi=img_dpi)
    return fig

def plot_data_vs(flight_id: str,device_id: str,df,sensor1: str,sensor2: str,units1: str, units2: str):
    '''Plot one data set vs another data set

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas Dataframe that has Alt,Temp and Pressure data
    :sensor1: First data column
    :sensor2: Second data column
    :unit1: Units for first data column
    :unit2: Units for second data column

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    
    hab_id = device_id + '-' + flight_id
    # Turn on subplots
    fig, ax1 = plt.subplots(figsize=(20, 10), dpi=img_dpi)
    color = 'tab:red'
    ax1.set_xlabel('time (s)')
    ax1.set_ylabel('{} {}'.format(sensor1,units1), color=color)
    ax1.plot(df[sensor1],color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'tab:blue'
    ax2.set_ylabel('{} {}'.format(sensor2,units2), color=color)  # we already handled the x-label with ax1
    ax2.plot(df[sensor2])
    ax2.tick_params(axis='y', labelcolor=color)
    # Always have a good title
    plt.title('{} Temp vs Humidity'.format(hab_id),color='c')
    # This allows us to save our pretty graph so we can frame it later
    plt.savefig('Plots/{}_{}_vs_{}_plot.png'.format(flight_id,sensor1,sensor2),bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig


def plot_map(center_map: list,degree_range: float,df,flight_id: str,device_id: str,fn: str):
    '''Plot Lat and Lon on OpenStreetMap

    Parameters
    ----------
    :center_map: array with Lat/Lon to center the map
    :degree_range: Amount of zoom on the map, higher number is more zoomed out
    :df: Pandas Dataframe that has Temp and Pressure data
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :fn: string that has the filename to use to save to, PDF and PNG is automatically added

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    
    tilemapbase.init(create=True)
    hab_id = device_id + '-' + flight_id
    color='blue'
    extent = tilemapbase.Extent.from_lonlat(center_map[1] - degree_range, center_map[1] + degree_range,center_map[0] - degree_range, center_map[0] + degree_range)
    extent = extent.to_aspect(1.0)
    # Convert to web mercator
    path = [tilemapbase.project(x,y) for x,y in zip(df.Lon, df.Lat)]
    x, y = zip(*path)
    fig, ax = plt.subplots(figsize=(20,20))
    plotter = tilemapbase.Plotter(extent, tilemapbase.tiles.build_OSM(), width=800)
    plotter.plot(ax)
    plt.ylabel('Latitude (Mercator)', color=color)
    plt.xlabel('Longitude (Mercator)', color=color)
    plt.title('{} GPS Plot on Street map with zoom {}'.format(hab_id,degree_range),color='r')
    ax.plot(x, y,"b-")
    plt.savefig('Plots/{}.pdf'.format(fn),bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/{}.png'.format(fn),bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig

def plot_map_arrows(center_map: list,degree_range: float,df,flight_id: str,device_id: str,fn: str):
    extent = tilemapbase.Extent.from_lonlat(center_map[1] - degree_range, center_map[1] + degree_range,
                  center_map[0] - degree_range, center_map[0] + degree_range)
    extent = extent.to_aspect(1.0)
    color = 'tab:blue'
    # Convert to web mercator
    path = [tilemapbase.project(x,y) for x,y in zip(df.Lon, df.Lat)]
    x, y = zip(*path)
    #Used to calculate arrows
    points = np.arange(0,len(y),20)
    x2 = np.array(x)[points]
    y2 = np.array(y)[points]
    head3 = np.array(df.Heading)[points]

    fig, ax = plt.subplots(figsize=(20,20))
    plotter = tilemapbase.Plotter(extent, tilemapbase.tiles.build_OSM(), width=800)
    plotter.plot(ax)
    plt.ylabel('Latitude (Mercator)', color=color)
    plt.xlabel('Longitude (Mercator)', color=color)
    plt.title('GPS Plot on Street map with arrows',color='r')
    ax.quiver(x2,y2,4*np.sin(np.pi*head3/180),4*np.cos(np.pi*head3/180))
    plt.savefig('Plots/{}.png'.format(fn),bbox_inches = 'tight',dpi = img_dpi)
    return fig


def plot_pos(flight_id: str,device_id: str,df):
    '''Plot Lat and Lon with no map background

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas dataframe

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    
    hab_id = device_id + '-' + flight_id
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    # Always have a good title and labels
    color = 'tab:blue'
    plt.ylabel('Latitude (DD.MM)', color=color)
    plt.xlabel('Longitude (DD.MM)', color=color)
    plt.title('{} GPS Plot'.format(hab_id),color='r')
    plt.plot(df.Lon,df.Lat)
    plt.savefig('Plots/gps_plot_nomap.pdf',bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/{}_gps_plot_nomap.png'.format(flight_id),bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig


def plot_3Dpos(flight_id: str,device_id: str,df):
    '''Plot Lat, Lon, and Alt in 3D with no map

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas dataframe

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    hab_id = device_id + '-' + flight_id
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    ax = fig.add_subplot(111,projection='3d')
    ax.plot3D(df.Lon,df.Lat,df.Altitude)
    ax.set_title(u'{} 3D plot of flight Path'.format(hab_id))
    ax.set_xlabel(u'Longitude (°E)', labelpad=10)
    ax.set_ylabel(u'Latitude (°N)', labelpad=10)
    ax.set_zlabel(u'Altitude (meters)', labelpad=20)
    ax.plot3D(df.Lon, df.Lat, df.Altitude, color = 'green', lw = 1.5)
    plt.savefig('Plots/3D_Map_View.pdf',bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/{} 3D_Map_View.png'.format(flight_id),bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig


def plot_yaw(flight_id: str,device_id: str,df):
    '''Process yaw data and plot it

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas dataframe

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    hab_id = device_id + '-' + flight_id
    pitch,roll=process_pitch_roll(df)
    yaw = process_yaw(df, pitch, roll)
    t = np.arange(df.shape[0])
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    plt.plot(t,np.rad2deg(yaw))
    plt.grid(which='Both')
    plt.title("{} Yaw rotation from magnetometer and accelerometer".format(hab_id))
    plt.xlabel('Samples')
    plt.ylabel('Degrees')
    # plt.savefig('Plots/mag_yaw.pdf',bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/mag_yaw.png',bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig

def plot_yaw_pitch_roll(flight_id: str,device_id: str,df):
    '''Process yaw, pitch and roll data and plot it

    Parameters
    ----------
    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas dataframe

    Returns
    -------
    returns fig, used mostly for testing

    Examples
    --------
    
    '''
    hab_id = device_id + '-' + flight_id
    pitch,roll=process_pitch_roll(df)
    yaw = process_yaw(df, pitch, roll)
    t = np.arange(df.shape[0])
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    plt.plot(t,np.rad2deg(yaw),color='red',label='Yaw')
    plt.plot(t,np.rad2deg(pitch),color='green',label='Pitch')
    plt.plot(t,np.rad2deg(roll),color='blue',label='Roll')
    plt.grid(which='Both')
    plt.title('{} Yaw, Pitch and Roll Graph'.format(hab_id))
    plt.xlabel('Samples')
    plt.ylabel('Degrees')
    plt.legend()
    # plt.savefig('Plots/yaw_pitch_roll.pdf',bbox_inches = "tight",dpi = img_dpi)
    plt.savefig('Plots/yaw_pitch_roll.png',bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig

def plot_gyro_vs_acc(gyro,acc):
    """
    plot_altvs - Altitude vs other data

    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas Dataframe that has Alt,Temp and Pressure data
    :return: returns fig, used mostly for testing
    """ 
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    t=np.arange(gyro.shape[0])
    plt.plot(t,gyro,t,acc)
    plt.grid(which='Both')
    plt.title('Pitch and Roll - Gyroscope vs Accelerometer')
    plt.legend(['gyroscope','accelerometer'])
    plt.xlabel('Samples')
    plt.ylabel('Rotation(degrees)')
    #plt.savefig('Plots/gyro_vs_accel.pdf',bbox_inches = 'tight',dpi = img_dpi)
    plt.savefig('Plots/gyro_vs_accel.png',bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return fig


def plot_gyro(flight_id,device_id,df):
    """
    plot_gyro - Plot Gyro data

    :flight_id: string with the ID of the HABET Flight
    :device_id: ID of the device the data is coming from
    :df: Pandas Dataframe that has Alt,Temp and Pressure data
    :return: returns fig, used mostly for testing
    """ 
    hab_id = device_id + '-' + flight_id
    gxi,gyi,gzi = process_gyro(df)
    t = np.arange(gxi.shape[0])  
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    plt.plot(t,np.rad2deg(gxi),t,np.rad2deg(gyi),t,np.rad2deg(gzi))
    plt.title('{} Angles from gyroscope'.format(hab_id))
    plt.grid(which='Both')
    plt.legend(['x','y','z'])
    plt.ylabel('Degrees')
    plt.xlabel('Time')
    #plt.savefig('Plots/gyro_plot.pdf',bbox_inches = 'tight',dpi = 300)
    plt.savefig('Plots/gyro_plot.png',bbox_inches = 'tight',dpi = img_dpi)
    plt.close()
    return gxi,gyi,gzi

def plot_mag(flight_id,device_id,df):
    hab_id = device_id + '-' + flight_id
    corr_x,corr_y,corr_z = calculate_mag_correction(df)
    mx = df.values[:,13] - corr_x
    my = df.values[:,14] - corr_y
    mz = df.values[:,15] - corr_z  

    t = np.arange(mx.shape[0])
    fig = plt.figure(figsize=(20, 10), dpi=img_dpi)
    plt.title('{} 3 axis magnetometer'.format(hab_id))
    plt.plot(t,mx,t,my,t,mz)
    plt.grid(which='Both')
    #plt.savefig('Plots/mag_graph.pdf',bbox_inches = 'tight',dpi = img_dpi)
    plt.savefig('Plots/mag_graph.png',bbox_inches = 'tight',dpi = img_dpi)
    return fig