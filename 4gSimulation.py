import numpy as np
from collections import deque
from typing import List
import math
import time

class User():
    def __init__(self, id: int, traffic_type: str, channel_quality: float, priority_level: int):
        super().__init__()
        self.id = id
        self.traffic_type = traffic_type
        self.channel_quality = channel_quality
        self.priority_level = priority_level
        self.throughput = 0
        self.rac = 0  # Resource allocation demand (RAC)
        self.target_rac = self.generate_rac()  # Initialize target RAC
        self.average_throughput = 0  # Initialize average throughput
        self.allocated_rbs = 0
        self.total_rbs = 0
        self.instantaneous_rate = 1
        self.InitRac = 0
    def generate_channel_quality(self):
        """Simulate variations in channel quality (e.g., fading) for each user."""
        self.channel_quality = max(0, self.channel_quality + np.random.normal(0, 2))

    def generate_rac(self) -> float:
        """Generate the resource allocation demand based on traffic type."""
        match self.traffic_type:
            case "video_streaming":
                return np.random.uniform(8000, 11000)  # High, constant bandwidth requirement
            case "web_browsing":    
                return np.random.exponential(1000) if np.random.rand() < 0.2 else 0  # Sporadic bursts
            case "voice_call":
                return np.random.uniform(100, 200)  # Constant, low bandwidth requirement
            case _:
                raise ValueError(f"Invalid traffic type: {self.traffic_type}")

    def minimumRBS(self):

        match self.traffic_type:
            case "video_streaming":
                return 20
            case "web_browsing":
                return 5
            case "voice_call":
                return 2

class BaseStation:
    def __init__(self, num_users: int, total_rbs: int):
        self.users: List[User] = [User(i + 100, self.generate_traffic_type(), self.generate_channel_quality(), self.generate_priority_level()) for i in range(num_users)]
        self.total_rbs =self.current_rbs= total_rbs  # Finite number of resource blocks
        self.total_throughput = 0
        self.fairness_index = 0
        self.RBCapacity = 150  # Capacity of each RB in Kbps
        self.queue = deque(self.users)
        

    def generate_traffic_type(self) -> str:
        """Randomly assign a traffic type to each user."""
        traffic_types = ["video_streaming", "web_browsing", "voice_call"]
        probabilities = [0.75, 0.15, 0.10]  # 75% web browsing, 15% voice call, 10% video streaming
        return np.random.choice(traffic_types, p=probabilities)

    def generate_channel_quality(self) -> float:
        """Randomly generate initial channel quality for users."""
        return np.random.uniform(0.1, 1.0)

    def generate_priority_level(self) -> int:
        """Assign a priority level (1-3) to each user."""
        return np.random.randint(1, 4)

    def calculate_available_resources(self) -> int:
        """Return the total number of available resource blocks."""
        return self.total_rbs
    
    def pfPriority(self):
        return  sorted(
            self.queue,
            key=lambda user: (user.instantaneous_rate) / (user.average_throughput + 1e-9),
            reverse=True
        )
    def reqRBsFormula(self,Cuser,queue):
        if Cuser.rac == 0:
            return 0
        
        sum = 0
        for user in queue:
            #print(user.id)
            sum +=user.minimumRBS()
            
        allocation = math.ceil(1/((sum+ 1e-10)/self.current_rbs))
        return min(Cuser.totalRbs,  Cuser.minimumRBS()*allocation)
         
       
    def round_robin_scheduler(self):
        """Distribute available resource blocks in a round-robin fashion."""
        
        count = 0 
        for _ in range(len(self.queue)):
            
            
            if self.current_rbs <= 1:
                break
            user = self.queue.popleft()
            
            
            required_rbs = self.reqRBsFormula(user,self.queue)
            
            allocated_rbs = min(self.current_rbs, required_rbs)
            
            user.total_rbs -= allocated_rbs 
            
            user.allocated_rbs +=allocated_rbs 
            
            
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))
            
            if allocated_rbs == 0:
                break
            
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
        
    def proportional_fair_scheduler(self):
        """Distribute available resource blocks based on proportional fairness`."""

        # Calculate available resources
        self.current_rbs = self.calculate_available_resources()

        # Sort users based on R/T, where R is the achievable rate and T is average throughput
        # Define this based on your logic
        
        self.queue = deque(self.pfPriority())
        

        for  _ in range(len(self.queue)) :
            if self.current_rbs <= 0:
                break
            # Pop the user from the left of the queue
            
            user = self.queue.popleft()
            # Calculate required and allocated RBs
            required_rbs = self.reqRBsFormula(user,self.queue)
            allocated_rbs = min(required_rbs, self.current_rbs)

            # Decrease available RBs
            self.current_rbs -= allocated_rbs

            # Update remaining RAC for the user after allocation
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))

            if allocated_rbs > 0:
                # Calculate the instantaneous achievable rate
                user.instantaneous_rate = allocated_rbs * self.RBCapacity * user.channel_quality
                user.throughput += user.instantaneous_rate
                user.totalRbs -= allocated_rbs
                user.allocated_rbs += allocated_rbs

                # Update average throughput with a smoothing factor (0.1)
                smoothing_factor = 0.1
                user.average_throughput = (1 - smoothing_factor) * user.average_throughput + smoothing_factor * user.instantaneous_rate

            # If RAC is not fully satisfied and we still have resources, re-queue the user
            if user.rac > 0 and self.current_rbs > 0:
                self.queue.append(user)

            # Check if available RBs are nearly exhausted and print "OOSpace" if so
            if self.current_rbs <= 1:
                print("OOSpace")
                break
            
            # Simulate TTI duration
            time.sleep(allocated_rbs / 2 / 1000)  # Example: 1ms per 2 RBs
        if not self.queue:
            return True
        # After resource allocation, calculate performance metrics if needed
        




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
            print('User:',user.id,'RAC:',user.rac,'Total Rbs:',user.totalRbs)

    def calculate_performance_metrics(self):
        """Calculate total throughput and fairness index at the end of each time step."""
        self.total_throughput = sum(user.throughput for user in self.users)
        self.fairness_index = self.calculate_fairness_index()

    def calculate_fairness_index(self):
        """Calculate the fairness index using Jain's fairness index formula."""
        throughputs = [user.throughput for user in self.users]
        squared_sum = sum(throughput ** 2 for throughput in throughputs)
        n = len(self.users)
        fairness_index = (sum(throughputs) ** 2) / (n * squared_sum) if squared_sum != 0 else 0
        return fairness_index

    def run_simulation(self, num_ttis: int):
        """Run the network simulation for a specified number of TTIs."""
        self.init_user_properties()
        self.update_user_properties()
        count =0
        for _ in range(num_ttis):
            self.current_rbs = self.total_rbs
            if self.round_robin_scheduler():
                break
            count +=1
        print('Round Robin\n')
        print("Total TTIs: ",count)
        self.calculate_performance_metrics()
        PrintResults()
      

def PrintResults():
    print(f"Total Throughput: {base_station.total_throughput:.2f} Kbps")
    print(f"Fairness Index: {base_station.fairness_index:.4f}")

    # Print individual user statistics
    for user in base_station.users:
        print(f"User {user.id} - Traffic Type: {user.traffic_type}, "
            f"Throughput: {user.throughput:.2f} Kbps, "
            f"Allocated RBs: {user.allocated_rbs},"
            f"Init Rac: {user.InitRac}")


# Example usage
num_users = 10
total_rbs = 100  # Total number of Resource Blocks
num_ttis = 1000  # Number of Transmission Time Intervals to simulate

base_station = BaseStation(num_users=num_users, total_rbs=total_rbs)
base_station.run_simulation(num_ttis=num_ttis)

# Print the performance metrics


#test

# def reqRBsFormula(self, Cuser, queue):
#         """Calculate the number of required RBs for a user, considering minimum demand and channel quality scaling."""
#         if Cuser.rac == 0:
#             return 0  # If no RAC is required, no RBs are needed.

#         # Calculate the sum of minimum RBs needed for all users in the queue.
#         total_minimum_rbs = sum(user.minimumRBS() for user in queue)
        
#         # Use a scaling factor for channel quality: users with better quality are favored.
#         quality_factor = max(0.1, Cuser.channel_quality)
        
#         # Calculate the fair share of RBs based on the minimum requirement and channel quality.
#         allocation = math.ceil((self.current_rbs * Cuser.minimumRBS() * quality_factor) / (total_minimum_rbs + 1e-10))
        
#         # Limit allocation to the user's total required RBs.
#         return min(allocation, Cuser.totalRbs)


# #ΒΗΜΑ 2
# if self.current_rbs > 0:
#         total_demand = sum(user.dynamicDemand() for user in users_sorted)  # Calculate total dynamic demand
#         for user in users_sorted:
#             if self.current_rbs <= 0:
#                 break
            
#             # Determine the portion of RBs to allocate based on traffic type
#             portion = self.get_allocation_portion(user.traffic_type)  # This can be a predefined value
#             fair_allocation = portion * (user.dynamicDemand() / total_demand) if total_demand > 0 else 0
            
#             # Allocate fair allocation up to the remaining RBs
#             allocated_rbs = min(math.ceil(fair_allocation), self.current_rbs)
#             if allocated_rbs > 0:
#                 user.allocated_rbs += allocated_rbs
#                 user.totalRbs -= allocated_rbs
#                 user.rac -= allocated_rbs * self.RBCapacity
#                 self.current_rbs -= allocated_rbs
