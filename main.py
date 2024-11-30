
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
    base_station.total_throughput = sum(user.throughput for user in base_station.users) / (len(base_station.users) * 1000)
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
        if scheduler == 'round_robin':
            if base_station.round_robin_scheduler():
                break
        elif scheduler == 'proportional_fair':
            if base_station.proportional_fair_scheduler():
                break
        
    calculate_performance_metrics(base_station)

    # Calculate total delay for RR
    total_delay = sum(user.queue_delay for user in base_station.users)
    if not verbose:
        print(f"\nTotal TTIs (Round Robin): {count}")
        print(f"Total Queue Delay (Round Robin): {total_delay} TTIs")
        print_results(base_station)
    return  base_station.fairness_index, base_station.total_throughput, total_delay

def run_simulation(base_station, num_ttis: int, verbose: bool = False):
    """Run the network simulation for a specified number of TTIs."""
    base_station.init_user_properties()
    rr_total_delay = 0
    pf_total_delay = 0

    # Round Robin Scheduling
    rfairnessidx, rthroughput, rr_delay = results(base_station, num_ttis=num_ttis,scheduler='round_robin', verbose=verbose)

    base_station.update_user_properties()

    # Reset user properties for Proportional Fair Scheduling
    pffairnessidx, pfthroughput, pf_delay = results(base_station, num_ttis=num_ttis,scheduler='proportional_fair', verbose=verbose)
    
    print("\n--- Delay Comparison ---")
    print(f"Total Delay (Round Robin): {rr_total_delay} TTIs")
    print(f"Total Delay (Proportional Fair): {pf_total_delay} TTIs")

    return rfairnessidx, pffairnessidx, rthroughput, pfthroughput, rr_delay, pf_delay

if __name__ == "__main__":
    # Example usage
    num_users = 10

    num_ttis = 5000  # Number of Transmission Time Intervals to simulate
    rbs = [20,50,80,110,200, 500]
    
    
    fig, axs = plt.subplots(2, 3, figsize=(18, 10))
    fig, th = plt.subplots(2, 3, figsize=(18, 10))
    fig, de = plt.subplots(2, 3, figsize=(18, 10))

    for j, rb in enumerate(rbs):
        rr_throughput, pf_throughput, rr_fairidx, pf_fairidx, rr_delay, pf_delay = [], [], [], [], [], []
        index = []
        
        for i in range(1, 30):
            base_station = Bs.BaseStation(num_users=num_users, total_rbs=rb)
            rr_fairness_index, pf_fairness_index, rrth, prth, rrd, pfd = run_simulation(base_station, num_ttis=num_ttis, verbose=True)
            
            rr_throughput.append(rrth)
            pf_throughput.append(prth)
            rr_fairidx.append(rr_fairness_index)
            pf_fairidx.append(pf_fairness_index)
            rr_delay.append(rrd)
            pf_delay.append(pfd)
            index.append(num_users)
            num_users = 10 * i
            
        # Fairness Index Plot
        ax = axs[j // 3, j % 3]
        ax.scatter(index, rr_fairidx, label='Round Robin Fairness Index', color='blue')
        ax.scatter(index, pf_fairidx, label='Proportional Fair Fairness Index', color='red')
        ax.set_xlabel('Simulation Run')
        ax.set_ylabel('Fairness Index')
        ax.set_title(f'Fairness Index Comparison for {rb} RBs')

        # Throughput Plot
        thh = th[j // 3, j % 3]
        thh.scatter(index, rr_throughput, label='Round Robin Throughput', color='blue')
        thh.scatter(index, pf_throughput, label='Proportional Fair Throughput', color='red')
        thh.set_xlabel('Simulation Run')
        thh.set_ylabel('Throughput (Kbps)')
        thh.set_title(f'Throughput Comparison for {rb} RBs')

        # Delay Plot
        ded = de[j // 3, j % 3]
        ded.scatter(index, rr_delay, label='Round Robin Delay', color='blue')
        ded.scatter(index, pf_delay, label='Proportional Fair Delay', color='red')
        ded.set_xlabel('Simulation Run')
        ded.set_ylabel('Queue Delay (TTIs)')
        ded.set_title(f'Delay Comparison for {rb} RBs')

        # Add legend once, outside the loop
        ax.legend()
        thh.legend()
        ded.legend()


    plt.tight_layout()
    plt.show()