import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Define Package Paths
    pkg_name = 'skyscout_core'
    pkg_dir = get_package_share_directory(pkg_name)
    
    # Path to your config and world files
    config_file = os.path.join(pkg_dir, 'config', 'drone_params.yaml')
    world_file = os.path.join(pkg_dir, 'worlds', 'disaster_environment.sdf') # Change if your main world has a different name

    # 2. Setup Gazebo Simulation
    # Note: Adjust 'gazebo_ros' depending on if you are using Gazebo Classic or Ignition/Gazebo Sim
    start_gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', world_file, '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    # 3. Setup SkyScout Nodes
    disaster_detection_node = Node(
        package=pkg_name,
        executable='disaster_detection', # Matches setup.py entry_point
        name='disaster_detection',
        output='screen',
        parameters=[config_file]
    )

    precision_align_node = Node(
        package=pkg_name,
        executable='precision_align_node', # Matches setup.py entry_point
        name='precision_align_node',
        output='screen',
        parameters=[config_file]
    )

    # 4. Create and Return the Launch Description
    return LaunchDescription([
        start_gazebo,
        disaster_detection_node,
        precision_align_node
    ])