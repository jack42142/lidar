import Foundation
import ARKit
import Combine

class LiDARStreamerViewModel: ObservableObject {
    @Published var status: String = "Ready"
    @Published var isStreaming: Bool = false
    @Published var serverIP: String = ""
    @Published var isLiDARAvailable: Bool = false

    private var arSession: ARSession?
    private var streamingTask: Task<Void, Never>?
    private var tcpConnection: TCPConnection?
    private var cancellables = Set<AnyCancellable>()

    init() {
        checkLiDARAvailability()
        setupARSession()
    }

    private func checkLiDARAvailability() {
        // Check if device has LiDAR scanner
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            isLiDARAvailable = true
            status = "LiDAR available"
        } else {
            isLiDARAvailable = false
            status = "LiDAR not available on this device"
        }
    }

    private func setupARSession() {
        guard isLiDARAvailable else { return }

        let configuration = ARWorldTrackingConfiguration()
        configuration.sceneReconstruction = .mesh

        arSession = ARSession()
        arSession?.run(configuration)

        status = "AR session started"
    }

    func toggleStreaming() {
        if isStreaming {
            stopStreaming()
        } else {
            startStreaming()
        }
    }

    private func startStreaming() {
        guard !serverIP.isEmpty else {
            status = "Please enter IP address"
            return
        }

        isStreaming = true
        status = "Connecting to \(serverIP):9999..."

        // Setup TCP connection
        tcpConnection = TCPConnection(host: serverIP, port: 9999)

        // Start streaming task
        streamingTask = Task {
            do {
                try await tcpConnection?.connect()
                await MainActor.run {
                    status = "Connected - Streaming LiDAR data"
                }

                // Stream depth data from AR session
                for await depthData in generateDepthDataStream() {
                    guard !Task.isCancelled else { break }

                    let jsonData = try JSONEncoder().encode(depthData)
                    try await tcpConnection?.send(data: jsonData)

                    // Small delay to prevent overwhelming the network
                    try await Task.sleep(nanoseconds: 33_000_000) // ~30 FPS
                }
            } catch {
                await MainActor.run {
                    status = "Error: \(error.localizedDescription)"
                    isStreaming = false
                }
            }
        }
    }

    private func stopStreaming() {
        isStreaming = false
        status = "Stopping stream..."

        streamingTask?.cancel()
        streamingTask = nil

        tcpConnection?.disconnect()
        tcpConnection = nil

        status = "Stream stopped"
    }

    private func generateDepthDataStream() -> AsyncStream<DepthFrame> {
        AsyncStream { continuation in
            // Create a repeating task to capture depth data
            Task {
                while !Task.isCancelled {
                    if let frame = arSession?.currentFrame,
                       let depthMap = try? frame.sceneDepth?.depthMap {

                        let width = CVPixelBufferGetWidth(depthMap)
                        let height = CVPixelBufferGetHeight(depthMap)

                        // Convert depth map to Float array
                        var depthFloat: [Float] = Array(repeating: 0, count: width * height)

                        CVPixelBufferLockBaseAddress(depthMap, .readOnly)
                        let baseAddress = CVPixelBufferGetBaseAddress(depthMap)!

                        let buffer = UnsafeBufferPointer(start: baseAddress.assumingMemoryBound(to: Float.self),
                                                       count: width * height)
                        depthFloat = Array(buffer)
                        CVPixelBufferUnlockBaseAddress(depthMap, .readOnly)

                        // Convert to 2D array for JSON serialization
                        var depth2D: [[Float]] = []
                        for y in 0..<height {
                            let rowStart = y * width
                            let rowEnd = rowStart + width
                            let row = Array(depthFloat[rowStart..<rowEnd])
                            depth2D.append(row)
                        }

                        let depthFrame = DepthFrame(
                            depthMap: depth2D,
                            timestamp: frame.timestamp,
                            width: width,
                            height: height
                        )

                        continuation.yield(depthFrame)
                    }

                    // Capture at ~30 FPS
                    try? await Task.sleep(nanoseconds: 33_000_000)
                }

                continuation.finish()
            }
        }
    }

    deinit {
        stopStreaming()
        arSession?.pause()
    }
}

// MARK: - Data Models

struct DepthFrame: Codable {
    let depthMap: [[Float]]
    let timestamp: TimeInterval
    let width: Int
    let height: Int
}

// MARK: - TCP Connection

class TCPConnection {
    private let host: String
    private let port: Int
    private var stream: Stream?
    private var outputStream: OutputStream?
    private var inputStream: InputStream?

    init(host: String, port: Int) {
        self.host = host
        self.port = port
    }

    func connect() throws {
        var readStream:  Unmanaged<CFReadStream>?
        var writeStream: Unmanaged<CFWriteStream>?

        CFStreamCreatePairWithSocketToHost(kCFAllocatorDefault,
                                          host as CFString,
                                          UInt32(port),
                                          &readStream,
                                          &writeStream)

        inputStream = readStream?.takeRetainedValue()
        outputStream = writeStream?.takeRetainedValue()

        inputStream?.schedule(in: .current, forMode: .common)
        outputStream?.schedule(in: .current, forMode: .common)

        inputStream?.open()
        outputStream?.open()
    }

    func send(data: Data) throws {
        try outputStream?.write([UInt8](data))
    }

    func disconnect() {
        inputStream?.close()
        outputStream?.close()

        inputStream?.remove(from: .current, forMode: .common)
        outputStream?.remove(from: .current, forMode: .common)

        inputStream = nil
        outputStream = nil
    }
}