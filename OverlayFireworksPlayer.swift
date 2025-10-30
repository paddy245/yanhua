import AppKit
import AVFoundation
import CoreGraphics

final class OverlayPlayerView: NSView {
    private let playerLayer = AVPlayerLayer()
    init(url: URL) {
        super.init(frame: .zero)
        wantsLayer = true
        layer?.backgroundColor = NSColor.clear.cgColor
        playerLayer.player = AVPlayer(url: url)
        playerLayer.videoGravity = .resizeAspect
        playerLayer.backgroundColor = NSColor.clear.cgColor
        layer?.addSublayer(playerLayer)
        NotificationCenter.default.addObserver(self, selector: #selector(restart), name: .AVPlayerItemDidPlayToEndTime, object: playerLayer.player?.currentItem)
        playerLayer.player?.isMuted = false
        playerLayer.player?.play()
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func layout() { super.layout(); playerLayer.frame = bounds }
    @objc private func restart() { playerLayer.player?.seek(to: .zero); playerLayer.player?.play() }
}

final class OverlayAppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    func applicationDidFinishLaunching(_ notification: Notification) {
        let fm = FileManager.default
        let root = URL(fileURLWithPath: "/Users/yangfeng/workspace/yanhua", isDirectory: true)
        let candidates = ["YANHUA_final.mp4", "final.mp4", "YANHUA_final_lossless.mkv", "final.mkv"]
        guard let url = candidates.compactMap({ root.appendingPathComponent($0) }).first(where: { fm.fileExists(atPath: $0.path) }) else {
            let alert = NSAlert()
            alert.messageText = "未找到视频文件"
            alert.informativeText = "请先运行 YANHUA_recreate.sh 生成成片。"
            alert.runModal()
            NSApp.terminate(nil)
            return
        }

        if let screen = NSScreen.main {
            // 计算右侧对齐的窗口矩形（默认靠右，9:16比例，自适应屏高的90%）
            let vf = screen.visibleFrame
            let margin = CGFloat(Double(ProcessInfo.processInfo.environment["OVERLAY_MARGIN"] ?? "40") ?? 40)
            let align = ProcessInfo.processInfo.environment["OVERLAY_ALIGN"] ?? "right" // right|left|center
            let hDefault = vf.height * 0.9
            let hVal = CGFloat(Double(ProcessInfo.processInfo.environment["OVERLAY_HEIGHT"] ?? "0") ?? 0)
            let targetH = hVal > 0 ? hVal : hDefault
            let wVal = CGFloat(Double(ProcessInfo.processInfo.environment["OVERLAY_WIDTH"] ?? "0") ?? 0)
            let targetW = wVal > 0 ? wVal : targetH * 9.0 / 16.0
            var x: CGFloat
            switch align.lowercased() {
            case "left":
                x = vf.minX + margin
            case "center":
                x = vf.midX - targetW/2.0
            default: // right
                x = vf.maxX - targetW - margin
            }
            let y = vf.minY + (vf.height - targetH)/2.0
            let rect = NSRect(x: x, y: y, width: targetW, height: targetH)

            window = NSWindow(contentRect: rect, styleMask: [.borderless], backing: .buffered, defer: false)
            window.isOpaque = false
            window.backgroundColor = .clear
            window.hasShadow = false
            window.ignoresMouseEvents = true   // 穿透，不拦截鼠标
            window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary] // 所有桌面可见
            // 提升窗口层级：置顶但不过度强势
            let level = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.floatingWindow)))
            window.level = level
            window.titleVisibility = .hidden
            window.titlebarAppearsTransparent = true
            window.setFrame(rect, display: true)
            window.contentView = OverlayPlayerView(url: url)
            window.makeKeyAndOrderFront(nil)
        }

        // 不抢前台焦点
        NSApp.activate(ignoringOtherApps: false)
    }
}

let app = NSApplication.shared
let delegate = OverlayAppDelegate()
app.setActivationPolicy(.accessory)
app.delegate = delegate
app.run()
