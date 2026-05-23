# SysInfo Stealer - Fundamentals of Malware Analysis

A demonstration malware project for educational purposes, showcasing information gathering, data exfiltration, and persistence techniques on Linux systems.

## Disclaimer

This project is created solely for educational purposes as part of malware analysis fundamentals coursework. It is intended to help understand malware behavior, detection mechanisms, and defensive strategies. **Use only in isolated, controlled environments such as virtual machines. Unauthorized deployment is illegal and unethical.**

## Project Overview

This project consists of three main components that demonstrate a complete Command & Control (C2) infrastructure:

1. **sysinfostealer.py** - The malware payload that collects system information and exfiltrates data
2. **attacker_server.py** - C2 server that receives and stores exfiltrated data
3. **data_viewer.py** - Utility to decode and display collected data in human-readable format

## Architecture

### Information Stealer (sysinfostealer.py)

The malware demonstrates the following capabilities:

**System Information Collection:**
- Hostname, username, and OS details
- CPU and memory information
- Disk usage statistics
- Network connections and running processes
- Logged-in users and IP addresses

**File Exfiltration:**
- Targets sensitive files: `/etc/passwd`, `/etc/hosts`, `.bash_history`
- SSH key discovery and collection
- Base64 encoding for data obfuscation

**Evasion Techniques:**
- Process name masquerading (appears as `systemd-network`)
- Anti-debugging checks (TracerPid monitoring, debugger detection)
- VM environment detection
- Single instance enforcement via file locking

**Persistence Mechanisms:**
- XDG autostart desktop entry creation
- Bashrc modification
- Crontab job installation
- Hidden binary placement in `~/.local/share/.cache/.systemd-helper`

**Network Communication:**
- Data obfuscation using double Base64 encoding with string reversal
- Periodic heartbeat signals to C2 server
- HTTP POST exfiltration to attacker-controlled endpoint

**Propagation Attempt:**
- SSH-based lateral movement via known_hosts

### C2 Server (attacker_server.py)

**Features:**
- Listens on port 8080 for incoming connections
- Receives obfuscated data via `/upload` endpoint
- Decodes multi-layer obfuscation (Base64 → Reverse → Base64 → JSON)
- Stores collected data with timestamp and hostname identifiers
- Heartbeat endpoint (`/heartbeat`) for client connectivity checks
- Organized storage in `Collected_Data/` directory

### Data Viewer (data_viewer.py)

**Features:**
- Parses JSON files from collected data
- Automatically decodes Base64-encoded fields
- Presents comprehensive report including:
  - System information summary
  - Memory and disk usage
  - Complete network connections listing
  - Running processes
  - Exfiltrated file contents
  - SSH keys
- Statistics and collection metadata

## Setup and Usage

### Prerequisites

```bash
# Python 3.x required
# Install dependencies
pip install requests pyinstaller
```

### Building the Malware Executable

```bash
pyinstaller --onefile --noconsole --name=systemd-network sysinfostealer.py
```

The compiled binary will be located in the `dist/` directory.

### Running the C2 Server

```bash
python3 attacker_server.py
```

Server will start on `0.0.0.0:8080` and create a `Collected_Data/` directory for storage.

### Configuration

Edit the target IP in `sysinfostealer.py`:

```python
ATTACKER_IP = "192.168.100.10"  # Change to your C2 server IP
ATTACKER_PORT = 8080
```

### Viewing Collected Data

```bash
python3 data_viewer.py Collected_Data/<hostname>_<timestamp>.json
```

### Persistence Locations

- Binary: `~/.local/share/.cache/.systemd-helper`
- Autostart: `~/.config/autostart/systemd-service.desktop`
- Bashrc: `~/.bashrc` (appended entry)
- Crontab: User crontab with `@reboot` trigger

### Network Communication

- **Exfiltration:** HTTP POST to `/upload` endpoint
- **Heartbeat:** HTTP GET to `/heartbeat` endpoint
- **User-Agent Spoofing:** Mimics Mozilla/Firefox traffic
- **Interval:** 30-second sleep between cycles

### File Collection Targets

```python
/etc/passwd
/etc/hosts
~/.ssh/id_rsa
~/.bash_history
~/.ssh/* (all files in SSH directory)
```

## Testing Environment

**Recommended Setup:**
- Isolated virtual machines (VirtualBox, VMware, KVM)
- Separate network segment or host-only networking
- Snapshot capability for clean state restoration
- No connection to production networks

**Tested On:**
- Kali Linux
- Ubuntu 20.04+

## Limitations

- Requires Python runtime (unless compiled with PyInstaller)
- Persistence methods require user-level privileges
- Network exfiltration easily detected by modern security tools
- Anti-VM checks are basic demonstrations
- No encryption for C2 communication (traffic is observable)

## Legal Notice

This software is provided for educational purposes only. The authors and contributors are not responsible for any misuse or damage caused by this program. Always ensure you have explicit permission before testing on any system you do not own. Unauthorized access to computer systems is illegal under laws including the Computer Fraud and Abuse Act (CFAA) and similar legislation worldwide.

## License

This project is provided as-is for educational purposes. Use responsibly and ethically.
