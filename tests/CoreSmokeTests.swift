import AppKit
import Foundation

@main
enum CoreSmokeTests {
    static func main() {
        let zeros = String(repeating: "0", count: 64)
        let ones = String(repeating: "f", count: 64)
        precondition(PerceptualHash.distance(zeros, zeros) == 0)
        precondition(PerceptualHash.distance(zeros, ones) == 256)

        let exact = ImageRecord(
            path: "/exact.png", hash: zeros, modificationTime: 0,
            pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let distant = ImageRecord(
            path: "/distant.png", hash: ones, modificationTime: 0,
            pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let outcome = ImageSearcher.search(
            hash: zeros,
            records: [distant, exact],
            minimumSimilarity: 80,
            limit: 20
        )
        precondition(outcome.results.map(\.record.path) == ["/exact.png"])
        precondition(outcome.results.first?.similarity == 100)
        precondition(!outcome.isClosestFallback)

        let fallback = ImageSearcher.search(
            hash: zeros,
            records: [distant],
            minimumSimilarity: 100,
            limit: 20
        )
        precondition(fallback.results.map(\.record.path) == ["/distant.png"])
        precondition(fallback.isClosestFallback)

        let recommendedDuplicate = ImageRecord(
            path: "/recommended.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 500, pixelHeight: 500, fileSize: 500
        )
        let selectedDuplicate = ImageRecord(
            path: "/selected.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let duplicateGroup = DuplicateGroup(
            id: "same",
            records: [recommendedDuplicate, selectedDuplicate]
        )
        let cleanupCandidates = DuplicateFinder.deletionCandidates(
            in: [duplicateGroup],
            keeping: [selectedDuplicate.id]
        )
        precondition(cleanupCandidates.map(\.id) == [recommendedDuplicate.id])

        let featureArchive = try! VisualFeatureEngine.makeQueryFeature(
            from: URL(fileURLWithPath: "icon.png")
        )
        let feature = VisualFeature(region: .full, observationArchive: featureArchive)
        let featureDistance = VisualFeatureEngine.minimumDistance(
            from: featureArchive,
            to: [feature]
        )
        precondition(featureDistance != nil && abs(featureDistance!) < 0.0001)

        let width = 200
        let height = 200
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        )!
        context.setFillColor(NSColor.systemRed.cgColor)
        context.fill(CGRect(x: 0, y: 0, width: 130, height: 130))
        context.setFillColor(NSColor.systemBlue.cgColor)
        context.fill(CGRect(x: 70, y: 70, width: 130, height: 130))
        context.setFillColor(NSColor.black.cgColor)
        context.fill(CGRect(x: 20, y: 35, width: 70, height: 24))
        let fullImage = context.makeImage()!
        let crop = fullImage.cropping(to: CGRect(x: 0, y: 0, width: 130, height: 130))!
        let indexedFeatures = try! VisualFeatureEngine.makeIndexFeatures(from: fullImage)
        let cropFeature = try! VisualFeatureEngine.makeQueryFeature(from: crop)
        let cropDistance = VisualFeatureEngine.minimumDistance(
            from: cropFeature,
            to: indexedFeatures
        )
        precondition(cropDistance != nil && cropDistance! < 0.05)

        let paddedContext = CGContext(
            data: nil,
            width: 220,
            height: 220,
            bitsPerComponent: 8,
            bytesPerRow: 220 * 4,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        )!
        paddedContext.setFillColor(NSColor.white.cgColor)
        paddedContext.fill(CGRect(x: 0, y: 0, width: 220, height: 220))
        paddedContext.draw(crop, in: CGRect(x: 45, y: 45, width: 130, height: 130))
        let paddedFeature = try! VisualFeatureEngine.makeQueryFeature(
            from: paddedContext.makeImage()!
        )
        let paddedDistance = VisualFeatureEngine.minimumDistance(
            from: paddedFeature,
            to: indexedFeatures
        )
        precondition(paddedDistance != nil && paddedDistance! < 0.4)
        print("Core smoke tests passed")
    }
}
