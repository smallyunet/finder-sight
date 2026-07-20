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
