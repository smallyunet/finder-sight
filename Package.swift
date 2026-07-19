// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FinderSight",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "FinderSight", targets: ["FinderSight"])
    ],
    targets: [
        .executableTarget(
            name: "FinderSight",
            path: "Sources/FinderSight"
        ),
        .testTarget(
            name: "FinderSightTests",
            dependencies: ["FinderSight"],
            path: "Tests/FinderSightTests"
        )
    ],
    swiftLanguageModes: [.v5]
)
