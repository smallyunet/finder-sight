import AppKit
import SwiftUI
import UniformTypeIdentifiers

private enum WorkspaceDestination: Hashable {
    case search
    case duplicates
}

struct ContentView: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        NavigationSplitView {
            sidebar
                .navigationSplitViewColumnWidth(min: 200, ideal: 240, max: 300)
        } detail: {
            mainContent
        }
        .frame(minWidth: 760, minHeight: 560)
        .toolbar {
            ToolbarItemGroup {
                Button(action: model.addDirectory) {
                    Label("Add Folder", systemImage: "folder.badge.plus")
                }
                .disabled(model.isWorking)

                Button(action: model.indexNow) {
                    Label("Update Index", systemImage: "arrow.clockwise")
                }
                .disabled(model.isWorking || model.config.directories.isEmpty)
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

    private var workspaceSelection: Binding<WorkspaceDestination?> {
        Binding(
            get: { model.mode == .duplicates ? .duplicates : .search },
            set: { destination in
                switch destination {
                case .search: model.activateSearch()
                case .duplicates: model.activateDuplicates()
                case nil: break
                }
            }
        )
    }

    private var sidebar: some View {
        VStack(spacing: 0) {
            List(selection: workspaceSelection) {
                Section("Workspace") {
                    Label("Search", systemImage: "sparkle.magnifyingglass")
                        .tag(WorkspaceDestination.search)
                    Label("Duplicates", systemImage: "square.on.square")
                        .tag(WorkspaceDestination.duplicates)
                }

                Section("Library") {
                    if model.config.directories.isEmpty {
                        Text("No folders added")
                            .foregroundStyle(.secondary)
                    } else {
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
                            .contextMenu {
                                Button("Reveal in Finder") { model.reveal(path) }
                                Divider()
                                Button("Remove Folder", role: .destructive) {
                                    model.removeDirectory(path)
                                }
                            }
                        }
                    }
                }
            }
            .listStyle(.sidebar)

            HStack(spacing: 8) {
                Image(systemName: "photo.on.rectangle")
                Text("\(model.records.count.formatted()) images")
                    .monospacedDigit()
                Spacer()
                Button(action: model.addDirectory) {
                    Image(systemName: "plus")
                }
                .buttonStyle(.borderless)
                .disabled(model.isWorking)
                .help("Add Folder")
                .accessibilityLabel("Add Folder")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
            .padding(12)
            .background(.bar)
        }
    }

    private var mainContent: some View {
        VStack(spacing: 16) {
            if model.isIndexing {
                IndexingBanner()
                    .transition(.move(edge: .top).combined(with: .opacity))
            }

            Group {
                switch model.mode {
                case .ready, .searchResults:
                    SearchWorkspace()
                        .transition(.opacity)
                case .duplicates:
                    DuplicateWorkspace()
                        .transition(.opacity)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
        }
        .padding(24)
        .background(Color(nsColor: .windowBackgroundColor))
    }
}

private struct IndexingBanner: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        VStack(spacing: 8) {
            HStack {
                Label(model.status, systemImage: "arrow.triangle.2.circlepath")
                    .font(.callout)
                    .lineLimit(1)
                Spacer()
                Button("Cancel", action: model.cancelIndexing)
                    .buttonStyle(.link)
            }
            ProgressView(value: model.progress)
                .progressViewStyle(.linear)
                .accessibilityLabel("Indexing progress")
                .accessibilityValue("\(Int(model.progress * 100)) percent")
        }
        .padding(12)
        .background(Color.accentColor.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
        .overlay {
            RoundedRectangle(cornerRadius: 10)
                .stroke(Color.accentColor.opacity(0.18))
        }
    }
}

private struct SearchWorkspace: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        VStack(spacing: 16) {
            DropZone(compact: model.queryImage != nil)
                .frame(height: model.queryImage == nil ? 178 : 92)

            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(sectionTitle)
                        .font(.title2.weight(.semibold))
                    if model.mode == .ready && !model.config.directories.isEmpty {
                        Text("Search across \(model.records.count.formatted()) indexed images")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                }
                Spacer()
            }

            Group {
                switch model.mode {
                case .ready:
                    readyContent
                case .searchResults:
                    SearchResultsGrid()
                case .duplicates:
                    EmptyView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    @ViewBuilder
    private var readyContent: some View {
        if model.config.directories.isEmpty {
            EmptyState(
                icon: "folder.badge.plus",
                title: "Build Your Image Library",
                message: "Add one or more folders before searching your local images.",
                actionTitle: "Add Folder",
                action: model.addDirectory
            )
        } else {
            EmptyState(
                icon: "photo.on.rectangle.angled",
                title: "Choose an Image to Begin",
                message: "Drop an image above, choose a file, or paste one with ⌘V."
            )
        }
    }

    private var sectionTitle: String {
        switch model.mode {
        case .ready:
            return model.config.directories.isEmpty ? "Search" : "Ready to Search"
        case .searchResults:
            if model.results.isEmpty { return "No Matches Found" }
            return model.showingClosestResults
                ? "Showing \(model.results.count) Closest Images"
                : "\(model.results.count) Matches"
        case .duplicates:
            return "Search"
        }
    }
}

private struct DropZone: View {
    @EnvironmentObject private var model: AppModel
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isTargeted = false
    @State private var isHovering = false
    let compact: Bool

    var body: some View {
        ZStack(alignment: .topTrailing) {
            Button(action: model.selectQueryImage) {
                ZStack {
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(backgroundColor)
                        .overlay {
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .strokeBorder(
                                    isTargeted ? Color.accentColor : Color(nsColor: .separatorColor),
                                    style: StrokeStyle(
                                        lineWidth: isTargeted ? 2 : 1,
                                        dash: compact ? [] : [7, 5]
                                    )
                                )
                        }

                    if let image = model.queryImage {
                        HStack(spacing: 14) {
                            Image(nsImage: image)
                                .resizable()
                                .scaledToFit()
                                .frame(width: 112, height: 68)
                                .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
                                .clipShape(RoundedRectangle(cornerRadius: 8))

                            VStack(alignment: .leading, spacing: 4) {
                                Text("Query Image")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Text(model.queryLabel)
                                    .font(.headline)
                                    .lineLimit(1)
                                Text("Click to choose a different image")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            if model.isWorking && !model.isIndexing {
                                ProgressView()
                                    .controlSize(.small)
                                    .accessibilityLabel("Searching")
                            }
                        }
                        .padding(.horizontal, 16)
                    } else {
                        VStack(spacing: 9) {
                            Image(systemName: "photo.badge.plus")
                                .font(.system(size: 38, weight: .light))
                                .foregroundStyle(.tint)
                            Text("Drop an image here")
                                .font(.headline)
                            Text("or click to choose · ⌘V to paste")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .help(compact ? "Choose a different image" : "Choose an image to search")
            .onHover { isHovering = $0 }

            if model.queryImage != nil {
                Button(action: model.clearSearch) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.title2)
                        .symbolRenderingMode(.hierarchical)
                }
                .buttonStyle(.borderless)
                .help("Clear search")
                .accessibilityLabel("Clear search")
                .padding(9)
            }
        }
        .onDrop(of: [UTType.fileURL.identifier], isTargeted: $isTargeted) { providers in
            guard let provider = providers.first else { return false }
            _ = provider.loadObject(ofClass: NSURL.self) { object, _ in
                guard let url = object as? URL else { return }
                Task { @MainActor in model.handleDroppedURL(url) }
            }
            return true
        }
        .animation(reduceMotion ? nil : .easeOut(duration: 0.18), value: isTargeted)
        .animation(reduceMotion ? nil : .easeOut(duration: 0.18), value: isHovering)
    }

    private var backgroundColor: Color {
        if isTargeted { return Color.accentColor.opacity(0.10) }
        if isHovering { return Color(nsColor: .controlBackgroundColor).opacity(0.82) }
        return Color(nsColor: .controlBackgroundColor)
    }
}

private struct SearchResultsGrid: View {
    @EnvironmentObject private var model: AppModel

    var body: some View {
        if model.results.isEmpty {
            if model.status.hasPrefix("Moved ") {
                EmptyState(
                    icon: "trash",
                    title: "Result Moved to Trash",
                    message: "The file was removed from your results and local index."
                )
            } else {
                EmptyState(
                    icon: "magnifyingglass",
                    title: "No Matches Found",
                    message: "Try lowering the minimum match score or adding more folders."
                )
            }
        } else {
            VStack(alignment: .leading, spacing: 10) {
                if model.showingClosestResults {
                    Label(
                        "No images met the minimum score. These are the closest alternatives.",
                        systemImage: "info.circle"
                    )
                    .font(.callout)
                    .foregroundStyle(.secondary)
                }
                ScrollView {
                    LazyVGrid(
                        columns: [GridItem(.adaptive(minimum: 156, maximum: 210), spacing: 16)],
                        spacing: 16
                    ) {
                        ForEach(model.results) { result in
                            ResultCard(result: result)
                        }
                    }
                    .padding(2)
                }
            }
        }
    }
}

private struct ResultCard: View {
    @EnvironmentObject private var model: AppModel
    @FocusState private var isFocused: Bool
    @State private var isHovering = false
    let result: SearchResult

    var body: some View {
        Button {
            model.open(result.record.path)
        } label: {
            VStack(alignment: .leading, spacing: 7) {
                ZStack(alignment: .topTrailing) {
                    Thumbnail(path: result.record.path)
                        .frame(height: 126)
                        .frame(maxWidth: .infinity)
                        .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 9))
                    if isHovering {
                        Image(systemName: "arrow.up.forward.app.fill")
                            .symbolRenderingMode(.hierarchical)
                            .padding(7)
                            .background(.ultraThinMaterial, in: Circle())
                            .padding(7)
                    }
                }
                Text(fileURL.lastPathComponent)
                    .font(.subheadline.weight(.medium))
                    .lineLimit(1)
                Text(fileURL.deletingLastPathComponent().lastPathComponent)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                Label(
                    "\(result.similarity)% \(result.isVisualMatch ? "visual" : "match")",
                    systemImage: result.isVisualMatch ? "eye.fill" : "checkmark.circle.fill"
                )
                .font(.caption.weight(.semibold))
                .foregroundStyle(scoreColor)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .focused($isFocused)
        .padding(10)
        .background(cardBackground, in: RoundedRectangle(cornerRadius: 12))
        .overlay {
            RoundedRectangle(cornerRadius: 12)
                .stroke(
                    isFocused ? Color.accentColor : Color(nsColor: .separatorColor).opacity(isHovering ? 0.85 : 0.5),
                    lineWidth: isFocused ? 2 : 1
                )
        }
        .onHover { isHovering = $0 }
        .help("Open \(fileURL.lastPathComponent)")
        .accessibilityLabel(
            "\(fileURL.lastPathComponent), \(result.similarity) percent \(result.isVisualMatch ? "visual similarity" : "match")"
        )
        .accessibilityHint("Opens the image")
        .contextMenu {
            Button("Open Image") { model.open(result.record.path) }
            Button("Reveal in Finder") { model.reveal(result.record.path) }
            Divider()
            Button("Copy Path") {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(result.record.path, forType: .string)
            }
            Divider()
            Button("Move to Trash…", role: .destructive) {
                model.moveSearchResultToTrash(result)
            }
        }
    }

    private var fileURL: URL { URL(fileURLWithPath: result.record.path) }

    private var cardBackground: Color {
        isHovering ? Color(nsColor: .controlBackgroundColor) : Color(nsColor: .textBackgroundColor)
    }

    private var scoreColor: Color {
        result.similarity >= 95 ? .green : result.similarity >= 80 ? .accentColor : .orange
    }
}

private struct DuplicateWorkspace: View {
    @EnvironmentObject private var model: AppModel
    @State private var keeperIDs: [String: String] = [:]

    var body: some View {
        VStack(spacing: 16) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.title2.weight(.semibold))
                    Text(subtitle)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button(action: model.findDuplicates) {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
                .disabled(model.isWorking)
                if !candidates.isEmpty {
                    Button("Move \(candidates.count) to Trash", role: .destructive) {
                        model.moveDuplicatesToTrash(keeping: Set(keeperIDs.values))
                    }
                    .disabled(model.isWorking)
                }
            }

            if model.isWorking && !model.isIndexing {
                VStack(spacing: 12) {
                    ProgressView()
                    Text("Checking your library for exact duplicates…")
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if model.duplicateGroups.isEmpty {
                EmptyState(
                    icon: "checkmark.circle",
                    title: "No Duplicates Found",
                    message: "Every indexed image in your library is unique."
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: 14) {
                        ForEach(Array(model.duplicateGroups.enumerated()), id: \.element.id) { index, group in
                            DuplicateGroupCard(
                                index: index,
                                group: group,
                                keeperID: keeperIDs[group.id] ?? group.records.first?.id,
                                onSelectKeeper: { keeperIDs[group.id] = $0 }
                            )
                        }
                    }
                    .padding(2)
                }
            }
        }
        .onAppear(perform: syncKeepers)
        .onChange(of: model.duplicateGroups) { _ in syncKeepers() }
    }

    private var candidates: [ImageRecord] {
        model.duplicateGroups.flatMap { group in
            let keeperID = keeperIDs[group.id] ?? group.records.first?.id
            return group.records.filter { $0.id != keeperID }
        }
    }

    private var title: String {
        model.duplicateGroups.isEmpty
            ? "Duplicates"
            : "\(model.duplicateGroups.count) Duplicate Groups"
    }

    private var subtitle: String {
        guard !model.duplicateGroups.isEmpty else {
            return "Review exact copies and safely recover storage space."
        }
        let size = ByteCountFormatter.string(
            fromByteCount: candidates.reduce(0) { $0 + $1.fileSize },
            countStyle: .file
        )
        return "Choose one image to keep in each group · About \(size) recoverable"
    }

    private func syncKeepers() {
        var next: [String: String] = [:]
        for group in model.duplicateGroups {
            if let existing = keeperIDs[group.id], group.records.contains(where: { $0.id == existing }) {
                next[group.id] = existing
            } else {
                next[group.id] = group.records.first?.id
            }
        }
        keeperIDs = next
    }
}

private struct DuplicateGroupCard: View {
    let index: Int
    let group: DuplicateGroup
    let keeperID: String?
    let onSelectKeeper: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Group \(index + 1)")
                    .font(.headline)
                Text("\(group.records.count) images")
                    .foregroundStyle(.secondary)
                Spacer()
                Label("Select one to keep", systemImage: "checkmark.circle")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            ScrollView(.horizontal) {
                HStack(spacing: 12) {
                    ForEach(group.records) { record in
                        DuplicateRecordCard(
                            record: record,
                            isKeeper: record.id == keeperID,
                            onSelectKeeper: { onSelectKeeper(record.id) }
                        )
                    }
                }
            }
        }
        .padding(16)
        .background(Color(nsColor: .textBackgroundColor), in: RoundedRectangle(cornerRadius: 12))
        .overlay {
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(nsColor: .separatorColor).opacity(0.5))
        }
    }
}

private struct DuplicateRecordCard: View {
    @EnvironmentObject private var model: AppModel
    @FocusState private var isFocused: Bool
    @State private var isHovering = false
    let record: ImageRecord
    let isKeeper: Bool
    let onSelectKeeper: () -> Void

    var body: some View {
        Button(action: onSelectKeeper) {
            VStack(alignment: .leading, spacing: 6) {
                Thumbnail(path: record.path)
                    .frame(width: 148, height: 100)
                    .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 8))
                Text(fileURL.lastPathComponent)
                    .font(.caption.weight(.medium))
                    .lineLimit(1)
                Text("\(record.pixelWidth) × \(record.pixelHeight) · \(formattedSize)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                Label(
                    isKeeper ? "Keep this image" : "Choose to keep",
                    systemImage: isKeeper ? "checkmark.circle.fill" : "circle"
                )
                .font(.caption.weight(.semibold))
                .foregroundStyle(isKeeper ? Color.green : Color.secondary)
            }
            .frame(width: 148, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .focused($isFocused)
        .padding(9)
        .background(cardBackground, in: RoundedRectangle(cornerRadius: 10))
        .overlay {
            RoundedRectangle(cornerRadius: 10)
                .stroke(borderColor, lineWidth: isKeeper || isFocused ? 2 : 1)
        }
        .onHover { isHovering = $0 }
        .help(isKeeper ? "Selected to keep" : "Select this image to keep")
        .accessibilityLabel(
            "\(fileURL.lastPathComponent), \(record.pixelWidth) by \(record.pixelHeight), \(formattedSize), \(isKeeper ? "selected to keep" : "will move to Trash")"
        )
        .accessibilityHint("Selects this image as the copy to keep")
        .contextMenu {
            Button("Open Image") { model.open(record.path) }
            Button("Reveal in Finder") { model.reveal(record.path) }
            Divider()
            Button("Keep This Image") { onSelectKeeper() }
        }
    }

    private var fileURL: URL { URL(fileURLWithPath: record.path) }

    private var formattedSize: String {
        ByteCountFormatter.string(fromByteCount: record.fileSize, countStyle: .file)
    }

    private var cardBackground: Color {
        if isKeeper { return Color.green.opacity(0.08) }
        if isHovering { return Color(nsColor: .controlBackgroundColor) }
        return Color(nsColor: .textBackgroundColor)
    }

    private var borderColor: Color {
        if isFocused { return .accentColor }
        if isKeeper { return .green }
        return Color(nsColor: .separatorColor).opacity(isHovering ? 0.8 : 0.35)
    }
}

private struct Thumbnail: View {
    let path: String
    @State private var image: NSImage?

    var body: some View {
        Group {
            if let image {
                Image(nsImage: image)
                    .resizable()
                    .scaledToFit()
            } else {
                ZStack {
                    Image(systemName: "photo")
                        .font(.largeTitle)
                        .foregroundStyle(.tertiary)
                    ProgressView()
                        .controlSize(.small)
                }
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .task(id: path) {
            let loaded = await Task.detached(priority: .utility) {
                LoadedThumbnail(
                    image: ThumbnailCache.shared.image(at: path, maxPixelSize: 360)
                )
            }.value
            image = loaded.image
        }
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
                .font(.system(size: 42, weight: .light))
                .foregroundStyle(.secondary)
            Text(title)
                .font(.title3.weight(.semibold))
            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            if let actionTitle, let action {
                Button(actionTitle, action: action)
                    .buttonStyle(.borderedProminent)
            }
        }
        .frame(maxWidth: 440)
    }
}
