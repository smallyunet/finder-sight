import AppKit
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    @State private var updateStatus = ""
    @State private var isChecking = false

    var body: some View {
        Form {
            Section("Search") {
                HStack {
                    Slider(
                        value: Binding(
                            get: { Double(model.config.similarityThreshold) },
                            set: {
                                model.config.similarityThreshold = Int($0)
                                model.saveSettings()
                            }
                        ),
                        in: 0...100,
                        step: 1
                    )
                    Text("\(model.config.similarityThreshold)%")
                        .monospacedDigit()
                        .frame(width: 44, alignment: .trailing)
                }
                Stepper(
                    "Maximum results: \(model.config.maxResults)",
                    value: Binding(
                        get: { model.config.maxResults },
                        set: {
                            model.config.maxResults = $0
                            model.saveSettings()
                        }
                    ),
                    in: 1...100
                )
            }

            Section("About") {
                LabeledContent("Version", value: AppConstants.version)
                HStack {
                    Button(isChecking ? "Checking…" : "Check for Updates") {
                        checkForUpdates()
                    }
                    .disabled(isChecking)
                    Text(updateStatus)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Link("View Finder Sight on GitHub", destination: URL(string: "https://github.com/smallyunet/finder-sight")!)
            }
        }
        .formStyle(.grouped)
        .padding(8)
        .frame(width: 460, height: 300)
    }

    private func checkForUpdates() {
        isChecking = true
        updateStatus = ""
        Task {
            do {
                let release = try await UpdateService.latestRelease()
                if UpdateService.isNewer(release.tagName, than: AppConstants.version) {
                    updateStatus = "Version \(release.tagName) is available"
                    if let url = URL(string: release.htmlURL) { NSWorkspace.shared.open(url) }
                } else {
                    updateStatus = "You’re up to date"
                }
            } catch {
                updateStatus = "Couldn’t check for updates"
            }
            isChecking = false
        }
    }
}

struct GitHubRelease: Decodable {
    let tagName: String
    let htmlURL: String

    enum CodingKeys: String, CodingKey {
        case tagName = "tag_name"
        case htmlURL = "html_url"
    }
}

enum UpdateService {
    static func latestRelease() async throws -> GitHubRelease {
        let url = URL(string: "https://api.github.com/repos/smallyunet/finder-sight/releases/latest")!
        var request = URLRequest(url: url)
        request.setValue("FinderSight/\(AppConstants.version)", forHTTPHeaderField: "User-Agent")
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
        return try JSONDecoder().decode(GitHubRelease.self, from: data)
    }

    static func isNewer(_ tag: String, than current: String) -> Bool {
        tag.trimmingCharacters(in: CharacterSet(charactersIn: "vV"))
            .compare(current, options: .numeric) == .orderedDescending
    }
}
