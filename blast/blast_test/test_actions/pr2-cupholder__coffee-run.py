#--------------------------------------------------------------------
#Copyright (c) 2015
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions 
#are met:
#  1. Redistributions of source code must retain the above copyright 
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above 
#     copyright notice, this list of conditions and the following 
#     disclaimer in the documentation and/or other materials 
#     provided with the distribution.
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 
#"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT 
#LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
#FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE 
#COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
#INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
#HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
#ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
#ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#--------------------------------------------------------------------

class BlastPr2CoffeeRunActionExec(BlastActionExec):
    def __init__(self):
        BlastActionExec.__init__(self)
    def run(self, parameters):
        #Hunt down an empty ziplock bag so that we can have the bot grab it
        #and bring it to the person. Save its location so we have good manners
        #and put the object back where we found it.
        try:
            empty_uid, return_pos, surface = self.plan_hunt("left-arm", "empty_ziplock_1L_bag")
        except BlastFindObjectError:
            self.set_failure("no-bag")
            return
       

        #Grab the money bag of of the human
        #Note that we drive to the human location by setting it as a world
        #limit on the grab object action. Why do this instead of just driving
        #to the human? Because if we drove, then what action would we run?
        #The move action would fail if for some reason we were already at the
        #current location (which could very well be the case). Further, once the
        #robot reach the location, it could conceviably move to another before
        #actually running the grab (although this is very unlikely).
        print "-"*30, "Grab money bag", "-"*30
        self.plan_action("give-object", {"tts-text": "Empty Bag"},
                         {"robot-location": parameters["person_location"],
                          "robot-holders": {"left-arm": empty_uid}})
        self.plan_action("grab-object", {"tts-text": "Money Bag"},
                         {"robot-location": parameters["person_location"]})
        self.set_robot_holder("left-arm", "coffee_money_bag")

        money_bag = self.get_robot_holder("left-arm") #Get the UID of the object

        #It is important for us to use world limit constraints. The reason
        #is that we don't want an action to drop and then pick up the money bag.
        #To see why we need this, imagine there's a table at the shop with a money 
        #bag on it. If for some reason travelling there without the bag is faster
        #(2 handed door opening or something) then the robot will throw out the
        #bag and grab the other one since all bags are the same as far as BLAST
        #cares. By putting in this exact constraint, we can prevent this from
        #ever happening.
        

        #Drive to the coffee shop and try to pick up the coffee cup
        #We make sure the same money bag is in the hand of the
        #robot before execution with a robot-holders world limit
        print "-"*30, "Execute buy coffee action", "-"*30
        self.plan_action("buy-coffee", {"shop": parameters["shop"]}, 
                         {"robot-holders": {"left-arm": money_bag}})
        coffee_cup = self.get_robot_holder("cupholder")

        #Now that we have purchased the coffee cup, we can drive back to
        #the person and deliver the cup and take back the empty bag
        print "-"*30, "Give out coffee", "-"*30
        self.plan_action("give-object", {"tts-text": "Coffee Cup"}, 
                         {"robot-holders": {"cupholder": coffee_cup},
                          "robot-location": parameters["person_location"]})
        self.plan_action("grab-object", {"tts-text": "Empty Bag"},
                         {"robot-location": parameters["person_location"]})
        self.set_robot_holder("left-arm", "empty_ziplock_1L_bag")
        empty_bag = self.get_robot_holder("left-arm")

        
        print "-"*30, "Replace Object", "-"*30
        #Put back down the empty bag on the table so it can be reused. Note
        #that we use plan_place here instead of directly planning the 
        #table-place-object action. This is so that if in the future the bag
        #may be picked up off of another surface it will still work for the
        #return.
        self.plan_place(empty_bag, surface, return_pos)

set_action_exec(BlastPr2CoffeeRunActionExec)
