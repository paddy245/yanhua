# YANHUA 脚本使用说明

> 与原视频保持一致的烟花效果复刻与播放
>
> 引用来源：[YouTube Shorts](https://youtube.com/shorts/1TVx6hkrJNE?feature=share)

## 环境要求
- macOS（已验证）
- 需要可用的网络（首次下载原视频时）
- 依赖工具：
  - Homebrew（建议）
  - ffmpeg（视频合并/播放）
  - Python 3（已自带）

## 安装依赖
如未安装 Homebrew，可参考官网安装。随后执行：
```bash
brew install ffmpeg
python3 -m pip install --user yt-dlp
```

运行脚本时若缺少依赖，会自动提示并给出安装方式。

## 一键复刻原视频
生成与原版一致的母版（无损 mkv）与兼容 mp4：
```bash
/Users/yangfeng/workspace/yanhua/YANHUA_recreate.sh
```
完成后会在目录生成：
- 无损母版：`YANHUA_final_lossless.mkv`（或 `final.mkv`，脚本会同时生成）
- 兼容版本：`YANHUA_final.mp4`（或 `final.mp4`）
- 参数信息：`analysis.json`

说明：
- 脚本内部会自动用 `yt-dlp` 分别下载视频轨与音频轨，并用 `ffmpeg` 无损合并。
- mp4 版本采用高质量 H.264 + AAC 转码，播放兼容性更好。

## 弹窗播放“原版画面”
直接弹窗播放与链接一致的内容：
```bash
python3 /Users/yangfeng/workspace/yanhua/play_yanhua.py
```
- 优先使用 `ffplay` 播放；若未安装则回退到 OpenCV 弹窗播放。
- 如本地尚未生成成片，脚本会先自动调用 `YANHUA_recreate.sh` 生成后再播放。

可选：直接使用 `ffplay` 播放：
```bash
ffplay -hide_banner -loglevel error -autoexit \
  "/Users/yangfeng/workspace/yanhua/YANHUA_final_lossless.mkv"
```

## 悬浮穿透层播放（不挡前台应用）
将原版视频以“置顶透明、鼠标穿透”的方式悬浮播放，不影响前台操作：

1) 编译一次（或需要更新时）：
```bash
swiftc -framework AppKit -framework AVFoundation -framework CoreGraphics \
  -o "/Users/yangfeng/workspace/yanhua/OverlayFireworksPlayer" \
  "/Users/yangfeng/workspace/yanhua/OverlayFireworksPlayer.swift"
```

2) 运行（悬浮播放，完全穿透）：
```bash
"/Users/yangfeng/workspace/yanhua/OverlayFireworksPlayer"
```

停止方式：
- 在终端里按下 Ctrl+C（如果前台是该进程）
- 或在任意终端执行：`pkill -f OverlayFireworksPlayer`
- 也可在“活动监视器”里结束 `OverlayFireworksPlayer`

## 桌面壁纸层播放（显示在桌面图标后）
将原版视频作为桌面背景播放（不遮挡任何窗口）：

1) 编译一次（或需要更新时）：
```bash
swiftc -framework AppKit -framework AVFoundation -framework CoreGraphics \
  -o "/Users/yangfeng/workspace/yanhua/DesktopFireworksPlayer" \
  "/Users/yangfeng/workspace/yanhua/DesktopFireworksPlayer.swift"
```

2) 运行（作为桌面背景播放）：
```bash
"/Users/yangfeng/workspace/yanhua/DesktopFireworksPlayer"
```

停止方式：
- 在终端里按下 Ctrl+C（如果前台是该进程）
- 或执行：`pkill -f DesktopFireworksPlayer`
- 也可在“活动监视器”里结束 `DesktopFireworksPlayer`

## 程序化烟花动画（可选）
如果你希望“运行脚本产生相似的烟花动画（非原视频逐帧）”，可运行：
```bash
python3 /Users/yangfeng/workspace/yanhua/yanhua_fireworks.py
```
这会：
- 弹窗实时播放烟花动画
- 同时导出与原版分辨率/帧率一致的 `YANHUA_fireworks.mp4`

首次运行若缺依赖将提示安装：
```bash
python3 -m pip install --user pygame opencv-python
```

停止方式：
- 按 `ESC` 退出窗口
- 或在终端里按下 `Ctrl+C`

## 常见问题
- Q: 运行时提示找不到 `ffmpeg`？
  - A: 执行 `brew install ffmpeg` 安装后重试。
- Q: 下载视频失败/卡住？
  - A: 可能是网络波动，重试或更换网络；也可先手动安装 `yt-dlp` 后再运行。
- Q: 播放时黑屏或无窗口？
  - A: 若使用 OpenCV 播放，窗口是否被其他窗口遮挡；或直接使用 `ffplay` 命令播放。
- Q: 悬浮/壁纸播放器如何关闭？
  - A: 在终端执行 `pkill -f OverlayFireworksPlayer` 或 `pkill -f DesktopFireworksPlayer`，或在活动监视器结束进程。
- Q: 要固定体积/码率用于平台上传？
  - A: 可在 `YANHUA_recreate.sh` 中调整 mp4 转码配置（如 `-crf`、`-preset` 或设置 `-b:v`、`-maxrate`）。

## 文件说明
- `YANHUA_recreate.sh`：一键下载/合并原视频，输出 mkv 与 mp4（默认高质量）
- `play_yanhua.py`：若无成片会自动生成，随后弹窗播放“与原视频一致”的画面
- `yanhua_fireworks.py`：程序化烟花动画（可选），导出 `YANHUA_fireworks.mp4`
- `YANHUA_final_lossless.mkv`：无损母版（vp9 + aac）
- `YANHUA_final.mp4`：兼容更好的 H.264 + AAC 版本
- `analysis.json`：视频格式/流信息（分辨率、帧率、时长等）

---
如需我将输出文件改名、控制体积（例如 ≤20MB/≤50MB）、或统一帧率/分辨率（如 1080×1920@30fps），告诉我你的平台要求即可。
