import os
import subprocess
import sys

ROOT = os.path.dirname(__file__)
MKV = os.path.join(ROOT, "YANHUA_final_lossless.mkv")
MP4 = os.path.join(ROOT, "YANHUA_final.mp4")
RECREATE = os.path.join(ROOT, "YANHUA_recreate.sh")


def ensure_assets():
	if os.path.exists(MKV) or os.path.exists(MP4):
		return
	if not os.path.exists(RECREATE):
		raise SystemExit("找不到一键脚本 YANHUA_recreate.sh，无法生成视频资源")
	print("[INFO] 未发现现成成片，开始自动生成...")
	res = subprocess.run([RECREATE], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
	print(res.stdout)
	if not (os.path.exists(MKV) or os.path.exists(MP4) or os.path.exists(os.path.join(ROOT, "final.mkv")) or os.path.exists(os.path.join(ROOT, "final.mp4"))):
		raise SystemExit("生成失败：未找到成片文件")


def has_ffplay():
	return subprocess.call(["bash", "-lc", "command -v ffplay >/dev/null 2>&1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def main():
	ensure_assets()
	# 选择优先播放的文件
	video = MKV if os.path.exists(MKV) else MP4 if os.path.exists(MP4) else (
		os.path.join(ROOT, "final.mkv") if os.path.exists(os.path.join(ROOT, "final.mkv")) else os.path.join(ROOT, "final.mp4")
	)
	if not os.path.exists(video):
		raise SystemExit("未找到可播放视频文件")

	# 水印内容，可通过环境变量覆盖
	watermark = os.environ.get("WATERMARK", "paddy")
	print(f"[PLAY] 正在播放: {video} | 水印: {watermark}")
	if has_ffplay():
		# -fs 全屏可去掉，-autoexit 播放结束自动关闭
		# 使用 drawtext 叠加水印（右下角），依赖 libfreetype/fontconfig
		drawtext = (
			f"drawtext=text='{watermark}':font='Helvetica':fontsize=36:"
			"fontcolor=white:alpha=0.7:box=1:boxcolor=0x00000088:"
			"x=w-tw-20:y=h-th-20"
		)
		cmd = [
			"ffplay", "-hide_banner", "-loglevel", "error", "-autoexit",
			"-window_title", watermark,
			"-vf", drawtext,
			video,
		]
		subprocess.run(cmd)
		return

	# OpenCV 回退方案（窗口置顶行为依赖系统设置）
	try:
		import cv2
	except Exception:
		raise SystemExit("未安装 ffplay，且缺少 OpenCV。请安装：pip install opencv-python")
	cap = cv2.VideoCapture(video)
	if not cap.isOpened():
		raise SystemExit("无法打开视频文件")
	win_title = watermark
	cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)
	cv2.resizeWindow(win_title, 360, 640)
	while True:
		ok, frame = cap.read()
		if not ok:
			break
		# 叠加右下角水印
		try:
			h, w = frame.shape[:2]
			text = watermark
			font = cv2.FONT_HERSHEY_SIMPLEX
			scale = 1.0
			thickness = 2
			(tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
			x = max(10, w - tw - 20)
			y = max(th + 10, h - 20)
			# 半透明底框
			overlay = frame.copy()
			cv2.rectangle(overlay, (x - 10, y - th - 8), (x + tw + 10, y + 8), (0, 0, 0), -1)
			frame = cv2.addWeighted(overlay, 0.4, frame, 0.6, 0)
			# 文本
			cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
		except Exception:
			pass
		cv2.imshow(win_title, frame)
		key = cv2.waitKey(1)
		if key == 27:  # ESC
			break
	cap.release()
	cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
