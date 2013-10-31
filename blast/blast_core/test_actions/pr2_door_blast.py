

class BlastPr2DoorBlastActionExec(BlastActionExec):
    def __init__(self, robot, manager, guid):
        BlastActionExec.__init__(self, robot, manager, guid)
    def run(self, parameters):
        self.set_location(self.get_surface(parameters["door"])["locations"]["out_exit"])
set_action_exec("pr2", "door_blast", BlastPr2DoorBlastActionExec)
