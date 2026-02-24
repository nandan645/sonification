import random
import math
from GML import *
from GML_analysis import *
import numpy as np
import cv2
import logging
import sys
import time
from kivy.core.image import Image
from kivy.core.window import Window

"""
Class used for creating GML trees from still images and from video frames
"""
class GML_tree_builder():
    rootNode=None
    circles=None
    features=[]
    prev_root_phase=0

    identifiers=[]
    image_scale=1.0
    photo_pos=[200,200]
    photo=None
    photo1=None
    photo2=None
    prev_image_file=None
    photo_colours=None
    photo_dims=None

    button1=None

    building_tree=False


    video_capture=None
    img_key_points=None
    update_frame_count=0

    texture1=None

    ppm_mode=0 #7
    ppm_modes=["All","Primes","Helm7","Fractions","Golden Mean",
    "Fibonacci","Pythagorean5","Pythagorean6", "Vedic", "Raga",
    "Dorian","Constants"]

    #Video camera capture parameters
    video_x_res=640
    video_y_res=480
    image_scale_video=1.0
    preferred_camera_resolutions=[(7680, 4320),(3840, 2160),(2560, 1440),(1920, 1080),(1600, 1200),(1280, 1024),(1280, 960),(1280, 720),(1024, 768),(800, 600),(640, 480),]
    camera_device_number=0
    video_on=False
    mirror_mode=False
    video_frame_counter=0
    frame_update_rate=1
    video_underlay_update_rate=0 #increase for slower update rate of image under GML
    show_opencv_Window=False


    feature_filter_rate=4
    minimum_probability_use=0.015
    minimum_probability_track=0.5
    feature_tracking_dist=50

    #Video analysis parameters
    total_feature_allowance=64 #60 #Total number of features to detect and use
    orb_feature_count=int(total_feature_allowance/4)
    sift_feature_count=int(total_feature_allowance/4)
    fast_feature_count=int(total_feature_allowance/4)
    good_feature_count=int(total_feature_allowance/4)
    #orb_flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS
    orb_flags=cv2.DRAW_MATCHES_FLAGS_DEFAULT
    feature_size=8

    #filter2d=np.zeros((160,120))

    display_ratio_lists=True #Disabled in video mode
    debug=False
    tracking_debug=False
    print_feature_tracking_list=False
    show_opencv_with_circles=False
    tracking_result_debug=False #Shows tracking results
    random_test=True
    run_test_cases=False

    circle_size=10
    circle_rad=100

    sonic_phase_advance=0.5 #Passed to sonification
    tempo=20

    #circle_lock=None

    saved_photo=False


    def __init__(self, video_on, button1):
        super(GML_tree_builder, self).__init__()

        self.video_on = video_on
        self.button1 = button1

        if self.video_on == True:
            logging.info("[Tree Builder] Enabling camera capture")

            self.video_capture = cv2.VideoCapture(self.camera_device_number)

            if not self.video_capture.isOpened():
                logging.error("[Tree Builder] Camera failed to open")
            else:
                logging.info("[Tree Builder] Camera opened successfully")

            # Force MJPEG (required for many HKVISION cameras)
            self.video_capture.set(
                cv2.CAP_PROP_FOURCC,
                cv2.VideoWriter_fourcc(*'MJPG')
            )

            # Set max supported resolution AFTER opening
            self._set_max_camera_resolution()

            # Ensure proper color conversion
            self.video_capture.set(cv2.CAP_PROP_CONVERT_RGB, 1)

            self.display_ratio_lists = False

    def _set_max_camera_resolution(self):
        if self.video_capture is None or not self.video_capture.isOpened():
            return

        best_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH) or self.video_x_res)
        best_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.video_y_res)

        for target_width, target_height in self.preferred_camera_resolutions:
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)

            actual_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            actual_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

            if actual_width >= target_width and actual_height >= target_height:
                best_width = actual_width
                best_height = actual_height
                break

            if (actual_width * actual_height) > (best_width * best_height):
                best_width = actual_width
                best_height = actual_height

        self.video_x_res = best_width
        self.video_y_res = best_height
        logging.info(f"[Tree Builder] Camera resolution selected: {self.video_x_res}x{self.video_y_res}")
    def __del__(self):
        # body of destructor
        if(self.video_on==True):
            logging.info("[Tree Builder] Releasing camera capture")
            cv2.destroyAllWindows()
            self.video_capture.release()


    def setButton(self,button1):
        self.button1=button1

    def set_circle_detect_dimensions(self,circle_size,circle_rad):
        self.circle_size=circle_size
        self.circle_rad=circle_rad

    def frame_ready(self):
        if(self.video_on==True):
            if(self.video_frame_counter%self.frame_update_rate==0):
                return True
            else:
                return False
        else:
            return False



    """
    Increment and cycle throughthe PPM method selected
    """
    def increment_ppm_mode(self):
        self.ppm_mode+=1
        if(self.ppm_mode>=len(self.ppm_modes)):
            self.ppm_mode=0

    """
    Return the text name for the PPM method selected
    """
    def ppm_mode_text(self):
        return self.ppm_modes[self.ppm_mode]

    """
    Return true if the tree is currently being built
    """
    def is_building_tree(self):
        return self.building_tree

    """
    Track all features by id
    """
    def tracking_all(self,length):
        length_inc_bindu=length+1
        for id in range(0,length_inc_bindu):
            self.identifiers.append(id)

    """
    Track all features by nearest circlular path (freq)
    """
    def tracking_nearest(self,length):
        length_inc_bindu=length+1
        for id in range(0,length_inc_bindu):
            self.identifiers.append(-99)

    """
    A mixture of tracking methods
    """
    def tracking_mixed(self,length):
        length_inc_bindu=length+1
        for id in range(0,length_inc_bindu):
            if(random.random()>0.5):
                self.identifiers.append(-99) # Track nearest
            else:
                self.identifiers.append(id) # Track by id

    """
    Build a GML tree using an
    """
    def build_tree(self,limit,show_circles=False):
        self.building_tree=True
        id=0

        #Create a list of previous tree inorder to allow tracking
        #and reassignment of phase
        if(self.rootNode is None):
            initial_tracking_list=[[-1,-1,-1]]
            print("No Root Node")
        else:
            #self.circle_lock.acquire()
            initial_tracking_list=self.rootNode.read_identifiers(100)
            #self.circle_lock.release()
            if(self.print_feature_tracking_list):
                print("Pre build GML tracking list: ",initial_tracking_list)

        parent_node=None
        self.rootNode=GML_2D('GML',2,[155,170,70],0.0001, 10, parent=parent_node)
        self.rootNode.set_relay_flag(True)
        self.rootNode.set_identifier(id)
        self.rootNode.set_cursor(self.prev_root_phase)
        self.rootNode.calc_mypos()
        if (self.circles is None):
            print("No extra circles to add to GML")
            return self.rootNode

        size=10
        colour=[100,100,100]
        freq=100

        circ=0

        if(self.debug==True):
            print("PPM_mode:",self.ppm_mode)

        if(self.ppm_mode==1):
            ratios=[1,2,3,5,7,11,13,17,19,23,29,31,
            1/2,1/3,1/5,1/7,1/11,1/13,1/17,1/19,1/23,1/29,1/31,
            1/2,2/2,3/2,5/2,7/2,11/2,13/2,17/2,19/2,23/2,29/2,31/2,
            1/4,2/4,3/4,5/4,7/4,11/4,13/4,17/4,19/4,23/4,29/4,31/4,
            1/8,2/8,3/8,5/8,7/8,11/8,13/8,17/8,19/8,23/8,29/8,31/8]

        if(self.ppm_mode==2):
            # Helm7
            ratios=[16/15,15/16,5/4,4/5,3/4,4/3,3/2,2/3,8/5,5/8,15/8,8/15,2]
        elif(self.ppm_mode==3):
            ratios=[1,2/3,3/2,1/2,2/1,3/4,4/3]

        elif(self.ppm_mode==4):
            golden = (1 + 5 ** 0.5) / 2
            root2 = (2 ** 0.5)
            ratios=[1,golden, 1/golden,golden/2,golden/4,golden/8]
            ratios=[1,math.pi, 1/math.pi,math.pi/2,math.pi/4,math.pi/8]

        elif(self.ppm_mode==5):
            """Fibonacci"""
            ratios=[
            1/21/2, 2/21/2, 3/21/2, 5/21/2, 8/21/2, 13/21/2,
            21/21/2, 34/21/2, 55/21/2, 89/21/2, 144/21/2,
            1/21, 2/21, 3/21, 5/21, 8/21, 13/21,
            21/21, 34/21, 55/21, 89/21, 144/21]

        elif(self.ppm_mode==6):
            """ Pythagorean ratios across multiple octaves """
            ratios=[
            1*1,1*2/3,1*3/2,1*1/2,1*2/1,1*3/4,1*4/3,
            2*1,2*1/3,2*3/2,2*1/2,2*2/1,2*3/4,2*4/3,
            3*1,3*1/3,3*3/2,3*1/2,3*2/1,3*3/4,3*4/3,
            4*1,4*1/3,4*3/2,4*1/2,4*2/1,4*3/4,4*4/3,
            5*1,5*1/3,5*3/2,5*1/2,5*2/1,5*3/4,5*4/3,
            6*1,6*1/3,6*3/2,6*1/2,6*2/1,6*3/4,6*4/3]

        elif(self.ppm_mode==7):
            """ Pythagorean ratios across multiple octaves """
            ratios=[
            1/8,2/3/8,3/2/8,1/2/8,2/1/8,3/4/8,4/3/8,
            1/4,2/3/4,3/2/4,1/2/4,2/1/4,3/4/4,4/3/4,
            1/2,2/3/2,3/2/2,1/2/2,2/1/2,3/4/2,4/3/2,
            1*1,1*2/3,1*3/2,1*1/2,1*2/1,1*3/4,1*4/3,
            2*1,2*1/3,2*3/2,2*1/2,2*2/1,2*3/4,2*4/3,
            3*1,3*1/3,3*3/2,3*1/2,3*2/1,3*3/4,3*4/3,
            4*1,4*1/3,4*3/2,4*1/2,4*2/1,4*3/4,4*4/3,
            5*1,5*1/3,5*3/2,5*1/2,5*2/1,5*3/4,5*4/3,
            6*1,6*1/3,6*3/2,6*1/2,6*2/1,6*3/4,6*4/3,
            7*1,7*1/3,7*3/2,7*1/2,7*2/1,7*3/4,7*4/3,
            8*1,8*1/3,8*3/2,8*1/2,8*2/1,8*3/4,8*4/3
            ]

        elif(self.ppm_mode==8):
            """ Vedic """
            ratios=[
            1/8,8/15/8,4/7/8,3/5/8,5/8/8,2/3/8,5/7/8,3/4/8,4/5/8,5/6/8,8/8/8,1/2/8,
            1/4,8/15/4,4/7/4,3/5/4,5/8/4,2/3/4,5/7/4,3/4/4,4/5/4,5/6/4,8/8/4,1/2/4,
            1/2,8/15/2,4/7/2,3/5/2,5/8/2,2/3/2,5/7/2,3/4/2,4/5/2,5/6/2,8/8/2,1/2/2,
            1,8/15,4/7,3/5,5/8,2/3,5/7,3/4,4/5,5/6,8/8,1/2,
            16/15,9/8,6/5,5/4,4/3,7/5,3/2,8/5,5/3,7/4,15/8,
            135/128,25/24,21/20,15/14,
            2,2*16/15,2*9/8,2*6/5,2*5/4,2*4/3,2*7/5,2*3/2,2*8/5,2*5/3,2*7/4,2*15/8,
            2*135/128,2*25/24,2*21/20,2*15/14
            ]

        elif(self.ppm_mode==9):
            """Raga"""
            ratios=[
            2/3/8,3/2/8,4/3/8,3/4/8,5/3/8,3/5/8,5/4/8,4/5/8,9/8/8,8/9/8,15/8/8,8/15/8,
            2/3/4,3/2/4,4/3/4,3/4/4,5/3/4,3/5/4,5/4/4,4/5/4,9/8/4,8/9/4,15/8/4,8/15/4,
            2/3/2,3/2/2,4/3/2,3/4/2,5/3/2,3/5/2,5/4/2,4/5/2,9/8/2,8/9/2,15/8/2,8/15/2,
            2/3,3/2,4/3,3/4,5/3,3/5,5/4,4/5,9/8,8/9,15/8,8/15,
            2/3*2,3/2*2,4/3*2,3/4*2,5/3*2,3/5*2,5/4*2,4/5*2,9/8*2,8/9*2,15/8*2,8/15*2,
            2/3*3,3/2*3,4/3*3,3/4*3,5/3*3,3/5*3,5/4*3,4/5*3,9/8*3,8/9*3,15/8*3,8/15*3
            ]

        elif(self.ppm_mode==10):
            """ Dorian Hindu-Greek """
            ratios=[
            1,15/16,8/9,9/10,9/8,16/15,10/9,2,1/2
            ]

        elif(self.ppm_mode>=11):
            """ Constants """
            ratios=[
            0.31830988618,0.36787944117,0.5,0.61803398875,0.63661977236,0.70710678118,0.73575888234,1,1.14412280564,1.2360679775,1.41421356237,1.61803398875,1.92211551408,2,2.28824561127,2.61803398875,2.71828182846,2.82842712475,3.14159265359,3.2360679775,4.39827238945,5.43656365692,6.22009646417,6.28318530718,8.53973422267,13.8175802272
            ]

        if(self.debug==True):
            print(self.ppm_modes[self.ppm_mode])

        # max_add=0
        #Loop through all features and add the singularity points to the GML tree
        for (x, y, r, feature_colour, type_colour, prob) in self.circles:
            if(prob<self.minimum_probability_use):
                continue #Skip low probability features
            if(x<2 or y<2):
                continue
            #print(x,y)
            pos=[(x/self.image_scale)+self.photo_pos[0],(y/self.image_scale)+self.photo_pos[1]]
            [nearest_node,max_d]=self.rootNode.nearest(pos,1000000,limit)
            angle=nearest_node.angleTo(pos)
            dist=nearest_node.distanceTo(pos)
            freq=dist

            #print("Initial freq:",freq)

            """ This is frequency quantisation """
            nearest_parent=nearest_node.parent
            if(nearest_parent==None):
                nearest_parent=nearest_node
            freq_root=nearest_parent.return_orbit_radius()
            if(freq_root<1 and self.ppm_mode!=0 ):
                freq_root=1
                if(self.debug==True):
                    print("Less than 1")

            """if ppm_mode=0, use frequency as is,
            otherwaise quantise to the nearest ratio ratio"""
            if(self.ppm_mode!=0):
                request_freq=freq
                an_array = np.array(ratios)
                #print (freq_root)
                multiplied_array = an_array * freq_root
                takeClosest = lambda num,collection:min(collection,key=lambda x:abs(x-num))
                freq=takeClosest(freq,multiplied_array)
                if(self.debug==True):
                    print("Dist:",dist," Root:",freq_root," Chosen:",freq)
                if(dist>300):
                    freq=dist
                    """Skip large jumps"""

            size=3
            col=circ#/2
            if (col>255):
                col=255
            full_r=r/10

            area=None
            area_colour=None #[255,255,255,255]

            gm1=GML_2D('GML_'+str(circ),size,area_colour,freq,angle, parent=nearest_node, area=area)

            id+=1

            while(id>=len(self.identifiers)):
                if(self.debug):
                    print("ID Warning: ",id,len(self.identifiers))
                self.identifiers.append(-99)
            gm1.set_identifier(self.identifiers[id])

            #Find circles with matching identifier
            if (self.identifiers[id]!=-99):
                track_list = [index for (index, tracking_tuple) in enumerate(initial_tracking_list) if tracking_tuple[0]==self.identifiers[id]]
                if(len(track_list)>0):
                    tracking_phase=initial_tracking_list[track_list[0]][2] #Use latest phase
                    track_id=initial_tracking_list[track_list[0]][0]
                    if(self.tracking_debug==True):
                        print("found:",track_list[0]," id:",track_id," phase:",tracking_phase," prev:",gm1.cursor_phase)

                        #Track the previous phase
                    gm1.set_cursor(tracking_phase)
                    gm1.set_freq(freq)
                    gm1.set_probability(prob)
                    if(self.tracking_result_debug==True):
                        if(tracking_phase>4000):
                            print(">>> phase too large")
                        print("Found tracking id:",track_id," tracking_phase:",tracking_phase)
            else:
                #Find similar size circles
                nearest=-1
                nearest_freq=99999999
                #print("list:",initial_tracking_list," len:",len(initial_tracking_list))
                for index2 in range(0,len(initial_tracking_list)):
                    freq_dist=abs(freq-initial_tracking_list[index2][1])
                    if(freq_dist<nearest_freq):
                        nearest_freq=freq_dist
                        nearest=index2
                #print("looking for:",freq," nearest freq:",nearest_freq,nearest)
                if (nearest>0):
                    nearest_dist=abs(freq-nearest_freq)
                    if(nearest_dist<800):
                        tracking_phase=initial_tracking_list[nearest][2]
                        if(self.tracking_debug==True):
                            print("nearest freq:",freq," freq2:",initial_tracking_list[nearest][1]," index",index2," phase:",tracking_phase," prev:",gm1.cursor_phase)
                        gm1.set_cursor(tracking_phase)
                        gm1.set_freq(freq)
                        gm1.set_probability(prob/2)
                        #print("Final freq:",gm1.freq)
                        if(self.tracking_result_debug==True):
                            if(tracking_phase>4000):
                                print(">>> phase too large")
                                print("Recycling index:",nearest," tracking_phase:",tracking_phase)
                                initial_tracking_list.pop(nearest)
                    else:
                        print("Not near",nearest_dist)
                        #gm1.advance_cursor(0.5)
                        gm1.set_freq(freq)
                        gm1.set_cursor(gm1.phase) #90 deg offset to start
                        gm1.set_probability(0.2)
                        initial_tracking_list.pop(nearest)
                else:
                    tracking_phase=initial_tracking_list[nearest][2]
                    print("Not found:",tracking_phase)
                    gm1.set_freq(freq)
                    gm1.set_cursor(gm1.phase) #90 deg offset to start
                    gm1.set_probability(0.1)

            #gm1=GML_2D('GML1',size,[col,100,150],freq,angle, parent=nearest_node, area=area)
            gm1.calc_mypos() #Needed for image mode
            #gm1.set_relay_flag(True)

            if(self.photo is None):
                #print(feature_colour)
                if(feature_colour!=1.0):
                    new_area=None
                    #print("Area colour",feature_colour)
                    area_colour=feature_colour
                else:
                    new_area=None
                    area_colour=[255,255,255]
                    print("No Area colour",area_colour)
            else:
                new_area=grab_circular_photo_blit(self.photo, self.photo_colours, self.photo_dims, self.image_scale ,self.texture1,gm1.mypos[0]-self.photo_pos[0],gm1.mypos[1]-self.photo_pos[1],full_r,full_r,BLACK,5)
                area_colour=new_area[3]

            if(area_colour[0]<20 and area_colour[1]<20 and area_colour[2]<20):
                #Assume black is background and not required as a circle
                if(self.debug==True):
                    print("Removing child singularity")
                nearest_node.remove_child(gm1)

            new_area_colour=saturateColour(area_colour,1.4)
            if(new_area is not None):
                gm1.update_area(new_area) #,area_colour)
            gm1.update_colour(new_area_colour)

            circ+=1
            if(show_circles==True):
                create_circular_blit(pos, 2, 0, [200, 0, 0], [0, 0, 0],127,False,0)

            if(self.debug==True):
                print(str(circ)+" x:"+str(pos[0])+" y:"+str(pos[1])+" x2:"+str(gm1.mypos[0])+" y2:"+str(gm1.mypos[1]))
        if(self.debug==True):
            print("Circles:"+str(circ))

        if(self.display_ratio_lists):
            ratio_list(self.rootNode,100,1,True)
            adjacient_ratio_list(self.rootNode,100,True)

        if(self.print_feature_tracking_list):
            #print("Initial GML tracking list: ",initial_tracking_list)
            tracking_list=self.rootNode.read_identifiers(100)
            #print("Final GML tracking list: ",tracking_list)

        self.capture_from_camera()
        self.building_tree=False
        self.prev_root_phase=self.rootNode.cursor_phase
        if(self.show_opencv_with_circles):
            self.rootNode.opencv_plot_gml(cv2,100,self.img_key_points,self.photo_pos,False)
        return self.rootNode

    """
    Read the RGB colour of a point on the opencv image
    """
    def colour_from_cv(self,cv_image,x,y):
        return [cv_image[y,x,2],cv_image[y,x,1],cv_image[y,x,0]]

    """
    Find only circular features
    """
    def add_circlular_features(self,image,dim,size,rad):
        #self.circle_lock.acquire()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        resized = cv2.resize(gray, dim, interpolation = cv2.INTER_AREA)
        print('Circles Resized Dimensions : ',resized.shape)

        """
        Find circles within the image
        """
        while((self.circles is None) or (self.circles.size<7)):
            self.circles = cv2.HoughCircles(resized, cv2.HOUGH_GRADIENT,rad,size)
            rad-=20
            if(rad<1):
                rad=1
            if(self.circles is not None):
                print(self.circles.size)
        # ensure at least some circles were found
        if self.circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            self.circles = np.round(self.circles[0, :]).astype("int")

        #Add an extra column which is used elsewhere to record feature colour
        circle_arr_rows=self.circles.shape[0]
        self.circles=np.c_[ self.circles, np.ones(circle_arr_rows), np.ones(circle_arr_rows), np.ones(circle_arr_rows) ]
        #print ("Circles",self.circles)

        self.tracking_all(len(self.circles))

    # Capture a frame from video and apply feature detections

    def capture_from_camera(self,redraw_only=False):
        if(self.video_on==False):
            return
        if(self.run_test_cases):
            self.video_test_cases()
            return

        ret,frame = self.video_capture.read()
        # print("Video read")

        if (self.saved_photo == False):
            filename = "freq_data/frame_snapshot_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".png"
            try:
                cv2.imwrite(filename, frame)
                self.saved_photo = True
            except Exception as e:
                sys.exit('file {}, {}'.format(filename,  e))

        if (frame is None):
            print("No image captured")
            return

        if(self.mirror_mode==True):
            frame2=cv2.flip(frame, 1)
        else:
            frame2=frame

        if(redraw_only):
            img_key_points=frame
            return

        #https://docs.opencv.org/3.4/d8/d01/group__imgproc__color__conversions.html
        gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        orb = cv2.ORB_create(self.orb_feature_count,fastThreshold=0, edgeThreshold=0)
        kp_orb, des = orb.detectAndCompute(gray, None)
        sift = cv2.SIFT_create(self.sift_feature_count)
        kp_sift,des = sift.detectAndCompute(gray,None)
        fast = cv2.FastFeatureDetector_create(40)
        kp_fast = fast.detect(gray,None)

        # https://opencv24-python-tutorials.readthedocs.io/en/latest/py_tutorials/py_feature2d/py_shi_tomasi/py_shi_tomasi.html
        corners = cv2.goodFeaturesToTrack(gray,25,0.01,self.good_feature_count)
        if(corners is not None):
            corners = np.int0(corners)
        else:
            print("Corners is None")
            corners = []


        self.img_key_points=frame2

        self.features=[]
        self.identifiers=[]
        self.identifiers.append(-99) #Add identifier for root
        #self.identifiers.append(-99) #Add identifier for root

        top=self.img_key_points.shape[0]

        #Red SIFT
        for i in range(0,len(kp_sift)):
            pos=np.int0(kp_sift[i].pt)
            x,y = pos.ravel()
            feature_colour=self.colour_from_cv(frame2,x,y)
            self.features.append([x,top-y,0,tuple(feature_colour),tuple([0,0,255]),1.0])

        #Green ORB
        for i in range(0,len(kp_orb)):
            pos=np.int0(kp_orb[i].pt)
            x,y = pos.ravel()
            feature_colour=self.colour_from_cv(frame2,x,y)
            self.features.append([x,top-y,0,tuple(feature_colour),tuple([0,255,0]),1.0])

        #Yellow ORB
        fast_feature_total=0
        for i in range(0,len(kp_fast)):
            if(fast_feature_total<self.fast_feature_count):
                pos=np.int0(kp_fast[i].pt)
                x,y = pos.ravel()
                feature_colour=self.colour_from_cv(frame2,x,y)
                self.features.append([x,top-y,0,tuple(feature_colour),tuple([0,255,255]),1.0])
            fast_feature_total+=1

        #Blue goodFeaturesToTrack
        for i in corners:
            x,y = i.ravel()
            feature_colour=self.colour_from_cv(frame2,x,y)
            self.features.append([x,top-y,0,tuple(feature_colour),tuple([255,0,0]),1.0])

        #self.circle_lock.acquire()
        #Ensure features and circles are same size
        if(self.circles is None):
            self.circles=[]
        while(len(self.circles)<len(self.features)):
            self.circles.append([1,1,-1,tuple([0,0,0]),tuple([0,0,0]),0.0])


        #prev_circles=self.circles


        last_index=len(self.features)-1
        for i in range(len(self.features)):

            #Find nearest previous
            min_index=0
            min=99999
            for k in range(len(self.circles)):
                if(self.circles[k][2]!=-1):
                    dist=math.sqrt((self.features[i][0]-self.circles[k][0])**2 + (self.features[i][1]-self.circles[k][1])**2)
                    if(dist<min):
                        min=dist
                        min_index=k
            #print (dist)
            if(min<self.feature_tracking_dist):
                j=min_index
                filter_rate=self.feature_filter_rate
                self.features[i][2]=1
                self.circles[j][5]=(self.circles[i][5]+3)/2 # Increase probability
            else:

                #find lowest probability
                min_index2=0
                min_prob=10
                for k2 in range(len(self.circles)):
                    if(self.circles[k2][5]<min_prob):
                        min_prob=self.circles[k2][5]
                        min_index2=k2
                j=min_index2
                #print("Min:",j)
                self.circles[k2][5]=1
                filter_rate=0
                self.circles[i][2]=-2 #Signify not tracked

            x=self.features[i][0]
            y=self.features[i][1]
            #self.filter2d[int(x/4)][int(y/4)]+=1
            if(self.circles[j][2]==-1):
                self.circles[j][0]=x
                self.circles[j][1]=y
            else:
                self.circles[j][0]=(filter_rate*self.circles[j][0]+x)/(filter_rate+1)
                self.circles[j][1]=(filter_rate*self.circles[j][1]+y)/(filter_rate+1)
            self.circles[j][2]=self.features[i][2]
            self.circles[j][3]=self.features[i][3]
            self.circles[j][4]=self.features[i][4]

        #ranks=rankdata(self.filter2d).reshape(self.filter2d.shape)

        id_count=0
        for (x, y, r, feature_colour,type_colour,prob) in self.circles:
            #print("x",x,"y",y,feature_colour,type_colour)
            x1=int(x)
            y1=int(top-y)
            f_colour=tuple([int(feature_colour[2]),int(feature_colour[1]),int(feature_colour[0])])
            if(prob>self.minimum_probability_use):
                cv2.circle(self.img_key_points,(x1,y1),self.feature_size,type_colour,-1)
                cv2.circle(self.img_key_points,(x1,y1),5,f_colour,-1)
            if(prob>self.minimum_probability_track):
                if(r==-2):
                    self.identifiers.append(-99) #Not tracked
                else:
                    self.identifiers.append(id_count+100) #Tracked
            else:
                self.identifiers.append(-99) #Low probability not tracked
                #print("tracking",id_count)
            #self.identifiers.append(id_count+100)
            self.circles[id_count][5]=self.circles[id_count][5]/2 #Reduce probability of all
            id_count+=1

        if(self.show_opencv_Window):
            try:
                cv2.imshow('frame',self.img_key_points)
                #cv2.waitKey(1)
            except:
                print("cv2 exception")


    # Load a video capture and draw to the kivy screen
    def _video_fit_scale(self, frame_width, frame_height):
        available_width = max(1, Window.width - self.photo_pos[0] - 10)
        available_height = max(1, Window.height - self.photo_pos[1] - 10)

        scale_x = frame_width / available_width
        scale_y = frame_height / available_height
        fit_scale = max(scale_x, scale_y)

        if fit_scale <= 0:
            fit_scale = 1.0

        # Keep user scale if it already makes image smaller than fit target.
        return max(self.image_scale_video, fit_scale)

    def draw_video(self):
        if(self.img_key_points is None):
            print("No key points")
            return
        #print("draw_video")
        self.image_scale=self._video_fit_scale(self.img_key_points.shape[1], self.img_key_points.shape[0])

        self.update_frame_count+=1
        if(self.update_frame_count>self.video_underlay_update_rate):
            #print("Update frame")
            self.video_frame_counter+=1
            self.update_frame_count=0
            # convert image to texture
            buf1 = cv2.flip(self.img_key_points, 0)
            buf = buf1.tostring()
            self.texture1 = Texture.create(size=(self.img_key_points.shape[1], self.img_key_points.shape[0]), colorfmt='bgr')
            self.texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            #print(self.img_key_points.shape)
            self.photo_dims=[self.img_key_points.shape[1],self.img_key_points.shape[0]]
            output = self.img_key_points.copy()

        #Following creates the base layer for the GML overlay
        self.photo_dims=[self.img_key_points.shape[1],self.img_key_points.shape[0]]
        with self.button1.canvas:
            Color(1, 1, 1)
            Rectangle(pos=self.photo_pos,size=[self.photo_dims[0]/self.image_scale, self.photo_dims[1]/self.image_scale], texture=self.texture1)

    # Load an image and draw to the kivy screen
    def draw_photo(self,image_file):
        if(self.button1 is None):
            print("No button1")
            return
        if(self.video_on==True):
            #print("Call draw video")
            self.draw_video()
            return
        if(image_file!=self.prev_image_file):
             self.photo = Image.load(filename=image_file,keep_data=True)
             #color = self.photo.read_pixel(150, 150)
             #self.photo.reload()
             self.prev_image_file=image_file
             rect = self.photo.texture.size
             self.photo_dims=[self.photo.texture.size[0],self.photo.texture.size[1]]
             if(self.photo_colours is None):
                 self.photo_colours=get_pixel_colors(self.photo.texture,rect)
                 print("Read photo colours")
        rect = self.photo.texture.size
        #scale= rect[0]/(screen_width-40)
        self.image_scale=3
        with self.button1.canvas:
            #screen.blit(pygame.transform.scale(self.photo, (rect[0]/scale, rect[1]/scale)), (200, 200))
            Color(1, 1, 1)
            #Rectangle(size=Window.size, texture=self.photo.texture)
            #Rectangle(pos=[10,10],size=[100,100], texture=self.photo.texture)
            Rectangle(pos=self.photo_pos,size=[self.photo_dims[0]/self.image_scale, self.photo_dims[1]/self.image_scale], texture=self.photo.texture)
        with self.button1.canvas:
            self.photo1 = Fbo(size=(self.photo_dims[0]/self.image_scale,self.photo_dims[1]/self.image_scale))
            with self.photo1:
                Color(1, 1, 1)
                Rectangle(pos=(0,0),size=[self.photo_dims[0]/self.image_scale, self.photo_dims[1]/self.image_scale], texture=self.photo.texture)
        self.texture1=self.photo1.texture



    def video_test_cases(self):
        if(self.random_test):
            rand_scale=0.1
            rand1=randint(int(-10*rand_scale),int(10*rand_scale))
            rand2=randint(int(-10*rand_scale),int(10*rand_scale))
            rand3=randint(int(-10*rand_scale),int(10*rand_scale))
            rand4=randint(int(-5*rand_scale),int(5*rand_scale))
            rand5=randint(int(-50*rand_scale),int(50*rand_scale))
        else:
            rand1=rand2=rand3=rand4=rand5=0
        centre_x=320
        centre_y=240
        ret,frame = self.video_capture.read()
        self.img_key_points=frame
        #self.circle_lock.acquire()
        self.circles=[]
        self.circles.append([centre_x+rand5,centre_y,27,[0,200,0],[0,255,0],1.0])
        self.circles.append([centre_x+50+rand4,centre_y+56,20,[0,200,0],[0,255,0],1.0])
        self.circles.append([centre_x+150+rand3,centre_y+105,20,[0,200,0],[0,255,0],1.0])
        self.circles.append([centre_x+161,centre_y+104,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+172+rand1,centre_y+103,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+183,centre_y+152,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+194+rand2,centre_y+201,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+163+rand2,centre_y+106,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+153+rand2,centre_y+101,20,[255,0,0],[0,255,0],1.0])
        self.circles.append([centre_x+4+rand2,centre_y-7,20,[255,0,0],[0,255,0],1.0])

        #self.circle_lock.release()
        #self.test_plot_circle_points(self.circles)

    def test_plot_circle_points(self,points):
        top=480
        #print("Circle plot:",len(points))
        for (x, y, r, feature_colour,type_colour,prob) in points:
            #print("x",x,"y",y,feature_colour,type_colour)
            x1=int(x)
            y1=int(top-y)
            cv2.circle(self.img_key_points,(x1,y1),10,[255,255,255],-1)
        cv2.imshow('frame',self.img_key_points)

    def test_plot_point(self,x,y):
        top=480
        x1=int(x)
        y1=int(top-y)
        cv2.circle(self.img_key_points,(x1,y1),4,[0,0,255],-1)
        cv2.imshow('frame',self.img_key_points)

    def test_plot_circle(self,x,y,r):
        top=480
        x1=int(x)
        y1=int(top-y)
        cv2.circle(self.img_key_points,(x1,y1),r,[0,255,0],1)
        cv2.imshow('frame',self.img_key_points)
