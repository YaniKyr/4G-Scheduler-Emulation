
from tabulate import tabulate
import matplotlib.pyplot as plt
import  BaseStation as Bs

def calculate_fairness_index(base_station):
    """Calculate the fairness index using Jain's fairness index formula."""
    throughputs = [user.throughput for user in base_station.users]
    squared_sum = sum(throughput ** 2 for throughput in throughputs)
    n = len(base_station.users)
    fairness_index = (sum(throughputs) ** 2) / (n * squared_sum) if squared_sum != 0 else 0
    return fairness_index

def calculate_performance_metrics(base_station):
    """Calculate total throughput and fairness index at the end of each time step."""
    base_station.total_throughput = sum(user.throughput for user in base_station.users)
    base_station.fairness_index = calculate_fairness_index(base_station)
    
def print_results(base_station):
    print(f"Total Throughput: {base_station.total_throughput:.2f} Kbps")
    print(f"Fairness Index: {base_station.fairness_index:.4f}")
    headers = ["ID", "Traffic Type",  "Throughput", "Allocated RBs", "Initial Rac", "Queue Delay (TTIs)"]
    data = [[user.id, user.traffic_type, f"{user.throughput:.2f}", user.allocated_rbs, f"{user.InitRac:.2f}", user.queue_delay] for user in base_station.users]
    print(tabulate(data, headers=headers, tablefmt="grid"))

def results(base_station, num_ttis: int,scheduler,verbose: bool = False):
    print(f"\n--- {scheduler} Scheduling ---")
    count = 0
    for tti in range(num_ttis):
        base_station.current_rbs = base_station.total_rbs
        count += 1
        #print(f"\nTTI {tti + 1}:")
        #for user in base_station.users:
        #    print(f"User {user.id}: Queue Delay: {user.queue_delay} TTIs")
        if scheduler == 'round_robin':
            if base_station.round_robin_scheduler():
                break
        elif scheduler == 'proportional_fair':
            if base_station.proportional_fair_scheduler():
                break
        
    calculate_performance_metrics(base_station)

    # Calculate total delay for RR
    rr_total_delay = sum(user.queue_delay for user in base_station.users)
    print(f"\nTotal TTIs (Round Robin): {count}")
    print(f"Total Queue Delay (Round Robin): {rr_total_delay} TTIs")
    print_results(base_station)
    return  base_station.fairness_index, base_station.total_throughput

def run_simulation(base_station, num_ttis: int, verbose: bool = False):
    """Run the network simulation for a specified number of TTIs."""
    base_station.init_user_properties()
    rr_total_delay = 0
    pf_total_delay = 0

    # Round Robin Scheduling
    rfairnessidx, rthroughput = results(base_station, num_ttis=num_ttis,scheduler='round_robin', verbose=verbose)

    base_station.update_user_properties()
    # Reset user properties for Proportional Fair Scheduling
    pffairnessidx, pfthroughput = results(base_station, num_ttis=num_ttis,scheduler='proportional_fair', verbose=verbose)
    
    print("\n--- Delay Comparison ---")
    print(f"Total Delay (Round Robin): {rr_total_delay} TTIs")
    print(f"Total Delay (Proportional Fair): {pf_total_delay} TTIs")

    return rfairnessidx, pffairnessidx, rthroughput, pfthroughput

if __name__ == "__main__":
    # Example usage
    num_users = 10
    total_rbs = 100 # Total number of Resource Blocks
    num_ttis = 5000  # Number of Transmission Time Intervals to simulate
    rr_throughput = []
    pf_throughput = []
    rr_fairidx = []
    pf_fairidx = []
    index = []
    for i in range(1,30):
        base_station = Bs.BaseStation(num_users=num_users, total_rbs=total_rbs)
        rr_fairness_index,pf_fairness_index, rrth,prth =run_simulation(base_station,num_ttis=num_ttis, verbose= True)
        
        rr_throughput.append(rrth)
        pf_throughput.append(prth)
        rr_fairidx.append(rr_fairness_index)
        pf_fairidx.append(pf_fairness_index)
        index.append(i)
        num_users = 10* i

    plt.scatter(index, rr_fairidx, label='Round Robin Throughput', color='blue')
    plt.scatter(index, pf_fairidx, label='Proportional Fair Throughput', color='red')
    plt.xlabel('Simulation Run')
    plt.ylabel('Fairness Index')
    plt.title('Fairness Index Comparison')
    plt.legend()
    plt.show()