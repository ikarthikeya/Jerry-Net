import subprocess
import time
import os
import psutil

clumsy_dir = "clumsy"
# go to clumsy directory
os.chdir(clumsy_dir)
# Start Clumsy with 10% packet loss
cmd = "clumsy.exe --drop on --drop-inbound on --drop-outbound on --drop-chance 20.0"
process = subprocess.Popen(cmd, shell=True)

try:
    # Let Clumsy run for a specific duration
    print("Clumsy is running...")
    time.sleep(10)  # Let it run for 10 seconds (or however long you need)
finally:
    # Terminate the Clumsy process
    parent = psutil.Process(process.pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()

    print("Process and its children terminated.")