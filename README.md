**Team:** Wingmen
#  SkyScout: Autonomous UAV Urban Disaster Response System

Domain: Open Innovation Status: Prototype 

SkyScout is an Autonomous UAV Urban Disaster Response System. Built on open-source architecture while leveraging industry-grade systems, it provides a cost-effective and scalable solution for real-world deployment.

---

##  The Problem & Our Solution
The first 60 minutes after a disaster are the most critical for saving lives and minimizing damage. Current systems rely heavily on slow human reporting and manual deployment. 

SkyScout solves this by deploying an autonomous surveillance drone that continuously monitors target areas using onboard sensors and cameras. It uses AI/ML algorithms to detect fires, flood and structural damage. Once detected, the system automatically identifies the exact location, navigates to the affected area, and performs immediate rapid response actions like dropping emergency medical kits.

---

##  Core Features
* **Real-Time Vision Processing**: Continuous frame-by-frame analysis using YOLO for detecting disaster zones.
* **Autonomous Alignment System**: Uses image-based error correction to precisely align the drone over the target.
* **Closed-Loop Control Logic**: A robust Detection → Alignment → Validation → Action* pipeline ensures a stable response.
* **Autonomous Payload Deployment:** Automatically triggers payload drops after stable alignment and resumes its mission.

---

##  Tech Stack
This project utilizes a highly decentralized node-based framework, allowing perception, decision, and execution to run independently.
* **Middleware / Framework:** ROS2 Humble 
* **Simulation Environment:** Gazebo Harmonic (Digital Twin) 
* **Flight Controller Stack:** Ardupilot SITL & MAVROS 
* **Ground Control Station:** QGroundControl 
* **Computer Vision:** YOLOv8 
* **Primary Language:** Python 

---

##  Demonstration

This is the Ardupilot drone which we will be using for the simulation.

![Drone image](IMG-20260415-WA0011.jpg)

Disaster site and dashboard

![Drone image](IMG-20260415-WA0013.jpg)

Detection on the disaster site

![Drone image](IMG-20260415-WA0007.jpg)

---

##  Quick Start & Execution Sequence
First make sure you are using Ubuntu 22.04
and have ROS2 Humble installed, if not you check the [documentation](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) for installation.
Similiarly you also need to download and install:

[Ardupilot](https://ardupilot.org/dev/docs/building-setup-linux.html)

[Gazebo Harmonic](https://gazebosim.org/docs/harmonic/install_ubuntu/#binary-installation-on-ubuntu)

[QGC](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html#ubuntu)

and Mavros
```bash
sudo apt update
sudo apt install ros-humble-mavros ros-humble-mavros-extras
sudo /opt/ros/humble/lib/mavros/install_geographiclib_datasets.sh
```
After having these softwares
```bash
git clone https://github.com/yourusername/SkyScout.git
cd SkyScout
pip install -r requirements.txt
cd src
colcon build --symlink-install
source install/setup.bash
```
Now
To run the SkyScout system in the simulation environment, you will need to open multiple terminal tabs. Ensure your ROS 2 workspace is built (`colcon build`) and sourced (`source install/setup.bash`) in every new terminal.

**Terminal 1: Launch Simulation & ROS Bridges**
Start the Gazebo environment, load the custom disaster world, and initialize the camera/payload bridges.
```bash
ros2 launch skyscout_core system.launch.py
```
**Terminal 2: Initialize ArduPilot SITL**
Boot the Software-In-The-Loop (SITL) physics flight controller for the drone.
```bash
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --map --console --mavproxy-args="--out=127.0.0.1:14551"
```
**Terminal 3: Start MAVROS (Communication Bridge)**
Establish the connection between the ROS 2 network and the ArduPilot flight controller, filtering out unnecessary distance sensor warnings.
```bash
ros2 run mavros mavros_node --ros-args -p fcu_url:=udp://127.0.0.1:14551@14555 -p tgt_system:=1 -p tgt_component:=1 2>&1 | grep -v "mavros.distance_sensor"
```
Terminal 4: Launch Disaster Detection (AI Module)
Start the YOLO/MobileViT perception node to scan the camera feed.
```bash
ros2 run skyscout_core disaster_detection
```
Terminal 5: Launch Precision Alignment (Control Module)
Start the closed-loop control system that manages the targeting HUD, alignment, and payload deployment.
```bash
ros2 run skyscout_core precision_align_node
```

##  Hardware Stack & Expected Cost (Real-World Deployment)
To achieve low-cost scalability, SkyScout is designed to run entirely on Commercial-Off-The-Shelf (COTS) hardware. The estimated cost for a fully autonomous prototype is between **₹33,500 - ₹44,000**.

| Component Category | Expected Hardware |
| :--- | :--- |
| **Companion Computer** | NVIDIA Jetson Nano (4GB) or Raspberry Pi 5 (8GB) |
| **Flight Controller** | Pixhawk 2.4.8 + M8N GPS |
| **Vision System** | Raspberry Pi Camera V3 or Logitech C920 |
| **Drone Base Kit** | F450 / S500 Frame, BLDC Motors, ESCs |
| **Actuator** | MG995 Servo Motor (for payload drop) |

---
##  Fault Tolerance & Edge Cases

The SkyScout architecture is designed with real-world noise and signal loss in mind. Our closed-loop control handles three critical failure conditions:

* **Detection Loss Recovery:** If YOLO temporarily loses the target due to camera blur or occlusion, the drone utilizes a memory buffer to maintain its last known trajectory while aggressively retrying detection.
* **Micro-Oscillation Damping:** We implemented a spatial deadband to filter out YOLO bounding-box jitter, preventing the drone from entering unstable feedback loops when directly over the target.
* **False-Positive Rejection:** Payload deployment requires a multi-frame consistency lock (12 sequential frames) to guarantee alignment and prevent accidental drops on false detections.
---
