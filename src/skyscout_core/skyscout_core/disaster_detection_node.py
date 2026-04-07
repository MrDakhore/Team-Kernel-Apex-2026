#!/usr/bin/env python3


import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from pathlib import Path


import torch
import torchvision.transforms as transforms
import timm
import cv2
import numpy as np


class DisasterDetectionNode(Node):
   def __init__(self):
       super().__init__('disaster_detection_ui')
       self.bridge = CvBridge()


       # ROS2 Configuration
       cam_topic = "/world/iris_disaster_world/model/iris_with_gimbal/model/gimbal/link/pitch_link/sensor/camera/image"
      
       from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
       qos = QoSProfile(
           reliability=ReliabilityPolicy.BEST_EFFORT,
           history=HistoryPolicy.KEEP_LAST,
           depth=10
       )
       self.create_subscription(Image, cam_topic, self.image_callback, qos)


       # Model Initialization
       model_path = str(Path.home() / "aerothon_yolo" / "disaster.pth")
       self.model = timm.create_model('mobilevit_s', pretrained=False, num_classes=4)
       self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
       self.model.eval()


       self.class_names = ['Damage', 'Fire', 'Flood', 'Normal']
       # BGR Colors: Damage (Orange), Fire (Red), Flood (Blue), Normal (Green)
       self.class_colors = [(0, 140, 255), (0, 0, 255), (255, 100, 0), (0, 255, 0)]


       self.transform = transforms.Compose([
           transforms.ToPILImage(),
           transforms.Resize((256, 256)),
           transforms.ToTensor()
       ])


       cv2.namedWindow("MISSION ANALYTICS", cv2.WINDOW_NORMAL)


   def draw_ui(self, frame, label, confidence, all_probs):
       h, w, _ = frame.shape
       active_color = self.class_colors[self.class_names.index(label)]
      
       # 1. PRIMARY OVERLAY (Glass effect header)
       header_h = 70
       overlay = frame.copy()
       cv2.rectangle(overlay, (0, 0), (w, header_h), (20, 20, 20), -1)
       cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
      
       # 2. STATUS INDICATOR
       cv2.line(frame, (0, header_h), (w, header_h), active_color, 2)
       status_text = f"ANALYSIS: {label.upper()}"
       cv2.putText(frame, status_text, (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)


       # 3. ANALYTICS SIDEBAR
       bar_x = 25
       bar_y_start = 110
       panel_w = 240
       panel_h = 140
      
       # Sidebar Background
       sidebar_overlay = frame.copy()
       cv2.rectangle(sidebar_overlay, (15, 85), (panel_w, 85 + panel_h), (10, 10, 10), -1)
       cv2.addWeighted(sidebar_overlay, 0.6, frame, 0.4, 0, frame)


       # 4. CLASS PROBABILITY BARS
       for i, (name, prob) in enumerate(zip(self.class_names, all_probs)):
           y = bar_y_start + (i * 30)
          
           # Label
           cv2.putText(frame, name[:3].upper(), (25, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
          
           # Bar Logic
           full_bar_w = 140
           current_bar_w = int(full_bar_w * prob)
          
           # Draw Bar Background
           cv2.rectangle(frame, (70, y - 12), (70 + full_bar_w, y), (50, 50, 50), -1)
           # Draw Bar Fill
           cv2.rectangle(frame, (70, y - 12), (70 + current_bar_w, y), self.class_colors[i], -1)
          
           # Percentage
           cv2.putText(frame, f"{int(prob*100)}%", (75 + full_bar_w, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)


       # 5. CROSSHAIR / TARGETING RETICLE (Center)
       cx, cy = w // 2, h // 2
       gap = 15
       length = 30
       cv2.line(frame, (cx - gap - length, cy), (cx - gap, cy), (255, 255, 255), 1)
       cv2.line(frame, (cx + gap, cy), (cx + gap + length, cy), (255, 255, 255), 1)
       cv2.line(frame, (cx, cy - gap - length), (cx, cy - gap), (255, 255, 255), 1)
       cv2.line(frame, (cx, cy + gap), (cx, cy + gap + length), (255, 255, 255), 1)


       return frame


   def image_callback(self, msg):
       try:
           frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
          
           # Preprocessing and Inference
           input_tensor = self.transform(frame).unsqueeze(0)
           with torch.no_grad():
               outputs = self.model(input_tensor)
               probs = torch.softmax(outputs, dim=1)[0]
               pred_idx = torch.argmax(probs).item()


           label = self.class_names[pred_idx]
           confidence = probs[pred_idx].item()


           # Appling UI
           processed_frame = self.draw_ui(frame, label, confidence, probs.tolist())


           cv2.imshow("MISSION ANALYTICS", processed_frame)
           cv2.waitKey(1)


       except Exception as e:
           self.get_logger().error(f"Inference Error: {e}")


def main():
   rclpy.init()
   node = DisasterDetectionNode()
   try:
       rclpy.spin(node)
   except KeyboardInterrupt:
       pass
   finally:
       cv2.destroyAllWindows()
       rclpy.shutdown()


if __name__ == "__main__":
   main()
