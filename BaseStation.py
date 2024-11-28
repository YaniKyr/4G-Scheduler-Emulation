import numpy as np
from collections import deque
from typing import List
import math
import time

import user as User

class BaseStation:
    def __init__(self, num_users: int, total_rbs: int):

        self.users: List[User.User] = [User.User(i,  self.generate_traffic_type(), self.generate_priority_level(), np.random.uniform(1, 1000)) for i in range(num_users)]
        self.total_rbs =self.current_rbs= total_rbs  # Finite number of resource blocks
        self.total_throughput = 0
        self.fairness_index = 0
        self.a = 1
        self.RBCapacity = 150  # Capacity of each RB in Kbps
        self.queue = deque(self.users)

    def generate_traffic_type(self) -> str:
        """Randomly assign a traffic type to each user."""
        traffic_types = ["video_streaming", "web_browsing", "voice_call"]
        probabilities = [0.05, 0.05, 0.90]  # 75% voice call, 15% web browsing, 10% video streaming
        return np.random.choice(traffic_types, p=probabilities)


    def generate_priority_level(self) -> int:
        """Assign a priority level (1-3) to each user."""
        return np.random.randint(1, 4)

    def calculate_available_resources(self) -> int:
        """Return the total number of available resource blocks."""
        return self.total_rbs

    def pfPriority(self):
        return sorted(
            self.queue,
            key=lambda user: (
                # Instantaneous rate (channel quality)
                user.generate_channel_quality() 
                / 
                # Average throughput raised to power α (default 1)
                ((user.average_throughput + 1e-9) ** self.a)
            ),
            reverse=True
        )

    def reqRBsFormula(self,Cuser,queue):
        if Cuser.rac == 0:
            return 0
        rbsum = sum(user.minimumRBS() for user in queue)
        
        allocation = math.ceil(1/((rbsum+ 1e-10)/self.current_rbs))
        return min(Cuser.totalRbs,  max(Cuser.minimumRBS() ,Cuser.minimumRBS()*allocation))
         
       
    def round_robin_scheduler(self):
        """Distribute available resource blocks in a round-robin fashion."""
        for _ in range(len(self.queue)):
            user = self.queue.popleft()

            if self.current_rbs <=1:
                user.queue_delay += 1
                self.queue.append(user)
                break


            # Delay control
            if user.current_delay > 0:
                user.current_delay -= 1
                #print(f"User {user.id} is delayed by 1 TTI. Remaining Delay: {user.current_delay}")
                self.queue.append(user)
                continue

            required_rbs = self.reqRBsFormula(user, self.queue)
            allocated_rbs = min(self.current_rbs, required_rbs)
            if self.current_rbs < allocated_rbs:
                # User is not serviced this TTI
                if user.current_delay == 0 and not (user.traffic_type == "web_browsing" and user.rac == 0):
                    user.queue_delay += 1
                    print(f"User {user.id} is delayed by 1 TTI (Queue Delay Incremented). Total Queue Delay: {user.queue_delay}")
                self.queue.append(user)
                continue

            
            self.current_rbs -= allocated_rbs
            
            user.throughput += allocated_rbs * self.RBCapacity * user.generate_channel_quality()
            user.throughput = min(user.throughput, user.InitRac)
            user.rac = max(0, math.ceil(allocated_rbs * self.RBCapacity - user.rac))

            user.totalRbs -= allocated_rbs
            user.allocated_rbs += allocated_rbs

            #print(f"User {user.id} is serviced. Allocated {allocated_rbs} RBs. Remaining RAC: {user.rac}")
            if user.rac > 0:
                self.queue.append(user)

        time.sleep(1 / 2000)  # Simulate TTI duration

        if not self.queue:
            return True

 
    def proportional_fair_scheduler(self):
        """Distribute available resource blocks based on proportional fairness."""
        self.current_rbs = self.calculate_available_resources()
        self.queue = deque(self.pfPriority())

        for _ in range(len(self.queue)):
            user = self.queue.popleft()
            if self.current_rbs <=1:
                user.queue_delay += 1
                self.queue.append(user)
                break

            if user.current_delay > 0:
                user.current_delay -= 1
                self.queue.append(user)
                continue

            required_rbs = self.reqRBsFormula(user, self.queue)
            allocated_rbs = min(self.current_rbs, required_rbs)
            if self.current_rbs < allocated_rbs:
                # User is not serviced this TTI
                if user.current_delay == 0 and not (user.traffic_type == "web_browsing" and user.rac == 0):
                    user.queue_delay += 1
                self.queue.append(user)
                continue

            self.current_rbs -= allocated_rbs
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))

            user.throughput += (allocated_rbs * self.RBCapacity * user.generate_channel_quality())
            
            user.totalRbs -= allocated_rbs
            user.allocated_rbs += allocated_rbs


            smoothing_factor = 0.1
            user.average_throughput = (1 - smoothing_factor) * user.average_throughput + smoothing_factor * user.throughput

            if user.rac > 0:
                self.queue.append(user)

            

        time.sleep(1 / 2000)  # Simulate TTI duration
        if not self.queue:
            return True
        

    def update_user_properties(self):
        """Update each user's channel quality each time step."""
        for user in self.users:
            user.rac = user.InitRac
            user.totalRbs = math.ceil(user.rac/self.RBCapacity)
            user.allocated_rbs = 0
            user.throughput = 0
            self.queue = deque(self.users)
            
    def init_user_properties(self):
        """Initialize each user's values."""
        for user in self.users:
            user.generate_channel_quality()
            user.rac = user.generate_rac()
            user.InitRac = user.rac
            user.totalRbs = math.ceil(user.rac/self.RBCapacity)
            #print('User:',user.id,'RAC:',user.rac,'Total Rbs:',user.totalRbs)




