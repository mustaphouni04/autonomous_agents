import asyncio
import random
import py_trees
import py_trees as pt
from py_trees import common
import Goals_BT
import Sensors

class BN_DoNothing(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        super(BN_DoNothing, self).__init__("BN_DoNothing")

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT.DoNothing(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        self.my_goal.cancel()

class BN_ForwardStop(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_ForwardStop, self).__init__("BN_ForwardStop")
        self.logger.debug("Initializing BN_ForwardStop")
        self.my_agent = aagent

    def initialise(self):
        self.logger.debug("Create Goals_BT.ForwardStop task")
        self.my_goal = asyncio.create_task(Goals_BT.ForwardStop(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        self.logger.debug("Terminate BN_ForwardStop")
        self.my_goal.cancel()

class BN_TurnRandom(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_TurnRandom, self).__init__("BN_TurnRandom")
        self.my_agent = aagent

    def initialise(self):
        self.my_goal = asyncio.create_task(Goals_BT.Turn(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        self.logger.debug("Terminate BN_TurnRandom")
        self.my_goal.cancel()

class BN_RandomRoam(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_RandomRoam, self).__init__("BN_RandomRoam")
        self.logger.debug("Initializing BN_RandomRoam")
        self.my_agent = aagent

    def initialise(self):
        self.logger.debug("Create Goals_BT.RandomRoam task")
        self.my_goal = asyncio.create_task(Goals_BT.RandomRoam(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        self.logger.debug("Terminate BN_RandomRoam")
        self.my_goal.cancel()

class BN_Avoid(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_goal = None
        super(BN_Avoid, self).__init__("BN_Avoid")
        self.logger.debug("Initializing BN_Avoid")
        self.my_agent = aagent

    def initialise(self):
        self.logger.debug("Create Goals_BT.Avoid task")
        self.my_goal = asyncio.create_task(Goals_BT.Avoid(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        self.logger.debug("Terminate BN_Avoid")
        self.my_goal.cancel()

class BN_DetectFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        super(BN_DetectFlower, self).__init__("BN_DetectFlower")

    def update(self):
        if Goals_BT.DetectFlower(self.my_agent).run():
            print("Flower detected, prioritizing MoveToFlower")
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.FAILURE

class BN_MoveToFlower(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        super(BN_MoveToFlower, self).__init__("BN_MoveToFlower")

    def initialise(self):
        print("Starting MoveToFlower task")
        self.my_goal = asyncio.create_task(Goals_BT.MoveToFlower(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                return pt.common.Status.SUCCESS
            else:
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal and not self.my_goal.done():
            self.my_goal.cancel()

class BN_CheckInventoryFull(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        super(BN_CheckInventoryFull, self).__init__("BN_CheckInventoryFull")

    def update(self):
        if Goals_BT.CheckInventoryFull(self.my_agent).run():
            print("Inventory full, prioritizing ReturnToBase")
            return pt.common.Status.SUCCESS
        else:
            return pt.common.Status.FAILURE

class BN_ReturnToBase(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        self.my_agent = aagent
        self.my_goal = None
        super(BN_ReturnToBase, self).__init__("BN_ReturnToBase")

    def initialise(self):
        print("Starting ReturnToBase task")
        self.my_goal = asyncio.create_task(Goals_BT.ReturnToBase(self.my_agent).run())

    def update(self):
        if not self.my_goal.done():
            return pt.common.Status.RUNNING
        else:
            if self.my_goal.result():
                print("ReturnToBase completed successfully")
                return pt.common.Status.SUCCESS
            else:
                print("ReturnToBase failed")
                return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        if self.my_goal and not self.my_goal.done():
            self.my_goal.cancel()
            print("ReturnToBase task cancelled")

class BTRoam:
    def __init__(self, aagent):
        py_trees.logging.level = py_trees.logging.Level.DEBUG
        self.aagent = aagent

        # Behavior tree structure
        root = pt.composites.Selector(name="Root", memory=False)

        # Return to base when inventory is full
        return_to_base = pt.composites.Sequence(name="ReturnToBase", memory=True)
        return_to_base.add_children([BN_CheckInventoryFull(aagent), BN_ReturnToBase(aagent)])

        # Collect flowers
        collect_flower = pt.composites.Sequence(name="CollectFlower", memory=True)
        collect_flower.add_children([BN_DetectFlower(aagent), BN_MoveToFlower(aagent)])

        # Wander (avoid obstacles or roam)
        wander = pt.composites.Selector(name="Wander", memory=True)
        wander.add_children([
            BN_Avoid(aagent),
            BN_RandomRoam(aagent)
        ])

        root.add_children([return_to_base, collect_flower, wander])
        self.behaviour_tree = pt.trees.BehaviourTree(root)

    def set_invalid_state(self, node):
        node.status = pt.common.Status.INVALID
        for child in node.children:
            self.set_invalid_state(child)

    def stop_behaviour_tree(self):
        self.set_invalid_state(self.behaviour_tree.root)

    async def tick(self):
        self.behaviour_tree.tick()
        await asyncio.sleep(0)