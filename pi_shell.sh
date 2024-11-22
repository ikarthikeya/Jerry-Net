pip install -r requirements.txt
cd ~/Jerry-Net/main

# Run the first Python script in a new terminal
tmux new-session -d -s session1 "python3 satellite_server_modified.py"

# Run the second Python script in a new terminal
tmux split-window -h "python3 no_ml_earth_client.py"
tmux attach -t session1