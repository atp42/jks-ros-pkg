#!/usr/bin/python

import roslib
roslib.load_manifest('robotpass')
import rospy
import actionlib
import sys, os, math

from pr2_controllers_msgs.msg import *
from pr2_gripper_sensor_msgs.msg import *
from pr2_controllers_msgs.msg import *
from trajectory_msgs.msg import *
from sensor_msgs.msg import *
from robotpass.msg import *
import cv
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError


class RobotPass(object):
    def __init__(self, name, left, right):
        self.result = PassObjectResult()
        self.l_gripper_pos = 0
        self.r_gripper_pos = 0
        self.hit_started = False

        #Positions database for arms
        self.position_high = [[0.0, -0.350, 0.0, -1.225, 3.14159, -1.65, 0.0],
                              [0.0, -0.350, 0.0, -1.625, 3.14159, -1.65, 0.0]]
        self.position_medium = [[0.0, 0.640, 0.0, -1.925, 3.14159, -1.25, 0.0],
                                [0.0, 0.640, 0.0, -2.325, 3.14159, -1.25, 0.0]]
        self.position_low = [[0.0, 0.900, 0.0, -0.825, 3.14159, 0, 0.0],
                             [0.0, 1.200, 0.0, -1.225, 3.14159, 0, 0.0]]
        self.position_db = {0: self.position_low, 1: self.position_medium, 2: self.position_high}

        self.stash_low = {0: [2.1339572013257304, -0.091108732183497729, -0.32299417263835628, -2.1179687143792689, 18.241037622294144 - math.pi * 2, -0.89756419129607556, 0.13109237626572012], }
        self.stash_high = {0: [2.1255836329726749, -0.3337269716470736, -0.24746704941813968, -1.8277034380552961, 11.906203130338264, -0.97553217611455001, 0.12960064186230591], }
        self.stash_back = {0: [2.0678806272922126, 0.051856687863030673, -0.29605456180821554, -1.9498899184629934, -0.47689138482042087, -1.1624609998357744, -0.13265248181800637], }
        self.action_name = name
        self.action_server = actionlib.SimpleActionServer(self.action_name, PassObjectAction, execute_cb=self.execute_cb, auto_start=False)
        self.bridge = CvBridge()
        self.process_gripper_right = False
        self.process_gripper_left = False
        self.gripper_image_right = False
        self.gripper_image_left = False
        self.gripper_object_right = False
        self.gripper_object_left = False
        wait_for = []
        self.l_arm = False
        self.r_arm = False
        self.l_arm_pos = False
        self.r_arm_pos = False
        self.arm_goal = False
        if (left):
            self.l_arm = actionlib.SimpleActionClient("l_arm_controller/joint_trajectory_action", JointTrajectoryAction)
            self.l_arm_names = ["l_shoulder_pan_joint", "l_shoulder_lift_joint", "l_upper_arm_roll_joint",
                              "l_elbow_flex_joint", "l_forearm_roll_joint", "l_wrist_flex_joint", "l_wrist_roll_joint"]
            self.l_gripper = actionlib.SimpleActionClient("l_gripper_sensor_controller/gripper_action", Pr2GripperCommandAction)
            self.l_sensor = actionlib.SimpleActionClient("l_gripper_sensor_controller/event_detector", PR2GripperEventDetectorAction)
            self.l_camera = rospy.Subscriber("/l_forearm_cam/image_rect_color", Image, self.process_image_left)
            wait_for += [self.l_arm, self.l_gripper, self.l_sensor]
        if (right):
            self.r_arm = actionlib.SimpleActionClient("r_arm_controller/joint_trajectory_action", JointTrajectoryAction)
            self.r_arm_names = ["r_shoulder_pan_joint", "r_shoulder_lift_joint", "r_upper_arm_roll_joint",
                         "r_elbow_flex_joint", "r_forearm_roll_joint", "r_wrist_flex_joint", "r_wrist_roll_joint"]
            self.r_gripper = actionlib.SimpleActionClient("r_gripper_sensor_controller/gripper_action", Pr2GripperCommandAction)
            self.r_sensor = actionlib.SimpleActionClient("r_gripper_sensor_controller/event_detector", PR2GripperEventDetectorAction)
            self.r_camera = rospy.Subscriber("/r_forearm_cam/image_rect_color", Image, self.process_image_right)
            wait_for += [self.r_arm, self.r_gripper, self.r_sensor]
        rospy.Subscriber("joint_states", JointState, self.joint_state_callback)
        for actionclient in wait_for:
            rospy.loginfo("Wait for item")
            actionclient.wait_for_server()
        self.action_server.start()
    
    def process_image_right(self, data):
        if (self.process_gripper_right):
            self.gripper_object_right, self.gripper_image_right = self.process_gripper_image(data, self.gripper_image_right, (0, 0, 100, 100))

    def process_image_left(self, data):
        if (self.process_gripper_left):
            self.gripper_object_left, self.gripper_image_left = self.process_gripper_image(data, self.gripper_image_left, (244, 160, 160, 180))
        
    def process_gripper_image(self, data, current_image, sub_rect):
        try:
            bimg = self.bridge.imgmsg_to_cv(data, "bgr8")
        except CvBridgeError, e:
            print e

        sub_data = cv.GetSubRect(bimg, sub_rect)
        
        if (current_image == False):
            #print "No current image"
            return (False, sub_data)
        else:
            cv.AbsDiff(sub_data, current_image, sub_data)
            delta = cv.Sum(sub_data)
            total = 0
            for i in delta:
                total = total + i
            if (total > 1000000.0):
                result = True
            else:
                result = False
            #print result, delta

            return (result, current_image)

    def start_object_vision(self, hand):
        if (hand == 0):
            self.gripper_object_left = False
            self.gripper_image_left = False
            self.process_gripper_left = True
        else:
            self.gripper_object_right = False
            self.gripper_image_right = False
            self.process_gripper_right = True

    def stop_object_vision(self):
        self.gripper_object_left = False
        self.gripper_image_left = False
        self.process_gripper_left = False
        self.gripper_object_right = False
        self.gripper_image_right = False
        self.process_gripper_right = False
        
    def check_object_vision(self, hand):
        #print self.gripper_object_left, self.gripper_object_right
        if (hand == 0):
            return self.gripper_object_left
        else:
            return self.gripper_object_right


    def move_arm(self, arm, arm_names, angles, duration=2):
        self.arm_goal = angles
        goal = JointTrajectoryGoal()
        goal.trajectory.header.stamp = rospy.get_rostime()
        goal.trajectory.joint_names = arm_names
        goal.trajectory.points = [JointTrajectoryPoint()]
        goal.trajectory.points[0].positions = angles
        goal.trajectory.points[0].velocities = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        goal.trajectory.points[0].time_from_start = rospy.Duration.from_sec(duration)
        arm.send_goal(goal)

    def grip(self, gripper, pos, effort):
        goal = Pr2GripperCommandGoal()
        goal.command.position = pos    # position open (9 cm)
        goal.command.max_effort = effort  # Do not limit effort (negative)
        gripper.send_goal(goal)

    def gripper_release(self, gripper):
        self.grip(gripper, 0.09, -1.0)
    
    def gripper_close(self, gripper):
        self.grip(gripper, 0.0, 20)
    
    def start_wait_for_hit(self, sensor, hand=None, mag = 4.5):
        if (hand != None):
            self.start_object_vision(hand)
        if (not self.hit_started):
            place_goal = PR2GripperEventDetectorGoal()
            place_goal.command.trigger_conditions = 4 # use just acceleration as our contact signal
            place_goal.command.acceleration_trigger_magnitude = mag # m/^2
            place_goal.command.slip_trigger_magnitude = 0.008 # slip gain
            sensor.send_goal(place_goal)
        else:
            rospy.logerr("Hit already started")
        self.hit_started = True

    def wait_for_hit(self, sensor, hand=None, arm=None):
        if (not self.hit_started):
            self.start_wait_for_hit(sensor, hand=hand)
        vision_hc = 0
        while not rospy.is_shutdown():
            print "Wait"
            if (hand != None and self.check_object_vision(hand)):
                vision_hc = vision_hc + 1
                if (vision_hc > 5):
                    print "Hit due to vision"
                    break
            else:
                vision_hc = 0
            if (arm != None):
                if (self.get_deflection(arm)):
                    print "Arm deflection hit"
                    break
            if (sensor.wait_for_result(rospy.Duration(0.1))):
                print "Sensor gripper hit"
                break
        self.stop_object_vision()
        self.hit_started = False
    
    def tts(self, text):
        #FIXME: Should use sound_play once we fix it.
        out = open("/tmp/tts_buf", "w")
        out.write(text)
        out.close()
        os.system("text2wave -o /tmp/tts_buf.wav /tmp/tts_buf && aplay /tmp/tts_buf.wav ; rm /tmp/tts_buf /tmp/tts_buf.wav")
    
    def joint_state_callback(self, msg):
        self.arm_pos_callback(msg)
        for i in zip(msg.name, msg.position):
            if (i[0] == "l_gripper_joint"):
                self.l_gripper_pos = i[1]
            if (i[0] == "r_gripper_joint"):
                self.r_gripper_pos = i[1]
    
    def get_items(self, hand):
        if (hand == 0):
            return (self.l_arm, self.l_arm_names, self.l_gripper, self.l_sensor)
        if (hand == 1):
            return (self.r_arm, self.r_arm_names, self.r_gripper, self.r_sensor)
        return False

    def get_gripper_pos(self, hand):
        if (hand == 0):
            return self.l_gripper_pos
        if (hand == 1):
            return self.r_gripper_pos
        return 0


    def arm_pos_callback(self, msg):
        pos = {}
        for i in zip(msg.name, msg.position):
            pos[i[0]] = i[1]
        if (self.l_arm):
            arr = []
            for p in self.l_arm_names:
                arr.append(pos[p])
            self.l_arm_pos = arr
        if (self.r_arm):
            arr = []
            for p in self.r_arm_names:
                arr.append(pos[p])
            self.r_arm_pos = arr

    def get_deflection(self, hand):
        pos = self.r_arm_pos
        if (hand == 0):
            pos = self.l_arm_pos
        sum = 0
        for i in zip(self.l_arm_pos, self.arm_goal):
            delta = i[0] - i[1]
            while (delta > math.pi):
                delta = delta - math.pi * 2
            while (delta < -math.pi):
                delta = delta + math.pi * 2
            if (delta < 0):
                delta = delta * -1
            sum = sum + delta
        if (0.005 > sum):
            return False
        return True



    def stash_object(self, object_name, hand):
        arm, arm_names, gripper, sensor = self.get_items(hand)
        self.move_arm(arm, arm_names, self.stash_high[hand], 5)
        arm.wait_for_result()
        self.move_arm(arm, arm_names, self.stash_low[hand], 3)
        arm.wait_for_result()
        self.gripper_release(gripper)
        gripper.wait_for_result()
        self.move_arm(arm, arm_names, self.stash_back[hand], 2)
    
    def unstash_object(self, object_name, hand):
        arm, arm_names, gripper, sensor = self.get_items(hand)
        self.gripper_release(gripper)
        self.move_arm(arm, arm_names, self.stash_back[hand], 5)
        arm.wait_for_result()
        self.move_arm(arm, arm_names, self.stash_low[hand], 2)
        arm.wait_for_result()
        self.gripper_close(gripper)
        gripper.wait_for_result()
        self.move_arm(arm, arm_names, self.stash_high[hand], 3)
        arm.wait_for_result()
    
    def take_object(self, object_name, position, hand):
        arm, arm_names, gripper, sensor = self.get_items(hand)
        position = self.position_db[position]
        self.gripper_release(gripper)
        self.move_arm(arm, arm_names, position[0], 3)
        arm.wait_for_result()
        gripper.wait_for_result()
        
        grasped = False
        width = 0.002
        while grasped == False:
            while grasped == False:
                self.start_wait_for_hit(sensor, hand)
                self.tts("Please pass me the %s." % object_name)
                self.wait_for_hit(sensor, hand, hand)

                self.gripper_close(gripper)
                gripper.wait_for_result()
                rospy.sleep(2.0)

                print self.get_gripper_pos(hand)
                if (self.get_gripper_pos(hand) > width):
                    grasped = True
                else:
                    self.tts("I don't think I got the %s. Let's try again." % object_name)
                    self.gripper_release(gripper)
                    gripper.wait_for_result()
                    rospy.sleep(1.0)
                    
            self.move_arm(arm, arm_names, position[1], 1)
            arm.wait_for_result()
            last = self.get_gripper_pos(hand)
            hc = 0
            while not rospy.is_shutdown() and hc < 5:
                current = self.get_gripper_pos(hand)
                delta = last - current
                if (delta < 0.0001):
                    hc = hc + 1
                else:
                    hc = 0
                print current, delta
                last = current
                rospy.sleep(0.1)
            if (self.get_gripper_pos(hand) > width):
                grasped = True
                self.tts("Thank you!")
            else:
                grasped = False
                self.tts("I don't think I got the %s. Let's try again." % object_name)
                self.move_arm(arm, arm_names, position[0], 1)
                self.gripper_release(gripper)
                arm.wait_for_result()
                gripper.wait_for_result()
                rospy.sleep(1.0)

    def give_object(self, object_name, position, hand):
        arm, arm_names, gripper, sensor = self.get_items(hand)
        position = self.position_db[position]
        self.move_arm(arm, arm_names, position[0], 3)
        arm.wait_for_result()
        self.gripper_close(gripper)
        gripper.wait_for_result()

        self.start_wait_for_hit(sensor, None, 4.0)
        self.tts("Please take the %s." % object_name)
        self.wait_for_hit(sensor, arm=hand)
        
        self.gripper_release(gripper)
        gripper.wait_for_result()

        self.move_arm(arm, arm_names, position[1], 1)
        arm.wait_for_result()
        self.tts("Thank you!")

    def execute_cb(self, goal):
        if (goal.direction == PassObjectGoal.TAKE_OBJECT):
            self.take_object(goal.object_name, goal.arm_position, goal.arm)
        if (goal.direction == PassObjectGoal.GIVE_OBJECT):
            self.give_object(goal.object_name, goal.arm_position, goal.arm)
        if (goal.direction == PassObjectGoal.STASH_OBJECT):
            self.stash_object(goal.object_name, goal.arm)
        if (goal.direction == PassObjectGoal.UNSTASH_OBJECT):
            self.unstash_object(goal.object_name, goal.arm)
        self.action_server.set_succeeded(self.result)


##################
if __name__ == '__main__':
    rospy.init_node('robotpass')
    server = RobotPass("pass_object", not "--no-left" in sys.argv[1:], not "--no-right" in sys.argv[1:])
    if ("--test" in sys.argv[1:]):
        print "Doing self-test with give and take"
        hand = None
        if ("--use-left" in sys.argv[1:]):
            hand = 0
        if ("--use-right" in sys.argv[1:]):
            hand = 1
        if (hand == None):
            print "Testing has failed: specify a hand with --use-left or --use-right"
        else:
            while not rospy.is_shutdown():
                print "Waiting for client"
                test_client = actionlib.SimpleActionClient("pass_object", PassObjectAction)
                test_client.wait_for_server()
                print "Have server"
                print "Try take"
                take_goal = PassObjectGoal()
                take_goal.arm = hand
                take_goal.direction = PassObjectGoal.TAKE_OBJECT
                take_goal.arm_position = PassObjectGoal.HIGH
                take_goal.object_name = "dinosore"
                test_client.send_goal(take_goal)
                test_client.wait_for_result()
                print "Done take"

                print "Try stash"
                stash_goal = PassObjectGoal()
                stash_goal.arm = hand
                stash_goal.direction = PassObjectGoal.STASH_OBJECT
                stash_goal.object_name = "test object"
            #test_client.send_goal(stash_goal)
            #test_client.wait_for_result()
                print "Done stash"

                print "Try unstash"
                stash_goal = PassObjectGoal()
                stash_goal.arm = hand
                stash_goal.direction = PassObjectGoal.UNSTASH_OBJECT
                stash_goal.object_name = "test object"
            #test_client.send_goal(stash_goal)
            #test_client.wait_for_result()
                print "Done stash"

                print "Try give"
                give_goal = PassObjectGoal()
                give_goal.arm = hand
                give_goal.direction = PassObjectGoal.GIVE_OBJECT
                give_goal.arm_position = PassObjectGoal.HIGH
                give_goal.object_name = "dinosore"
                test_client.send_goal(give_goal)
                test_client.wait_for_result()
                print "Done give"
                print "Done selftest"
            

            
            

    rospy.spin()








