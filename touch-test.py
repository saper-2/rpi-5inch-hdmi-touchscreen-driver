#!/usr/bin/env python3

import struct
import time
import math
import glob
import uinput
import pyudev
import os
import pygame
from pygame.locals import *
import sys
import select
from random import randint

bg_color = (0x40, 0x40, 0x40)
text_font_size = 24
text_font_name = "monospace"
frame_buffer = "/dev/fb0"
calib_file = "/etc/pointercal"

def draw_touchpoint(sf, point, pt_size, pt_color): #, msg):
	sf.fill(bg_color)
	print("Drawing calibration point at location: ",point)
	psz = int(pt_size/2)
	# calc cross location
	pygame.draw.line(sf, pt_color, (point[0]-psz, point[1]), (point[0]+psz, point[1]), 1)
	pygame.draw.line(sf, pt_color, (point[0], point[1]-psz), (point[0], point[1]+psz), 1)
	
	# draw circle if half-point-size is more than 10px
	if (psz>10):
		pygame.draw.circle(sf, pt_color, point, int(psz/2), 1)
	
	# in middle of display show message
	#f = pygame.font.SysFont("monospace", text_font_size)
	#txt = f.render(msg, 1, (0xff,0xff,0xff), None)
	#sf.blit( txt, (  (sf.get_width()/2)-(txt.get_width()/2), (sf.get_height()/2)-(txt.get_height()/2)  )  )
	
	pygame.display.update()

# convert touch panel raw location point into real point using formula from tslib -> linear.c file
def display_touch_point(c, pt):
	#samp->x = pt[0] ; samp->y = pt[1];
	#xtemp = samp->x; ytemp = samp->y;
	dx = ( c[2] + c[0]*pt[0] + c[1]*pt[1] ) / c[6]; # samp->x =	( lin->a[2] + lin->a[0]*xtemp + lin->a[1]*ytemp ) / lin->a[6];
	dy = ( c[5] + c[3]*pt[0] + c[4]*pt[1] ) / c[6]; # samp->y =	( lin->a[5] + lin->a[3]*xtemp + lin->a[4]*ytemp ) / lin->a[6];
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
	
	
	
def test_calib_screen(tp_dev):
	with open(tp_dev, 'rb') as tp_f:
		print("Reading device")
		
		os.environ["SDL_FBDEV"] = frame_buffer
		pygame.init()
		
		cal_data = read_pointercal_calib_file()
		
		ssize = (pygame.display.Info().current_w, pygame.display.Info().current_h)
		screen = pygame.display.set_mode(ssize, pygame.FULLSCREEN)
		
		print("Screen size is: ", ssize)
		
		# calc touch points
		pt = [randint(0,ssize[0]-1),randint(0,ssize[1]-1)]
		pt_color = (0x00,0x00,0xff)
		
		draw_touchpoint(screen, pt, 40, pt_color )
		# draw touch point info
		f = pygame.font.SysFont(text_font_name, text_font_size)
		txt = f.render('Random test point: {0}'.format(pt) , 1, (0xff,0xff,0xff), None)
		sy_txt = (screen.get_height()/2)-(txt.get_height()/2)
		screen.blit( txt, (  (screen.get_width()/2)-(txt.get_width()/2), sy_txt  )  )
		
		temp_p = [0,0]
		pygame.display.update()
		
		try:
			b = tp_f.read(22)
			(tag, btnLeft, x, y) = struct.unpack_from('>c?HH', b)
			print(" btn=", btnLeft, " x y=", x, y)
			temp_p[0] = x
			temp_p[1] = y
		except:
			print('failed to read from touchpanel device: ' + str(tp_dev))
			return
		
		time.sleep(0.05)
		
		#if we have touch
		if (btnLeft):
			dp = display_touch_point(cal_data, temp_p)
			off = [pt[0]-dp[0], pt[1]-dp[1]]
			# raw touch point location
			txt = f.render('Data x={0} y={1}'.format(temp_p[0], temp_p[1]) , 1, (0xff,0xff,0xff), None)
			sy_txt += txt.get_height()
			screen.blit( txt, (  (screen.get_width()/2)-(txt.get_width()/2), sy_txt )  )
			sy_txt += txt.get_height()
			# add touch location
			txt = f.render('Touch location: {0} x {1}'.format(dp[0], dp[1]) , 1, (0xff,0xff,0xff), None)
			screen.blit( txt, (  (screen.get_width()/2)-(txt.get_width()/2), sy_txt  )  )
			sy_txt += txt.get_height()
			# add lcd point location
			txt = f.render('Point location: {0} x {1}'.format(pt[0], pt[1]) , 1, (0xff,0xff,0xff), None)
			screen.blit( txt, (  (screen.get_width()/2)-(txt.get_width()/2), sy_txt  )  )
			sy_txt += txt.get_height()
			# offset info
			txt = f.render('Offset (display-touch): {0} x {1}'.format(off[0],off[1]) , 1, (0xff,0xff,0xff), None)
			screen.blit( txt, (  (screen.get_width()/2)-(txt.get_width()/2), sy_txt  )  )
			
			pygame.display.update()
			
			print("Display point: ", pt)
			print("RAW touch data: ",temp_p)
			print("Calc touch point: ",dp)
			print("Offset (display-touch): ",off)
			
		#endif
		pygame.display.update()
		print("Program will terminate in 10sec.")
		
		time.sleep(10.0)

			
if __name__ == "__main__":
	#os.system("chmod 666 /dev/hidraw*")

	#while True:
	# try:
	print("Searching for USB touchpanel controller: D-WAV Scientific Co., Ltd (USB VID=0EEF & PID=0005)")
	hidrawDevices = glob.glob("/dev/hidraw*")

	context = pyudev.Context()

	deviceFound = None
	for hid in hidrawDevices:
		device = pyudev.Device.from_device_file(context, hid)
		if "0EEF:0005" in device.device_path:
			deviceFound = hid

	if deviceFound:
		print("Device found: ", deviceFound)
		test_calib_screen(deviceFound)
		sys.exit()
		# read_and_emulate_mouse(deviceFound)
		# except:
		#	 print("Error:", sys.exc_info())
		#	 pass
		# finally:
		#	 time.sleep(1)