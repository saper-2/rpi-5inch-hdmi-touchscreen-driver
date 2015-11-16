#!/usr/bin/env python3

import struct
import time
import math
import glob
import uinput
import pyudev
import os

# convert touch panel raw location point into real point using formula from tslib -> linear.c file
def display_touch_point(c, pt):
    #samp->x = pt[0] ; samp->y = pt[1];
    #xtemp = samp->x; ytemp = samp->y;
    dx = ( c[2] + c[0]*pt[0] + c[1]*pt[1] ) / c[6]; # samp->x =    ( lin->a[2] + lin->a[0]*xtemp + lin->a[1]*ytemp ) / lin->a[6];
    dy = ( c[5] + c[3]*pt[0] + c[4]*pt[1] ) / c[6]; # samp->y =    ( lin->a[5] + lin->a[3]*xtemp + lin->a[4]*ytemp ) / lin->a[6];
    #if (info->dev->res_x && lin->cal_res_x) samp->x = samp->x * info->dev->res_x / lin->cal_res_x;
    #if (info->dev->res_y && lin->cal_res_y) samp->y = samp->y * info->dev->res_y / lin->cal_res_y;
    
    return [int(dx),int(dy)]

# read calibration data from pointercal created by ts_calibrate (from tslib)
def read_pointercal_calib_file():
    # a1..a7 are touch panel calibration coefficients
    a1=1 #0
    a2=0 #1
    a3=0 #2
    a4=0 #3
    a5=1 #4
    a6=0 #5
    a7=1 #6
    # scx, scy are screen dimensions at moment of performing calibration
    scx=0
    scy=0
    # file is built from single line, values are space separated, there is 9 values
    try:
        with open(calib_file,'r') as ff:
            a1,a2,a3,a4,a5,a6,a7,scx,scy = ff.readline().split()
    except:
        print("No tslib calibration file, using defaults.")
    
    print("A1..A7: ",a1,a2,a3,a4,a5,a6,a7)
    print("Screen dims: X=",scx," Y=", scy)
    return [int(a1),int(a2),int(a3),int(a4),int(a5),int(a6),int(a7)]
    
    

# Wait and find devices
def read_and_emulate_mouse(deviceFound):
    with open(deviceFound, 'rb') as f:
        print("Read buffer")

        device = uinput.Device([
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT,
            uinput.ABS_X,
            uinput.ABS_Y,
        ])
        
        cal_data = read_pointercal_calib_file()

        clicked = False
        rightClicked = False
        (lastX, lastY) = (0, 0)
        startTime = time.time()

        while True:
            try:
                b = f.read(22)
                (tag, btnLeft, x, y) = struct.unpack_from('>c?HH', b)
                print(btnLeft, x, y)
            except:
                print('failed to read from deviceFound' + str(deviceFound))
                return
            
            time.sleep(0.01)

            if btnLeft:
                # calc real touch point
                dp = display_touch_point(cal_data, [x,y])
                # dp[0] - LCD X , dp[1] - LCD Y
                device.emit(uinput.ABS_X, dp[0], True)
                device.emit(uinput.ABS_Y, dp[1], True)

                if not clicked:
                    print("Left click")
                    device.emit(uinput.BTN_LEFT, 1)
                    clicked = True
                    startTime = time.time()
                    (lastX, lastY) = (x, y)

                duration = time.time() - startTime
                movement = math.sqrt(pow(x - lastX, 2) + pow(y - lastY, 2))

                if clicked and (not rightClicked) and (duration > 1) and (movement < 20):
                    print("Right click")
                    device.emit(uinput.BTN_RIGHT, 1)
                    device.emit(uinput.BTN_RIGHT, 0)
                    rightClicked = True
            else:
                print("Release")
                clicked = False
                rightClicked = False
                device.emit(uinput.BTN_LEFT, 0)


if __name__ == "__main__":
    os.system("modprobe uinput")
    os.system("chmod 666 /dev/hidraw*")
    os.system("chmod 666 /dev/uinput*")

    while True:
        # try:
        print("Waiting device")
        hidrawDevices = glob.glob("/dev/hidraw*")

        context = pyudev.Context()

        deviceFound = None
        for hid in hidrawDevices:
            device = pyudev.Device.from_device_file(context, hid)
            if "0EEF:0005" in device.device_path:
                deviceFound = hid

        if deviceFound:
            print("Device found", deviceFound)
            read_and_emulate_mouse(deviceFound)
            # except:
            #     print("Error:", sys.exc_info())
            #     pass
            # finally:
            #     time.sleep(1)
