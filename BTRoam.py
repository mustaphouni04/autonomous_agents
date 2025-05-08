import asyncio
import random
import py_trees
import py_trees as pt
from py_trees import common
import Goals_BT
from Goals_BT import DetectAstronaut, FollowAstronaut, BiteAstronaut, MoveAway
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

class BN_DetectAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_DetectAstronaut")
        self.agent = aagent
    def update(self):
        return common.Status.SUCCESS if DetectAstronaut(self.agent).run() else common.Status.FAILURE

class BN_FollowAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_FollowAstronaut")
        self.agent = aagent
        self.task = None
    def initialise(self):
        self.task = asyncio.create_task(FollowAstronaut(self.agent).run())
    def update(self):
        if not self.task.done(): return common.Status.RUNNING
        return common.Status.SUCCESS if self.task.result() else common.Status.FAILURE
    def terminate(self, new_status):
        if self.task and not self.task.done(): self.task.cancel()

class BN_BiteAstronaut(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_BiteAstronaut")
        self.agent = aagent
        self.task = None
    def initialise(self):
        self.task = asyncio.create_task(BiteAstronaut(self.agent).run())
    def update(self):
        if not self.task.done(): return common.Status.RUNNING
        return common.Status.SUCCESS if self.task.result() else common.Status.FAILURE

class BN_MoveAway(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super().__init__("BN_MoveAway")
        self.agent = aagent
        self.task = None
    def initialise(self):
        self.task = asyncio.create_task(MoveAway(self.agent).run())
    def update(self):
        if not self.task.done(): return common.Status.RUNNING
        return common.Status.SUCCESS if self.task.result() else common.Status.FAILURE

class BN_DetectFrozen(pt.behaviour.Behaviour):
    def __init__(self, aagent):
        super(BN_DetectFrozen, self).__init__("BN_DetectFrozen")
        self.my_agent = aagent
        self.i_state = aagent.i_state

    def initialise(self):
        # no async goal to start
        pass

    def update(self):
        # If the agent is stunned/frozen, succeed so the frozen sequence runs
        if self.i_state.isFrozen:
            return pt.common.Status.SUCCESS
        return pt.common.Status.FAILURE

    def terminate(self, new_status: common.Status):
        # nothing to clean up
        pass

class BTRoam:
    def __init__(self, aagent):
        py_trees.logging.level = py_trees.logging.Level.DEBUG
        self.aagent = aagent

        agent_type = aagent.AgentParameters["type"]
        # Build root selector
        root = pt.composites.Selector(name="Selector_root", memory=False)

        if agent_type == "AAgentCritterMantaRay":
            # --- 1) Frozen check (sticky) ---
            frozen = pt.composites.Sequence(name="Sequence_Frozen", memory=True)
            frozen.add_children([
                BN_DetectFrozen(aagent),
                BN_DoNothing(aagent)
            ])

            # --- 2) Hunt & Bite sequence (sticky) ---
            hunt = pt.composites.Sequence(name="Sequence_HuntAstronaut", memory=True)
            hunt.add_children([
                BN_DetectAstronaut(aagent),
                BN_FollowAstronaut(aagent),
                BN_BiteAstronaut(aagent),
                BN_MoveAway(aagent)
            ])

            # --- 3) Wander when nothing else applies ---
            wander = pt.composites.Selector(name="Wander", memory=True)
            wander.add_children([
                BN_Avoid(aagent),
                BN_RandomRoam(aagent)
            ])

            root.add_children([frozen, hunt, wander])

        else:
            # --- Astronaut’s original tree ---
            return_to_base = pt.composites.Sequence(name="ReturnToBase", memory=True)
            return_to_base.add_children([
                BN_CheckInventoryFull(aagent),
                BN_ReturnToBase(aagent)
            ])

            collect_flower = pt.composites.Sequence(name="CollectFlower", memory=True)
            collect_flower.add_children([
                BN_DetectFlower(aagent),
                BN_MoveToFlower(aagent)
            ])

            wander = pt.composites.Selector(name="Wander", memory=True)
            wander.add_children([
                BN_Avoid(aagent),
                BN_RandomRoam(aagent)
            ])

            root.add_children([return_to_base, collect_flower, wander])

        # Finalize the tree
        self.behaviour_tree = pt.trees.BehaviourTree(root)

    def set_invalid_state(self, node):
        node.status = pt.common.Status.INVALID
        for child in getattr(node, "children", []):
            self.set_invalid_state(child)

    def stop_behaviour_tree(self):
        self.set_invalid_state(self.behaviour_tree.root)

    async def tick(self):
        self.behaviour_tree.tick()
        await asyncio.sleep(0)