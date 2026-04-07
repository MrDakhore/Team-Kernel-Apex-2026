from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'skyscout_core'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # This tells ROS 2 where to find your launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        # This tells ROS 2 where to find your Gazebo SDF world files
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*.sdf'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Team Kernel-Apex-2026',
    maintainer_email='your_email@example.com',
    description='SkyScout Autonomous UAV Urban Disaster Response System',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'perception_node = skyscout_core.perception_node:main',
            'decision_node = skyscout_core.decision_node:main',
            'execution_node = skyscout_core.execution_node:main',
            'disaster_detection_node = skyscout_core.disaster_detection_node:main',
            'precision_align_node = skyscout_core.precision_align_node:main',
        ],
    },
)
