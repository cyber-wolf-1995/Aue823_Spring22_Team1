#!/usr/bin/env python3
from cmath import inf

from numpy import False_, average
import rospy # Python library for ROS
from sensor_msgs.msg import LaserScan # LaserScan type message is defined in sensor_msgs
from geometry_msgs.msg import Twist #
from statistics import mean

#global variable to switch from wallfollowing to obstacle avoidance
isObsAvd = False
corr_ang_list = [0.0]
counter = 0
bElseloop = True
thrcounter = 0
thrleft = 0
thr = 0
e11,e21,e31 = 0,0,0
u = 0
sub_wlflw = None
sub_ObsAvd = None

class Clbk_obj(object):

    def __init__(self):
        self.move = Twist() # Creates a Twist message type object
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)  # Publisher object which will publish "Twist" type messages
        self.node = rospy.init_node('wallAndObstacle')
        self.isObsAvd = False
        self.isObsL = False
        self.isObsR = False
        self.isObsF = False


def callback_ObsAvd(dt, args):
    #tme = rospy.Time.now()
    #rospy.loginfo("\n obstacle avoidance callback called at \n" +str(tme.secs))
    if(args.isObsAvd==True):

        thr1 = 0.3 # Laser scan range threshold
        thr2 = 0.3
        pub = args.pub
        move = args.move
        saturated_dist = 0.5
        max_gap = []
        max_gap_ornt = []
        center_ornt = 0
        rospy.loginfo('-------------------Inside obstacle avoidance----------------------')
        kw = 0.1                      # Proportional constant for angular velocity control

        #gap detection
        detection = list(dt.ranges[-90:90])
        gap = []
        ornt = []
        for i in range(len(detection)):
            if(detection[i]>saturated_dist):
                gap.append(detection[i])
                ornt.append(i)
            elif(len(gap)>len(max_gap)):
                    max_gap = gap
                    max_gap_ornt = ornt
                    gap.clear
                    ornt.clear                            
            else:
                if(len(gap)>1):
                    gap.clear 
                    ornt.clear
                else:
                    continue

        #getting the center of max gap
        if(len(max_gap)>1):
            if(len(max_gap)%2==0):       
                center_ornt = max_gap_ornt[int(len(max_gap_ornt)/2)]
            else:
                center_ornt = max_gap_ornt[int((len(max_gap_ornt)-1)/2)]

            if(center_ornt<=90):
                #corresponds to 270 to 0 degrees
                center_ornt = -center_ornt
            else:
                #corresponds to 0 to 90 degrees
                center_ornt = 90 - center_ornt

            rospy.loginfo('\n the max gap is of length %d and has center at %d',len(max_gap),center_ornt)

            #making the robot go to the center_ornt
            move.angular.z = kw*center_ornt
            move.linear.x = 0.1
        else:
            move.angular.z = 0
            move.linear.x = 0.1

        rospy.loginfo("The linear vel is %f & angular vel is %f\n", move.linear.x, move.angular.z)   
        pub.publish(move) # publish the move object

        

def callback_WlFlw(dt, args):


    if(args.isObsAvd==False):
        #tme = rospy.Time.now()
        #rospy.loginfo("\n wall follower callback called at \n" +str(tme.secs))
        thr_obs = 0.3 # Laser scan range threshold
        saturated_dist = 1
        left_obs = 0
        left_obs_counter = 0
        right_obs = 0
        right_obs_counter = 0
        front_obs = 0
        front_obs_counter = 0
        front_saturated_dist = 1.5

        #left section
        for i in range(30,60):
            if(dt.ranges[i]==inf):
                left_obs+=saturated_dist
                left_obs_counter+=1
            else:
                left_obs+=dt.ranges[i]
                left_obs_counter+=1
        left_obs=left_obs/left_obs_counter

        #right section
        for i in range(300,330):
            if(dt.ranges[i]==inf):
                right_obs+=saturated_dist
                right_obs_counter+=1
            else:
                right_obs+=dt.ranges[i]
                right_obs_counter+=1
        right_obs=right_obs/right_obs_counter

        #front section
        front1 = list(dt.ranges[0:5])
        front2 = list(dt.ranges[-5:])
        front_dist = front1 + front2

        for i in range(len(front_dist)):
            if(front_dist[i]==inf):
                front_obs+=front_saturated_dist
                front_obs_counter+=1
            else:
                front_obs+=front_dist[i]
                front_obs_counter+=1
        front_obs=front_obs/front_obs_counter

        if(left_obs < thr_obs):
                args.isObsL = True
                rospy.loginfo("\n left below threshold \n")
        if(right_obs < thr_obs):
                args.isObsR = True
                rospy.loginfo("\n right below threshold \n")
        if(front_obs < thr_obs):
                args.isObsF = True
                rospy.loginfo("\n front below threshold \n")

        if(args.isObsL==True and args.isObsR==True or args.isObsF==True):
                args.isObsAvd =True
                rospy.loginfo("\n ************ condition for obstacle avoidance met ************ \n")

        #if front_obs<thr_obs and (left_obs<thr_obs or right_obs<thr_obs):
        #    args.isObsAvd = True
        #    rospy.loginfo("\n switching from wall follower to obstacle avoidance\n" + str(args.isObsAvd))

        else:

            rospy.loginfo("\n Inside wallfollower callback \n" )
            global corr_ang_list, counter, bElseloop, thrcounter, thrleft, e11, e21, e31, u, thr, isObsAvd, sub_wlflw
            thr1 = 0.25 # Laser scan range threshold
            #saturated_dist = 1
            left_avg = 0
            left_counter = 0
            right_avg = 0
            right_counter = 0
            front_avg = 0
            front_min = 0
            front_counter = 0
            #front_saturated_dist = 1.5

            #left section
            for i in range(75,106):
                if(dt.ranges[i]==inf):
                    left_avg+=saturated_dist
                    left_counter+=1
                else:
                    left_avg+=dt.ranges[i]
                    left_counter+=1
            left_avg=left_avg/left_counter

            #right section
            for i in range(255,286):
                if(dt.ranges[i]==inf):
                    right_avg+=saturated_dist
                    right_counter+=1
                else:
                    right_avg+=dt.ranges[i]
                    right_counter+=1
            right_avg=right_avg/right_counter

            #front section
            front1 = list(dt.ranges[0:10])
            front2 = list(dt.ranges[-11:])
            front_dist = front1 + front2

            for i in range(len(front_dist)):
                if(front_dist[i]==inf):
                    front_avg+=front_saturated_dist
                    front_counter+=1
                else:
                    front_avg+=front_dist[i]
                    front_counter+=1
            front_avg=front_avg/front_counter

            pub = args.pub
            move = args.move
            margin = 0.1
            
            thr1 = 0.3 # Laser scan range threshold

            #creating a discretized pid controller
            kp = 0.5
            ki = 0.0
            kd = 0.3
            k11 = kp + ki + kd
            k21 = -kp - 2*kd
            k31 = kd

            #using the minimum front
            front_min = min(front_dist)

            if(front_min<=0.5):
                move.linear.x = 0.0
                move.angular.z = 0.3
                #rospy.loginfo("turning. Inside outer if \n")

            elif(abs(left_avg-right_avg)<= 0.3 and 0.5<front_avg<=2):
                
                move.linear.x = 0.2
                move.angular.z = 0.0
                #rospy.loginfo("going straight. Inside outer elif \n")
                
            else:
                if(thr1 > right_avg - left_avg > margin):
                    #rospy.loginfo("Right greater. Inside if \n")
                    correction = right_avg - left_avg
                    correction_lin = 0.3#limit the maximum speed

                    e31 = e21
                    e21 = e11
                    e11 = correction
                    u = u + k11*e11 + k21*e21 + k31*e31

                    move.angular.z = -u
                    move.linear.x = correction_lin

                    corr_ang_list[0] =  move.angular.z
                    
                elif(0.3 > left_avg - right_avg > margin):
                    #rospy.loginfo("Left greater. Inside elif \n")
                    correction = (left_avg - right_avg)
                    correction_lin = 0.3#limit the maximum speed

                    e31 = e21
                    e21 = e11
                    e11 = correction
                    u = u + k11*e11 + k21*e21 + k31*e31

                    move.angular.z = u
                    move.linear.x = correction_lin
                    
                    corr_ang_list[0] =  move.angular.z

                elif(0.75 > right_avg - left_avg >0.3):
                    #rospy.loginfo("Right too great. Inside elif2 \n")
                    correction = right_avg - left_avg
                    correction_lin = 0.3#limit the maximum speed

                    e31 = e21
                    e21 = e11
                    e11 = correction
                    u = u + k11*e11 + k21*e21 + k31*e31

                    move.angular.z = -1.25*u
                    move.linear.x = correction_lin

                    corr_ang_list[0] =  move.angular.z

                elif(0.75 > left_avg - right_avg >0.3):
                    #rospy.loginfo("Left too great. Inside elif3 \n")
                    correction = (left_avg - right_avg)
                    correction_lin = 0.3#limit the maximum speed

                    e31 = e21
                    e21 = e11
                    e11 = correction
                    u = u + k11*e11 + k21*e21 + k31*e31

                    move.angular.z = 0.75*u
                    move.linear.x = 0.75*correction_lin

                    corr_ang_list[0] =  move.angular.z
                else:
                    
                    move.linear.x = 0.2
                    move.angular.z = -corr_ang_list[0]
                    #rospy.loginfo("Almost equal. Inside else \n")

            #rospy.loginfo("The linear vel is %f & angular vel is %f\n", move.linear.x, move.angular.z)
            pub.publish(move) # publish the move object

def main():
    global isObsAvd
    #value = input("Please enter a string:\n")

    #callback arguments storing object
    wlflw_obj = Clbk_obj()

    #rospy.loginfo("Value of the boolean is  \n" + str(isObsAvd))
    #if isObsAvd is False:
    #    wallfollower_fn(wlflw_obj)

    #else:
    #    rospy.loginfo("\n Exiting wallfollow. Going into obstacle avoidance \n")
    #    obstacleAvoidance_fn(wlflw_obj)
    
    #create two dummy callbacks and put their data in a global variable
    #create an evaluation condition for the variable's value at the start and print it with timestamps
    try:
        sub_wlflw = rospy.Subscriber("/scan", LaserScan, callback_WlFlw,  wlflw_obj, queue_size=1)  # Subscriber object which will listen "LaserScan" type messages
                                                        # from the "/scan" Topic and call the "callback" function
                                                        # each time it reads something from the Topic
        sub_ObsAvd = rospy.Subscriber("/scan", LaserScan, callback_ObsAvd,  wlflw_obj, queue_size=1)  # Subscriber object which will listen "LaserScan" type messages
                                                        # from the "/scan" Topic and call the "callback" function
                                                        # each time it reads something from the Topic
        rospy.spin() # Loops infinitely until someone stops the program execution
    except rospy.ROSInterruptException:
        pass
    
    rospy.loginfo("Coming out of first callback \n")

if __name__ == '__main__':
    main()
    #rospy.spin() # Loops infinitely until someone stops the program execution

