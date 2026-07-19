import Foundation

enum ImageIndexer {
    static func scan(
        directories: [String],
        existing: [String: ImageRecord],
        progress: @escaping @Sendable (Int, Int, String) -> Void
    ) -> [ImageRecord] {
        let manager = FileManager.default
        let keys: [URLResourceKey] = [.isRegularFileKey, .contentModificationDateKey, .fileSizeKey]
        var urls: [URL] = []

        for path in directories {
            let root = URL(fileURLWithPath: path, isDirectory: true)
            guard let enumerator = manager.enumerator(
                at: root,
                includingPropertiesForKeys: keys,
                options: [.skipsHiddenFiles, .skipsPackageDescendants]
            ) else { continue }

            for case let url as URL in enumerator {
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

        DispatchQueue.concurrentPerform(iterations: total) { index in
            autoreleasepool {
                let url = urls[index]
                let values = try? url.resourceValues(forKeys: Set(keys))
                let mtime = values?.contentModificationDate?.timeIntervalSince1970 ?? 0
                let record: ImageRecord?

                if let cached = existing[url.path], cached.modificationTime == mtime {
                    record = cached
                } else if let result = try? PerceptualHash.make(from: url) {
                    record = ImageRecord(
                        path: url.path,
                        hash: result.hash,
                        modificationTime: mtime,
                        pixelWidth: result.width,
                        pixelHeight: result.height,
                        fileSize: Int64(values?.fileSize ?? 0)
                    )
                } else {
                    record = nil
                }

                lock.lock()
                if let record { records.append(record) }
                completed += 1
                let current = completed
                lock.unlock()
                progress(current, total, url.lastPathComponent)
            }
        }

        return records.sorted { $0.path.localizedStandardCompare($1.path) == .orderedAscending }
    }
}

enum ImageSearcher {
    static func search(
        hash: String,
        records: [ImageRecord],
        minimumSimilarity: Int,
        limit: Int
    ) -> [SearchResult] {
        let threshold = Int(256.0 * (1.0 - Double(minimumSimilarity) / 100.0))
        let ranked = records.map {
            SearchResult(record: $0, distance: PerceptualHash.distance(hash, $0.hash))
        }.sorted {
            if $0.distance == $1.distance { return $0.record.path < $1.record.path }
            return $0.distance < $1.distance
        }
        let matches = ranked.filter { $0.distance <= threshold }
        return Array((matches.isEmpty ? ranked : matches).prefix(max(1, limit)))
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
