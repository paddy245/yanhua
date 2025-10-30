#!/usr/bin/env bash
set -euo pipefail

# Config
VIDEO_URL="https://youtube.com/shorts/1TVx6hkrJNE?feature=share"
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
BASENAME="yanhua_src"
VIDEO_WEBM="$WORKDIR/${BASENAME}.fvideo.webm"
AUDIO_WEBM="$WORKDIR/${BASENAME}.faudio.webm"
MERGED_MKV="$WORKDIR/final.mkv"          # 无损合并（原编码：vp9+opus）
FINAL_MP4="$WORKDIR/final.mp4"           # 兼容广泛（h264+aac）
META_JSON="$WORKDIR/analysis.json"

command -v ffmpeg >/dev/null 2>&1 || { echo "[ERR] 未找到 ffmpeg，请先安装 (brew install ffmpeg)"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "[ERR] 未找到 python3"; exit 1; }

# 尽量使用本地的 yt-dlp（pip --user 安装）
if ! python3 -m yt_dlp --version >/dev/null 2>&1; then
  echo "[INFO] 未检测到 yt-dlp，开始安装..."
  python3 -m pip install --user yt-dlp
fi

# 1) 下载视频与音频
if [[ ! -f "$VIDEO_WEBM" || ! -f "$AUDIO_WEBM" ]]; then
  echo "[INFO] 开始下载：$VIDEO_URL"
  # 选择视频轨与音频轨分别保存（避免自动合并失败）
  python3 -m yt_dlp -f "bv*" -o "$VIDEO_WEBM" "$VIDEO_URL"
  python3 -m yt_dlp -f "ba*" -o "$AUDIO_WEBM" "$VIDEO_URL"
else
  echo "[INFO] 发现已下载的轨道文件，跳过下载"
fi

# 2) 无损合并到 MKV（保持与原版一致的编码与画质）
echo "[INFO] 合并音视频为 MKV（无损）: $MERGED_MKV"
ffmpeg -y -i "$VIDEO_WEBM" -i "$AUDIO_WEBM" -c copy "$MERGED_MKV"

# 3) 输出关键参数到 analysis.json，便于校验
ffprobe -v error -show_format -show_streams -print_format json "$MERGED_MKV" > "$META_JSON"
echo "[INFO] 已导出参数到: $META_JSON"

# 4) 可选：转码为 MP4（h264 + aac），以提升兼容性（视觉一致）
echo "[INFO] 生成兼容更广的 MP4 版本: $FINAL_MP4"
# 尽量保持分辨率/帧率与源一致（由 ffmpeg 自动继承），使用高质量编码设置
ffmpeg -y -i "$MERGED_MKV" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k "$FINAL_MP4"

# 5) 简单一致性校验：对比时长差异（秒级）
get_duration() { ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$1"; }
D_MKV=$(printf '%.2f' "$(get_duration "$MERGED_MKV")")
D_MP4=$(printf '%.2f' "$(get_duration "$FINAL_MP4")")
echo "[CHECK] MKV时长: $D_MKV s | MP4时长: $D_MP4 s"

echo "[DONE] 生成完成：\n- 无损文件: $MERGED_MKV\n- MP4文件: $FINAL_MP4\n- 参数文件: $META_JSON"
