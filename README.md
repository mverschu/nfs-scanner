
# NFS Scanner and Mounter

## Screenshots

Scanning phase:
![image](https://github.com/mverschu/nfs-scanner/assets/69352107/162fb707-85dc-44e4-963a-6d8f5d24b521)

## Overview
NFS Scanner and Mounter is a Python tool designed to scan, list, and mount NFS shares on a given network range or a single IP address. It leverages `nmap` for scanning and `showmount` for listing available NFS shares. The tool supports multi-threaded scanning and offers options to remember scanned NFS shares, allowing for efficient and repeated use.

## Features
- **NFS Discovery**: Scan a range of IPs or a single IP to discover available NFS shares.
- **List NFS Shares**: List all mountable NFS shares on the discovered IPs.
- **Mount NFS Shares**: Mount discovered NFS shares and display their contents.
- **Recursive Listing**: Option to list all files within the NFS shares recursively.
- **Remember Scanned Shares**: Save the results of NFS scans to reuse in future runs without rescanning.
- **Clean-up**: Automatically unmounts and removes directories created during the operation.

## Prerequisites
- Python 3.x
- `nmap` installed and accessible from the command line
- `showmount` command available (typically part of the `nfs-common` package on Linux)
- Install required Python packages using:
  ```sh
  pip install tqdm termcolor pandas python-nmap
  ```

## Usage
Run the script with appropriate permissions (typically as root or using `sudo`).

### Scanning and Listing NFS Shares
To scan a range of IPs and list all available shares:
```sh
sudo python3 nfs-scanner.py --range 192.168.1.0/24 --list
```

To scan a single IP and list all available shares:
```sh
sudo python3 nfs-scanner.py --ip 192.168.1.100 --list
```

### Mounting NFS Shares
To scan a range of IPs, mount available shares, and show their contents:
```sh
sudo python3 nfs-scanner.py --range 192.168.1.0/24 --mount
```

To scan a single IP, mount available shares, and show their contents:
```sh
sudo python3 nfs-scanner.py --ip 192.168.1.100 --mount
```

To include files in the listing, add the `--recursive` flag:
```sh
sudo python3 nfs-scanner.py --range 10.0.0.0/24 --mount --recursive
```

### Remembering Scanned Shares
To remember the scanned NFS shares for future use:
```sh
sudo python3 nfs-scanner.py --range 192.168.1.0/24 --list --remember
```

To use the remembered NFS shares without scanning again:
```sh
sudo python3 nfs-scanner.py --list --remember
```

### Running in a Python 3 Virtual Environment

To ensure that you have a clean and isolated environment for running the NFS Scanner and Mounter script, it's a good idea to use a Python virtual environment. Here's how to set it up:

1. **Install `virtualenv`** (if you don't have it already):
    ```sh
    pip3 install virtualenv
    ```

2. **Create a virtual environment**:
    ```sh
    virtualenv venv
    ```

3. **Activate the virtual environment**:
    - On Windows:
      ```sh
      venv\Scripts\activate
      ```
    - On macOS and Linux:
      ```sh
      source venv/bin/activate
      ```

4. **Install the required Python packages**:
    ```sh
    pip3 install -r requirements.txt
    ```

5. **Run the script**:

6. **Deactivate the virtual environment** when you're done:
    ```sh
    deactivate
    ```

By following these steps, you'll ensure that your system's Python environment remains clean and that the NFS Scanner and Mounter script runs with the required dependencies.

### Clean-up
The script will automatically unmount and clean up directories created during the operation.
