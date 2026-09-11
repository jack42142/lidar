import SwiftUI
import ARKit

struct ContentView: View {
    @StateObject private var viewModel = LiDARStreamerViewModel()

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text("LiDAR Streamer")
                    .font(.largeTitle)
                    .padding()

                // Status indicator
                StatusView(status: viewModel.status)
                    .padding(.horizontal)

                // Connection settings
                VStack(alignment: .leading, spacing: 8) {
                    Text("Computer IP Address:")
                        .font(.headline)
                    TextField("Enter IP address", text: $viewModel.serverIP)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .keyboardType(.numberPad)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)

                    Text("Port: 9999")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal)

                // Control button
                Button(action: {
                    viewModel.toggleStreaming()
                }) {
                    Text(viewModel.isStreaming ? "Stop Streaming" : "Start Streaming")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(viewModel.isStreaming ? Color.red : Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
                .padding(.horizontal)
                .disabled(!viewModel.isLiDARAvailable)

                // LiDAR availability notice
                if !viewModel.isLiDARAvailable {
                    Text("LiDAR sensor not available on this device")
                        .font(.caption)
                        .foregroundColor(.orange)
                        .padding()
                }

                Spacer()
            }
            .padding()
            .navigationTitle("LiDAR Streamer")
        }
    }
}

struct StatusView: View {
    let status: String

    var body: some View {
        VStack(alignment: .leading) {
            Text("Status:")
                .font(.headline)
            Text(status)
                .font(.body)
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
        }
    }
}