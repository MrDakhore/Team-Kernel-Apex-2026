# GUI & Telemetry Logic

The GUI module renders a custom OpenCV Mission Analytics Dashboard to provide operators and judges with real-time insight into the drone's autonomous processes.

## Core Operations
1. **Dynamic Coloring:** Changes the UI color palette based on system state (Amber for Scanning, Green for Locked, Yellow for Payload Deployed).
2. **Targeting Reticle:** Draws geometric brackets around the detected target and calculates a line connecting the camera center to the target center.
3. **Telemetry Overlay:** Displays local spatial coordinates (X, Y, Z), YOLO AI confidence percentages, system mode, and an active progress bar showing the payload lock-on status.

## Logic Snippet
```python
def draw_hud(self, visual, cx_img, cy_img, status):
    main_color = (0, 255, 150)  # Neon Cyan/Green
    
    # Draw Deadband & Tolerance Rings
    cv2.circle(visual, (cx_img, cy_img), DEAD_BAND, (0, 100, 50), 1, cv2.LINE_AA)
    cv2.circle(visual, (cx_img, cy_img), LAND_ERROR_PIX, main_color, 1, cv2.LINE_AA)
    
    # Draw Telemetry Text
    cv2.putText(visual, f"SYS_MODE  : {status}", (40, 40), font, scale, main_color)
    cv2.putText(visual, f"AI_CONF    : {self.hud_data['yolo_conf']*100:.1f}%", (40, h - 100))

    # Draw Lock-On Progress Bar
    align_pct = min(100.0, (self.good_align_count / REQUIRED_GOOD_FRAMES) * 100)
    fill_w = int((align_pct / 100.0) * bar_w)
    cv2.rectangle(visual, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), (0, 255, 0), -1)