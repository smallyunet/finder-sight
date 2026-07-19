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
        let results = ImageSearcher.search(
            hash: zeros,
            records: [distant, exact],
            minimumSimilarity: 80,
            limit: 20
        )
        precondition(results.map(\.record.path) == ["/exact.png"])
        precondition(results.first?.similarity == 100)
        print("Core smoke tests passed")
    }
}
