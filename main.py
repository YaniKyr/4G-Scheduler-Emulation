from tabulate import tabulate
import matplotlib.pyplot as plt
import BaseStation as Bs
import numpy as np

def calculate_weighted_fairness_index(base_station):
    """
    Calculate a weighted fairness index that normalizes throughput 
    based on each user's initial resource allocation demand.
    """
    normalized_throughputs = []
    
    for user in base_station.users:
        # Normalize throughput by dividing actual throughput by initial resource demand
        if user.InitRac > 0:
            normalized_throughput = user.throughput / user.InitRac
            normalized_throughputs.append(normalized_throughput)
        else:
            # Handle edge case of zero initial resource demand
            normalized_throughputs.append(0)
    
    # Calculate weighted Jain's fairness index
    squared_sum = sum(throughput ** 2 for throughput in normalized_throughputs)
    n = len(normalized_throughputs)
    
    # Prevent division by zero
    weighted_fairness_index = (sum(normalized_throughputs) ** 2) / (n * squared_sum) if squared_sum != 0 else 0
    
    return weighted_fairness_index

def print_detailed_fairness_info(base_station):
    """
    Print detailed information about each user's resource allocation
    to help understand the fairness calculation
    """
    print("\nDetailed Resource Allocation Analysis:")
    print("----------------------------------------")
    headers = ["ID", "Traffic Type", "Initial RAC", "Actual Throughput", "Normalized Throughput"]
    data = []
    
    for user in base_station.users:
        if user.InitRac > 0:
            normalized_throughput = user.throughput / user.InitRac
            data.append([
                user.id, 
                user.traffic_type, 
                f"{user.InitRac:.2f}", 
                f"{user.throughput:.2f}", 
                f"{normalized_throughput:.4f}"
            ])
    
    print(tabulate(data, headers=headers, tablefmt="grid"))

def calculate_performance_metrics(base_station):
    """Calculate total throughput and weighted fairness index at the end of each time step."""
    base_station.total_throughput = sum(user.throughput for user in base_station.users) / (len(base_station.users) * 1000)
    base_station.fairness_index = calculate_weighted_fairness_index(base_station)
    
def print_results(base_station):
    print(f"Total Throughput: {base_station.total_throughput:.2f} Kbps")
    print(f"Weighted Fairness Index: {base_station.fairness_index:.4f}")
    
    # Optional: Print detailed fairness information
    print_detailed_fairness_info(base_station)
    
    headers = ["ID", "Traffic Type", "Throughput", "Allocated RBs", "Initial Rac", "Queue Delay (TTIs)"]
    data = [[user.id, user.traffic_type, f"{user.throughput:.2f}", user.allocated_rbs, f"{user.InitRac:.2f}", user.queue_delay] for user in base_station.users]
    print(tabulate(data, headers=headers, tablefmt="grid"))

def results(base_station, num_ttis: int, scheduler, verbose: bool = False):
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
    return base_station.fairness_index, base_station.total_throughput, total_delay

def run_simulation(base_station, num_ttis: int, verbose: bool = False):
    """Run the network simulation for a specified number of TTIs."""
    base_station.init_user_properties()
    rr_total_delay = 0
    pf_total_delay = 0

    # Round Robin Scheduling
    rfairnessidx, rthroughput, rr_delay = results(base_station, num_ttis=num_ttis, scheduler='round_robin', verbose=verbose)

    base_station.update_user_properties()

    # Reset user properties for Proportional Fair Scheduling
    pffairnessidx, pfthroughput, pf_delay = results(base_station, num_ttis=num_ttis, scheduler='proportional_fair', verbose=verbose)
    
    print("\n--- Delay Comparison ---")
    print(f"Total Delay (Round Robin): {rr_delay} TTIs")
    print(f"Total Delay (Proportional Fair): {pf_delay} TTIs")

    return rfairnessidx, pffairnessidx, rthroughput, pfthroughput, rr_delay, pf_delay

if __name__ == "__main__":
    # Example usage
    num_users = 10

    num_ttis = 5000  # Number of Transmission Time Intervals to simulate
    rbs = [20, 110, 200]
    
    # Create subplots for fairness index, throughput, and delay
    fig_fairness, axs_fairness = plt.subplots(2, 3, figsize=(18, 10))
    fig_throughput, axs_throughput = plt.subplots(2, 3, figsize=(18, 10))
    fig_delay, axs_delay = plt.subplots(2, 3, figsize=(18, 10))

    for j, rb in enumerate(rbs):
        rr_throughput, pf_throughput = [], []
        rr_fairidx, pf_fairidx = [], []
        rr_delay, pf_delay = [], []
        user_counts = []
        
        for i in range(1, 30):
            base_station = Bs.BaseStation(num_users=num_users, total_rbs=rb)
            rr_fairness_index, pf_fairness_index, rrth, prth, rrd, pfd = run_simulation(base_station, num_ttis=num_ttis, verbose=True)
            
            rr_throughput.append(rrth)
            pf_throughput.append(prth)
            rr_fairidx.append(rr_fairness_index)
            pf_fairidx.append(pf_fairness_index)
            rr_delay.append(rrd)
            pf_delay.append(pfd)
            user_counts.append(num_users)
            num_users = 10 * i
        
        # Fairness Index Plot
        ax_fairness = axs_fairness[j // 3, j % 3]
        ax_fairness.plot(user_counts, rr_fairidx, label='Round Robin Fairness Index', marker='o', color='blue')
        ax_fairness.plot(user_counts, pf_fairidx, label='Proportional Fair Fairness Index', marker='o', color='red')
        ax_fairness.set_ylim(0, 1)
        ax_fairness.set_xlabel('Number of Users')
        ax_fairness.set_ylabel('Weighted Fairness Index')
        ax_fairness.set_title(f'Fairness Index Comparison for {rb} RBs')
        ax_fairness.legend()

        # Throughput Plot
        ax_throughput = axs_throughput[j // 3, j % 3]
        ax_throughput.plot(user_counts, rr_throughput, label='Round Robin Throughput', marker='o', color='blue')
        ax_throughput.plot(user_counts, pf_throughput, label='Proportional Fair Throughput', marker='o', color='red')
        ax_throughput.set_ylim(0, max(max(rr_throughput), max(pf_throughput)) * 1.1)
        ax_throughput.set_xlabel('Number of Users')
        ax_throughput.set_ylabel('Throughput (Mbps)')
        ax_throughput.set_title(f'Throughput Comparison for {rb} RBs')
        ax_throughput.legend()

        # Delay Plot
        ax_delay = axs_delay[j // 3, j % 3]
        ax_delay.plot(user_counts, rr_delay, label='Round Robin Delay', marker='o', color='blue')
        ax_delay.plot(user_counts, pf_delay, label='Proportional Fair Delay', marker='o', color='red')
        ax_delay.set_xlabel('Number of Users')
        ax_delay.set_ylabel('Queue Delay (TTIs)')
        ax_delay.set_title(f'Delay Comparison for {rb} RBs')
        ax_delay.legend()

    plt.tight_layout()
    plt.show()