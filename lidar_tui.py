#!/usr/bin/env python3
"""
Lidar TUI Application
A terminal user interface for scanning 3D surfaces with lidar and displaying the resulting model.
Supports both simulated data and real iPhone LiDAR data (via network stream).
"""

import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Label, Select
from textual.containers import Container, Vertical, Horizontal
from textual.worker import Worker, WorkerState
import socket
import json


class LidarTUI(App):
    """A Textual app for lidar scanning and 3D model visualization."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 80%;
        height: 80%;
        border: thick green;
        padding: 1 2;
    }

    #status-label {
        text-align: center;
        margin: 1 0;
        height: 3;
    }

    #scan-button {
        width: 100%;
        height: 3;
        margin: 1 0;
    }

    #info-label {
        text-align: center;
        margin: 1 0;
        color: cyan;
    }

    #controls-container {
        height: auto;
        margin: 1 0;
    }

    Select {
        width: 30%;
    }
    """

    def __init__(self):
        super().__init__()
        self.is_scanning = False
        self.point_cloud = None
        self.data_source = "simulation"  # or "iphone"
        self.iphone_socket = None
        self.iphone_data_thread = None
        self.latest_depth_map = None
        self.depth_map_lock = threading.Lock()
        self.status_update_queue = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Container(
            Vertical(
                Label("Lidar 3D Scanner", id="title-label"),
                Horizontal(
                    Label("Data Source: ", id="source-label"),
                    Select(
                        [
                            ("Simulation", "simulation"),
                            ("iPhone LiDAR (Network)", "iphone")
                        ],
                        value="simulation",
                        id="source-select"
                    ),
                    id="controls-container"
                ),
                Static("Ready to scan. Press the button to start.", id="status-label"),
                Button("Start Scan", id="scan-button", variant="primary"),
                Label("Note: For iPhone LiDAR, ensure device is streaming depth data to this machine on port 9999", id="info-label"),
                id="main-container"
            )
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle source selection changes."""
        if event.select.id == "source-select":
            self.data_source = event.value
            # Update status directly since we're in the main thread
            self.query_one("#status-label").update(f"Data source set to: {self.data_source}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "scan-button":
            if not self.is_scanning:
                self.start_scan()
            else:
                self.stop_scan()

    def start_scan(self) -> None:
        """Start the lidar scanning process."""
        self.is_scanning = True
        self.query_one("#scan-button").label = "Stop Scan"
        self.query_one("#scan-button").variant = "error"

        if self.data_source == "iphone":
            self.query_one("#status-label").update("Connecting to iPhone LiDAR stream...")
            # Start iPhone data receiver thread
            self.iphone_data_thread = threading.Thread(target=self.iphone_data_receiver, daemon=True)
            self.iphone_data_thread.start()
            # Wait a moment for connection to establish
            time.sleep(0.5)
        else:
            self.query_one("#status-label").update("Scanning... (simulating lidar data)")

        # Start scanning worker
        self.run_worker(self.scan_lidar, exclusive=True, thread=True)

    def stop_scan(self) -> None:
        """Stop the lidar scanning process."""
        self.is_scanning = False
        self.query_one("#scan-button").label = "Start Scan"
        self.query_one("#scan-button").variant = "primary"

        if self.data_source == "iphone" and self.iphone_socket:
            try:
                self.iphone_socket.close()
            except:
                pass
            self.iphone_socket = None

        self.query_one("#status-label").update("Scan stopped. Press Start Scan to begin again.")

    def iphone_data_receiver(self) -> None:
        """Receive depth map data from iPhone LiDAR stream."""
        try:
            self.iphone_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.iphone_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.iphone_socket.bind(('0.0.0.0', 9999))
            self.iphone_socket.listen(1)
            self.iphone_socket.settimeout(1.0)  # 1 second timeout for accept

            self.update_status("Waiting for iPhone connection on port 9999...")

            while self.is_scanning:
                try:
                    conn, addr = self.iphone_socket.accept()
                    self.update_status(f"Connected to iPhone at {addr[0]}")

                    # Handle connection in a loop
                    while self.is_scanning:
                        try:
                            # Receive data size first (4 bytes)
                            size_data = conn.recv(4)
                            if not size_data:
                                break
                            n = int.from_bytes(size_data, byteorder='big')

                            # Receive the actual data
                            data = b""
                            while len(data) < n:
                                packet = conn.recv(n - len(data))
                                if not packet:
                                    break
                                data += packet

                            if len(data) == n:
                                # Parse JSON data containing depth map
                                try:
                                    depth_data = json.loads(data.decode('utf-8'))
                                    depth_map = np.array(depth_data['depth_map'], dtype=np.float32)
                                    with self.depth_map_lock:
                                        self.latest_depth_map = depth_map
                                except (json.JSONDecodeError, KeyError) as e:
                                    print(f"Error parsing iPhone data: {e}")

                        except socket.timeout:
                            continue
                        except ConnectionResetError:
                            break

                    conn.close()

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"iPhone receiver error: {e}")
                    break

        except Exception as e:
            self.update_status(f"iPhone connection error: {str(e)}")
        finally:
            if self.iphone_socket:
                try:
                    self.iphone_socket.close()
                except:
                    pass
                self.iphone_socket = None

    def scan_lidar(self) -> None:
        """Main scanning logic - handles both simulation and real iPhone data."""
        try:
            if self.data_source == "iphone":
                self.scan_iphone_lidar()
            else:
                self.scan_simulated_lidar()
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.call_from_thread(self.scan_error)

    def scan_simulated_lidar(self) -> None:
        """Simulate lidar scanning and generate point cloud data."""
        self.update_status("Generating point cloud...")

        # Create a sample point cloud mimicking iPhone LiDAR characteristics
        # iPhone LiDAR typically has ~640x480 resolution but we'll simulate a subset
        width, height = 320, 240  # Reduced for performance

        # Generate coordinates
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        x_grid, y_grid = np.meshgrid(x, y)

        # Simulate a scene with objects at various distances
        # Create a ground plane and some floating objects
        z_ground = 0.5 - 0.3 * y_grid  # Sloped ground
        z_objects = np.zeros_like(z_ground)

        # Add a floating sphere
        sphere_center = np.array([0.0, 0.0, 1.5])
        sphere_radius = 0.3
        dist_from_center = np.sqrt((x_grid - sphere_center[0])**2 +
                                  (y_grid - sphere_center[1])**2)
        sphere_mask = dist_from_center < sphere_radius
        z_objects[sphere_mask] = sphere_center[2] - np.sqrt(sphere_radius**2 -
                                                           dist_from_center[sphere_mask]**2)

        # Add a box
        box_min, box_max = -0.5, 0.5
        box_y_min, box_y_max = -0.2, 0.2
        box_z = 0.8
        box_mask = (x_grid >= box_min) & (x_grid <= box_max) & \
                   (y_grid >= box_y_min) & (y_grid <= box_y_max)
        z_objects[box_mask] = box_z

        # Combine surfaces (take closest point)
        z_surface = np.minimum(z_ground, z_objects)

        # Add noise similar to iPhone LiDAR
        noise_level = 0.02  # 2cm noise
        noise = np.random.normal(0, noise_level, z_surface.shape)
        z_noisy = z_surface + noise

        # Filter out invalid points (too close or too far)
        valid_mask = (z_noisy > 0.2) & (z_noisy < 5.0)  # 20cm to 5m range

        # Extract point cloud
        points = np.stack([
            x_grid[valid_mask],
            y_grid[valid_mask],
            z_noisy[valid_mask]
        ], axis=-1)

        # Downsample if too many points
        if len(points) > 50000:
            indices = np.random.choice(len(points), 50000, replace=False)
            points = points[indices]

        self.point_cloud = points

        self.update_status("Point cloud generated. Preparing visualization...")
        time.sleep(1)  # Simulate processing delay

        if self.is_scanning:
            self.update_status("Displaying 3D model... (Close the window to return to TUI)")
            self.visualize_point_cloud(points)

            if self.is_scanning:
                self.call_from_thread(self.scan_completed)
        else:
            self.update_status("Scan cancelled.")

    def scan_iphone_lidar(self) -> None:
        """Scan using real iPhone LiDAR data from network stream."""
        self.update_status("Waiting for iPhone LiDAR data...")

        # Wait for initial data
        timeout = time.time() + 10  # 10 second timeout
        while self.is_scanning and time.time() < timeout:
            with self.depth_map_lock:
                if self.latest_depth_map is not None:
                    break
            time.sleep(0.1)

        if not self.is_scanning:
            self.update_status("Scan cancelled while waiting for iPhone data.")
            return

        if self.latest_depth_map is None:
            self.update_status("Timeout: No iPhone LiDAR data received. Using simulation instead.")
            self.scan_simulated_lidar()
            return

        self.update_status("Processing iPhone LiDAR data...")

        # Process the depth map into a point cloud
        depth_map = self.latest_depth_map.copy()
        height, width = depth_map.shape

        # iPhone LiDAR intrinsic parameters (approximate)
        fx = fy = width * 0.8  # Focal length
        cx, cy = width / 2, height / 2  # Principal point

        # Create coordinate grids
        x_indices, y_indices = np.meshgrid(np.arange(width), np.arange(height))

        # Convert to 3D points
        z_values = depth_map
        x_values = (x_indices - cx) * z_values / fx
        y_values = (y_indices - cy) * z_values / fy

        # Stack and reshape
        points = np.stack([x_values, y_values, z_values], axis=-1)
        points = points.reshape(-1, 3)

        # Filter valid points
        valid_mask = (points[:, 2] > 0.2) & (points[:, 2] < 5.0) & ~np.isnan(points).any(axis=1)
        points = points[valid_mask]

        # Downsample if needed
        if len(points) > 100000:
            indices = np.random.choice(len(points), 100000, replace=False)
            points = points[indices]

        self.point_cloud = points.astype(np.float32)

        self.update_status(f"iPhone LiDAR data processed. {len(points)} points. Preparing visualization...")
        time.sleep(0.5)

        if self.is_scanning:
            self.update_status("Displaying 3D model... (Close the window to return to TUI)")
            self.visualize_point_cloud(points)

            if self.is_scanning:
                self.call_from_thread(self.scan_completed)
        else:
            self.update_status("Scan cancelled.")

    def visualize_point_cloud(self, points) -> None:
        """Create a 3D scatter plot of the point cloud."""
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Color points by height (z-value) for better visualization
        if len(points) > 0:
            scatter = ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                               c=points[:, 2], cmap='viridis', s=1)
            plt.colorbar(scatter, label='Height (Z)')
        else:
            ax.scatter([], [], [])

        # Set labels
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Y (meters)')
        ax.set_zlabel('Z (meters)')
        title = 'LiDAR Point Cloud (3D Model)'
        if self.data_source == 'iphone':
            title += ' - iPhone LiDAR'
        ax.set_title(title)

        # Set equal aspect ratio and reasonable limits
        if len(points) > 0:
            # Center the point cloud
            centroid = np.mean(points, axis=0)
            points_centered = points - centroid

            # Get max range
            max_range = np.max(np.abs(points_centered)) * 1.1

            ax.set_xlim(centroid[0] - max_range, centroid[0] + max_range)
            ax.set_ylim(centroid[1] - max_range, centroid[1] + max_range)
            ax.set_zlim(centroid[2] - max_range, centroid[2] + max_range)
        else:
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.set_zlim(0, 2)

        plt.show(block=True)

    def update_status(self, message: str) -> None:
        """Update the status label from any thread."""
        # If we're in the main thread, update directly
        if threading.current_thread() == self._thread:
            self.query_one("#status-label").update(message)
        else:
            # If we're in a different thread, use call_from_thread
            self.call_from_thread(self._update_status_label, message)

    def _update_status_label(self, message: str) -> None:
        """Actually update the status label (called from main thread)."""
        self.query_one("#status-label").update(message)

    def scan_completed(self) -> None:
        """Called when scanning and visualization completes."""
        self.is_scanning = False
        self.query_one("#scan-button").label = "Start Scan"
        self.query_one("#scan-button").variant = "primary"

        if self.data_source == "iphone":
            self.query_one("#status-label").update("iPhone LiDAR scan completed. Press Start Scan to scan again.")
        else:
            self.query_one("#status-label").update("Simulation scan completed. Press Start Scan to scan again.")

    def scan_error(self) -> None:
        """Called when an error occurs during scanning."""
        self.is_scanning = False
        self.query_one("#scan-button").label = "Start Scan"
        self.query_one("#scan-button").variant = "primary"
        self.query_one("#status-label").update("Error occurred during scanning.")


def main():
    """Run the application."""
    app = LidarTUI()
    app.run()


if __name__ == "__main__":
    main()