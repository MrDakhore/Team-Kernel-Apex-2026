# Execution Logic

The execution module translates the decisions into physical actions in the simulation via MAVROS (MAVLink to ROS bridge) and Gazebo topics.

## Core Operations
1. **Dynamic Setpoints:** Converts the smoothed pixel errors into physical meter adjustments using a pixel-to-meter constant (`K_PIX2M`). 
2. **Flight Control:** Publishes `PositionTarget` messages to MAVROS at 10Hz to physically move the drone over the target.
3. **Payload & Mission Resume:** Triggers the ROS-to-Gazebo detachment service, then automatically switches the ArduPilot flight mode back to `AUTO` to continue the mission.

## Logic Snippet
```python
# Convert pixel error to physical setpoint commands
delta_x = max(min(K_PIX2M * avg_dx, MAX_DELTA), -MAX_DELTA)
delta_y = max(min(K_PIX2M * avg_dy, MAX_DELTA), -MAX_DELTA)

self.raw_sp.position.x = self.current_x + delta_y * SMOOTH_FACTOR
self.raw_sp.position.y = self.current_y + delta_x * SMOOTH_FACTOR

# Execution: Payload Drop and Mode Switch
if execution_condition_met:
    # 1. Drop Payload
    self.detach_pub.publish(Empty())
    
    # 2. Resume AUTO Mission
    req = SetMode.Request()
    req.custom_mode = "AUTO"
    self.mode_client.call_async(req)