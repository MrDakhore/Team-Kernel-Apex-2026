#!/usr/bin/env python3
"""
PrecisionAlignLandNode — ArduPilot SAFE version + Payload Drop + AUTO resume
----------------------------------------------------------------------------
- Passive until helipad detected and vehicle armed
- Aligns over helipad using YOLO detections
- On stable alignment: DROPS PAYLOAD via /payload/detach (ROS→Gazebo)
- Then switches mode back to AUTO so mission continues
- After AUTO request: no more setpoints or mode changes
"""


import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, Empty
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import PositionTarget, State as MavState
from mavros_msgs.srv import SetMode, CommandLong
from ultralytics import YOLO
from cv_bridge import CvBridge
from pathlib import Path
from collections import deque
import cv2
import time
import numpy as np


# ========== CONFIG ==========
ALT_HOLD = 5.0
K_PIX2M = 0.0085
MAX_DELTA = 0.5
LAND_ERROR_PIX = 20 
REQUIRED_GOOD_FRAMES = 12
AVG_WINDOW = 5
DEAD_BAND = 5
SMOOTH_FACTOR = 0.65
DETECT_HOLD_TIME = 1.0
PUBLISH_HZ = 10.0
# ============================




class PrecisionAlignLandNode(Node):
   def __init__(self):
       super().__init__('precision_align_land_ardupilot')


       # Load YOLO
       model_path = str(Path.home() / "aerothon_yolo" / "target.pt")
       self.model = YOLO(model_path)


       # MAVROS state subscriber
       self.mav_state = None
       self.sub_state = self.create_subscription(
           MavState, "/mavros/state", self.mav_state_cb, 10
       )


       # MAVROS setpoints + services
       self.setpoint_pub = self.create_publisher(
           PositionTarget, "/mavros/setpoint_raw/local", 10
       )
       self.mode_client = self.create_client(SetMode, "/mavros/set_mode")
       self.cmd_client = self.create_client(CommandLong, "/mavros/cmd/command")


       # Detection status
       self.detection_pub = self.create_publisher(Bool, "/helipad/detected", 10)


       # Payload detach
       self.detach_pub = self.create_publisher(Empty, "/payload/detach", 10)


       # Camera
       cam_topic = "/world/iris_disaster_world/model/iris_with_gimbal/model/gimbal/link/pitch_link/sensor/camera/image"
       self.sub_img = self.create_subscription(
           Image, cam_topic, self.detect_callback, qos_profile_sensor_data
       )


       # Pose
       self.sub_pose = self.create_subscription(
           PoseStamped, "/mavros/local_position/pose",
           self.pose_callback, qos_profile_sensor_data
       )


       self.bridge = CvBridge()
       self.current_x = self.current_y = self.current_z = 0.0


       # RAW SETPOINT
       self.raw_sp = PositionTarget()
       self.raw_sp.coordinate_frame = PositionTarget.FRAME_LOCAL_NED
       self.raw_sp.type_mask = (
           PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY |
           PositionTarget.IGNORE_VZ | PositionTarget.IGNORE_AFX |
           PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
           PositionTarget.IGNORE_YAW_RATE
       )
       self.raw_sp.position.z = ALT_HOLD


       # Filters
       self.dx_window = deque(maxlen=AVG_WINDOW)
       self.dy_window = deque(maxlen=AVG_WINDOW)
       self.good_align_count = 0


       # State flags
       self.guided_enabled = False      
       self.landing_sent = False        
       self.detect_start = None
       self.activated = False           
       self.payload_dropped = False     


       # HUD Data Cache
       self.hud_data = {
           'yolo_conf': 0.0,
           'delta_x': 0.0,
           'delta_y': 0.0,
           'dx_pix': 0,
           'dy_pix': 0
       }


       # FPS
       self.prev_time = time.time()
       self.fps = 0.0


       cv2.namedWindow("Drone Terminal - Optical Targeting", cv2.WINDOW_NORMAL)
       self.create_timer(1.0 / PUBLISH_HZ, self.publish_setpoint)


       self.get_logger().info("🚁 SAFE Precision Align node loaded. Passive until helipad detection & armed.")


   def mav_state_cb(self, msg):
       self.mav_state = msg


   def pose_callback(self, msg):
       self.current_x = msg.pose.position.x
       self.current_y = msg.pose.position.y
       self.current_z = msg.pose.position.z


   def detect_callback(self, msg):
       try:
           now = time.time()
           self.fps = 1.0 / max(now - self.prev_time, 1e-6)
           self.prev_time = now


           frame = self.bridge.imgmsg_to_cv2(msg, "rgb8")
           frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
           visual = frame.copy()


           h, w = frame.shape[:2]
           cx_img, cy_img = w // 2, h // 2


           results = self.model.predict(frame, conf=0.7, verbose=False)
           detected = len(results[0].boxes) > 0
           self.detection_pub.publish(Bool(data=detected))


           status = "SCANNING / PASSIVE"
           target_color = (255, 150, 0)  # Amber for scanning/detecting


           # Reset HUD data if nothing detected
           if not detected:
               self.hud_data['yolo_conf'] = 0.0
               self.hud_data['dx_pix'] = 0
               self.hud_data['dy_pix'] = 0


           # ================== PASSIVE MODE ==================
           if not self.activated:
               if detected:
                   box_data = max(results[0].boxes, key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1]))
                   self.hud_data['yolo_conf'] = float(box_data.conf[0])


                   if self.detect_start is None:
                       self.detect_start = now
                   elif now - self.detect_start >= DETECT_HOLD_TIME:
                       if not self.mav_state:
                           self.get_logger().warn("⚠ MAV state unknown")
                       elif self.mav_state.armed:
                           self.enable_guided()
                           self.guided_enabled = True
                           self.activated = True
               else:
                   self.detect_start = None


           # ================== ACTIVE MODE ==================
           else:
               status = "ENGAGED / ALIGNING"
               if self.landing_sent:
                   status = "MISSION AUTO RESUMED"
                   target_color = (150, 150, 150) # Gray out target when done
               elif self.payload_dropped:
                   status = "PAYLOAD DEPLOYED"
                   target_color = (0, 255, 255) # Yellow on drop


               if detected and not self.landing_sent:
                   box_data = max(results[0].boxes, key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1]))
                   self.hud_data['yolo_conf'] = float(box_data.conf[0])
                  
                   x1, y1, x2, y2 = box_data.xyxy[0].cpu().numpy()
                   cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)


                   dx_pix = cx - cx_img
                   dy_pix = cy - cy_img


                   self.hud_data['dx_pix'] = dx_pix
                   self.hud_data['dy_pix'] = dy_pix


                   if abs(dx_pix) < DEAD_BAND: dx_pix = 0
                   if abs(dy_pix) < DEAD_BAND: dy_pix = 0


                   self.dx_window.append(dx_pix)
                   self.dy_window.append(dy_pix)


                   avg_dx = sum(self.dx_window) / len(self.dx_window)
                   avg_dy = sum(self.dy_window) / len(self.dy_window)


                   delta_x = max(min(K_PIX2M * avg_dx, MAX_DELTA), -MAX_DELTA)
                   delta_y = max(min(K_PIX2M * avg_dy, MAX_DELTA), -MAX_DELTA)
                  
                   self.hud_data['delta_x'] = delta_x
                   self.hud_data['delta_y'] = delta_y


                   self.raw_sp.position.x = self.current_x + delta_y * SMOOTH_FACTOR
                   self.raw_sp.position.y = self.current_y + delta_x * SMOOTH_FACTOR


                   aligned = abs(avg_dx) < LAND_ERROR_PIX and abs(avg_dy) < LAND_ERROR_PIX
                   self.good_align_count = self.good_align_count + 1 if aligned else 0


                   if aligned:
                       target_color = (0, 255, 0) # Green for lock
                       status = "TARGET LOCKED"


                   if self.good_align_count >= REQUIRED_GOOD_FRAMES and not self.payload_dropped:
                       self.detach_pub.publish(Empty())
                       self.payload_dropped = True


                       if not self.landing_sent:
                           req = SetMode.Request()
                           req.custom_mode = "AUTO"
                           self.mode_client.call_async(req)
                           self.landing_sent = True


                   # Target Visualization
                   cv2.rectangle(visual, (int(x1), int(y1)), (int(x2), int(y2)), target_color, 1)
                   # Outer target corners
                   ln = 15
                   cv2.line(visual, (int(x1), int(y1)), (int(x1)+ln, int(y1)), target_color, 2)
                   cv2.line(visual, (int(x1), int(y1)), (int(x1), int(y1)+ln), target_color, 2)
                   cv2.line(visual, (int(x2), int(y2)), (int(x2)-ln, int(y2)), target_color, 2)
                   cv2.line(visual, (int(x2), int(y2)), (int(x2), int(y2)-ln), target_color, 2)
                  
                   # Target center point
                   cv2.circle(visual, (cx, cy), 3, target_color, -1)
                   # Line connecting center to target
                   cv2.line(visual, (cx_img, cy_img), (cx, cy), target_color, 1, cv2.LINE_AA)


           self.draw_hud(visual, cx_img, cy_img, status)
           cv2.imshow("Drone Terminal - Optical Targeting", visual)
           cv2.waitKey(1)


       except Exception as e:
           self.get_logger().error(f"❌ detect_callback: {e}")


   def enable_guided(self):
       req = SetMode.Request()
       req.custom_mode = "GUIDED"
       self.mode_client.call_async(req)


       cmd = CommandLong.Request()
       cmd.command = 92
       cmd.param1 = 1.0
       self.cmd_client.call_async(cmd)


   def publish_setpoint(self):
       if not self.activated or self.landing_sent:
           return
       self.raw_sp.header.stamp = self.get_clock().now().to_msg()
       self.setpoint_pub.publish(self.raw_sp)


   # ------------------------------------------------------------------
   def draw_hud(self, visual, cx_img, cy_img, status):
       """Draws a data-rich, sci-fi/military style HUD."""
       h, w = visual.shape[:2]
      
       main_color = (0, 255, 150)  # Neon Cyan/Green
       alert_color = (0, 100, 255) # Orange/Red for warnings
       text_color = (220, 255, 220)


       # 1. Advanced Center Reticle
       gap = 25
       length = 20
       # Crosshairs
       cv2.line(visual, (cx_img - gap - length, cy_img), (cx_img - gap, cy_img), main_color, 1, cv2.LINE_AA)
       cv2.line(visual, (cx_img + gap, cy_img), (cx_img + gap + length, cy_img), main_color, 1, cv2.LINE_AA)
       cv2.line(visual, (cx_img, cy_img - gap - length), (cx_img, cy_img - gap), main_color, 1, cv2.LINE_AA)
       cv2.line(visual, (cx_img, cy_img + gap), (cx_img, cy_img + gap + length), main_color, 1, cv2.LINE_AA)
      
       # Deadband circle & tolerance ring
       cv2.circle(visual, (cx_img, cy_img), DEAD_BAND, (0, 100, 50), 1, cv2.LINE_AA)
       cv2.circle(visual, (cx_img, cy_img), LAND_ERROR_PIX, main_color, 1, cv2.LINE_AA)


       # 2. Camera Corner Brackets (Full Screen)
       cl = 40 # corner length
       cv2.line(visual, (20, 20), (20+cl, 20), main_color, 2)
       cv2.line(visual, (20, 20), (20, 20+cl), main_color, 2)
       cv2.line(visual, (w-20, 20), (w-20-cl, 20), main_color, 2)
       cv2.line(visual, (w-20, 20), (w-20, 20+cl), main_color, 2)
       cv2.line(visual, (20, h-20), (20+cl, h-20), main_color, 2)
       cv2.line(visual, (20, h-20), (20, h-20-cl), main_color, 2)
       cv2.line(visual, (w-20, h-20), (w-20-cl, h-20), main_color, 2)
       cv2.line(visual, (w-20, h-20), (w-20, h-20-cl), main_color, 2)


       def put_text(img, text, pt, scale=0.45, color=text_color, align="left"):
           font = cv2.FONT_HERSHEY_SIMPLEX
           thickness = 1
           (tw, _), _ = cv2.getTextSize(text, font, scale, thickness)
           x, y = pt
           if align == "right": x -= tw
           cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)


       # 3. Top Left Data Block (System Status)
       start_y = 40
       put_text(visual, f"SYS_MODE  : {status}", (40, start_y), color=main_color)
       put_text(visual, f"ARM_STATE : {'ARMED' if self.mav_state and self.mav_state.armed else 'DISARMED'}", (40, start_y + 20))
       put_text(visual, f"MAV_MODE  : {self.mav_state.mode if self.mav_state else 'UNKNOWN'}", (40, start_y + 40))
      
       # 4. Top Right Data Block (Telemetry)
       put_text(visual, f"OPTICAL_FPS : {self.fps:.1f}", (w - 40, 40), align="right")
       put_text(visual, f"SYS_TIME    : {time.strftime('%H:%M:%S')}", (w - 40, 60), align="right")


       # 5. Bottom Right Data Block (Spatial Coordinates & Errors)
       br_y = h - 100
       put_text(visual, f"LOCAL_X : {self.current_x:>6.2f} m", (w - 40, br_y), align="right")
       put_text(visual, f"LOCAL_Y : {self.current_y:>6.2f} m", (w - 40, br_y + 20), align="right")
       put_text(visual, f"ALT_Z   : {self.current_z:>6.2f} m", (w - 40, br_y + 40), color=main_color, align="right")
      
       if self.activated and not self.landing_sent:
           put_text(visual, f"ERR_DX  : {self.hud_data['delta_x']:>6.3f} m", (w - 40, br_y + 60), align="right")
           put_text(visual, f"ERR_DY  : {self.hud_data['delta_y']:>6.3f} m", (w - 40, br_y + 80), align="right")


       # 6. Bottom Left Data Block (Targeting Metrics & Progress Bar)
       bl_y = h - 100
       put_text(visual, f"AI_CONF    : {self.hud_data['yolo_conf']*100:.1f}%", (40, bl_y))
       put_text(visual, f"OFFSET_PX  : {self.hud_data['dx_pix']}, {self.hud_data['dy_pix']}", (40, bl_y + 20))


       # Progress Bar for Lock
       align_pct = min(100.0, (self.good_align_count / REQUIRED_GOOD_FRAMES) * 100)
       put_text(visual, f"ALIGN_LOCK : {align_pct:.0f}%", (40, bl_y + 40), color=main_color)
      
       bar_w = 150
       bar_h = 8
       bar_x = 40
       bar_y = bl_y + 50
       # Outline
       cv2.rectangle(visual, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (100, 100, 100), 1)
       # Fill
       fill_w = int((align_pct / 100.0) * bar_w)
       if fill_w > 0:
           fill_color = (0, 255, 0) if align_pct == 100 else main_color
           cv2.rectangle(visual, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), fill_color, -1)




def main(args=None):
   rclpy.init(args=args)
   node = PrecisionAlignLandNode()
   try:
       rclpy.spin(node)
   except KeyboardInterrupt:
       pass
   cv2.destroyAllWindows()
   rclpy.shutdown()


if __name__ == "__main__":
   main()
