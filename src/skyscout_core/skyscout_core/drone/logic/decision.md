# Decision Logic

The decision module is the "brain" of the targeting system. It takes the pixel offsets from the perception module and determines if the drone is aligned well enough to drop the payload.

## Core Operations
1. **Noise Filtering:** Uses a moving average window (`deque(maxlen=AVG_WINDOW)`) to smooth out sudden camera jerks or YOLO bounding box jitter.
2. **Deadband Implementation:** Ignores minor pixel deviations (`DEAD_BAND`) to prevent the drone from endlessly micro-correcting.
3. **Alignment Lock:** The system must register a continuous "good alignment" for a set number of frames (`REQUIRED_GOOD_FRAMES`) before it decides to deploy the payload, ensuring safe and accurate drops.

## Logic Snippet
```python
# Deadband and Noise Filtering
if abs(dx_pix) < DEAD_BAND: dx_pix = 0
if abs(dy_pix) < DEAD_BAND: dy_pix = 0

self.dx_window.append(dx_pix)
self.dy_window.append(dy_pix)
avg_dx = sum(self.dx_window) / len(self.dx_window)

# Lock-on Evaluation
aligned = abs(avg_dx) < LAND_ERROR_PIX and abs(avg_dy) < LAND_ERROR_PIX
self.good_align_count = self.good_align_count + 1 if aligned else 0

if self.good_align_count >= REQUIRED_GOOD_FRAMES and not self.payload_dropped:
    # DECISION MADE: Deploy Payload
    self.payload_dropped = True
    ## Failsafe Mechanisms

### Case 1: Target Detection Lost
In a dynamic disaster environment, the camera feed may temporarily lose the target.
* **Mechanism:** The system maintains a `detect_start` timer and utilizes the `dx_window` / `dy_window` buffers. If a frame drops the detection, the drone temporarily relies on the smoothed historical average to drift safely in the last known correct direction while waiting for the YOLO confidence to recover.

### Case 2: Alignment Instability (Jitter)
Computer vision bounding boxes naturally jitter by a few pixels every frame, which can cause erratic drone movements.
* **Mechanism:** A `DEAD_BAND` threshold (5 pixels) is applied. If the pixel error falls within this radius, the error is artificially clamped to `0`. This forces the PID/control loop to settle and stop moving, stabilizing the drone for the final drop.

### Case 3: Premature / Unconfirmed Drops
A single false-positive frame could trigger a payload drop outside the designated zone.
* **Mechanism:** The `REQUIRED_GOOD_FRAMES` (12 frames) counter acts as a strict safety interlock. The system must register continuous, stable alignment across multiple frames. If even a single frame breaks the alignment condition, the counter resets to `0`, aborting the drop sequence until stability is regained.