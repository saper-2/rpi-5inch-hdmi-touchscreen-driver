RPi HDMI 5-inch LCD with resistive touchpanel
===================================
I have ordered a (let me quote title :smiley:) "5 inch LCD HDMI Touch Screen Display TFT LCD Panel Module Shield 800*480 for Banana Pi and Raspberry Pi 2 model B/B+" from Chinese seller (from aliexpress).
I didn't even bothered to ask for source code for driver, because I'm quiet sure, I wouldn't get anything from the seller anyway (by my expirence to get from seller for 3.5inch spi lcd tft driver sources)...
So I started to dig google, and I came across a https://github.com/derekhe/waveshare-7inch-touchscreen-driver , where this controller, or at least how the controller talk is explained. But there is no calibration so I ended with working touch panel only in small upper left rectangle where raw touch coordinates overlap with inside screen bounds (0,0 to 800,480).
In searching for calibration, I found tslib https://github.com/kergoth/tslib which have everything that is needed to calibrate touch panel. First, I have installed tslib from rpi repos but, this lib is soooooo old that it remembers dinosaurs :smile: . I had to build one from source. After that I struggled how to make this 5inch touch panel works under xserver... After 2 days, I got this panel working... And below you can find how I did it :smiley: :

My wiring is:
```
5V 1.2A PSU --> |> RPi2 HDMI|> --> LCD_HDMI
                |  RPi2  USB|> --> LCD_microUSB:Touch&Power
```

# 0. Setup RPi to work with this LCD (800x480)
===================================
Edit ```/boot/config.txt``` , and find line ```hdmi_force_hotplug=1```, if line is commented then uncomment it. Now uncomment (enable) and set:
* ```hdmi_group=2``` 
* ```hdmi_mode=87```

Add under hdmi_mode line:
```
hdmi_cvt 800 480 60 6 0 0 0
```
There is this option explained: https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=24679 , basically config HDMI to: 
- resolution 800x480px, 
- refresh 60Hz, 
- aspect ratio 15:9, 
- no margins, 
- no interlace, 
- normal blanking.

Now save, connect lcd if still not connected :smile: and reboot Pi

# 1. Identify touch controller usb info
This touch controller uses a GD32F103C8T6 (this is a pin-to-pin (and I think function-to-function too) clone of STM32F103C8T6, even font used for chip marking is identical :laughing: ) and XPT2046. Manufacturer (whoever is) probably took just the USB VID number from D-WAV Scientific Co., Ltd (or just typed some random number and hit a D-WAV VID) ...

First look at dmesg:
```
pi@raspiv2 ~ $ dmesg|grep 'usb\|hid'
...
[    2.055848] usb 1-1.3: new full-speed USB device number 4 using dwc_otg
[    2.159236] usb 1-1.3: New USB device found, idVendor=0eef, idProduct=0005
[    2.161604] usb 1-1.3: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[    2.163897] usb 1-1.3: Product: By ZH851
[    2.166167] usb 1-1.3: Manufacturer: RPI_TOUCH
[    2.168355] usb 1-1.3: SerialNumber: .B547034417
[    2.175660] hid-generic 0003:0EEF:0005.0001: hiddev0,hidraw0: USB HID v1.10 Device [RPI_TOUCH By ZH851] on usb-3f980000 usb-1.3/input0
...
```
So there is manufacturer: ```RPI_TOUCH``` and product named: ```By ZH851``` , this is a little different manufacturer than registered at usb.org :smirk: - and this touch panel doesn't have anything to them also... But, the most interesting is in line ```[    2.159236] usb 1-1.3: New USB device found, idVendor=0eef, idProduct=0005``` which contains usb VID (idVendor) and PID (idProduct). 
I have touch panel that identify itself as VID & PID:
```
VID=0x0eef
PID=0x0005
```

This is what lsusb says - confirms VID & PID (0eef:0005):
```
pi@raspiv2 ~ $ lsusb
Bus 001 Device 004: ID 0eef:0005 D-WAV Scientific Co., Ltd
Bus 001 Device 005: ID 24ae:1000
Bus 001 Device 003: ID 0424:ec00 Standard Microsystems Corp. SMSC9512/9514 Fast Ethernet Adapter
Bus 001 Device 002: ID 0424:9514 Standard Microsystems Corp.
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

# 2. Identify format
I have a touch controller that identify itself with ```VID=0x0eef``` . There are 2 versions: 
* one uses a 25 byte long touch data , 
* the other (in my case) use a 22 byte long touch data . 

To identify them:

First, look at the last line in dmesg, there is a line just under serial number with a this touch panel usb vid:pid ```0EEF:0005``` followed by dot and endpoint number, after that is duble dot and names of devices registered in ```/dev/``` in my case this is ```hidraw0``` . Now I check what I have in ```/dev``` from hidraw devices:

```
pi@raspiv2 ~ $ ls -la /dev|grep hid
crw-rw-rw-  1 root root    247,   0 Nov 16 00:12 hidraw0
crw-rw-rw-  1 root root    247,   1 Nov 16 00:12 hidraw1
crw-rw-rw-  1 root root    247,   2 Nov 16 00:12 hidraw2
```
I have 3 usb-hid compliant devices, one is a touch panel, two are for wireless mouse & keyboard . Which one is which, I'll just test each one of them :smile: ...

Go for first, type ```sudo xxd -c 25 /dev/hidraw0``` and I touch the panel screen with finger. If on terminal shows up some lines, then this device is my touch panel. I found my touch panel at first try :smiley: ```hidraw0``` (hit ```Ctrl+C``` to exit) :

```
pi@raspiv2 ~ $ sudo xxd -c 25 /dev/hidraw0
0000000: aa01 08b3 09a4 bb00 0000 0000 0000 0000 0000 0000 0000 aa01 08  .........................
0000019: 9c09 d4bb 0000 0000 0000 0000 0000 0000 0000 00aa 0108 9b09 d2  .........................
0000032: bb00 0000 0000 0000 0000 0000 0000 0000 aa01 08ad 0983 bb00 00  .........................
000004b: 0000 0000 0000 0000 0000 0000 00aa 0000 0000 00bb 0000 0000 00  .........................
0000064: 0000 0000 0000 0000 0000 aa01 07c5 0b54 bb00 0000 0000 0000 00  ...............T.........
000007d: 0000 0000 0000 00aa 0107 c30b 53bb 0000 0000 0000 0000 0000 00  ............S............
0000096: 0000 0000 aa01 07d1 0b43 bb00 0000 0000 0000 0000 0000 0000 00  .........C...............
00000af: 00aa 0107 ef0b 22bb 0000 0000 0000 0000 0000 0000 0000 00aa 00  ......"..................
```

How to tell, if I have 25 or 22 bytes version? 
Each report frame of touch start from 0xAA, followed by byte that tell if this is a touch or release. After this are 2 coordinates (x and Y) of touch in 16bit value (2 byte per each coordinate: 2 bytes for X and 2 bytes for Y - 4 bytes total). After that, is 0xBB and goes few 0x00's (in multi-touch panels (capacitive) in those bytes are placed up to 5 additional touch points).
In first line there is already a start of next frame (0xAA) at 23rd byte, so I change parameter ```-c``` to 22 ( 25-(23-1) = 3 too much, 25-3=22):
```
pi@raspiv2 ~ $ sudo xxd -c 22 /dev/hidraw0
0000000: aa01 0a93 07dc bb00 0000 0000 0000 0000 0000 0000 0000  ......................
0000016: aa01 0a80 07b7 bb00 0000 0000 0000 0000 0000 0000 0000  ......................
000002c: aa01 0a7d 07b3 bb00 0000 0000 0000 0000 0000 0000 0000  ...}..................
0000042: aa01 0a7b 07b8 bb00 0000 0000 0000 0000 0000 0000 0000  ...{..................
0000058: aa01 0a7c 07bb bb00 0000 0000 0000 0000 0000 0000 0000  ...|..................
000006e: aa00 0000 0000 bb00 0000 0000 0000 0000 0000 0000 0000  ......................
```
Now I have a nicely aligned each frame start at first byte (first column), and each frame fit exactly one line. So I have touch panel that report a touch with 22 bytes...

# 3. Install tslib

<b>Don't install tslib from raspberry pi repositories</b> this version is older than dinosaurs. I have to build more recent version from sources, so without grumbling:

```
pi@raspiv2 ~ $ mkdir tslib
pi@raspiv2 ~/tslib $ cd tslib
pi@raspiv2 ~/tslib $ git clone https://github.com/kergoth/tslib.git
pi@raspiv2 ~/tslib $ cd tslib
pi@raspiv2 ~/tslib/tslib $ sudo apt-get install dh-autoreconf
pi@raspiv2 ~/tslib/tslib $ ./autogen.sh
```
```autogen.sh``` can produce some warning but they are not critical so ignore them :smile:
```
pi@raspiv2 ~/tslib/tslib $ ./configure
pi@raspiv2 ~/tslib/tslib $ make
pi@raspiv2 ~/tslib/tslib $ sudo make install
```

Libraries are installed at: ```/usr/local/lib/libts-1.0.so.0.0.0```, tslib plugin drivers are installed at ```/usr/local/lib/ts```

Now add to system path tslib plugin modules, create new file by (I use ```vi```):
```
pi@raspiv2 ~/tslib/tslib $ sudo vi /etc/ld.so.conf.d/tslib.conf
```
Add in file:
```
# tslib library path
/usr/local/lib/ts
```

Save, exit editor, and run to update LD path: 
```
pi@raspiv2 ~/tslib/tslib $ sudo ldconfig
```

Now copy from ```tslib/etc`` to ```/etc``` config file:
```
pi@raspiv2 ~/tslib/tslib $ sudo cp etc/ts.conf /etc/ts.conf
```

Check ```ts.conf``` content and uncoment line ```module raw_input``` ( ```pi@raspiv2 ~/tslib/tslib $ sudo vi /etc/ts.conf``` ):

```
# Uncomment if you wish to use the linux input layer event interface
module_raw input

# Uncomment if you're using a Sharp Zaurus SL-5500/SL-5000d
# module_raw collie

# Uncomment if you're using a Sharp Zaurus SL-C700/C750/C760/C860
# module_raw corgi

# Uncomment if you're using a device with a UCB1200/1300/1400 TS interface
# module_raw ucb1x00

# Uncomment if you're using an HP iPaq h3600 or similar
# module_raw h3600

# Uncomment if you're using a Hitachi Webpad
# module_raw mk712

# Uncomment if you're using an IBM Arctic II
# module_raw arctic2

module pthres pmin=1
module variance delta=30
module dejitter delta=100
module linear
```

Now test tslib by running ts_test, specify in command line tslib constans (TSLIB_CONFIGFILE - configruation file path, and TSLIB_FBDEVICE - frame buffer device, default for HDMI this is ```/dev/fb0```):
```
pi@raspiv2 ~ $ sudo TSLIB_CONFFILE=/etc/ts.conf TSLIB_FBDEVICE=/dev/fb0 ts_test
```
Now, appear black screen with croshair in middle and 3 buttons: <b>Drag</b> , <b>Draw</b> , <b>Quit</b>
Hit ```Ctrl+C``` to terminate.

tslib now works, now I need user-space touch driver to install.

# 4. Install python user-space driver

```
pi@raspiv2 ~ $ cd tslib
pi@raspiv2 ~/tslib $ git clone 
pi@raspiv2 ~/tslib $ git clone https://github.com/saper-2/rpi-5inch-hdmi-touchscreen-driver.git
pi@raspiv2 ~/tslib $ cd rpi-5inch-hdmi-touchscreen-driver
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ chmod +x install-prepare.sh
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ ./install-prepare.sh
```

Now, I check what I have input devices before running the user-space driver. I have:
```
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ ls /dev/input/
by-id  by-path  event0  event1  mice  mouse0
```

Now, start a driver main script and see if touch panel is found:
```
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ sudo ./touch.py
Waiting device
Device found /dev/hidraw2
Read buffer
No tslib calibration file, using defaults.
A1..A7:  1 0 0 0 1 0 1
Screen dims: X= 0  Y= 0
```

When I touch screen, in terminal shows up new lines:
```
True 2275 2697
Left click
True 2283 2673
True 2293 2682
True 2308 2704
True 2308 2776
False 0 0
Release
```

Start 2nd terminal, and check what new a event type input device was created, while the driver is running in first terminal:
```
pi@raspiv2 ~ $ ls /dev/input/
by-id  by-path  event0  event1  event2  js0  mice  mouse0  mouse1
```

The new ones are: ```/dev/input/event2``` and ```/dev/input/mouse1``` . Particually, I'm most interrested in ```event2``` .

Now I can run calibration program from tslib using as device ```event2``` :
```
pi@raspiv2 ~ $ sudo TSLIB_CONFFILE=/etc/ts.conf TSLIB_CALIBFILE=/etc/pointercal TSLIB_FBDEVICE=/dev/fb0 TSLIB_TSDEVICE=/dev/input/event2 ts_calibrate
```

Now show up a calibration program, touch 5 times at requested points with stylus.

[calib-screen.png]

Program closes itself after getting 5 points. I have in console now:
```
pi@raspiv2 ~ $ sudo TSLIB_CONFFILE=/etc/ts.conf TSLIB_CALIBFILE=/etc/pointercal TSLIB_FBDEVICE=/dev/fb0 TSLIB_TSDEVICE=/dev/input/event2 ts_calibrate
xres = 800, yres = 480
Took 6 samples...
Top left : X =  378 Y =  586
Took 13 samples...
Top right : X = 3728 Y =  621
Took 11 samples...
Bot right : X = 3728 Y = 3565
Took 10 samples...
Bot left : X =  371 Y = 3561
Took 12 samples...
Center : X = 2038 Y = 2087
-28.129211 0.208733 0.000249
-26.048889 -0.000745 0.128396
Calibration constants: -1843476 13679 16 -1707140 -48 8414 65536
```

Check if ```/etc/pointercal``` file have calibration constans:
```
pi@raspiv2 ~ $ cat /etc/pointercal
13679 16 -1843476 -48 8414 -1707140 65536 800 480pi@raspiv2 ~ $
```

<u>Info:</u> Last 2 values 800 and 480 are screen size.

In first terminal hit few times in succession ```Ctrl+C``` to stop driver script.

Now run again driver script and check if calibration constans are loaded:
```
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ sudo ./touch.py
Waiting device
Device found /dev/hidraw2
Read buffer
A1..A7:  13679 16 -1843476 -48 8414 -1707140 65536
Screen dims: X= 800  Y= 480
```

Looks like the calibration values loaded by driver from file are identical to those from ts_calibrate - this is great.

I have already started Xserver with displayed desktop, so when I touch there cursor goes, and as I move my finger on screen the cursor follows :smiley:

# 5. Test calibration program
To test calibration I created a small python program: touch-test.py . Just run it with sudo and you can test how precisie is calibration. This of course depends how precise you can touch the displayed point :smile:

```
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ sudo ./touch-test.py
```

# 6. Install user-space touch driver

This is easy, stop driver if still running in terminal (hit few times in succesion ```Ctrl+C``` ).

Just run install.sh:
```
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ sudo ./install.sh
Set execution bit...
Copy user-space driver and start as service script...
Apply execution bit to driver file and service script...
Set service to start driver at boot time....
Done.
```

If there is no errors then driver is installed and should be already running :smiley:

If not running then start it with ```sudo /etc/init.d/touch.sh start```

========================================
# About

I have modiffied a https://github.com/derekhe/waveshare-7inch-touchscreen-driver to works with VID=0eef PID=0005 and 22 bytes report length touch panel. I have also added a calibration because author of oryginal driver requested $$$ for calibration. I have published this under MIT license so you can do with it anything, and I do not take any responsibilites if something goes wrong.


Tested on Raspbian: ```2015-09-24-raspbian-jessie.img``` with all updates to now (2015-11-16).


# Credits
* tslib author https://github.com/kergoth/tslib
* author of https://github.com/derekhe/waveshare-7inch-touchscreen-driver for discovering how the controller talks
