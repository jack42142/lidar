# iOS LiDAR Streamer for TUI App

An iOS application that streams LiDAR depth data from compatible iOS devices (iPhone Pro models, iPad Pro) to the Python Lidar TUI application over TCP.

## Requirements
- iOS device with LiDAR sensor (iPhone 12 Pro/Pro Max or later, iPad Pro 2020 or later)
- Xcode 13.0 or later
- iOS 14.0 or later

## How It Works
1. Uses ARKit to access the LiDAR sensor's depth data
2. Converts depth data to a format suitable for transmission
3. Streams the data as JSON over TCP to a specified IP address and port
4. Designed to work with the Python Lidar TUI application

## Setup Instructions
1. Copy this entire folder to your macOS machine with Xcode installed
2. Open `iOS_LiDAR_Streamer.xcodeproj` in Xcode
3. Configure your development team in the project settings
4. Build and run on a compatible iOS device
5. In the app, enter the IP address of your computer running the Python TUI app
6. Tap "Start Streaming" to begin transmitting LiDAR data
7. In the Python TUI app, select "iPhone LiDAR (Network)" and press "Start Scan"

## Data Format
The app streams data as JSON with this format:
```
{"depth_map": [[float values...]], "timestamp": double, "width": int, "height": int}
```
Where `depth_map` is a 2D array of depth values in meters.

## Notes
- Make sure your iOS device and computer are on the same network
- The Python TUI app listens on port 9999 by default
- You may need to adjust firewall settings to allow incoming connections
- Depth values represent distance from the camera in meters