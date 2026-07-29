import AppKit
import CoreGraphics
import ImageIO
import VisionBridge

enum VisualFeatureError: LocalizedError {
    case unreadableImage
    case featureGenerationFailed

    var errorDescription: String? {
        switch self {
        case .unreadableImage: return "The image could not be read for visual matching."
        case .featureGenerationFailed: return "Visual features could not be generated."
        }
    }
}

enum VisualFeatureRegion: String, Codable, CaseIterable, Sendable {
    case full
    case center
    case topLeft
    case topRight
    case bottomLeft
    case bottomRight

    var normalizedRect: CGRect {
        switch self {
        case .full:
            return CGRect(x: 0, y: 0, width: 1, height: 1)
        case .center:
            return CGRect(x: 0.15, y: 0.15, width: 0.70, height: 0.70)
        case .topLeft:
            return CGRect(x: 0, y: 0, width: 0.65, height: 0.65)
        case .topRight:
            return CGRect(x: 0.35, y: 0, width: 0.65, height: 0.65)
        case .bottomLeft:
            return CGRect(x: 0, y: 0.35, width: 0.65, height: 0.65)
        case .bottomRight:
            return CGRect(x: 0.35, y: 0.35, width: 0.65, height: 0.65)
        }
    }
}

struct VisualFeature: Codable, Hashable, Sendable {
    let region: VisualFeatureRegion
    let observationArchive: Data
}

enum VisualFeatureEngine {
    static let version = 1
    private static let maximumAnalysisDimension = 1_600
    private static let borderAnalysisDimension = 384

    static func makeIndexFeatures(from url: URL) throws -> [VisualFeature] {
        let image = try loadImage(from: url)
        return try makeIndexFeatures(from: image)
    }

    static func makeIndexFeatures(from image: CGImage) throws -> [VisualFeature] {
        try makeFeatures(from: image, regions: VisualFeatureRegion.allCases)
    }

    static func makeQueryFeature(from url: URL) throws -> Data {
        let image = try loadImage(from: url)
        return try makeFeatures(from: image, regions: [.full])[0].observationArchive
    }

    static func makeQueryFeature(from image: NSImage) throws -> Data {
        var rect = CGRect(origin: .zero, size: image.size)
        guard let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
            throw VisualFeatureError.unreadableImage
        }
        return try makeQueryFeature(from: cgImage)
    }

    static func makeQueryFeature(from image: CGImage) throws -> Data {
        try makeFeatures(from: image, regions: [.full])[0].observationArchive
    }

    static func minimumDistance(
        from queryArchive: Data,
        to features: [VisualFeature]
    ) -> Float? {
        guard !features.isEmpty else { return nil }
        let archives = features.map(\.observationArchive) as CFArray
        let distance = FSMinimumFeaturePrintDistance(queryArchive as CFData, archives)
        return distance.isFinite ? distance : nil
    }

    static func similarity(for distance: Float) -> Int {
        let normalized = max(0, min(2, distance))
        return max(0, min(100, Int(((1 - normalized / 2) * 100).rounded())))
    }

    private static func makeFeatures(
        from sourceImage: CGImage,
        regions: [VisualFeatureRegion]
    ) throws -> [VisualFeature] {
        let image = trimUniformBorder(from: downscaledIfNeeded(sourceImage))
        return try regions.map { region in
            let crop = crop(image, to: region.normalizedRect) ?? image
            var error: Unmanaged<CFError>?
            guard let retainedArchive = FSCreateFeaturePrintArchive(crop, &error) else {
                if let error {
                    throw error.takeRetainedValue() as Error
                }
                throw VisualFeatureError.featureGenerationFailed
            }
            let archive = retainedArchive as Data
            return VisualFeature(region: region, observationArchive: archive)
        }
    }

    private static func loadImage(from url: URL) throws -> CGImage {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
            throw VisualFeatureError.unreadableImage
        }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: maximumAnalysisDimension,
            kCGImageSourceShouldCacheImmediately: true
        ]
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary) else {
            throw VisualFeatureError.unreadableImage
        }
        return image
    }

    private static func crop(_ image: CGImage, to normalizedRect: CGRect) -> CGImage? {
        let width = CGFloat(image.width)
        let height = CGFloat(image.height)
        let rect = CGRect(
            x: normalizedRect.minX * width,
            y: normalizedRect.minY * height,
            width: normalizedRect.width * width,
            height: normalizedRect.height * height
        ).integral.intersection(CGRect(x: 0, y: 0, width: width, height: height))
        guard rect.width >= 8, rect.height >= 8 else { return nil }
        return image.cropping(to: rect)
    }

    private static func downscaledIfNeeded(_ image: CGImage) -> CGImage {
        let longestEdge = max(image.width, image.height)
        guard longestEdge > maximumAnalysisDimension else { return image }
        let scale = CGFloat(maximumAnalysisDimension) / CGFloat(longestEdge)
        let width = max(1, Int((CGFloat(image.width) * scale).rounded()))
        let height = max(1, Int((CGFloat(image.height) * scale).rounded()))
        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return image
        }
        context.interpolationQuality = .high
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        return context.makeImage() ?? image
    }

    private static func trimUniformBorder(from image: CGImage) -> CGImage {
        let scale = min(
            1,
            CGFloat(borderAnalysisDimension) / CGFloat(max(image.width, image.height))
        )
        let sampleWidth = max(1, Int((CGFloat(image.width) * scale).rounded()))
        let sampleHeight = max(1, Int((CGFloat(image.height) * scale).rounded()))
        let bytesPerRow = sampleWidth * 4
        var pixels = [UInt8](repeating: 0, count: sampleHeight * bytesPerRow)
        guard let context = CGContext(
            data: &pixels,
            width: sampleWidth,
            height: sampleHeight,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return image
        }
        context.interpolationQuality = .medium
        context.draw(image, in: CGRect(x: 0, y: 0, width: sampleWidth, height: sampleHeight))

        let corners = [
            pixel(in: pixels, width: sampleWidth, x: 0, y: 0),
            pixel(in: pixels, width: sampleWidth, x: sampleWidth - 1, y: 0),
            pixel(in: pixels, width: sampleWidth, x: 0, y: sampleHeight - 1),
            pixel(in: pixels, width: sampleWidth, x: sampleWidth - 1, y: sampleHeight - 1)
        ]
        guard let uniformCorners = uniformCornerCluster(corners) else { return image }
        let background = average(uniformCorners)

        var minX = sampleWidth
        var minY = sampleHeight
        var maxX = -1
        var maxY = -1
        for y in 0..<sampleHeight {
            for x in 0..<sampleWidth {
                let value = pixel(in: pixels, width: sampleWidth, x: x, y: y)
                if isForeground(value, comparedTo: background) {
                    minX = min(minX, x)
                    minY = min(minY, y)
                    maxX = max(maxX, x)
                    maxY = max(maxY, y)
                }
            }
        }
        guard maxX >= minX, maxY >= minY else { return image }

        let padding = 0
        minX = max(0, minX - padding)
        minY = max(0, minY - padding)
        maxX = min(sampleWidth - 1, maxX + padding)
        maxY = min(sampleHeight - 1, maxY + padding)

        let retainedWidth = maxX - minX + 1
        let retainedHeight = maxY - minY + 1
        let retainedArea = retainedWidth * retainedHeight
        let totalArea = sampleWidth * sampleHeight
        guard retainedArea >= max(64, totalArea / 100),
              retainedArea <= Int(Double(totalArea) * 0.96) else {
            return image
        }

        let sourceRect = CGRect(
            x: CGFloat(minX) / CGFloat(sampleWidth) * CGFloat(image.width),
            y: CGFloat(minY) / CGFloat(sampleHeight) * CGFloat(image.height),
            width: CGFloat(retainedWidth) / CGFloat(sampleWidth) * CGFloat(image.width),
            height: CGFloat(retainedHeight) / CGFloat(sampleHeight) * CGFloat(image.height)
        ).integral.intersection(
            CGRect(x: 0, y: 0, width: image.width, height: image.height)
        )
        return image.cropping(to: sourceRect) ?? image
    }

    private static func pixel(
        in pixels: [UInt8],
        width: Int,
        x: Int,
        y: Int
    ) -> (r: Int, g: Int, b: Int, a: Int) {
        let offset = (y * width + x) * 4
        return (
            Int(pixels[offset]),
            Int(pixels[offset + 1]),
            Int(pixels[offset + 2]),
            Int(pixels[offset + 3])
        )
    }

    private static func uniformCornerCluster(
        _ corners: [(r: Int, g: Int, b: Int, a: Int)]
    ) -> [(r: Int, g: Int, b: Int, a: Int)]? {
        for seed in corners {
            let cluster = corners.filter {
                abs($0.a - seed.a) <= 32 && colorDistance($0, seed) <= 42
            }
            if cluster.count >= 3 { return cluster }
        }
        return nil
    }

    private static func average(
        _ pixels: [(r: Int, g: Int, b: Int, a: Int)]
    ) -> (r: Int, g: Int, b: Int, a: Int) {
        (
            pixels.reduce(0) { $0 + $1.r } / pixels.count,
            pixels.reduce(0) { $0 + $1.g } / pixels.count,
            pixels.reduce(0) { $0 + $1.b } / pixels.count,
            pixels.reduce(0) { $0 + $1.a } / pixels.count
        )
    }

    private static func isForeground(
        _ pixel: (r: Int, g: Int, b: Int, a: Int),
        comparedTo background: (r: Int, g: Int, b: Int, a: Int)
    ) -> Bool {
        if background.a < 24 { return pixel.a >= 32 }
        return abs(pixel.a - background.a) > 32 || colorDistance(pixel, background) > 38
    }

    private static func colorDistance(
        _ lhs: (r: Int, g: Int, b: Int, a: Int),
        _ rhs: (r: Int, g: Int, b: Int, a: Int)
    ) -> Int {
        let red = lhs.r - rhs.r
        let green = lhs.g - rhs.g
        let blue = lhs.b - rhs.b
        return Int(Double(red * red + green * green + blue * blue).squareRoot())
    }
}
