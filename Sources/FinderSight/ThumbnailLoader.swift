import AppKit
import ImageIO

struct LoadedThumbnail: @unchecked Sendable {
    let image: NSImage?
}

final class ThumbnailCache: @unchecked Sendable {
    static let shared = ThumbnailCache()

    private let cache = NSCache<NSString, NSImage>()

    private init() {
        cache.countLimit = 300
        cache.totalCostLimit = 128 * 1024 * 1024
    }

    func image(at path: String, maxPixelSize: Int) -> NSImage? {
        let modificationTime = (try? FileManager.default.attributesOfItem(atPath: path)[.modificationDate] as? Date)?
            .timeIntervalSince1970 ?? 0
        let key = "\(path)|\(maxPixelSize)|\(modificationTime)" as NSString
        if let cached = cache.object(forKey: key) { return cached }

        let url = URL(fileURLWithPath: path) as CFURL
        guard let source = CGImageSourceCreateWithURL(url, nil) else { return nil }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceThumbnailMaxPixelSize: maxPixelSize,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceShouldCacheImmediately: true
        ]
        guard let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            return nil
        }
        let image = NSImage(cgImage: thumbnail, size: .zero)
        cache.setObject(image, forKey: key, cost: thumbnail.bytesPerRow * thumbnail.height)
        return image
    }
}
