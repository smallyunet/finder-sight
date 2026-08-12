import AppKit
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var model: AppModel
    @State private var updateStatus = ""
    @State private var isChecking = false
    @State private var availableRelease: GitHubRelease?

    var body: some View {
        Form {
            Section("Search") {
                LabeledContent("Minimum match score") {
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
                        .accessibilityLabel("Minimum match score")
                        Text("\(model.config.similarityThreshold)%")
                            .monospacedDigit()
                            .frame(width: 44, alignment: .trailing)
                    }
                }
                .help("Only images at or above this similarity are shown as matches.")

                Text("Higher scores return fewer, more visually similar images.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                LabeledContent("Maximum results") {
                    Stepper(
                        "\(model.config.maxResults)",
                        value: Binding(
                            get: { model.config.maxResults },
                            set: {
                                model.config.maxResults = $0
                                model.saveSettings()
                            }
                        ),
                        in: 1...100
                    )
                    .monospacedDigit()
                }

                Text("Limits how many matches or closest alternatives appear after a search.")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                HStack {
                    Spacer()
                    Button("Restore Search Defaults") {
                        model.resetSearchSettings()
                    }
                    .disabled(
                        model.config.similarityThreshold == AppConstants.defaultSimilarity
                            && model.config.maxResults == AppConstants.defaultMaxResults
                    )
                }
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
                if let availableRelease,
                   let releaseURL = URL(string: availableRelease.htmlURL) {
                    Link("View \(availableRelease.tagName) Release", destination: releaseURL)
                }
                Link("View Finder Sight on GitHub", destination: URL(string: "https://github.com/smallyunet/finder-sight")!)
            }
        }
        .formStyle(.grouped)
        .padding(8)
        .frame(width: 520, height: 450)
    }

    private func checkForUpdates() {
        isChecking = true
        updateStatus = ""
        availableRelease = nil
        Task {
            do {
                let release = try await UpdateService.latestRelease()
                if UpdateService.isNewer(release.tagName, than: AppConstants.version) {
                    updateStatus = "Version \(release.tagName) is available"
                    availableRelease = release
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
