pip install -r requirements.txt
# Run the first Python script in a new terminal
gnome-terminal -- bash -c "python main/satellite_server_modified.py; exec bash"

# Run the second Python script in a new terminal
gnome-terminal -- bash -c "python main/earth_client_modified.py; exec bash"
