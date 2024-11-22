import numpy as np
from collections import deque
from typing import List
import math
import time
from tabulate import tabulate
import matplotlib.pyplot as plt
class User():
    def __init__(self, id: int, traffic_type: str, priority_level: int, user_delay: int):
        self.delay = self.current_delay = user_delay
        self.id = id
        self.traffic_type = traffic_type
        self.priority_level = priority_level
        self.throughput = 0
        self.rac = 0  # Resource allocation demand (RAC)
        self.average_throughput = 0  # Initialize average throughput
        self.allocated_rbs = 0
        self.total_rbs = 0
        self.instantaneous_rate = 1
        self.InitRac = 0
        self.queue_delay = 0  


    def generate_channel_quality(self) -> float:
        """Randomly generate initial channel quality for users."""
        return np.random.uniform(0.1, 1.0)

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

        self.users: List[User] = [User(i,  self.generate_traffic_type(), self.generate_priority_level(), np.random.uniform(1, 1000)) for i in range(num_users)]
        self.total_rbs =self.current_rbs= total_rbs  # Finite number of resource blocks
        self.total_throughput = 0
        self.fairness_index = 0
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
        return min(Cuser.totalRbs,  max(Cuser.minimumRBS() ,Cuser.minimumRBS()*allocation))
         
       
    def round_robin_scheduler(self):
        """Distribute available resource blocks in a round-robin fashion."""
        
        count = 0 
        for _ in range(len(self.queue)):
            
            
            if self.current_rbs <= 1:
                #print("OOSpace")
                break
            user = self.queue.popleft()
            
            if user.current_delay > 0:
                user.current_delay -= 1
                self.queue.append(user)
                continue
            
            required_rbs = self.reqRBsFormula(user,self.queue)
            
            if required_rbs == 0 or self.current_rbs <= 0:
                # User is not serviced this TTI
                # Increment queue_delay only for non-web_browsing users or when RAC > 0
                if user.current_delay == 0 and not (user.traffic_type == "web_browsing" and user.rac == 0):
                    user.queue_delay += 1
                self.queue.append(user)
                continue


            
            
            allocated_rbs = min(self.current_rbs, required_rbs)
            user.allocated_rbs += allocated_rbs
            user.totalRbs -= allocated_rbs             
            
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))
            user.throughput += allocated_rbs * self.RBCapacity * user.generate_channel_quality() # Update throughput based on allocated RBs
            self.current_rbs -= allocated_rbs
              # Sleep for TTI duration (1ms per 2 RBs)

            #print(f"User {user.id} has been allocated {user.allocated_rbs} RBs, Remaining RAC: {user.rac}, with required RBs: {required_rbs}, and totalRbs: {available_rbs}")
            if user.rac> 0:   
                self.queue.append(user)

        #print(f"Queue: {[user.id for user in self.queue]}")
        time.sleep(1/2000)

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
            if user.current_delay > 0:
                user.current_delay -= 1
                self.queue.append(user)
                continue
            # Calculate required and allocated RBs
            required_rbs = self.reqRBsFormula(user,self.queue)
            allocated_rbs = min(required_rbs, self.current_rbs)

            # Decrease available RBs
            self.current_rbs -= allocated_rbs

            # Update remaining RAC for the user after allocation
            user.rac = max(0, math.ceil(user.rac - allocated_rbs * self.RBCapacity))

            if allocated_rbs > 0:
                # Calculate the instantaneous achievable rate
                user.instantaneous_rate = allocated_rbs * self.RBCapacity * user.generate_channel_quality()
                user.throughput += user.instantaneous_rate
                user.totalRbs -= allocated_rbs
                user.allocated_rbs += allocated_rbs

                # Update average throughput with a smoothing factor (0.1)
                smoothing_factor = 1
                user.average_throughput = (1 - smoothing_factor) * user.average_throughput + smoothing_factor * user.instantaneous_rate

            # If RAC is not fully satisfied and we still have resources, re-queue the user
            if user.rac > 0 :
                self.queue.append(user)

            # Check if available RBs are nearly exhausted and print "OOSpace" if so
            if self.current_rbs <= 1:
                #print("OOSpace")
                break
            
            # Simulate TTI duration
            time.sleep(1 / 2000)  # Example: 1ms per 2 RBs
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
            #print('User:',user.id,'RAC:',user.rac,'Total Rbs:',user.totalRbs)


    def calculate_fairness_index(self):
        """Calculate the fairness index using Jain's fairness index formula."""
        throughputs = [user.throughput for user in self.users]
        squared_sum = sum(throughput ** 2 for throughput in throughputs)
        n = len(self.users)
        fairness_index = (sum(throughputs) ** 2) / (n * squared_sum) if squared_sum != 0 else 0
        return fairness_index
    
    def calculate_performance_metrics(self):
        """Calculate total throughput and fairness index at the end of each time step."""
        self.total_throughput = sum(user.throughput for user in self.users)
        self.fairness_index = self.calculate_fairness_index()
    def print_results(self):
        print(f"Total Throughput: {base_station.total_throughput:.2f} Kbps")
        print(f"Fairness Index: {base_station.fairness_index:.4f}")
        headers = ["ID", "Traffic Type",  "Throughput", "Allocated RBs", "Initial Rac", "Queue Delay (TTIs)"]
        data = [[user.id, user.traffic_type, f"{user.throughput:.2f}", user.allocated_rbs, f"{user.InitRac:.2f}", user.queue_delay] for user in self.users]
        print(tabulate(data, headers=headers, tablefmt="grid"))


    def run_simulation(self, num_ttis: int, verbose: bool = False):
        """Run the network simulation for a specified number of TTIs."""
        self.init_user_properties()
        count=0

        for _ in range(num_ttis):
           
            self.current_rbs = self.total_rbs
            count+=1
            
            if self.round_robin_scheduler():
                break
        self.calculate_performance_metrics()
        if not verbose:
            print('\nRound Robin')
            print("Total TTIs: ",count)
            
            self.print_results() 
        rr_throughput = self.fairness_index



        count=0
        self.update_user_properties()
        for _ in range(num_ttis):
            
            self.current_rbs = self.total_rbs
            
            count+=1
            if self.proportional_fair_scheduler():
                break
        self.calculate_performance_metrics()
        if not verbose:
            print('\nPropotional Fair')
            print("Total TTIs: ",count)
            
            
            self.print_results()
        return rr_throughput, self.fairness_index

# Example usage
num_users = 10
total_rbs = 100  # Total number of Resource Blocks
num_ttis = 10000  # Number of Transmission Time Intervals to simulate
rr_throughput = []
pf_throughput = []
index = []
for i in range(1,100):
    base_station = BaseStation(num_users=num_users, total_rbs=total_rbs)
    rr,pr =base_station.run_simulation(num_ttis=num_ttis, verbose= True)
    print(rr)
    rr_throughput.append(rr)
    index.append(i)
    pf_throughput.append(pr)
    num_users = 10* i

plt.scatter(index, rr_throughput, label='Round Robin Throughput', color='blue')
plt.scatter(index, pf_throughput, label='Proportional Fair Throughput', color='red')
plt.xlabel('Simulation Run')
plt.ylabel('Fairness Index')
plt.title('Fairness Index Comparison')
plt.legend()
plt.show()