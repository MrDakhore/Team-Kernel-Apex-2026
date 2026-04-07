# Perception Logic

The perception module acts as the "eyes" of the SkyScout drone, processing raw camera feeds from the Gazebo simulation to detect mission-critical targets.

## Core Operations
1. **Image Subscription:** The system subscribes to the gimbal camera topic (`/world/iris_disaster_world/.../image`).
2. **Real-Time Inference:** A YOLO (You Only Look Once) model evaluates each frame to detect the helipad or target zone.
3. **Spatial Calculation:** If a target is detected, the bounding box is extracted and its exact center pixel `(cx, cy)` is calculated relative to the image center `(cx_img, cy_img)`.

## Logic Snippet
```python
# Frame acquisition and inference
frame = self.bridge.imgmsg_to_cv2(msg, "rgb8")
results = self.model.predict(frame, conf=0.7, verbose=False)
detected = len(results[0].boxes) > 0

# Target extraction
if detected:
    box_data = max(results[0].boxes, key=lambda b: (b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1]))
    x1, y1, x2, y2 = box_data.xyxy[0].cpu().numpy()
    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
    
    # Calculate pixel offset from camera center
    dx_pix = cx - cx_img
    dy_pix = cy - cy_img