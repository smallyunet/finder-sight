import AppKit
import XCTest
@testable import FinderSight

final class FinderSightTests: XCTestCase {
    func testHashDistance() {
        let zeros = String(repeating: "0", count: 64)
        let ones = String(repeating: "f", count: 64)
        XCTAssertEqual(PerceptualHash.distance(zeros, zeros), 0)
        XCTAssertEqual(PerceptualHash.distance(zeros, ones), 256)
    }

    func testSearchThresholdAndRanking() {
        let exact = ImageRecord(
            path: "/exact.png", hash: String(repeating: "0", count: 64),
            modificationTime: 0, pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let distant = ImageRecord(
            path: "/distant.png", hash: String(repeating: "f", count: 64),
            modificationTime: 0, pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let outcome = ImageSearcher.search(
            hash: exact.hash,
            records: [distant, exact],
            minimumSimilarity: 80,
            limit: 20
        )
        XCTAssertEqual(outcome.results.map(\.record.path), ["/exact.png"])
        XCTAssertEqual(outcome.results.first?.similarity, 100)
        XCTAssertFalse(outcome.isClosestFallback)
    }

    func testSearchFallsBackToNearestResults() {
        let record = ImageRecord(
            path: "/nearest.png", hash: String(repeating: "f", count: 64),
            modificationTime: 0, pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let outcome = ImageSearcher.search(
            hash: String(repeating: "0", count: 64),
            records: [record],
            minimumSimilarity: 100,
            limit: 20
        )
        XCTAssertEqual(outcome.results.map(\.record.path), ["/nearest.png"])
        XCTAssertTrue(outcome.isClosestFallback)
    }

    func testVisualFeatureRoundTripDistance() throws {
        let image = NSImage(size: NSSize(width: 160, height: 120))
        image.lockFocus()
        NSColor.white.setFill()
        NSRect(x: 0, y: 0, width: 160, height: 120).fill()
        NSColor.systemPurple.setFill()
        NSBezierPath(ovalIn: NSRect(x: 38, y: 18, width: 84, height: 84)).fill()
        NSColor.black.setFill()
        NSRect(x: 72, y: 38, width: 16, height: 62).fill()
        image.unlockFocus()

        let archive = try VisualFeatureEngine.makeQueryFeature(from: image)
        let feature = VisualFeature(region: .full, observationArchive: archive)
        let distance = try XCTUnwrap(
            VisualFeatureEngine.minimumDistance(from: archive, to: [feature])
        )

        XCTAssertEqual(distance, 0, accuracy: 0.0001)
        XCTAssertEqual(VisualFeatureEngine.similarity(for: distance), 100)
    }

    func testRegionalFeatureFindsAnExactCrop() throws {
        let width = 200
        let height = 200
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return XCTFail("Could not create test image context")
        }
        context.setFillColor(NSColor.systemRed.cgColor)
        context.fill(CGRect(x: 0, y: 0, width: 130, height: 130))
        context.setFillColor(NSColor.systemBlue.cgColor)
        context.fill(CGRect(x: 70, y: 70, width: 130, height: 130))
        context.setFillColor(NSColor.black.cgColor)
        context.fill(CGRect(x: 20, y: 35, width: 70, height: 24))
        guard let fullImage = context.makeImage(),
              let crop = fullImage.cropping(to: CGRect(x: 0, y: 0, width: 130, height: 130)) else {
            return XCTFail("Could not create test images")
        }

        let indexed = try VisualFeatureEngine.makeIndexFeatures(from: fullImage)
        let query = try VisualFeatureEngine.makeQueryFeature(from: crop)
        let distance = try XCTUnwrap(
            VisualFeatureEngine.minimumDistance(from: query, to: indexed)
        )

        XCTAssertLessThan(distance, 0.05)
        XCTAssertGreaterThanOrEqual(VisualFeatureEngine.similarity(for: distance), 97)
    }

    func testVisualSimilarityCanPromoteAResult() {
        let record = ImageRecord(
            path: "/visual.png", hash: String(repeating: "f", count: 64),
            modificationTime: 0, pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let result = SearchResult(record: record, distance: 256, visualDistance: 0.3)

        XCTAssertEqual(result.similarity, 85)
        XCTAssertTrue(result.isVisualMatch)
    }

    func testDuplicateQualityPrefersResolution() {
        let small = ImageRecord(
            path: "/small.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 100, pixelHeight: 100, fileSize: 500
        )
        let large = ImageRecord(
            path: "/large.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 500, pixelHeight: 500, fileSize: 100
        )
        XCTAssertTrue(DuplicateFinder.qualityFirst(large, small))
    }

    func testDuplicateCleanupRespectsSelectedKeeper() {
        let recommended = ImageRecord(
            path: "/recommended.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 500, pixelHeight: 500, fileSize: 500
        )
        let selected = ImageRecord(
            path: "/selected.jpg", hash: "same", modificationTime: 0,
            pixelWidth: 100, pixelHeight: 100, fileSize: 100
        )
        let group = DuplicateGroup(id: "same", records: [recommended, selected])

        let candidates = DuplicateFinder.deletionCandidates(
            in: [group],
            keeping: [selected.id]
        )

        XCTAssertEqual(candidates.map(\.id), [recommended.id])
    }

    func testVersionComparison() {
        XCTAssertTrue(UpdateService.isNewer("v0.2.0", than: "0.1.6"))
        XCTAssertFalse(UpdateService.isNewer("v0.1.6", than: "0.1.6"))
    }

    func testCancelledIndexDoesNotProduceReplacementRecords() throws {
        let directory = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }

        let controller = IndexingController()
        controller.cancel()
        let result = ImageIndexer.scan(
            directories: [directory.path],
            existing: [:],
            controller: controller,
            progress: { _, _, _ in }
        )
        XCTAssertTrue(result.wasCancelled)
        XCTAssertTrue(result.records.isEmpty)
    }
}
