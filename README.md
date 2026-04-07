**Team:** Kernel Apex 2026
# 🚁 SkyScout: Autonomous UAV Urban Disaster Response System

Domain:Smart City 
Status:Prototype / Hackathon Build 

SkyScout is an Autonomous UAV Urban Disaster Response System. Built on open-source architecture while leveraging industry-grade systems, it provides a cost-effective and scalable solution for real-world deployment.

---

## 🚨 The Problem & Our Solution
The first 60 minutes after a disaster are the most critical for saving lives and minimizing damage. Current systems rely heavily on slow human reporting and manual deployment. 

SkyScout solves this by deploying an autonomous surveillance drone that continuously monitors urban areas using onboard sensors and cameras. It uses AI/ML algorithms to detect disasters such as fires, smoke, or structural damage. Once detected, the system automatically identifies the exact location, navigates to the affected area, and performs immediate rapid response actions like dropping emergency medical kits.

---

## ✨ Core Features
* **Real-Time Vision Processing**: Continuous frame-by-frame analysis using YOLO for detecting disaster zones.
* **Autonomous Alignment System**: Uses image-based error correction to precisely align the drone over the target.
* **Closed-Loop Control Logic**: A robust Detection → Alignment → Validation → Action* pipeline ensures a stable response.
* **Autonomous Payload Deployment:** Automatically triggers payload drops after stable alignment and resumes its mission.

---

## 🛠️ Tech Stack
This project utilizes a highly decentralized node-based framework, allowing perception, decision, and execution to run independently.
* **Middleware / Framework:** ROS2 Humble 
* **Simulation Environment:** Gazebo Harmonic (Digital Twin) 
* **Flight Controller Stack:** Ardupilot SITL & MAVROS 
* **Ground Control Station:** QGroundControl 
* **Computer Vision:** YOLOv8 
* **Primary Language:** Python 

---

## ⚙️ Hardware Stack & Expected Cost (Real-World Deployment)
To achieve low-cost scalability, SkyScout is designed to run entirely on Commercial-Off-The-Shelf (COTS) hardware. The estimated cost for a fully autonomous prototype is between **₹33,500 - ₹44,000**.

| Component Category | Expected Hardware |
| :--- | :--- |
| **Companion Computer** | NVIDIA Jetson Nano (4GB) or Raspberry Pi 5 (8GB) |
| **Flight Controller** | Pixhawk 2.4.8 + M8N GPS |
| **Vision System** | Raspberry Pi Camera V3 or Logitech C920 |
| **Drone Base Kit** | F450 / S500 Frame, BLDC Motors, ESCs |
| **Actuator** | MG995 Servo Motor (for payload drop) |

---

## 📂 Repository Structure
```text
SkyScout/
├── README.md                
├── requirements.txt         # Python dependencies (YOLOv8, OpenCV, etc.)
├── assets/                  # Demo GIFs and System Architecture diagrams
├── models/                  
│   └── yolov8_disaster.pt   # Custom trained weights for disaster detection
└── src/                     # ROS 2 Workspace
    └── skyscout_core/
        ├── launch/          
        │   └── skyscout_sim.launch.py
        ├── worlds/
        │   └── disaster_environment.sdf 
        ├── config/          
        │   └── drone_params.yaml
        └── └── skyscout_core/   
            ├── disaster_detection_node.py  # MobileViT disaster classification
            └── precision_align_node.py   # Integrated alignment & landing HUD
```
git clone https://github.com/yourusername/SkyScout.git
cd SkyScout

pip install -r requirements.txt
  
cd src
colcon build --symlink-install
source install/setup.bash

# Launch the Gazebo digital twin and the ROS 2 control nodes
ros2 launch skyscout_core skyscout_sim.launch.py
