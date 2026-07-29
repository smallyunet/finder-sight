import Foundation

final class IndexingController: @unchecked Sendable {
    private let lock = NSLock()
    private var cancelled = false

    var isCancelled: Bool {
        lock.withLock { cancelled }
    }

    func cancel() {
        lock.withLock { cancelled = true }
    }
}

enum ImageIndexer {
    static func scan(
        directories: [String],
        existing: [String: ImageRecord],
        controller: IndexingController = IndexingController(),
        progress: @escaping @Sendable (Int, Int, String) -> Void
    ) -> IndexingResult {
        let manager = FileManager.default
        let keys: [URLResourceKey] = [.isRegularFileKey, .contentModificationDateKey, .fileSizeKey]
        var urls: [URL] = []
        var discoveryFailures = 0

        directoryLoop: for path in directories {
            guard !controller.isCancelled else { break }
            let root = URL(fileURLWithPath: path, isDirectory: true)
            guard let enumerator = manager.enumerator(
                at: root,
                includingPropertiesForKeys: keys,
                options: [.skipsHiddenFiles, .skipsPackageDescendants]
            ) else {
                discoveryFailures += 1
                continue
            }

            for case let url as URL in enumerator {
                guard !controller.isCancelled else { break directoryLoop }
                guard AppConstants.supportedExtensions.contains(url.pathExtension.lowercased()),
                      (try? url.resourceValues(forKeys: [.isRegularFileKey]).isRegularFile) == true else {
                    continue
                }
                urls.append(url)
            }
        }

        let total = urls.count
        let lock = NSLock()
        var records: [ImageRecord] = []
        records.reserveCapacity(total)
        var completed = 0
        var failedCount = discoveryFailures
        var visualFeatureFailureCount = 0

        DispatchQueue.concurrentPerform(iterations: total) { index in
            autoreleasepool {
                guard !controller.isCancelled else { return }
                let url = urls[index]
                let values = try? url.resourceValues(forKeys: Set(keys))
                let mtime = values?.contentModificationDate?.timeIntervalSince1970 ?? 0
                let record: ImageRecord?

                if let cached = existing[url.path],
                   cached.modificationTime == mtime,
                   !(cached.visualFeatures ?? []).isEmpty {
                    record = cached
                } else if let result = try? PerceptualHash.make(from: url) {
                    let visualFeatures = (try? VisualFeatureEngine.makeIndexFeatures(from: url)) ?? []
                    record = ImageRecord(
                        path: url.path,
                        hash: result.hash,
                        modificationTime: mtime,
                        pixelWidth: result.width,
                        pixelHeight: result.height,
                        fileSize: Int64(values?.fileSize ?? 0),
                        visualFeatures: visualFeatures
                    )
                } else {
                    record = nil
                }

                lock.lock()
                if let record {
                    records.append(record)
                    if (record.visualFeatures ?? []).isEmpty {
                        visualFeatureFailureCount += 1
                    }
                } else {
                    failedCount += 1
                }
                completed += 1
                let current = completed
                lock.unlock()
                progress(current, total, url.lastPathComponent)
            }
        }

        let sorted = records.sorted { $0.path.localizedStandardCompare($1.path) == .orderedAscending }
        return IndexingResult(
            records: sorted,
            failedCount: failedCount,
            visualFeatureFailureCount: visualFeatureFailureCount,
            wasCancelled: controller.isCancelled
        )
    }
}

enum ImageSearcher {
    struct Query: Sendable {
        let hash: String
        let visualFeature: Data?
    }

    static func search(
        hash: String,
        records: [ImageRecord],
        minimumSimilarity: Int,
        limit: Int
    ) -> SearchOutcome {
        search(
            query: Query(hash: hash, visualFeature: nil),
            records: records,
            minimumSimilarity: minimumSimilarity,
            limit: limit
        )
    }

    static func search(
        query: Query,
        records: [ImageRecord],
        minimumSimilarity: Int,
        limit: Int
    ) -> SearchOutcome {
        let ranked = records.map { record in
            let visualDistance = query.visualFeature.flatMap {
                VisualFeatureEngine.minimumDistance(from: $0, to: record.visualFeatures ?? [])
            }
            return SearchResult(
                record: record,
                distance: PerceptualHash.distance(query.hash, record.hash),
                visualDistance: visualDistance
            )
        }.sorted {
            if $0.similarity == $1.similarity {
                if $0.distance == $1.distance { return $0.record.path < $1.record.path }
                return $0.distance < $1.distance
            }
            return $0.similarity > $1.similarity
        }
        let matches = ranked.filter { $0.similarity >= minimumSimilarity }
        let isFallback = matches.isEmpty && !ranked.isEmpty
        let visibleResults = matches.isEmpty ? ranked : matches
        return SearchOutcome(
            results: Array(visibleResults.prefix(max(1, limit))),
            isClosestFallback: isFallback
        )
    }
}

enum DuplicateFinder {
    static func groups(in records: [ImageRecord], directories: [String]) -> [DuplicateGroup] {
        let roots = directories.map { URL(fileURLWithPath: $0).standardizedFileURL.path }
        let validRecords = records.filter { record in
            FileManager.default.fileExists(atPath: record.path) && roots.contains { root in
                record.path == root || record.path.hasPrefix(root.hasSuffix("/") ? root : root + "/")
            }
        }
        return Dictionary(grouping: validRecords, by: \.hash)
            .filter { $0.value.count > 1 }
            .map { hash, images in
                DuplicateGroup(id: hash, records: images.sorted(by: qualityFirst))
            }
            .sorted {
                if $0.records.count == $1.records.count { return $0.id < $1.id }
                return $0.records.count > $1.records.count
            }
    }

    static func deletionCandidates(in groups: [DuplicateGroup]) -> [ImageRecord] {
        groups.flatMap { Array($0.records.dropFirst()) }
    }

    static func qualityFirst(_ lhs: ImageRecord, _ rhs: ImageRecord) -> Bool {
        let lhsPixels = lhs.pixelWidth * lhs.pixelHeight
        let rhsPixels = rhs.pixelWidth * rhs.pixelHeight
        if lhsPixels != rhsPixels { return lhsPixels > rhsPixels }
        if lhs.fileSize != rhs.fileSize { return lhs.fileSize > rhs.fileSize }
        let priority = ["tif": 6, "tiff": 6, "png": 5, "heic": 5, "heif": 5,
                        "webp": 4, "jpg": 3, "jpeg": 3, "bmp": 2, "gif": 1]
        let lhsPriority = priority[URL(fileURLWithPath: lhs.path).pathExtension.lowercased()] ?? 0
        let rhsPriority = priority[URL(fileURLWithPath: rhs.path).pathExtension.lowercased()] ?? 0
        if lhsPriority != rhsPriority { return lhsPriority > rhsPriority }
        return lhs.path.localizedStandardCompare(rhs.path) == .orderedAscending
    }
}
