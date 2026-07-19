import SwiftUI

@main
struct FinderSightApp: App {
    @StateObject private var model = AppModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified)
        .defaultSize(width: 1040, height: 720)
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("Add Folder…") { model.addDirectory() }
                    .keyboardShortcut("o", modifiers: .command)
            }
            CommandMenu("Library") {
                Button("Update Index") { model.indexNow() }
                    .keyboardShortcut("i", modifiers: .command)
                Button("Find Duplicates") { model.findDuplicates() }
                    .keyboardShortcut("d", modifiers: .command)
                Divider()
                Button("Clear Index…") { model.clearIndex() }
            }
            CommandGroup(replacing: .pasteboard) {
                Button("Paste Image") { model.pasteImage() }
                    .keyboardShortcut("v", modifiers: .command)
            }
        }

        Settings {
            SettingsView()
                .environmentObject(model)
        }
    }
}
