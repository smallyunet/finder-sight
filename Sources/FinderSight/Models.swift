import Foundation

enum AppConstants {
    static var version: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String
            ?? "development"
    }
    static let bundleIdentifier = "com.smallyunet.finder-sight"
    static let indexVersion = 1
    static let defaultSimilarity = 80
    static let defaultMaxResults = 20
    static let supportedExtensions: Set<String> = [
        "jpg", "jpeg", "png", "webp", "bmp", "gif", "heic", "heif",
        "tiff", "tif", "ico"
    ]

    static var supportDirectory: URL {
        let base = FileManager.default.urls(
            for: .applicationSupportDirectory,
            in: .userDomainMask
        ).first!
        return base.appendingPathComponent("FinderSight", isDirectory: true)
    }

    static var configURL: URL { supportDirectory.appendingPathComponent("config.json") }
    static var indexURL: URL { supportDirectory.appendingPathComponent("swift-image-index.json") }
}

struct AppConfig: Codable, Equatable {
    var directories: [String] = []
    var similarityThreshold: Int = AppConstants.defaultSimilarity
    var maxResults: Int = AppConstants.defaultMaxResults

    enum CodingKeys: String, CodingKey {
        case directories
        case similarityThreshold = "similarity_threshold"
        case maxResults = "max_results"
    }
}

struct ImageRecord: Codable, Hashable, Identifiable, Sendable {
    var id: String { path }
    let path: String
    let hash: String
    let modificationTime: TimeInterval
    let pixelWidth: Int
    let pixelHeight: Int
    let fileSize: Int64
}

struct IndexArchive: Codable {
    let version: Int
    let records: [ImageRecord]
}

struct SearchResult: Identifiable, Hashable {
    var id: String { record.path }
    let record: ImageRecord
    let distance: Int

    var similarity: Int {
        max(0, min(100, Int((1.0 - Double(distance) / 256.0) * 100.0)))
    }
}

struct SearchOutcome: Equatable {
    let results: [SearchResult]
    let isClosestFallback: Bool
}

struct IndexingResult {
    let records: [ImageRecord]
    let failedCount: Int
    let wasCancelled: Bool
}

struct DuplicateGroup: Identifiable, Hashable {
    let id: String
    let records: [ImageRecord]
}

enum ContentMode: Equatable {
    case ready
    case searchResults
    case duplicates
}
