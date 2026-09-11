# Building the iOS LiDAR Streamer App

## Prerequisites
1. macOS with Xcode 13.0 or later installed
2. iOS device with LiDAR sensor (iPhone 12 Pro/Pro Max or later, iPad Pro 2020 or later)
3. Apple Developer account (free for personal use, paid for distribution)

## Step-by-Step Build Instructions

### Method 1: Using Xcode (Recommended)

1. **Create the project folder structure**:
   ```
   iOS_LiDAR_Streamer/
   ├── iOS_LiDAR_Streamer.xcodeproj/
   │   └── project.pbxproj
   ├── iOS_LiDAR_Streamer/
   │   ├── Info.plist
   │   ├── LiDARStreamerApp.swift
   │   ├── ContentView.swift
   │   └── LiDARStreamerViewModel.swift
   └── README.md
   ```

2. **Create the Xcode project**:
   - Open Xcode
   - Select "Create a new Xcode project"
   - Choose "App" under iOS tab
   - Click Next
   - Set Product Name: "iOS_LiDAR_Streamer"
   - Set Team: Your Apple Developer account
   - Set Organization Identifier: "com.yourname" (or similar)
   - Set Interface: "SwiftUI"
   - Set Life Cycle: "SwiftUI App"
   - Language: "Swift"
   - Click Next
   - Choose a location to save the project (select the iOS_LiDAR_Streamer folder)
   - Click Create

3. **Replace the generated files**:
   - Replace `LiDARStreamerApp.swift` with the provided version
   - Replace `ContentView.swift` with the provided version
   - Add `LiDARStreamerViewModel.swift` as a new file
   - Replace `Info.plist` with the provided version

4. **Add required frameworks**:
   - Select the project in the Project Navigator
   - Select the iOS_LiDAR_Streamer target
   - Go to the "General" tab
   - Under "Frameworks, Libraries, and Embedded Content", click "+"
   - Add: ARKit.framework

5. **Configure signing**:
   - In the "Signing & Capabilities" tab
   - Ensure "Automatically manage signing" is checked
   - Select your team

6. **Build and run**:
   - Connect your iOS device via USB
   - Select your device as the build target
   - Click the Build and Run button (▶️)

### Method 2: Using Swift Package Manager (Alternative)

If you prefer to use SwiftPM:

1. Create a new Swift package:
   ```bash
   mkdir iOS_LiDAR_Streamer && cd iOS_LiDAR_Streamer
   swift package init --type executable
   ```

2. Replace the Package.swift with:
   ```swift
   // swift-tools-version:5.5
   import PackageDescription

   let package = Package(
       name: "iOS_LiDAR_Streamer",
       platforms: [
           .iOS(.v14)
       ],
       products: [
           .executable(
               name: "iOS_LiDAR_Streamer",
               targets: ["iOS_LiDAR_Streamer"])
       ],
       dependencies: [],
       targets: [
           .target(
               name: "iOS_LiDAR_Streamer",
               dependencies: []),
           .testTarget(
               name: "iOS_LiDAR_StreamerTests",
               dependencies: ["iOS_LiDAR_Streamer"])
       ]
   )
   ```

3. Replace Sources/iOS_LiDAR_Streamer/main.swift with your SwiftUI app code

4. Build with: `swift build -Xswiftc "-target" -Xswiftc "arm64-apple-ios14.0"`

## Usage Instructions

1. **On your iOS device**:
   - Launch the "LiDAR Streamer" app
   - Enter your computer's IP address (find this in System Preferences → Network)
   - Ensure port is set to 9999
   - Tap "Start Streaming"

2. **On your computer running the Python TUI**:
   - Make sure port 9999 is accessible (adjust firewall if needed)
   - Run the lidar_tui.py application
   - Select "iPhone LiDAR (Network)" as the data source
   - Press "Start Scan"
   - The app will wait for and display the incoming LiDAR data

## Troubleshooting

- **Connection refused**: Check that your computer's firewall allows incoming connections on port 9999
- **No data received**: Verify the iOS device and computer are on the same network
- **LiDAR not available**: Ensure you're using a device with LiDAR sensor (iPhone 12 Pro/Pro Max or later, iPad Pro 2020 or later)
- **Camera access denied**: Go to Settings → Privacy & Security → Camera and enable it for the app

## Notes

- The app streams depth data at approximately 30 FPS
- Depth values are in meters from the camera sensor
- The data format is JSON: `{"depth_map": [[float...]], "timestamp": double, "width": int, "height": int}`
- Make sure to stop streaming when done to conserve battery and network resources