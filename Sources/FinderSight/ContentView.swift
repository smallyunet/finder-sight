import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @EnvironmentObject private var model: AppModel
    @State private var selectedDirectory: String?

    var body: some View {
        NavigationSplitView {
            sidebar
                .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 340)
        } detail: {
            mainContent
        }
        .frame(minWidth: 860, minHeight: 600)
        .toolbar {
            ToolbarItemGroup {
                Button(action: model.addDirectory) {
                    Label("Add Folder", systemImage: "folder.badge.plus")
                }
                Button(action: model.indexNow) {
                    Label("Update Index", systemImage: "arrow.clockwise")
                }
                .disabled(model.isWorking || model.config.directories.isEmpty)
                Button(action: model.findDuplicates) {
                    Label("Find Duplicates", systemImage: "square.on.square")
                }
                .disabled(model.isWorking || model.records.isEmpty)
            }
        }
        .task { model.prepare() }
        .alert("Finder Sight", isPresented: Binding(
            get: { model.errorMessage != nil },
            set: { if !$0 { model.errorMessage = nil } }
        )) {
            Button("OK", role: .cancel) { model.errorMessage = nil }
        } message: {
            Text(model.errorMessage ?? "")
        }
    }

    private var sidebar: some View {
        VStack(spacing: 0) {
            List(selection: $selectedDirectory) {
                Section("Library") {
                    ForEach(model.config.directories, id: \.self) { path in
                        Label {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(URL(fileURLWithPath: path).lastPathComponent)
                                    .lineLimit(1)
                                Text(path)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                                    .truncationMode(.middle)
                            }
                        } icon: {
                            Image(systemName: "folder")
                                .foregroundStyle(.tint)
                        }
                        .tag(path)
                        .contextMenu {
                            Button("Reveal in Finder") { model.reveal(path) }
                            Divider()
                            Button("Remove Folder", role: .destructive) {
                                model.removeDirectory(path)
                            }
                        }
                    }
                }

                Section("Tools") {
                    Button(action: model.findDuplicates) {
                        Label("Find Duplicates", systemImage: "square.on.square")
                    }
                    .buttonStyle(.plain)
                    Button(action: model.clearIndex) {
                        Label("Clear Index", systemImage: "trash")
                    }
                    .buttonStyle(.plain)
                }
            }
            .listStyle(.sidebar)

            VStack(alignment: .leading, spacing: 6) {
                Text(model.status)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                if model.isWorking {
                    ProgressView(value: model.progress)
                        .progressViewStyle(.linear)
                }
                HStack {
                    Text("\(model.records.count.formatted()) images")
                    Spacer()
                    Button(action: model.addDirectory) {
                        Image(systemName: "plus")
                    }
                    .buttonStyle(.borderless)
                    .help("Add Folder")
                    if let selectedDirectory {
                        Button(role: .destructive) {
                            model.removeDirectory(selectedDirectory)
                            self.selectedDirectory = nil
                        } label: {
                            Image(systemName: "minus")
                        }
                        .buttonStyle(.borderless)
                        .help("Remove Selected Folder")
                    }
                }
                .font(.caption)
            }
            .padding(12)
            .background(.bar)
        }
    }

    private var mainContent: some View {
        VStack(spacing: 18) {
            DropZone()
                .frame(height: 210)

            HStack {
                Text(sectionTitle)
                    .font(.title3.weight(.semibold))
                Spacer()
                if model.mode == .duplicates && !model.duplicateGroups.isEmpty {
                    Button("Move Duplicates to Trash", role: .destructive) {
                        model.moveDuplicatesToTrash()
                    }
                }
            }

            Group {
                switch model.mode {
                case .ready:
                    EmptyState(
                        icon: model.config.directories.isEmpty ? "folder.badge.plus" : "photo.on.rectangle.angled",
                        title: model.config.directories.isEmpty ? "Add an Image Folder" : "Ready to Search",
                        message: model.config.directories.isEmpty
                            ? "Choose folders that contain the images you want to search."
                            : "Drop, paste, or choose an image to find local matches.",
                        actionTitle: model.config.directories.isEmpty ? "Add Folder" : "Choose Image",
                        action: model.config.directories.isEmpty ? model.addDirectory : model.selectQueryImage
                    )
                case .searchResults:
                    SearchResultsGrid()
                case .duplicates:
                    DuplicateGroupsView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .padding(24)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var sectionTitle: String {
        switch model.mode {
        case .ready: return "Search Matches"
        case .searchResults: return model.results.isEmpty ? "No Matches Found" : "Found \(model.results.count) Matches"
        case .duplicates:
            let count = model.duplicateGroups.reduce(0) { $0 + $1.records.count }
            return model.duplicateGroups.isEmpty
                ? "No Duplicates Found"
                : "\(model.duplicateGroups.count) Duplicate Groups · \(count) Images"
        }
    }
}

private struct DropZone: View {
    @EnvironmentObject private var model: AppModel
    @State private var isTargeted = false

    var body: some View {
        Button(action: model.selectQueryImage) {
            ZStack(alignment: .topTrailing) {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(isTargeted ? Color.accentColor.opacity(0.10) : Color(nsColor: .controlBackgroundColor))
                    .overlay {
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .strokeBorder(
                                isTargeted ? Color.accentColor : Color(nsColor: .separatorColor),
                                style: StrokeStyle(lineWidth: isTargeted ? 2 : 1, dash: model.queryImage == nil ? [7, 5] : [])
                            )
                    }

                if let image = model.queryImage {
                    Image(nsImage: image)
                        .resizable()
                        .scaledToFit()
                        .padding(18)
                    Button(action: model.resetContent) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title2)
                            .symbolRenderingMode(.hierarchical)
                    }
                    .buttonStyle(.borderless)
                    .padding(12)
                } else {
                    VStack(spacing: 10) {
                        Image(systemName: "photo.badge.plus")
                            .font(.system(size: 42, weight: .light))
                            .foregroundStyle(.tint)
                        Text("Drop an image here")
                            .font(.headline)
                        Text("or click to choose · ⌘V to paste")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }

                if model.isWorking {
                    ProgressView()
                        .controlSize(.small)
                        .padding(14)
                }
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .onDrop(of: [UTType.fileURL.identifier], isTargeted: $isTargeted) { providers in
            guard let provider = providers.first else { return false }
            _ = provider.loadObject(ofClass: NSURL.self) { object, _ in
                guard let url = object as? URL else { return }
                Task { @MainActor in model.handleDroppedURL(url) }
            }
            return true
        }
    }
}

private struct SearchResultsGrid: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        if model.results.isEmpty {
            EmptyState(icon: "magnifyingglass", title: "No Matches Found", message: "Try lowering the minimum match score or adding more folders.")
        } else {
            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 145, maximum: 190), spacing: 18)], spacing: 20) {
                    ForEach(model.results) { result in
                        ResultCard(result: result)
                    }
                }
                .padding(2)
            }
        }
    }
}

private struct ResultCard: View {
    @EnvironmentObject private var model: AppModel
    let result: SearchResult

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Thumbnail(path: result.record.path)
                .frame(height: 125)
                .frame(maxWidth: .infinity)
                .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 10))
            Text(URL(fileURLWithPath: result.record.path).lastPathComponent)
                .font(.subheadline.weight(.medium))
                .lineLimit(1)
            Label("\(result.similarity)% match", systemImage: "checkmark.circle.fill")
                .font(.caption.weight(.semibold))
                .foregroundStyle(scoreColor)
        }
        .padding(10)
        .background(.background, in: RoundedRectangle(cornerRadius: 12))
        .overlay { RoundedRectangle(cornerRadius: 12).stroke(Color(nsColor: .separatorColor).opacity(0.5)) }
        .contentShape(Rectangle())
        .onTapGesture(count: 2) { model.reveal(result.record.path) }
        .contextMenu {
            Button("Reveal in Finder") { model.reveal(result.record.path) }
            Button("Open Image") { model.open(result.record.path) }
            Divider()
            Button("Copy Path") {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(result.record.path, forType: .string)
            }
        }
    }

    private var scoreColor: Color {
        result.similarity >= 95 ? .green : result.similarity >= 80 ? .accentColor : .orange
    }
}

private struct DuplicateGroupsView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        if model.duplicateGroups.isEmpty {
            EmptyState(icon: "checkmark.circle", title: "No Duplicates Found", message: "Indexed images in your library are unique.")
        } else {
            ScrollView {
                LazyVStack(spacing: 14) {
                    ForEach(Array(model.duplicateGroups.enumerated()), id: \.element.id) { index, group in
                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                Text("Group \(index + 1)").font(.headline)
                                Text("\(group.records.count) images").foregroundStyle(.secondary)
                                Spacer()
                                Text("Keeping best quality").font(.caption).foregroundStyle(.secondary)
                            }
                            ScrollView(.horizontal) {
                                HStack(spacing: 12) {
                                    ForEach(group.records) { record in
                                        VStack(alignment: .leading, spacing: 5) {
                                            Thumbnail(path: record.path)
                                                .frame(width: 120, height: 90)
                                                .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
                                            Text(URL(fileURLWithPath: record.path).lastPathComponent)
                                                .font(.caption)
                                                .lineLimit(1)
                                                .frame(width: 120, alignment: .leading)
                                            if record.id == group.records.first?.id {
                                                Label("Keep", systemImage: "checkmark.circle.fill")
                                                    .font(.caption2.weight(.semibold))
                                                    .foregroundStyle(.green)
                                            } else {
                                                Text("Duplicate").font(.caption2).foregroundStyle(.secondary)
                                            }
                                        }
                                        .onTapGesture(count: 2) { model.reveal(record.path) }
                                    }
                                }
                            }
                        }
                        .padding(16)
                        .background(.background, in: RoundedRectangle(cornerRadius: 12))
                        .overlay { RoundedRectangle(cornerRadius: 12).stroke(Color(nsColor: .separatorColor).opacity(0.5)) }
                    }
                }
                .padding(2)
            }
        }
    }
}

private struct Thumbnail: View {
    let path: String
    var body: some View {
        Group {
            if let image = NSImage(contentsOfFile: path) {
                Image(nsImage: image).resizable().scaledToFit()
            } else {
                Image(systemName: "photo").font(.largeTitle).foregroundStyle(.tertiary)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

private struct EmptyState: View {
    let icon: String
    let title: String
    let message: String
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(.secondary)
            Text(title)
                .font(.title3.weight(.semibold))
            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            if let actionTitle, let action {
                Button(actionTitle, action: action)
            }
        }
        .frame(maxWidth: 420)
    }
}
