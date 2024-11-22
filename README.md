# **Jerry-Net: LEO Satellite Communication Protocol**

### **Project Description**

This repository contains the initial stages of development for a custom **peer-to-peer network protocol** designed to operate within the context of **Low Earth Orbit (LEO) satellite constellations**, such as **Starlink** or **OneWeb**. The protocol aims to address the challenges of communication over satellite networks, specifically in terms of Inter-Satellite Link (ISL) and handover delays, using a robust, scalable approach that enhances performance for various use cases, including vehicular mobility, remote exploration, and underwater search and rescue.

### **Use Case and Objective**

We are focusing on building a protocol that facilitates:

- **Realistic emulations of LEO communication channels**.
- Handling **simultaneous parallel connections** from earth-based data sources to at least five satellite devices.
- Demonstrating and mitigating key satellite communication challenges, such as ISL and handover delays, while incorporating **hybrid wired-satellite communication**.

The protocol will be implemented and demonstrated using **Raspberry Pi (RPi)** devices, but the system should be able to scale to other platforms as needed.

### **Getting Started**

To get started with the project, follow the steps below to clone the repository and set up your development environment.

#### **Clone the Repository**

You can clone this repository by using the following Git command:

```bash
git clone https://github.com/ikarthikeya/Jerry-Net.git
```

#### **Run the Repository Locally**

##### **Method 1**

Make sure all dependencies are installed, run

```bash
pip install -r requirements.txt
```

Then run the following command in one terminal

```bash
python3 main/satellite_server_modified.py
```

And run the following command in the second terminal

```bash
python3 main/earth_client_modified.py
```
##### **Method 2**

With tmux installed in a conda environment or in the local Linux system, run

```bash
bash runme.sh
```

#### **Run the Repository on SCSS raspberry Pi**

Edit deploy.sh, fill in <your_user_name> and <your_pi_address>, then run

```bash
bash deploy.sh
```

As we need use tmux for multiplexing for the program. You have to log in your pi and go to directory ~/Jerry-Net/Jerry-Net, then run

```bash
bash pi_shell.sh
```
