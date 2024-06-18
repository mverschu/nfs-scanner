import os
import json
import shutil
import subprocess
import argparse
import ipaddress
import nmap
from termcolor import colored
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

REMEMBER_FILE = "nfs_remember.json"

def check_root():
    if os.geteuid() != 0:
        print(colored("[-] This script must be run as root", 'red'))
        exit(1)

def scan_ip(nm, ip):
    try:
        nm.scan(ip, '2049')
        if 'tcp' in nm[ip] and 2049 in nm[ip]['tcp'] and nm[ip]['tcp'][2049]['state'] == 'open':
            return {'IP': ip, 'Port': 2049}
    except Exception:
        pass
    return None

def discover_nfs(ip_range):
    nm = nmap.PortScanner()
    open_ports = []

    print(colored("[*] Starting NFS discovery", 'cyan'))
    with tqdm(total=len(ip_range), desc="Scanning IPs", ncols=75) as pbar:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(scan_ip, nm, str(ip)): ip for ip in ip_range}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
                    print(colored(f"[+] NFS service found on {result['IP']}:2049", 'green'))
                pbar.update(1)
    
    return open_ports

def list_nfs_shares(ip):
    try:
        result = subprocess.run(['showmount', '-e', ip], capture_output=True, text=True)
        if result.returncode == 0:
            shares = result.stdout.split('\n')[1:-1]  # Skip the first line and the last empty line
            shares = [line.split()[0] for line in shares]
            return shares
        else:
            print(colored(f"[-] Failed to list NFS shares from {ip}: {result.stderr}", 'red'))
            return []
    except Exception as e:
        print(colored(f"[-] Exception occurred while listing NFS shares: {e}", 'red'))
        return []

def mount_nfs(ip, share, mount_point):
    try:
        os.makedirs(mount_point, exist_ok=True)
        result = subprocess.run(['mount', f'{ip}:{share}', mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            print(colored(f"[+] Mounted NFS share {share} from {ip} to {mount_point}", 'green'))
            print(colored("[+] Successfully accessed the NFS share unauthenticated", 'green'))
            return True
        else:
            print(colored(f"[-] Failed to mount NFS share {share} from {ip}: {result.stderr}", 'red'))
            return False
    except Exception as e:
        print(colored(f"[-] Exception occurred while mounting: {e}", 'red'))
        return False

def list_contents(mount_point, recursive=False):
    try:
        print(colored("[*] Listing contents", 'cyan'))
        for root, dirs, files in os.walk(mount_point):
            level = root.replace(mount_point, '').count(os.sep)
            indent = '│   ' * level + '├── '
            print(colored(f"{indent}{os.path.basename(root)}/", 'yellow'))
            sub_indent = '│   ' * (level + 1) + '├── '
            if recursive:
                for f in files:
                    print(colored(f"{sub_indent}{f}", 'white'))
    except Exception as e:
        print(colored(f"[-] Exception occurred while listing contents: {e}", 'red'))

def parse_args():
    parser = argparse.ArgumentParser(description="NFS share scanner and mounter.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--range', type=str, help='IP range to scan (e.g., 192.168.1.1-192.168.1.255 or 192.168.1.0/24)')
    group.add_argument('--ip', type=str, help='Single IP to scan (e.g., 192.168.1.100)')
    parser.add_argument('--list', action='store_true', help='List all mountable NFS shares')
    parser.add_argument('--mount', action='store_true', help='Mount the shares and show their contents')
    parser.add_argument('--recursive', action='store_true', help='List all files in addition to directories')
    parser.add_argument('--remember', action='store_true', help='Remember the NFS shares discovered in the initial scan')
    return parser.parse_args()

def generate_ip_range(ip_range):
    try:
        if '-' in ip_range:
            start_ip, end_ip = ip_range.split('-')
            start_octets = start_ip.split('.')
            end_octets = end_ip.split('.')
            generated_ips = []

            for i in range(int(start_octets[-1]), int(end_octets[-1]) + 1):
                generated_ips.append('.'.join(start_octets[:-1] + [str(i)]))

            return generated_ips
        else:
            network = ipaddress.ip_network(ip_range, strict=False)
            return list(network.hosts())
    except ValueError as e:
        print(colored(f"[-] Invalid IP range format: {e}", 'red'))
        return []

def save_remembered_data(data):
    try:
        with open(REMEMBER_FILE, 'w') as f:
            json.dump(data, f)
        print(colored("[+] NFS shares have been remembered", 'green'))
    except Exception as e:
        print(colored(f"[-] Failed to remember NFS shares: {e}", 'red'))

def load_remembered_data():
    try:
        if os.path.exists(REMEMBER_FILE):
            with open(REMEMBER_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(colored(f"[-] Failed to load remembered NFS shares: {e}", 'red'))
        return None

def cleanup_mounts(mount_points):
    for mount_point in mount_points:
        try:
            subprocess.run(['umount', mount_point], capture_output=True, text=True)
            shutil.rmtree(mount_point)
            print(colored(f"[+] Cleaned up mount point {mount_point}", 'green'))
        except Exception as e:
            print(colored(f"[-] Failed to clean up mount point {mount_point}: {e}", 'red'))

def main():
    check_root()
    
    args = parse_args()

    remembered_data = None
    if args.remember:
        remembered_data = load_remembered_data()
    
    if args.range:
        ip_range = generate_ip_range(args.range)
    else:
        ip_range = [args.ip]

    if remembered_data:
        print(colored("[+] Using remembered NFS shares from previous scan", 'cyan'))
        open_ports = remembered_data['open_ports']
    else:
        open_ports = discover_nfs(ip_range)
        if args.remember:
            save_remembered_data({'open_ports': open_ports})

    mount_points = []

    if args.list:
        if open_ports:
            for entry in open_ports:
                ip = entry['IP']
                shares = list_nfs_shares(ip)
                if shares:
                    print(colored(f"\n[+] Available NFS shares on {ip}:", 'cyan'))
                    for share in shares:
                        print(colored(f"  {share}", 'green'))
                else:
                    print(colored(f"[-] No authenticated NFS shares available on {ip}", 'red'))

    if args.mount:
        if open_ports:
            df = pd.DataFrame(open_ports)
            print(colored("\n[*] Discovered NFS Endpoints:", 'cyan'))
            print(df.to_string(index=False))
        
        for entry in open_ports:
            ip = entry['IP']
            shares = list_nfs_shares(ip)
            for share in shares:
                mount_point = f"/mnt/{ip.replace('.', '_')}_{share.replace('/', '_')}"
                if mount_nfs(ip, share, mount_point):
                    mount_points.append(mount_point)
                    user_input = input(colored(f"[?] Do you want to list the contents of the NFS share {share} at {ip}? (y/n): ", 'blue')).strip().lower()
                    if user_input == 'y':
                        list_contents(mount_point, recursive=args.recursive)
                else:
                    print(colored(f"[-] Skipping content listing for {ip}:{share} due to mount failure.", 'red'))

    cleanup_mounts(mount_points)

if __name__ == "__main__":
    main()
