# Main Flight Code
# Set to run on boot

#! /usr/bin/env python3
import time
import serial
import os
import subprocess
from PIL import Image
from numpy import asarray
import numpy as np
import adafruit_fxos8700
import adafruit_fxas21002c
import board
import busio
import math
from picamera import PiCamera
import threading
from datetime import datetime

print("Running at Boot")
time.sleep(5)
#time.sleep(70)
print("Wakey wakey")
# pair bluetooth
subprocess.call('~/scripts/autopair', shell=True)

i2c = busio.I2C(board.SCL, board.SDA)
sensor1 = adafruit_fxos8700.FXOS8700(i2c)
sensor2 = adafruit_fxas21002c.FXAS21002C(i2c)
camera = PiCamera()

def main():
    #open serial port
    ser = serial.Serial(
        port='/dev/rfcomm0',
        baudrate = 256000,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
        )
    for i in picturenames:
        serialsendfile(ser, i, Image=True)
    # Based on IMU location, take pictures

    # Downlink Images



    # Read commands ??

def serialread(ser, data):
    while 1:
        x=ser.readline()
        print(x)
        #break at some point
        break

def serialwritefile(ser, filepath):

    #IMG NAME HERE
    f = open(filepath, 'rb')
    data = f.read()

    #Send File Size
    print("Sending Size")
    out = b''
    temp = len(data)
    for i in range(4):
        out = bytes([temp%256]) + out
        temp = math.floor(temp/256)
    ser.write(out)
    print("Size Sent")

    #Send file name
    print("Sending Name")
    #Send file name size
    out = b''
    temp = len(filepath)
    for i in range(4):
        out = bytes([temp%256]) + out
        temp = math.floor(temp/256)
    ser.write(out)
    #send file name for real
    ser.write(bytes(filepath, "utf-8"))

    #Send file
    print("Sending File")
    buffer = 2048
    while len(data) > buffer:
        ser.write(data[0:buffer])
        data = data[buffer:]
    ser.write(data)
    print("File Sent")

def serialsendfile(ser, filepath, Image=True):
    if Image:
        ser.write(b'i')
    else:
        ser.write(b't')
    serialwritefile(ser, filepath)

#preliminary function, send telemetry
# def telemetry():
# 	if yaw > 240 and yaw < 280:
# 		now = datetime.now()
#         dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
#
#         file_name = "telemetry" + "{dt}".format(dt = dt_string)
#
#         f = open(file_name, "w+")
#
#         f.write("Roll:{R}, Pitch: {P}, Yaw: {Y}, Current_Orbit: {CO}, pictures_captured: {PC}".format(R = roll, P = pitch, Y = yaw, CO = orbit_count, PC = len(empty_list)))
#         f.close()
#         print("telemetry packet created")
#
#         serialsendfile(ser, file_name, False)
# 		time_telem = time.time()

def takepic(piccounter):
    # print(variable)
    camera.capture("Picture" + str(piccounter) + ".jpg")
    # print()
    print("Took a picture!")
    serialsendfile(ser, "Picture" + str(piccounter) + ".jpg", Image=True)

def telemetry():
    #initializing variables
    count = 0
    orbit_count = 1
    previous_orbit_count = 0
    empty_list = []
    start_count = 0
    measure1 = time.time()
    measure2 = time.time()

    orbit_count = 1
    telemetrysent = False

    piccounter = 0
    measure3 = time.time()
    while True:
        accelX, accelY, accelZ = sensor1.accelerometer #m/s^2
        magX, magY, magZ = sensor1.magnetometer #gauss
        mag_offset = [44.4, 77.2, 340.85] #Insert mag_offset calibration values here
        mag_scale = [0.9961873638344227, 0.810726950354609, 1.3111111111] #Insert mag_scale calibration values

        magX = (magX - mag_offset[0]) * mag_scale[0]
        magY = (magY - mag_offset[1]) * mag_scale[1]
        magZ = (magZ - mag_offset[2]) * mag_scale[2]

        #Calculating RPY
        roll = np.arctan2((accelY),(((accelX)**2 + (accelZ)**2)**0.5))
        pitch = np.arctan2((accelX),(((accelY)**2 + (accelZ)**2)**0.5))
        mag_x = (magX * np.cos(pitch)) + (magY * np.sin(roll)) + np.sin(pitch) + (magZ*np.cos(roll)*np.sin(pitch))
        mag_y = (magY*np.cos(roll)) - (magZ*np.sin(roll))

        #Original Yaw Eq: (180/np.pi)*np.arctan2(-mag_y, mag_x)
        yaw = (180/np.pi)*np.arctan2(-mag_x, mag_y)

        #Fixing coordinate direction
        yaw = (yaw + 360) % 360
        pitch = (((180/np.pi) * pitch) + 360) % 360
        roll = (((180/np.pi) * roll) + 360) % 360

        #Account for miniscule differences
        yaw += 85

        #Bounding Yaw to 0-360 deg
        if yaw > 360:
            yaw -= 360

        if start_count == 0:
            starting_yaw = yaw
            start_count += 1

        #Setting up the orbit_counter within the overarching while true loop
        if orbit_count < 11:
            if measure2 - measure1 >= 60:   #Increment orbit_count every 60 seconds
                measure1 = measure2
                measure2 = time.time()
                orbit_count += 1
                telemetrysent = False
            else:
                measure2 = time.time()


            # def orbit_counter():
            #     threading.Timer(5.0, printit).start()
            #     print "Hello, World!"
            #
            # printit()

        if orbit_count == 9:
            uploadfile = open("uploadfile.txt", "wb")
            uploadfile .write("Pls upload!".encode())
            uploadfile .close()
            serialsendfile(ser, "uploadfile.txt", Image=False)

        if telemetrysent == False:
            if orbit_count != previous_orbit_count:
                previous_orbit_count = orbit_count
                now = datetime.now()
                dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")

                file_name = "telemetry" + "{dt}".format(dt = dt_string)

                f = open(file_name, "w+")

                f.write("Roll:{R}, Pitch: {P}, Yaw: {Y}, Current_Orbit: {CO}, pictures_captured: {PC}".format(R = roll, P = pitch, Y = yaw, CO = orbit_count, PC = len(empty_list)))
                f.close()
                print("telemetry packet created")

                serialsendfile(ser, file_name, False)

                telemetrysent = True 

        measure3 = time.time()
        leftovers = measure3 % 60
        print(leftovers)
        if (leftovers > 8 and leftovers < 10):
            takepic(piccounter)
            piccounter += 1
        elif (leftovers > 28 and leftovers < 30):
            takepic(piccounter)
            piccounter += 1
        elif (leftovers > 48 and leftovers < 50):
            takepic(piccounter)
            piccounter += 1
        '''elif (leftovers > 58 and leftovers < 60):
            takepic(piccounter)
            piccounter += 1'''

        #Delay for 1 second
        time.sleep(0.5)

    #MAKE SURE YAW VALUES ARE CORRECT
    #Capture image for poster board 1
    '''if orbit_count<=3:
        if yaw > 15 and yaw < 55:
            takepic(yaw)
        #Capture image for poster board 2
        if yaw > 160 and yaw < 200:
            takepic(yaw)
        #Capture image for poster board 3
        if yaw > 265 and yaw < 305:
            takepic(yaw)'''

ser = serial.Serial(
    port='/dev/rfcomm0',
    baudrate = 256000,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )

initfile = open("initfile.txt", "wb")
initfile.write("Pi has initialized!".encode())
initfile.close()
serialsendfile(ser, "initfile.txt", Image=False)

telemetrypackets=threading.Thread(target=telemetry())
telemtrypackets.start()