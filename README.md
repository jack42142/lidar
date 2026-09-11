# Lidar TUI Application

A terminal user interface for scanning 3D surfaces with lidar and displaying the resulting model.
Supports both simulated data and real iPhone LiDAR data (via network stream).

## Features
- Textual-based terminal UI
- Simulated lidar data generation (for testing without hardware)
- Real iPhone LiDAR support (via network stream)
- 3D point cloud visualization using matplotlib
- Start/stop scan controls
- Status updates during scanning process
- Data source selection (Simulation or iPhone LiDAR)

## Requirements
- Python 3.7+
- Dependencies listed in requirements.txt

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```bash
   python lidar_tui.py
   ```

2. In the TUI:
   - Select data source: "Simulation" or "iPhone LiDAR (Network)"
   - Press "Start Scan" to begin scanning
   - For Simulation: App generates synthetic point cloud data representing a 3D scene
   - For iPhone LiDAR: App waits for depth data streamed from your iPhone on port 9999
   - After data acquisition, a matplotlib 3D visualization window will open
   - Close the visualization window to return to the TUI
   - Press "Stop Scan" to cancel scanning at any time
   - Press "Start Scan" again to perform another scan

## iPhone LiDAR Setup
To use real iPhone LiDAR data:

1. **On your iPhone**, you need an app that can stream LiDAR depth data. Examples include:
   - Custom apps using ARKit/RealityKit
   - Third-party LiDAR streaming apps from the App Store
   - Developer tools like Apple's Reality Composer Pro

2. **Configure the streaming app** to:
   - Send depth map data as JSON over TCP
   - Stream to your computer's IP address on port 9999
   - Format: `{"depth_map": [[float values...]]}`, where the 2D array represents depth values in meters

3. **On your computer**:
   - Ensure port 9999 is accessible (check firewall settings)
   - Run the TUI application
   - Select "iPhone LiDAR (Network)" as the data source
   - Press "Start Scan"

## Notes
- This application includes simulated lidar data for demonstration and testing
- For real iPhone LiDAR, you need to provide the depth streaming mechanism
- The visualization uses matplotlib which provides interactive controls:
  - Rotate: Left mouse button + drag
  - Zoom: Scroll wheel
  - Pan: Right mouse button + drag or Ctrl + Left mouse button + drag
  - Color bar shows height (Z-axis) values

## Dependencies
- [Textual](https://textual.textualize.io/) - For the terminal user interface
- [NumPy](https://numpy.org/) - For numerical operations
- [Matplotlib](https://matplotlib.org/) - For 3D plotting and visualization

## License
MIT