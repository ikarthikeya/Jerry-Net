pip install -r requirements.txt
# Run the first Python script in a new terminal
tmux new-session -d -s session1 "python3 main/satellite_server_modified.py"

# Run the second Python script in the same terminal
tmux split-window -h "python3 main/no_ml_earth_client.py"
tmux attach -t session1
