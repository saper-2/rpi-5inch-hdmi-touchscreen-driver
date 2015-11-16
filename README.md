RPi HDMI 5-inch LCD with resistive touchpanel
===================================
I have ordered a (let me quote title :D) "5 inch LCD HDMI Touch Screen Display TFT LCD Panel Module Shield 800*480 for Banana Pi and Raspberry Pi 2 model B/B+" from chinese seller from aliexpress.
I didn't event bothered to ask for source code for driver, because I'm quiet sure, I wouldn't get anything from the seller anyway (by my expirence to get from seller for 3.5inch spi lcd tft driver sources)...
So I started to digg google, and I cam across a repo https://github.com/derekhe/waveshare-7inch-touchscreen-driver , where this controller is descripped rather well. But there is no calibration so I ended with working touch panel only in small upper ledft rectangle where raw touch coordinates overlapp with inside screen bounds (0,0 to 800,480).
In searching for calibration, I found tslib https://github.com/kergoth/tslib which have everything that is needed to calibrate touch panel. First I installed tslib from rpi repos but, this lib is soooooo old that it remembers dinosuars :smile: . I had to build one from source. After that I struggled how to make this 5inch touch panel works under xserver, but I got this panel working after doing some changes inside touch.py and using calibration data from tslib :smile:

My wiring is:
```
5V 1.2A PSU --> |> RPi2 HDMI|> --> LCD_HDMI
                |  RPi2  USB|> --> LCD_microUSB:Touch&Power
```

# 0. Setup RPi to work with this LCD (800x480)
Edit ```/boot/config.txt``` , and find line ```hdmi_force_hotplug=1```, if you have it commented then uncomment it. Now uncomment (enable) and set:
* ```hdmi_group=2``` 
* ```hdmi_mode=87```

Add under hdmi_mode line:
```
hdmi_cvt 800 480 60 6 0 0 0
```
There you have explained this line: https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=24679 , basically config HDMI to: resolution 800x480px, refresh 60Hz, aspect ratio 15:9, no margins, no interlace, normal blanking.

Now save, connect lcd if still not connected :smile: and reboot Pi

# 1. Identify touch controller usb info
This touchcontroller using a GD32F103C8T6 (this is a pin-to-pin (and I think function-to-functiuon too) clone of STM32F103C8T6, even font used for chip marking is identical :lol: ) and XPT2046. Manufacturer (whoever is) probably took just the USB VID number from D-WAV Scientific Co., Ltd...

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
So we have manufacturer: ```RPI_TOUCH``` and product named: ```By ZH851``` , this is a little different manufacturer than registered at usb.org - and this touch panel doesn't have anything to them... But we are more interested in line ```[    2.159236] usb 1-1.3: New USB device found, idVendor=0eef, idProduct=0005``` which contains usb VID (idVendor) and PID (idProduct). I have touch panel that identify itself as VID & PID:
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

If you can't identify you touch panel unplug everything else form usb and anything other than (VID:PID) ```1d6b:0002```, ```0424:9514``` and ```0424:ec00 ``` must be your touch panel controller.


# 2. Identify format
I assume that you have a touch controller that identify itself with ```VID=0x0eef``` , I know about 2 versions, one uses a 25 byte long touch data , while the other (my case) use a 22 byte long touch data . I will show how to identify them now:

First, look at the last line in dmesg, there is a line just under serial number with a this touch panel usb vid:pid ```0EEF:0005``` followed by dot and endpoint number (not need to know, but if you insist then google it), after that is duble dot and names of devices registered in ```/dev/``` in my case this is ```hidraw0``` . Check if you have in ```/dev/``` hidrawX (X - any number from 0 to x :smile: ):

```
pi@raspiv2 ~ $ ls -la /dev|grep hid
crw-rw-rw-  1 root root    247,   0 Nov 16 00:12 hidraw0
crw-rw-rw-  1 root root    247,   1 Nov 16 00:12 hidraw1
crw-rw-rw-  1 root root    247,   2 Nov 16 00:12 hidraw2
```
I have 3 usb-hid compiliant devices, one is a touch panel, two are for wireless mouse & keyboard . Which one is which, just test it :smile: (replace X with numbers that you have :) )

So go for first, type ```sudo xxd -c 25 /dev/hidraw0``` and touch the panel screen with your finger if some line appear then this device is your touch panel, in my case this is a device ```hidraw0``` (Use Ctrl+C to exit) :

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

So how to tell if I have 25 or 22 bytes, each report frame of touch start from 0xAA, followed by byte that tell if this is a touch or release, after this are 2 coordinates (x and Y) of touch in 16bit value (2 byte per each coordinate: 2 bytes for X and 2 bytes for Y - 4 bytes total). After that there is 0xBB and goes few 0x00's (in multitouch panels (capacitive ones) in those bytes are placed up to 5 additional touch points).
As you can see, in first line there is already a start of next frame (0xAA) at 23rd byte so I change parameter ```-c``` to 22 ( 25-(23-1) = 3 too much, 25-3=22):
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
_Don't install tslib from raspberry pi repositories_ this version is older than dinosaurs. You have to build one yourself. 
Without rambling:
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

Libraries are installed at: ```/usr/local/lib/libts-1.0.so.0.0.0```, tslib drivers are installed at ```/usr/local/lib/ts```

Now add to system path tslib modules, create new file by (I use ```vi```, you can use ```nano```):
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
Now should appear black screen with croshair in middle and 3 buttons: *Drag* , *Draw* , *Quit*
Hit ```Ctrl+C``` to terminate.

tslib now works, now we need user-space touch driver to install.

# 4. Install python user-space driver

```
pi@raspiv2 ~ $ cd tslib
pi@raspiv2 ~/tslib $ git clone 
pi@raspiv2 ~/tslib $ git clone https://github.com/saper-2/rpi-5inch-hdmi-touchscreen-driver.git
pi@raspiv2 ~/tslib $ cd rpi-5inch-hdmi-touchscreen-driver
pi@raspiv2 ~/tslib/rpi-5inch-hdmi-touchscreen-driver $ chmod +x install-prepare.sh

```

















Now 

# Install (Thanks Kaz Fukuoka to fix this guide)
ssh into your raspiberry

```
git clone https://github.com/derekhe/waveshare-7inch-touchscreen-driver
cd wavesahre-7inch-touchscreen-driver
chmod +x install.sh
sudo apt-get update
sudo ./install.sh
sudo restart
```

# How do I hack it
By looking at the dmesg information, we can see it is installed as a hid-generic driver, the vendor is 0x0eef(eGalaxy) and product is 0x0005.
0x0005 can't be found anywhere, I think the company wrote their own driver to support this.

## dmesg infomation
```
[    3.518144] usb 1-1.5: new full-speed USB device number 4 using dwc_otg
[    3.606036] udevd[174]: starting version 175
[    3.631476] usb 1-1.5: New USB device found, idVendor=0eef, idProduct=0005
[    3.641195] usb 1-1.5: New USB device strings: Mfr=1, Product=2, SerialNumber=3
[    3.653540] usb 1-1.5: Product: By ZH851
[    3.659956] usb 1-1.5: Manufacturer: RPI_TOUCH
[    3.659967] usb 1-1.5: SerialNumber: \xffffffc2\xffffff84\xffffff84\xffffffc2\xffffffa0\xffffffa0B54711U335
[    3.678577] hid-generic 0003:0EEF:0005.0001: hiddev0,hidraw0: USB HID v1.10 Device [RPI_TOUCH By ZH851] on usb-bcm2708_usb-1.5/input0
```
kernel config provide us more clue:
```
CONFIG_USB_EGALAX_YZH=y
```

It is really a eGalaxy based device. Google this config but found nothing. I don't have a eGalxy to compare, maybe waveshare's touchscreen is only modifed the product id.

Then I look at the response of hidraw driver:

## hidraw driver analysis
```
pi@raspberrypi ~/python $ sudo xxd -c 25 /dev/hidraw0
0000000: aa00 0000 0000 bb00 0000 0000 0000 0000 0000 0000 0000 0000 00  .........................
0000019: aa01 00c5 0134 bb01 0000 0000 0000 0000 0000 0000 0000 0000 cc  .....4...................
```

You can try by your self, by moving the figure on the screen you will notice the value changes.
Take one for example:
```
0000271: aa01 00e4 0139 bb01 01e0 0320 01e0 0320 01e0 0320 01e0 0320 cc  .....9..... ... ... ... .
```

"aa" is start of the command, "01" means clicked while "00" means unclicked. "00e4" and "0139" is the X,Y position (HEX).
"bb" is start of multi-touch, and the following bytes are the position of each point.

## Write the driver
I use python to read from hidraw driver and then use uinput to emulate the mouse. It is quite easy to do. Please look at the source code.

## Other systems
I think this driver can work in any linux system with hidraw and uinput driver support.

## Other displays
I received an email from Adam, this driver may work with another type of screen:

> Hi there. Wanted to say thank you for writing and sharing the user space driver for 7" USB touchscreen, you have saved me!

> Mine is branded Eleduino (see here for details: http://www.eleduino.com/5-Inch-HDMI-Input-Touch-Screen-for-Raspberry-PI-2-B-B-and-Banana-pro-pi-p10440.html) and I had exactly the same issue - closed source binary driver which simply replaced kernel modules.

> Your solution worked out of the box, and didn't even need calibration.

> You're a hero!

# Pro version features (in progress)
Please try this driver and if you need to support more, please [contact me](derekhe@april1985.com) to get the paid pro version.

1 More options:
  -  Set right click duration

2 Calibration:
  - On screen calibration
  - Scalable external screen calibration. So you can use touchscreen as a external touch panel

3 Multitouch:
  - Two fingures touch to simulate right click
  - Three fingures to scrool
