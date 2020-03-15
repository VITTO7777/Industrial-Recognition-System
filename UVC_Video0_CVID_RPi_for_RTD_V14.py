#!/usr/bin/python

#import picamera
from time import sleep
import cv2
import io
import numpy as np
import imutils

import os
import sys
import re

from datetime import datetime
from PIL import Image
from pyzbar import pyzbar

import requests
import json
######################
### Initialization ###
######################
#camera = picamera.PiCamera()
tray_ID_cache = ''

##################
### User Input ###
##################
#ID of this CVID/camera
CVID_id=0
# Motion detection sensitivity
min_area = 500
past_frame= None


capture_delays = 0.1
# Cooling time for Setting camera
cooling_delays = 0.1
# Saving path of captured ambience Raw img
tray_img_path = '/home/pi/Desktop/YANG_XG/testimages/Video0_tray_img.jpg'
# Saving path of QR captured Raw img
QR_img_path = '/home/pi/Desktop/YANG_XG/testimages/Video0_QR_img.jpg'
# Saving path of QR captured Binarized img
QR_img_BIN_path = '/home/pi/Desktop/YANG_XG/testimages/Video0_Bin.jpg'
# Saving path of stability analysis imgs
sta_anls0_path = '/home/pi/Desktop/YANG_XG/testimages/Video0_sta_anls0.jpg'
sta_anls1_path = '/home/pi/Desktop/YANG_XG/testimages/Video0_sta_anls1.jpg'
#A set of binarization thresholds
#lighter version
thre_tab=[20,30,40,60,70,80,90,100,110,120,140,160,180,200,212]
#darker version
#thre_tab=[192,168,60,40,150,160,180,207,212]
# URL of RTD-API
url = "http://st-mct-vm31/tracking/api/container/update/camera/info"
header = {}
txt_name = "temp_log.txt"

#####################################
###  Func: Camera Setting by v4l2 ###
#####################################

#                                              fps    : min=15 max=30 default=30 
#                      brightness 0x00980900 (int)    : min=-64 max=64 step=1 default=0 value=0
#                        contrast 0x00980901 (int)    : min=0 max=95 step=1 default=32 value=32
#                      saturation 0x00980902 (int)    : min=0 max=128 step=1 default=55 value=55
#  white_balance_temperature_auto 0x0098090c (bool)   : default=1 value=1
#       white_balance_temperature 0x0098091a (int)    : min=2800 max=6500 step=1 default=4600 value=2800 flags=inactive
#          backlight_compensation 0x0098091c (int)    : min=0 max=3 step=1 default=1 value=1
#                   exposure_auto 0x009a0901 (menu)   : min=0 max=3 default=3 value=3
#               exposure_absolute 0x009a0902 (int)    : min=1 max=5000 step=1 default=179 value=179 flags=inactive
#          exposure_auto_priority 0x009a0903 (bool)   : default=0 value=1
def Camera_Setting():
    #setting attributes
    fps = "15"
    brightness = "64"
    contrast = "12"
    saturation = "55"
    white_balance_temperature_auto = "1"
    white_balance_temperature = "5000"
    backlight_compensation = "3"
    exposure_auto = "3"
    exposure_absolute = "179"
    exposure_auto_priority = "0"
    #setting commands
    os.system("v4l2-ctl -d /dev/video0 --set-parm={}".format(fps))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('brightness',brightness))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('contrast',contrast))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('saturation',saturation))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('white_balance_temperature_auto',white_balance_temperature_auto))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('white_balance_temperature',white_balance_temperature))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('backlight_compensation',backlight_compensation))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('exposure_auto',exposure_auto))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('exposure_absolute',exposure_absolute))
    os.system("v4l2-ctl -d /dev/video0 --set-ctrl={}={}".format('exposure_auto_priority',exposure_auto_priority))
    print('Camera setting finished.')

    

#################################
###  Func: Upload Information ###
#################################
def RTD_API_Post(url,para,header):
    try:
        r = requests.post(url,data=para,headers=header)
        print("Status:",r.status_code)
        json_r = r.json()
        print(json_r)
    except BaseException as e:
        print("RTD-API posting fails",str(e))

#############################
#####  Func: TXT Writing ####
#############################
def Txt_Write(file_name,contents):
    while True:
        infos = str(datetime.now())+' '+contents+'\n'
        try:
            with open (file_name,'a') as f:
                #f.write(now)
                f.write(infos)
            break
        except:
            print('Writing failed. Retrying...')
            break


###############################
###### uvc_camera capture #####
###############################
def uvc_capture(filepath):
    #kindly notice command "/dev/video0" using physical address, do not use "/dev/video0" 
    commands = "fswebcam -d /dev/video0 --no-banner -r 1280x720 {}".format(filepath)
    capture = os.system(commands)
#if "--- Opening /dev/device0... stat: No such file or directory" means the device dedicated to incorrect USBports


#####################################
###  Func: Preprocess & Decode QR ###
#####################################
def decoder(threshold,file_path1,file_path2):#Input is the binarization threshold
        
    #Preprocessing
    img_tmp = Image.open(file_path1)
    img_tmp_BL = img_tmp.convert('L')#Convert to gray img

    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
            
    #Binarize the image
    img_tmp_BIN = img_tmp_BL.point(table,'1')
    img_tmp_BIN.save(file_path2)

    #Decode QR
    with open(file_path2,'rb') as image_file:
        image = Image.open(image_file)
        image.load()
        
    #this is for testing, to be removed and toggle another line        
    #codes=pyzbar.decode(Image.open(file_path_static))
    codes=pyzbar.decode(Image.open(file_path2))  
    return(codes)

###############################
###  Func: Top of Decode QR ###
###############################
def decoder_top(thre_tab,QR_img_path,QR_img_BIN_path,flag):

    global tray_ID_cache
#    sta_anls()
    #Decoding by going thru all thres
    for thres in thre_tab:
        codes=decoder(thres,QR_img_path,QR_img_BIN_path)
        if codes!=[]:
            break
            
    # Print results
    if codes==[]:
        if flag == 0:
            print('Ambient Lights too low, CVID disabled')
            now = datetime.now()
            print(str(now))
            #contents={"CameraId":str(CVID_id),"TrayId":"C0000","Existance":"0"}
            #RTD_API_Post(url,contents,header)
            
        elif flag == 1:
            print('Tray detected but no QR codes detected')
            now = datetime.now()
            print(str(now))
            contents={"CameraId":str(CVID_id),"TrayId":"D0000","Existance":"1"}
            tray_ID_cache = 'D0000'
            RTD_API_Post(url,contents,header)
            #Refresh DataLog
            Txt_Write(txt_name,'Unknown Tray~\n')

        else:
            if tray_ID_cache != '':
                print('Tray removed')
                now = datetime.now()
                print(str(now))
                contents={"CameraId":str(CVID_id),"TrayId":str(tray_ID_cache),"Existance":"0"}
                RTD_API_Post(url,contents,header)
                # Reset Tray_ID_cache
                tray_ID_cache = ''
                #Refresh DataLog
                Txt_Write(txt_name,'Tray removed~\n')

            else:
                print('No tray detected, false alarm')
                now = datetime.now()
                print(str(now))                
    else:
        #To extract data from obj codes
        tmp=codes[0].data 
        print('QR codes on Device0: %s' % tmp.decode('utf-8'))
        tray_ID_cache = tmp.decode('utf-8')
        now = datetime.now()
        print(str(now))
        contents={"CameraId":str(CVID_id),"TrayId":str(tmp.decode('utf-8')),"Existance":"1"}
        RTD_API_Post(url,contents,header)
        #Refresh DataLog
        Txt_Write(txt_name,str(tmp.decode('utf-8')))
    return tray_ID_cache

#################################
###  Func: Stability analysis ###
#################################
def sta_anls():
    while True:
        uvc_capture(sta_anls0_path)
        #convert image into a binary byte stream
        imageArr0 = CVTI2B(sta_anls0_path)
        data0 = np.frombuffer(imageArr0 , dtype=np.uint8)
        frame0 = cv2.imdecode(data0, 1)
        (h0, w0) = frame0.shape[:2]
        r0 = 500 / float(w0)
        dim0 = (500, int(h0 * r0))
        frame0 = cv2.resize(frame0, dim0, cv2.INTER_AREA) # We resize the frame
        gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY) # We apply a black & white filter
        gray0 = cv2.GaussianBlur(gray0, (21, 21), 0) # Then we blur the picture

        uvc_capture(sta_anls1_path)
        #convert image into a binary byte stream
        imageArr1 = CVTI2B(sta_anls1_path)
        data1 = np.frombuffer(imageArr1 , dtype=np.uint8)
        frame1 = cv2.imdecode(data1, 1)
        (h1, w1) = frame1.shape[:2]
        r1 = 500 / float(w1)
        dim1 = (500, int(h1 * r1))
        frame1 = cv2.resize(frame1, dim1, cv2.INTER_AREA) # We resize the frame
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY) # We apply a black & white filter
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0) # Then we blur the picture

#if necessary??
#    (h_gray0, w_gray0) = gray0.shape[:2]
#    (h_gray1, w_gray1) = gray1.shape[:2]
#    if h_gray0 != h_gray1 or w_gray0 != w_gray1: # This shouldnt occur but this is error handling
#        print('Two frames do not have the same sizes {0} {1} {2} {3}'.format(h_gray0, w_gray0, h_gray1, w_gray1))
#        return

        # compute the absolute difference between the current frame and first frame
        frame_delta = cv2.absdiff(gray0, gray1)
        # then apply a threshold to remove camera motion and other false positives (like light changes)
        thresh = cv2.threshold(frame_delta, 50, 255, cv2.THRESH_BINARY)[1]
        # dilate the thresholded image to fill in holes, then find contours on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # notice the opencv 4 returns variables in new sequence--Written by Yang Xinge 24/Feb/2020
        cnts = cnts[1] if imutils.is_cv2() else cnts[0]
        stability_flag = 1
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) > min_area:
                stability_flag = 0
        if stability_flag == 1:
            print("The frame is stable!")
            break
        else:
            print("The frame is unstable!")



###########################
###  Func: Tray sensing ###
###########################
def Tray_sense(delays,file_path):
#    camera.start_preview()
#    camera.resolution = (1280, 960)
#    camera.brightness = 70
#    camera.contrast = 50
#    camera.iso = 200
#    camera.image_effect = 'denoise'
    sleep(delays)
    uvc_capture(file_path)
#    camera.capture(file_path)
#    camera.stop_preview()
    im = cv2.imread(file_path,0)
    (mean,stddv) = cv2.meanStdDev(im)
    #low gray_value means dark environment, cannot work
    if mean < 50:
        return 0
    #gray_value in the middle means tray existing
    elif mean < 100:
        return 1
    #high gray_value means no tray
    else:
        return 2

##############################
### Func: Frame Comparison ###
##############################
def handle_new_frame(frame, past_frame, min_area,usbport_num):

    (h, w) = frame.shape[:2]
    r = 500 / float(w)
    dim = (500, int(h * r))
    frame = cv2.resize(frame, dim, cv2.INTER_AREA) # We resize the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # We apply a black & white filter
    gray = cv2.GaussianBlur(gray, (21, 21), 0) # Then we blur the picture

    # if the first frame is None, initialize it because there is no frame for comparing the current one with a previous one
    if past_frame is None:
        past_frame = gray
        return past_frame

    # check if past_frame and current have the same sizes
    (h_past_frame, w_past_frame) = past_frame.shape[:2]
    (h_current_frame, w_current_frame) = gray.shape[:2]
    if h_past_frame != h_current_frame or w_past_frame != w_current_frame: # This shouldnt occur but this is error handling
        print('Past frame and current frame do not have the same sizes {0} {1} {2} {3}'.format(h_past_frame, w_past_frame, h_current_frame, w_current_frame))
        return

    # compute the absolute difference between the current frame and first frame
    frame_delta = cv2.absdiff(past_frame, gray)
    # then apply a threshold to remove camera motion and other false positives (like light changes)
    thresh = cv2.threshold(frame_delta, 50, 255, cv2.THRESH_BINARY)[1]
    # dilate the thresholded image to fill in holes, then find contours on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # notice the opencv 4 returns variables in new sequence--Written by Yang Xinge 24/Feb/2020
    cnts = cnts[1] if imutils.is_cv2() else cnts[0]

    # loop over the contours
    for c in cnts:
        # if the contour is too small, ignore it
        if cv2.contourArea(c) < min_area:
            continue
        print("Motion detected on usbport{}!".format(usbport_num))
        now2 = datetime.now()
        print(str(now2))
        #If there is already an existance of tray,
        #Then, make an advanced response.
        if tray_ID_cache != '':
            print('Tray removed.')
            now = datetime.now()
            print(str(now))
            contents={"CameraId":str(CVID_id),"TrayId":str(tray_ID_cache),"Existance":"0"}
            RTD_API_Post(url,contents,header)
            #Refresh DataLog
            Txt_Write(txt_name,'Tray removed~\n')
            
        else:
            sta_anls()
        #Wait for motion still
        #sleep(capture_delays)
        #Judge existance of Tray
        tray_flag=Tray_sense(cooling_delays,tray_img_path)
        #QR Capture 
        uvc_capture(QR_img_path)
        #Img_Capture(camera,brightness,contrast,iso,cooling_delays,QR_img_path)       
        #Decode QR       
        decoder_top(thre_tab,QR_img_path,QR_img_BIN_path,tray_flag)           
        break

######################################
###### Convert Image to BytesArr #####
######################################
def CVTI2B(QR_img_path):
    ext = "jpg"
    im = Image.open(QR_img_path,mode = 'r')
    stream = io.BytesIO()
    imgformat = Image.registered_extensions()['.'+ext]
    im.save(stream,imgformat)
    imgByteArr = stream.getvalue()
    return imgByteArr

######################
###### Main Body #####
######################
if __name__ == '__main__':
    past_frame = None
    print("Starting motion detection")
    Camera_Setting()
    now = datetime.now()
    get_usbport_num = os.popen("udevadm info --attribute-walk --name=/dev/video0 |grep KERNELS")
    usbport_num = get_usbport_num.read()[18:19]
    print('USB Port'+usbport_num)
    print(str(now))
    try:
        while True:
            #capture an image by using os command
            #capture = os.system("fswebcam --no-banner -r 1280x720 testimages/imagetest1.jpg")
            uvc_capture(QR_img_path)
            #convert image into a binary byte stream
            imageArr = CVTI2B(QR_img_path)
            data = np.frombuffer(imageArr , dtype=np.uint8)
            frame = cv2.imdecode(data, 1)

            if frame is not None:
                past_frame = handle_new_frame(frame, past_frame, min_area, usbport_num)
            else:
                print("No more frame")
    finally:
        print("Exiting")