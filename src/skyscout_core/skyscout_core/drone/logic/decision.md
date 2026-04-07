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