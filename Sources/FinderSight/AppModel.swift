import AppKit
import Foundation
import SwiftUI

@MainActor
final class AppModel: ObservableObject {
    @Published var config = AppConfig()
    @Published private(set) var records: [ImageRecord] = []
    @Published private(set) var results: [SearchResult] = []
    @Published private(set) var duplicateGroups: [DuplicateGroup] = []
    @Published private(set) var mode: ContentMode = .ready
    @Published private(set) var queryImage: NSImage?
    @Published private(set) var isWorking = false
    @Published private(set) var progress = 0.0
    @Published private(set) var status = "Ready"
    @Published var errorMessage: String?

    private var didPrepare = false

    func prepare() {
        guard !didPrepare else { return }
        didPrepare = true
        loadConfig()
        loadIndex()
        if records.isEmpty && !config.directories.isEmpty {
            indexNow()
        }
    }

    func addDirectory() {
        let panel = NSOpenPanel()
        panel.title = "Add Image Folder"
        panel.prompt = "Add Folder"
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = true
        guard panel.runModal() == .OK else { return }

        for url in panel.urls where !config.directories.contains(url.path) {
            config.directories.append(url.path)
        }
        saveConfig()
        indexNow()
    }

    func removeDirectory(_ path: String) {
        config.directories.removeAll { $0 == path }
        records.removeAll { record in
            record.path == path || record.path.hasPrefix(path.hasSuffix("/") ? path : path + "/")
        }
        saveConfig()
        saveIndex()
        resetContent()
    }

    func selectQueryImage() {
        let panel = NSOpenPanel()
        panel.title = "Choose an Image"
        panel.prompt = "Search"
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedContentTypes = [.image]
        guard panel.runModal() == .OK, let url = panel.url else { return }
        search(url: url)
    }

    func handleDroppedURL(_ url: URL) {
        guard AppConstants.supportedExtensions.contains(url.pathExtension.lowercased()) else {
            errorMessage = "That image format is not supported."
            return
        }
        search(url: url)
    }

    func pasteImage() {
        let pasteboard = NSPasteboard.general
        if let urls = pasteboard.readObjects(forClasses: [NSURL.self]) as? [URL],
           let url = urls.first,
           AppConstants.supportedExtensions.contains(url.pathExtension.lowercased()) {
            search(url: url)
            return
        }
        if let image = NSImage(pasteboard: pasteboard) {
            search(image: image)
            return
        }
        errorMessage = "The clipboard does not contain a supported image."
    }

    func indexNow() {
        guard !isWorking else { return }
        guard !config.directories.isEmpty else {
            errorMessage = "Add at least one image folder first."
            return
        }
        isWorking = true
        progress = 0
        status = "Scanning folders…"
        let directories = config.directories
        let existing = Dictionary(uniqueKeysWithValues: records.map { ($0.path, $0) })

        Task {
            let indexed = await Task.detached(priority: .userInitiated) {
                ImageIndexer.scan(directories: directories, existing: existing) { current, total, name in
                    Task { @MainActor [weak self] in
                        guard let self else { return }
                        self.progress = total == 0 ? 0 : Double(current) / Double(total)
                        self.status = "Indexing \(current) of \(total) · \(name)"
                    }
                }
            }.value
            records = indexed
            saveIndex()
            status = "Indexed \(records.count) images"
            progress = 1
            isWorking = false
            if mode == .duplicates { findDuplicates() }
        }
    }

    func search(url: URL) {
        guard !records.isEmpty else {
            errorMessage = "The index is empty. Add a folder and index it first."
            return
        }
        guard let image = NSImage(contentsOf: url) else {
            errorMessage = "The selected image could not be opened."
            return
        }
        queryImage = image
        isWorking = true
        status = "Searching…"
        let currentRecords = records
        let similarity = config.similarityThreshold
        let limit = config.maxResults

        Task {
            do {
                let hash = try await Task.detached { try PerceptualHash.make(from: url).hash }.value
                let found = await Task.detached {
                    ImageSearcher.search(
                        hash: hash,
                        records: currentRecords,
                        minimumSimilarity: similarity,
                        limit: limit
                    )
                }.value
                results = found
                duplicateGroups = []
                mode = .searchResults
                status = "Found \(found.count) matches"
            } catch {
                errorMessage = error.localizedDescription
                status = "Search failed"
            }
            isWorking = false
        }
    }

    func search(image: NSImage) {
        guard !records.isEmpty else {
            errorMessage = "The index is empty. Add a folder and index it first."
            return
        }
        queryImage = image
        isWorking = true
        status = "Searching…"
        let currentRecords = records
        let similarity = config.similarityThreshold
        let limit = config.maxResults

        Task {
            do {
                let hash = try PerceptualHash.make(from: image)
                results = await Task.detached {
                    ImageSearcher.search(
                        hash: hash,
                        records: currentRecords,
                        minimumSimilarity: similarity,
                        limit: limit
                    )
                }.value
                duplicateGroups = []
                mode = .searchResults
                status = "Found \(results.count) matches"
            } catch {
                errorMessage = error.localizedDescription
                status = "Search failed"
            }
            isWorking = false
        }
    }

    func findDuplicates() {
        guard !records.isEmpty else {
            errorMessage = "The index is empty. Add a folder and index it first."
            return
        }
        isWorking = true
        status = "Finding duplicates…"
        let snapshot = records
        let directories = config.directories
        Task {
            duplicateGroups = await Task.detached {
                DuplicateFinder.groups(in: snapshot, directories: directories)
            }.value
            results = []
            mode = .duplicates
            status = duplicateGroups.isEmpty
                ? "No duplicates found"
                : "Found \(duplicateGroups.count) duplicate groups"
            isWorking = false
        }
    }

    func moveDuplicatesToTrash() {
        let candidates = DuplicateFinder.deletionCandidates(in: duplicateGroups)
        guard !candidates.isEmpty else { return }

        let alert = NSAlert()
        alert.messageText = "Move \(candidates.count) duplicates to Trash?"
        alert.informativeText = "Finder Sight will keep the highest-resolution image in each group."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Move to Trash")
        alert.addButton(withTitle: "Cancel")
        guard alert.runModal() == .alertFirstButtonReturn else { return }

        var failed = 0
        for record in candidates {
            do {
                try FileManager.default.trashItem(at: URL(fileURLWithPath: record.path), resultingItemURL: nil)
                records.removeAll { $0.path == record.path }
            } catch {
                failed += 1
            }
        }
        saveIndex()
        findDuplicates()
        if failed > 0 { errorMessage = "\(failed) files could not be moved to Trash." }
    }

    func clearIndex() {
        let alert = NSAlert()
        alert.messageText = "Clear the local image index?"
        alert.informativeText = "Your original image files will not be deleted."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Clear Index")
        alert.addButton(withTitle: "Cancel")
        guard alert.runModal() == .alertFirstButtonReturn else { return }
        records = []
        try? FileManager.default.removeItem(at: AppConstants.indexURL)
        resetContent()
        status = "Index cleared"
    }

    func resetContent() {
        results = []
        duplicateGroups = []
        queryImage = nil
        mode = .ready
    }

    func reveal(_ path: String) {
        NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: path)])
    }

    func open(_ path: String) {
        NSWorkspace.shared.open(URL(fileURLWithPath: path))
    }

    func saveSettings() {
        config.similarityThreshold = min(100, max(0, config.similarityThreshold))
        config.maxResults = min(100, max(1, config.maxResults))
        saveConfig()
    }

    private func loadConfig() {
        guard let data = try? Data(contentsOf: AppConstants.configURL),
              let decoded = try? JSONDecoder().decode(AppConfig.self, from: data) else { return }
        config = decoded
    }

    private func saveConfig() {
        try? FileManager.default.createDirectory(
            at: AppConstants.supportDirectory,
            withIntermediateDirectories: true
        )
        guard let data = try? JSONEncoder.pretty.encode(config) else { return }
        try? data.write(to: AppConstants.configURL, options: .atomic)
    }

    private func loadIndex() {
        guard let data = try? Data(contentsOf: AppConstants.indexURL),
              let archive = try? JSONDecoder().decode(IndexArchive.self, from: data),
              archive.version == AppConstants.indexVersion else { return }
        records = archive.records
        status = "Loaded \(records.count) images"
    }

    private func saveIndex() {
        try? FileManager.default.createDirectory(
            at: AppConstants.supportDirectory,
            withIntermediateDirectories: true
        )
        let archive = IndexArchive(version: AppConstants.indexVersion, records: records)
        guard let data = try? JSONEncoder().encode(archive) else { return }
        try? data.write(to: AppConstants.indexURL, options: .atomic)
    }
}

private extension JSONEncoder {
    static var pretty: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return encoder
    }
}
