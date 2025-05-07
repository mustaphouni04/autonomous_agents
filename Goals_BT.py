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
    def __init__(self, a_agent, distance_threshold: float = 1.0):
        self.a_agent = a_agent
        self.rc_sensor = a_agent.rc_sensor
        self.threshold = distance_threshold

    async def run(self) -> bool:
        # Pair hits with their object info
        hits = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]
        infos = self.rc_sensor.sensor_rays[Sensors.RayCastSensor.OBJECT_INFO]

        # Build a mask of True only for Rock/Wall hits within threshold
        close_mask = []
        for hit, info in zip(hits, infos):
            if hit and info and info.get("tag") in ("Rock", "Wall") and info.get("distance", float("inf")) < self.threshold:
                close_mask.append(True)
            else:
                close_mask.append(False)

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
        self.initial_flower_count = sum(item["amount"] for item in self.i_state.myInventoryList if item["name"] == "AlienFlower")
        self.lost_tolerance = 2   # how many consecutive “no-detections” we tolerate

    async def run(self):
        print("Starting MoveToFlower")
        lost_count = 0
       # Detect all flowers and pick a central direction (median ray)
        flower_indices = [
            idx for idx, ray in enumerate(zip(*self.rc_sensor.sensor_rays))
            if ray[Sensors.RayCastSensor.HIT]
               and ray[Sensors.RayCastSensor.OBJECT_INFO].get('tag') == 'AlienFlower'
        ]
        if not flower_indices:
            print("No flower detected")
            return False
        flower_ray_index = int(sorted(flower_indices)[len(flower_indices) // 2])
        print(f"Flower(s) detected at rays {flower_indices}, targeting ray {flower_ray_index}")

        if flower_ray_index is None:
            print("No flower detected")
            return False

        # Determine central ray index (assuming odd number of rays, e.g., 5 rays: center is 2)
        central_ray_index = len(self.rc_sensor.sensor_rays[Sensors.RayCastSensor.HIT]) // 2

        # Move toward flower
        timeout = 10  # seconds
        start_time = asyncio.get_event_loop().time()
        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"Movement attempt {attempt}")

            # Refresh flower list & re-pick median
            flower_indices = [
                idx for idx, ray in enumerate(zip(*self.rc_sensor.sensor_rays))
                if ray[Sensors.RayCastSensor.HIT]
                   and ray[Sensors.RayCastSensor.OBJECT_INFO].get('tag') == 'AlienFlower'
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

            flower_ray_index = int(sorted(flower_indices)[len(flower_indices) // 2])

            # Partial alignment + forward momentum:
            if flower_ray_index < central_ray_index:
                print("Flower detected on left, turn-left & move forward")
                await self.a_agent.send_message("action", "tl,10")
            elif flower_ray_index > central_ray_index:
                print("Flower detected on right, turn-right & move forward")
                await self.a_agent.send_message("action", "tr,10")
            else:
                print("Flower roughly ahead, move forward")
                # no turn needed
            # in all cases, advance a bit toward the flower
            await asyncio.sleep(0.2)                # give turn a moment
            await self.a_agent.send_message("action", "mf")
            await asyncio.sleep(0.8)                # forward hop toward target 

            # Check if flower collected
            current_flower_count = sum(item["amount"] for item in self.i_state.myInventoryList if item["name"] == "AlienFlower")
            if current_flower_count > self.initial_flower_count:
                print("Flower collected successfully")
                return True

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                print("Timeout: Flower not collected")
                return False

            await asyncio.sleep(0.3)

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
        """
        if self.i_state.currentNamedLoc != "Base":
            print("Teleport failed: Unable to reach Base")
            return False
        """
        print("Unloading flowers at Base")
        await self.a_agent.send_message("action", "leave,AlienFlower,2")
        # Verify inventory
        """
        flower_count = next(
            (item['amount'] for item in self.i_state.myInventoryList if item['name'] == 'AlienFlower'),
            0
        )
        if flower_count > 0:
            print(f"Warning: {flower_count} flowers remain in inventory after unload")
            self.i_state.myInventoryList = [item for item in self.i_state.myInventoryList if item["name"] != "AlienFlower"]
        # Move away from base
        print("Moving away from Base to clear area")
        await self.a_agent.send_message("action", "mf")
        await asyncio.sleep(2)
        await self.a_agent.send_message("action", random.choice(["tr,90", "tl,90"]))
        await asyncio.sleep(0.5)
        print("Resuming flower hunt")
        """
        return True

class CheckInventoryFull:
    def __init__(self, a_agent):
        self.a_agent = a_agent
        self.i_state = a_agent.i_state

    def run(self):  # Now synchronous
        flower_count = sum(item["amount"] for item in self.i_state.myInventoryList if item["name"] == "AlienFlower")
        return flower_count >= 2


