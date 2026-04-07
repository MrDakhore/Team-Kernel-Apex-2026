**Team:** Kernel Apex 2026
#  SkyScout: Autonomous UAV Urban Disaster Response System

Domain:Smart City 
Status:Prototype / Hackathon Build 

SkyScout is an Autonomous UAV Urban Disaster Response System. Built on open-source architecture while leveraging industry-grade systems, it provides a cost-effective and scalable solution for real-world deployment.

---

##  The Problem & Our Solution
The first 60 minutes after a disaster are the most critical for saving lives and minimizing damage. Current systems rely heavily on slow human reporting and manual deployment. 

SkyScout solves this by deploying an autonomous surveillance drone that continuously monitors urban areas using onboard sensors and cameras. It uses AI/ML algorithms to detect disasters such as fires, smoke, or structural damage. Once detected, the system automatically identifies the exact location, navigates to the affected area, and performs immediate rapid response actions like dropping emergency medical kits.

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

##  Repository Structure
```text
SkyScout/
│
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
│
├── assets/
│   └── architecture.png
│
├── models/
│   ├── target.pt                   # YOLO alignment model
│   └── disaster.pth                # MobileViT classification model
│
└── src/
    └── skyscout_core/
        ├── setup.py                # ROS 2 package build instructions
        ├── package.xml             # ROS 2 package dependencies
        │
        ├── launch/
        │   └── system.launch.py    # Master startup file for Gazebo & Nodes
        │
        ├── config/
        │   └── drone_params.yaml   # Centralized tuning variables
        │
        ├── drone/                  # Core Python Executables
        │   ├── __init__.py
        │   ├── core/
        │   │   ├── __init__.py
        │   │   └── precision_align_node.py
        │   │
        │   ├── detection/
        │   │   ├── __init__.py
        │   │   └── disaster_detection.py
        │   │
        │   └── logic/              # System Architecture Documentation
        │       ├── perception.md
        │       ├── decision.md
        │       ├── execution.md
        │       └── gui.md
        │
        ├── worlds/                 # Gazebo Simulation Environments
        │   ├── disaster_maps/
        │   │   ├── city_ruins.sdf
        │   │   └── collapsed_building.sdf
        │   │
        │   └── objects/
        │       └── models_source.md
        │
        └── docs/
            ├── architecture.md
            └── pipeline.md
```
git clone https://github.com/yourusername/SkyScout.git
cd SkyScout

pip install -r requirements.txt
  
cd src
colcon build --symlink-install
source install/setup.bash

# Launch the Gazebo digital twin and the ROS 2 control nodes
ros2 launch skyscout_core skyscout_sim.launch.py
