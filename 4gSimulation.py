import numpy as np
from collections import deque
from typing import List
import math
import time
import threading

class User(threading.Thread):
    def __init__(self, id: int, traffic_type: str, channel_quality: float, priority_level: int):
        super().__init__()
        self.id = id
        self.traffic_type = traffic_type
        self.channel_quality = channel_quality
        self.priority_level = priority_level
        self.throughput = 0
        self.rac = 0  # Resource allocation demand (RAC)
        self.allocated_rbs = self.minimumRBS(traffic_type)
        self.InitRac=0
        self.totalRbs = 0
    def generate_channel_quality(self):
        """Simulate variations in channel quality (e.g., fading) for each user."""
        self.channel_quality = max(0, self.channel_quality + np.random.normal(0, 2))

    def generate_rac(self) -> float:
        """Generate the resource allocation demand based on traffic type."""
        match self.traffic_type:
            case "video_streaming":
                return np.random.uniform(3000, 11000)  # High, constant bandwidth requirement
            case "web_browsing":    
                return np.random.exponential(1000) if np.random.rand() < 0.2 else 0  # Sporadic bursts
            case "voice_call":
                return np.random.uniform(100, 200)  # Constant, low bandwidth requirement
            case _:
                raise ValueError(f"Invalid traffic type: {self.traffic_type}")
    def minimumRBS(self,traffic_type):

        match traffic_type:
            case "video_streaming":
                return 20
            case "web_browsing":
                return 5
            case "voice_call":
                return 2
class BaseStation:
    def __init__(self, num_users: int, total_rbs: int):
        self.users: List[User] = [User(i, self.generate_traffic_type(), self.generate_channel_quality(), self.generate_priority_level()) for i in range(num_users)]
        self.total_rbs =self.current_rbs= total_rbs  # Finite number of resource blocks
        self.RBCapacity = 150  # Capacity of each RB in Kbps
        self.queue = deque(self.users)

    def generate_traffic_type(self) -> str:
        """Randomly assign a traffic type to each user."""
        traffic_types = ["video_streaming", "web_browsing", "voice_call"]
        return np.random.choice(traffic_types)

    def generate_channel_quality(self) -> float:
        """Randomly generate initial channel quality for users."""
        return np.random.uniform(0.1, 1.0)

    def generate_priority_level(self) -> int:
        """Assign a priority level (1-3) to each user."""
        return np.random.randint(1, 4)

    def calculate_available_resources(self) -> int:
        """Return the total number of available resource blocks."""
        return self.total_rbs

    def reqRBsFormula(self,Cuser,queue):
        if Cuser.rac == 0:
            return 0
        
        sum = 0
        for user in queue:
            #print(user.id)
            sum +=user.allocated_rbs
            
        allocation = math.ceil(1/(sum/self.current_rbs))
        if allocation >=1:
            return Cuser.allocated_rbs*allocation
        else:
            print("Fond Else") 
       
    def round_robin_scheduler(self):
        """Distribute available resource blocks in a round-robin fashion."""
        
        count = 0 
        for _ in range(len(self.queue)):
            
            
            if self.current_rbs <= 1:
                print("OOSpace")
                break
            user = self.queue.popleft()
            required_rbs = self.reqRBsFormula(user,self.queue)
            
            allocated_rbs = min(self.current_rbs, required_rbs)
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))
            
            print(f"User {user.id} requires {allocated_rbs} RBs")
            user.totalRbs += allocated_rbs
            user.throughput += allocated_rbs * self.RBCapacity  # Update throughput based on allocated RBs
            self.current_rbs -= allocated_rbs
            
            
              # Sleep for TTI duration (1ms per 2 RBs)

            #print(f"User {user.id} has been allocated {user.allocated_rbs} RBs, Remaining RAC: {user.rac}, with required RBs: {required_rbs}, and totalRbs: {available_rbs}")
            if allocated_rbs> 0:   
                self.queue.append(user)
        #print(f"Queue: {[user.id for user in self.queue]}")
        time.sleep(1/1000)

        if not self.queue:
           # print("All users have finished their RA")
            return True
 

    def update_user_properties(self):
        """Update each user's channel quality and RAC at each time step."""
        for user in self.users:
            user.generate_channel_quality()
            user.rac = user.generate_rac()
            user.InitRac = user.rac


    def calculate_fairness_index(self):
        """Calculate the fairness index using Jain's fairness index formula."""
        throughputs = [user.throughput for user in self.users]
        squared_sum = sum(throughput ** 2 for throughput in throughputs)
        n = len(self.users)
        fairness_index = (sum(throughputs) ** 2) / (n * squared_sum) if squared_sum != 0 else 0
        return fairness_index

    def run_simulation(self, num_ttis: int):
        """Run the network simulation for a specified number of TTIs."""
        self.update_user_properties()
        
        for _ in range(num_ttis):
            # Update user properties (RAC, channel qualrandom.rarity)
            
            self.current_rbs = self.total_rbs
            # Reset allocated RBs for each TTI
            

            # Allocate resources using the scheduling algorithms
            flag = self.round_robin_scheduler()  # Allocate resources via Round-Robin
            if flag: break
            #self.proportional_fair_scheduler()  # Allocate resources via Proportional Fair

            # Collect performance metrics
            #self.calculate_performance_metrics()
def calculate_performance_metrics(base_station):
    """Calculate total throughput and fairness index at the end of each time step."""
    total_throughput = sum(user.throughput for user in base_station.users)
    fairness_index = base_station.calculate_fairness_index()
    print(f"Total Throughput: {total_throughput:.2f} Kbps")
    print(f"Fairness Index: {fairness_index:.4f}")

# Example usage
num_users = 10

total_rbs = 100  # Total number of Resource Blocks
num_ttis = 1000  # Number of Transmission Time Intervals to simulate

base_station = BaseStation(num_users=num_users, total_rbs=total_rbs)
base_station.run_simulation(num_ttis=num_ttis)

# Print the performance metrics
calculate_performance_metrics(base_station)

# Print individual user statistics
for user in base_station.users:
    print(f"User {user.id} - Traffic Type: {user.traffic_type}, "
          f"Throughput: {user.throughput:.2f} Kbps, "
          f"Allocated RBs: {user.totalRbs}, "
          f'With Initial RAC: {user.InitRac}',
          f'Leftover RAC: {user.rac}')