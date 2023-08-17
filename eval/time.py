import os
import matplotlib.pyplot as plt
from collections import defaultdict

def read_log_file(file_path):
    process_times = defaultdict(list)
    current_process = None

    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if line.endswith('seconds'):
            process_name, time_str = line.rsplit(': ', 1)
            # Extract the numeric part of the time string and convert to ms
            time_value = float(time_str.split()[0]) * 1000
            process_times[process_name].append(time_value)

    return process_times

def calculate_average_times(process_times):
    average_times = {}
    for process_name, times_list in process_times.items():
        average_times[process_name] = sum(times_list) / len(times_list)
    return average_times

def write_results_to_file(case_name, average_times):
    with open('results.txt', 'a') as result_file:
        result_file.write(f"Case: {case_name}\n")
        for process_name, avg_time in average_times.items():
            result_file.write(f"{process_name}: {avg_time:.6f} ms\n")
        result_file.write("\n")

def plot_average_times(tinyjambu_variation, tls_times, no_tls_times):
    processes = list(tls_times.keys())
    tls_values = list(tls_times.values())
    no_tls_values = list(no_tls_times.values())
    
    plt.figure(figsize=(10, 6))
    
    # Reverse the order of processes and values
    processes.reverse()
    tls_values.reverse()
    no_tls_values.reverse()
    
    plt.plot(processes, tls_values, marker='o', label='With TLS')
    plt.plot(processes, no_tls_values, marker='x', label='Without TLS')
    
    plt.xlabel('Processes')
    plt.ylabel('Average Time (ms)')
    plt.title(f'Average Process Times for {tinyjambu_variation.split(",")[0]}')
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(f'{tinyjambu_variation.split(",")[0]}_plot.png')  # Save the plot as an image
    plt.show()

def main():
    case_files = [
        ("1execution_times.log", "tinyjambu128, no TLS"),
        ("2execution_times.log", "tinyjambu128, with TLS"),
        ("3execution_times.log", "tinyjambu192, no TLS"),
        ("4execution_times.log", "tinyjambu192, with TLS"),
        ("5execution_times.log", "tinyjambu256, no TLS"),
        ("6execution_times.log", "tinyjambu256, with TLS"),
    ]

    tls_cases = {}
    no_tls_cases = {}

    for file_name, case_name in case_files:
        file_path = os.path.join('/home/hadak/Desktop/thesis/TinyJAMBU-authentication-digital-twin-and-iot-devices/eval/', file_name)
        process_times = read_log_file(file_path)
        average_times = calculate_average_times(process_times)

        if "no TLS" in case_name:
            no_tls_cases[case_name] = average_times
        else:
            tls_cases[case_name] = average_times

    for tls_case_name, tls_case in tls_cases.items():
        no_tls_case_name = tls_case_name.replace(", with TLS", ", no TLS")
        no_tls_case = no_tls_cases.get(no_tls_case_name, {})  # Initialize with empty dictionary
        plot_average_times(tls_case_name, tls_case, no_tls_case)
        write_results_to_file(tls_case_name, tls_case)
        write_results_to_file(no_tls_case_name, no_tls_case)

if __name__ == "__main__":
    main()
