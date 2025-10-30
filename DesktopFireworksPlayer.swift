import AppKit
import AVFoundation
import CoreGraphics

final class PlayerView: NSView {
	private let playerLayer = AVPlayerLayer()
	init(url: URL) {
		super.init(frame: .zero)
		wantsLayer = true
		layer?.backgroundColor = NSColor.black.cgColor
		playerLayer.player = AVPlayer(url: url)
		playerLayer.videoGravity = .resizeAspectFill
		layer?.addSublayer(playerLayer)
		NotificationCenter.default.addObserver(self, selector: #selector(restart), name: .AVPlayerItemDidPlayToEndTime, object: playerLayer.player?.currentItem)
		playerLayer.player?.isMuted = false
		playerLayer.player?.play()
	}
	required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
	override func layout() { super.layout(); playerLayer.frame = bounds }
	@objc private func restart() { playerLayer.player?.seek(to: .zero); playerLayer.player?.play() }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
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
			window = NSWindow(contentRect: screen.frame, styleMask: [.borderless], backing: .buffered, defer: false)
            let desktopLevel = NSWindow.Level(rawValue: Int(CGWindowLevelForKey(.desktopWindow)))
            window.level = desktopLevel  // 显示在桌面图标后作为壁纸
			window.isOpaque = true
			window.backgroundColor = .black
			window.collectionBehavior = [.canJoinAllSpaces, .stationary] // 显示在所有空间
			window.ignoresMouseEvents = true
			window.titleVisibility = .hidden
			window.titlebarAppearsTransparent = true
			window.setFrame(screen.frame, display: true)
			window.contentView = PlayerView(url: url)
			window.makeKeyAndOrderFront(nil)
		}

		// 注册 ESC 退出（可选）
		NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
			if event.keyCode == 53 { NSApp.terminate(nil) }
			return event
		}
	}
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.setActivationPolicy(.accessory) // 不在 Dock 显示为前台 App
app.delegate = delegate
app.run()
