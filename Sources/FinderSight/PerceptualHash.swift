import AppKit
import CoreGraphics
import ImageIO

enum PerceptualHashError: LocalizedError {
    case unreadableImage
    case drawingFailed

    var errorDescription: String? {
        switch self {
        case .unreadableImage: return "The image could not be read."
        case .drawingFailed: return "The image could not be processed."
        }
    }
}

enum PerceptualHash {
    private static let width = 17
    private static let height = 16

    static func make(from url: URL) throws -> (hash: String, width: Int, height: Int) {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw PerceptualHashError.unreadableImage
        }
        return (try make(from: image), image.width, image.height)
    }

    static func make(from image: NSImage) throws -> String {
        var rect = CGRect(origin: .zero, size: image.size)
        guard let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
            throw PerceptualHashError.unreadableImage
        }
        return try make(from: cgImage)
    }

    static func make(from image: CGImage) throws -> String {
        var pixels = [UInt8](repeating: 0, count: width * height)
        guard let context = CGContext(
            data: &pixels,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width,
            space: CGColorSpaceCreateDeviceGray(),
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else {
            throw PerceptualHashError.drawingFailed
        }

        context.interpolationQuality = .high
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))

        var hex = ""
        hex.reserveCapacity(64)
        var nibble = 0
        var bitCount = 0
        for y in 0..<height {
            for x in 0..<(width - 1) {
                nibble = (nibble << 1) | (pixels[y * width + x] > pixels[y * width + x + 1] ? 1 : 0)
                bitCount += 1
                if bitCount == 4 {
                    hex.append(String(nibble, radix: 16))
                    nibble = 0
                    bitCount = 0
                }
            }
        }
        return hex
    }

    static func distance(_ lhs: String, _ rhs: String) -> Int {
        guard lhs.count == rhs.count else { return 256 }
        return zip(lhs, rhs).reduce(into: 0) { result, pair in
            guard let a = pair.0.hexDigitValue, let b = pair.1.hexDigitValue else {
                result += 4
                return
            }
            result += (a ^ b).nonzeroBitCount
        }
    }
}
