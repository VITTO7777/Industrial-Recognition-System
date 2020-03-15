import os
video_connected = []
port_connected = []
productid = []
##########################
### Searching Function ###
##########################
#string - the output got from terminal
#target - information seaching for
#wl - word length of target information
def srch_func(string, target, wl, start, end):
    length = len(string)
    for i in range(length):
        sample = string[i:i+wl]
        if target == sample:
            return string[i+start:i+end]
        else:
            continue


#show video list
def get_video():
    get_info = os.popen("ls /dev/video*")
    video_info = get_info.read()
    tars_list = ["/dev/video0", "/dev/video2", "/dev/video4", "/dev/video6"]
    for tars in tars_list:
        video_connected.append(srch_func(video_info, tars, 11, 0, 11))
        
        

#show camera product id
def get_port():
    for video in video_connected:
        if video != None:
            get_port = os.popen("udevadm info --attribute-walk --name={} |grep KERNELS".format(video))
            usbport = get_port.read()[18:19]
            port_connected.append(usbport)
        else:
            port_connected.append(None)
            continue

        

#port <==> productid
def get_productid():
    get_info = os.popen("sudo cat /sys/kernel/debug/usb/devices | grep -E '^([TSPD]:.*|)$'")
    product_info = get_info.read()
    for tars in port_connected:
        if tars != None:
            port_num = 'Port=0{}'.format(int(tars)-1)
            productid.append(srch_func(product_info, port_num, 7, 106, 129))
        else:
            productid.append(None)
            #print(srch_func(product_info, port_num, 7, 106, 129))
#print('USB Port info'+ws_num)

if __name__ == '__main__':
    print('Connected Device:')
    get_video()
    get_port()
    get_productid()
    for vi in range(4):
        print('{}: Port{}, {}'.format(video_connected[vi], port_connected[vi], productid[vi]))


