import math
import random
import asyncio
import Sensors
from collections import Counter

class DoNothing:
    """
    Does nothing
    """
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state

    async def run(self):
        print("Doing nothing")
        await asyncio.sleep(1)
        return True

class ForwardStop:
    """
    Moves forward till it finds an obstacle. Then stops.
    """
    STOPPED = 0
    MOVING = 1
    END = 2

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.state = self.STOPPED

    async def run(self):
        try:
            while True:
                if self.state == self.STOPPED:
                    await self.a_agent.send_message("action", "mf")
                    self.state = self.MOVING
                elif self.state == self.MOVING:
                    sensor_hits = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]
                    sensor_obj_info = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
                    obstacle_detected = any(
                        hit and obj_info and obj_info["tag"] != "AlienFlower"
                        for hit, obj_info in zip(sensor_hits, sensor_obj_info)
                    )
                    if obstacle_detected:
                        self.state = self.END
                        await self.a_agent.send_message("action", "stop")
                    else:
                        await asyncio.sleep(0)
                elif self.state == self.END:
                    return True
                else:
                    print("Unknown state: " + str(self.state))
                    return False
        except asyncio.CancelledError:
            print("***** TASK Forward CANCELLED")
            await self.a_agent.send_message("action", "stop")
            self.state = self.STOPPED

class Turn:
    """
    Randomly selects a rotation degree and direction, then waits for completion.
    """
    STOPPED = 0
    ROTATING = 1

    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.i_state = a_agent.i_state
        self.state = self.STOPPED
        self.target_rotation = None

    async def run(self):
        try:
            while True:
                if self.state == self.STOPPED:                     
                    degree = random.randint(10, 360)
                    direction = random.choice(["tr", "tl"])
                    print(f"Turning {degree} degrees to the {direction}")
                    current_rotation = self.i_state.rotation["y"]
                    if direction == "tr":
                        self.target_rotation = (current_rotation + degree) % 360 
                    else:
                        self.target_rotation = (current_rotation - degree) % 360
                    await self.a_agent.send_message("action", direction)
                    self.state = self.ROTATING
                elif self.state == self.ROTATING:
                    current_rotation = self.i_state.rotation["y"]
                    if abs(current_rotation - self.target_rotation) < 10:
                        print(f"Turn complete. Current rotation: {current_rotation}")
                        await self.a_agent.send_message("action", "nt")
                        self.state = self.STOPPED
                        return True
                    await asyncio.sleep(0.1)
                else:
                    print(f"Unknown state: {self.state}")
                    return False
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("***** TASK Turn CANCELLED")
            await self.a_agent.send_message("action", "stop")
            self.state = self.STOPPED

class RandomRoam:
    """
    Single‐step stochastic roaming:
      - If a flower is spotted: return False to preempt.
      - Otherwise, 20% chance to turn slightly, 80% to step forward.
      - Returns True whenever it issues an action.
    """
    def __init__(self, a_agent):
        self.a_agent = a_agent

    async def run(self) -> bool:
        if DetectFlower(self.a_agent).run():
            return False
        # 2) Decide action this tick
        if random.random() < 0.2:
            # do a small random turn
            direction = random.choice(["tl", "tr"])
            print(f"RandomRoam: small turn {direction}")
            await self.a_agent.send_message("action", direction)
            await asyncio.sleep(0.3)
            await self.a_agent.send_message("action", "nt")
        else:
            # move forward
            await self.a_agent.send_message("action", "mf")
            await asyncio.sleep(0.5)

        return True

    async def terminate(self, new_status):
        # ensure no leftover movement
        await self.a_agent.send_message("action", "stop")

class Avoid:
    """
    Single‐tick obstacle avoidance:
      - If any Rock/Wall is within threshold distance, turn away (one small step) and return True.
      - Otherwise return False so the tree moves on to RandomRoam.
    """
    def __init__(self, a_agent, distance_threshold: float = 2.5):  # previously 1.0
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.threshold = distance_threshold
        self.last_turn = None
        self.oscillations = 0
        self.osc_threshold = 4

    async def run(self) -> bool:
        # Pair hits with their object info
        hits = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]
        infos = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]

        # Build a mask of True for any relevant obstacles:
        # Astronaut dodges Critters; Critter dodges Flowers (in addition to Walls/Rocks)
        agent_type = self.a_agent.AgentParameters["type"]
        flower_mask = []
        rock_mask = []
        close_mask = []
        for hit, info in zip(hits, infos):
            if not hit or info is None:
                close_mask.append(False)
                flower_mask.append(False)
                rock_mask.append(False)
                continue
            tag = info.get("tag")
            dist = info.get("distance", float("inf"))
            if dist >= self.threshold:
                close_mask.append(False)
                flower_mask.append(False)
                rock_mask.append(False)
                continue

            # Always treat walls/rocks as obstacles
            if tag in ("Rock", "Wall"):
                close_mask.append(True)
                rock_mask.append(True)
                flower_mask.append(False)
                continue

            # Astronaut must dodge Critters
            if agent_type == "AAgentAstronaut" and tag == "CritterMantaRay":
                close_mask.append(True)
                flower_mask.append(False)
                rock_mask.append(False)
                continue

            # Critter must ignore walls/rocks but also avoid Flowers
            if agent_type == "AAgentCritterMantaRay" and tag == "AlienFlower":
                close_mask.append(True)
                flower_mask.append(True)
                rock_mask.append(False)
                continue

            # otherwise not an obstacle for this agent
            close_mask.append(False)
            flower_mask.append(False)
            rock_mask.append(False)
        
        # SPECIAL CASE: Critter jammed between two+ flowers only — back up
        if agent_type == "AAgentCritterMantaRay":
            flower_hits = sum(flower_mask)
            other_hits  = sum(rock_mask)
            if flower_hits >= 2 and other_hits == 0:
                # Simple escape: rotate then advance
                direction = random.choice(["tr", "tl"])
                print(f"Avoid: squeezed by {flower_hits} flowers—turning {direction} & moving forward")
                await self.a_agent.send_message("action", direction)
                await asyncio.sleep(0.5)
                await self.a_agent.send_message("action", "nt")
                await self.a_agent.send_message("action", "mf")
                await asyncio.sleep(0.5)
                return True

        # SPECIAL CASE: Critter oscillating stuck between obstacles
        if agent_type == "AAgentCritterMantaRay":
            # determine current turn direction from side counts
            mid = len(close_mask) // 2
            left_block  = sum(close_mask[:mid])
            right_block = sum(close_mask[mid+1:])
            # choose what we'd turn this tick
            current_turn = "tr" if left_block >= right_block else "tl"
            # detect alternation
            if self.last_turn and current_turn != self.last_turn:
                self.oscillations += 1
            else:
                self.oscillations = 0
            self.last_turn = current_turn

            if self.oscillations >= self.osc_threshold:
                # escape maneuver if stuck in oscillation
                print(f"Avoid: detected oscillation ({self.oscillations}), escaping")
                # rotate
                await self.a_agent.send_message("action", current_turn)
                await asyncio.sleep(1.5)
                await self.a_agent.send_message("action", "nt")
                # move forward
                await self.a_agent.send_message("action", "mf")
                await asyncio.sleep(0.5)
                # reset oscillation tracking
                self.oscillations = 0
                self.last_turn = None
                return True

        if not any(close_mask):
            # No obstacle close enough: let RandomRoam take over
            return False

        # Obstacle detected: pick turn direction based on side counts
        mid = len(close_mask) // 2
        left_block = sum(close_mask[:mid])    # count left side hits
        right_block = sum(close_mask[mid+1:]) # count right side hits

        # Turn away from the heavier side
        turn_cmd = "tr" if left_block >= right_block else "tl"
        print(f"Avoid: obstacle ahead, turning {turn_cmd}")
        await self.a_agent.send_message("action", turn_cmd)
        await asyncio.sleep(0.2)
        await self.a_agent.send_message("action", "nt")
        return True

    async def terminate(self, new_status):
        # ensure no leftover movement command
        await self.a_agent.send_message("action", "stop")

class DetectFlower:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor

    def run(self):  # Now synchronous
        sensor_obj_info = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        for value in sensor_obj_info:
            if value and value["tag"] == "AlienFlower":
                return True
        return False

class MoveToFlower:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.i_state = a_agent.i_state
        self.initial_flower_count = sum(
            item["amount"]
            for item in self.i_state.myInventoryList
            if item["name"] == "AlienFlower"
        )
        self.lost_tolerance = 2   # how many consecutive “no-detections” we tolerate
        # tuning constants:
        self.TURN_TIME = 0.3      # seconds spent turning per step
        self.FORWARD_TIME = 0.8   # seconds spent moving forward per step

    async def run(self):
        print("Starting MoveToFlower")
        lost_count = 0

        # initial detection
        flower_indices = [
            idx for idx, ray in enumerate(zip(*self.rc_sensor.sensor_rays))
            if ray[Sensors.RayCastSensor.HIT]
               and ray[Sensors.RayCastSensor.OBJECT_INFO].get("tag") == "AlienFlower"
        ]
        if not flower_indices:
            print("No flower detected")
            return False

        central_ray_index = len(self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]) // 2

        timeout = 10  # seconds
        start_time = asyncio.get_event_loop().time()
        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"Movement attempt {attempt}")

            # refresh
            flower_indices = [
                idx for idx, ray in enumerate(zip(*self.rc_sensor.sensor_rays))
                if ray[Sensors.RayCastSensor.HIT]
                   and ray[Sensors.RayCastSensor.OBJECT_INFO].get("tag") == "AlienFlower"
            ]
            if not flower_indices:
                lost_count += 1
                if lost_count <= self.lost_tolerance:
                    print(f"Transient loss ({lost_count}/{self.lost_tolerance}), moving forward to reacquire")
                    await self.a_agent.send_message("action", "mf")
                    await asyncio.sleep(0.5)
                    continue
                else:
                    print("Flower lost, stopping pursuit")
                    return False
            else:
                lost_count = 0

            # pick median flower
            flower_ray_index = int(sorted(flower_indices)[len(flower_indices)//2])
            print(f"Flower(s) at rays {flower_indices}, targeting ray {flower_ray_index}")

            # align & move
            if flower_ray_index < central_ray_index:
                print("Turn left toward flower")
                await self.a_agent.send_message("action", "tl")
                await asyncio.sleep(self.TURN_TIME)
                await self.a_agent.send_message("action", "nt")
            elif flower_ray_index > central_ray_index:
                print("Turn right toward flower")
                await self.a_agent.send_message("action", "tr")
                await asyncio.sleep(self.TURN_TIME)
                await self.a_agent.send_message("action", "nt")
            else:
                print("Flower roughly ahead, no turn")

            # always advance
            await self.a_agent.send_message("action", "mf")
            await asyncio.sleep(self.FORWARD_TIME)

            # check collection
            current = sum(
                item["amount"]
                for item in self.i_state.myInventoryList
                if item["name"] == "AlienFlower"
            )
            if current > self.initial_flower_count:
                print("Flower collected successfully")
                return True

            # timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                print("Timeout: Flower not collected")
                return False

        print("Failed to collect flower after max attempts")
        return False

class ReturnToBase:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.i_state = a_agent.i_state

    async def run(self):
        print("Returning to Base")
        await self.a_agent.send_message("action", "walk_to,Base")
        await asyncio.sleep(0.5)
        
        print("Unloading flowers at Base")
        await self.a_agent.send_message("action", "leave,AlienFlower,2")
        
        return True

class CheckInventoryFull:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.i_state = a_agent.i_state

    def run(self):  # Now synchronous
        flower_count = sum(item["amount"] for item in self.i_state.myInventoryList if item["name"] == "AlienFlower")
        return flower_count >= 2

class DetectAstronaut:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.sensor = a_agent.rc_sensor

    def run(self) -> bool:
        # Any ray detecting tag "Astronaut"?
        for info in self.sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]:
            if info and info.get("tag") == "Astronaut":
                return True
        return False

class FollowAstronaut:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.sensor = a_agent.rc_sensor
        # tuning durations
        self.TURN_TIME = 0.2
        self.FORWARD_TIME = 0.5

    async def run(self) -> bool:
        # Locate all rays that see the Astronaut
        hits = self.sensor.sensor_rays[Sensors.RayCastSensor.HIT]
        infos = self.sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]
        indices = [
            i for i, info in enumerate(infos)
            if hits[i] and info and info.get("tag") == "Astronaut"
        ]
        if not indices:
            return False
        # pick median
        mid_ray = len(hits) // 2
        target = sorted(indices)[len(indices)//2]
        # turn toward her
        if target < mid_ray:
            await self.a_agent.send_message("action", "tl")
            await asyncio.sleep(self.TURN_TIME)
            await self.a_agent.send_message("action", "nt")
        elif target > mid_ray:
            await self.a_agent.send_message("action", "tr")
            await asyncio.sleep(self.TURN_TIME)
            await self.a_agent.send_message("action", "nt")
        # then move forward
        await self.a_agent.send_message("action", "mf")
        await asyncio.sleep(self.FORWARD_TIME)
        return True

class BiteAstronaut:
    def __init__(self, a_agent):
        self.a_agent = a_agent

    async def run(self) -> bool:
        # send bite action once
        await self.a_agent.send_message("action", "bite")
        # allow the engine to stun the astronaut
        await asyncio.sleep(0.1)
        return True


class MoveAway:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.BACKUP_TIME = 0.5   # how long to back away
        self.SAFETY_TIME = 1.0   # forward “recovery” time
        self.ROTATE_TIME = 0.5   # how long to spend turning

    async def run(self) -> bool:
        # 1) Back away
        await self.a_agent.send_message("action", "mb")
        await asyncio.sleep(self.BACKUP_TIME)

        # 2) Spin to give the Astronaut space
        direction = random.choice(["tr", "tl"])
        print(f"MoveAway: rotating {direction} for space")
        await self.a_agent.send_message("action", direction)
        await asyncio.sleep(self.ROTATE_TIME)
        await self.a_agent.send_message("action", "nt")

        # 3) Advance forward a bit
        await self.a_agent.send_message("action", "mf")
        await asyncio.sleep(self.SAFETY_TIME)

        return True