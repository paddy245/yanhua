import os
import sys
import math
import random
import time
from dataclasses import dataclass

# Lazy imports for environments without pygame/cv2
try:
	import pygame
except Exception as e:
	pygame = None
try:
	import cv2
	import numpy as np
except Exception as e:
	cv2 = None

def ensure_deps():
	missing = []
	if pygame is None:
		missing.append("pygame")
	if cv2 is None:
		missing.append("opencv-python")
	if missing:
		raise RuntimeError(f"缺少依赖: {', '.join(missing)}。请先安装后再运行。")

# Rendering config (align with source video)
WIDTH = 720
HEIGHT = 1280
FPS = 30
DURATION_SEC = 7.67  # 与原视频时长对齐
BACKGROUND = (6, 8, 12)  # 暗夜天空

# Firework parameters
GRAVITY = 0.15
AIR_DRAG = 0.995
ROCKET_MIN_SPEED = 16
ROCKET_MAX_SPEED = 22
PARTICLES_PER_BURST = 140
PARTICLE_SPEED_MIN = 2.0
PARTICLE_SPEED_MAX = 7.5
PARTICLE_LIFE_MIN = 45
PARTICLE_LIFE_MAX = 75
TRAIL_DECAY = 0.86
BLUR_ALPHA = 30  # motion blur strength (0-255)

# Timed bursts to roughly match a short video rhythm
SCHEDULE = [0.6, 2.2, 3.6, 5.0, 6.2]  # seconds, approximate evenly spaced

@dataclass
class Particle:
	x: float
	y: float
	vx: float
	vy: float
	life: int
	color: tuple
	size: float


def hsv_to_rgb(h, s, v):
	h = float(h % 1.0)
	i = int(h * 6.0)
	f = h * 6.0 - i
	p = int(255 * v * (1.0 - s))
	q = int(255 * v * (1.0 - f * s))
	t = int(255 * v * (1.0 - (1.0 - f) * s))
	v = int(255 * v)
	i = i % 6
	if i == 0:
		return (v, t, p)
	if i == 1:
		return (q, v, p)
	if i == 2:
		return (p, v, t)
	if i == 3:
		return (p, q, v)
	if i == 4:
		return (t, p, v)
	return (v, p, q)


class Firework:
	def __init__(self, x, y, target_y):
		self.x = x
		y0 = y
		self.y = y0
		self.target_y = target_y
		self.vx = random.uniform(-1.2, 1.2)
		self.vy = -random.uniform(ROCKET_MIN_SPEED, ROCKET_MAX_SPEED)
		self.exploded = False
		self.particles = []
		base_hue = random.random()
		self.palette = [
			hsv_to_rgb((base_hue + random.uniform(-0.03, 0.03)) % 1.0, 1.0, 1.0)
			for _ in range(6)
		]

	def update(self):
		if not self.exploded:
			self.vy += GRAVITY * 0.6
			self.x += self.vx
			self.y += self.vy
			if self.y <= self.target_y or self.vy > 0:
				self.explode()
		else:
			next_particles = []
			for p in self.particles:
				p.vx *= AIR_DRAG
				p.vy = p.vy * AIR_DRAG + GRAVITY
				p.x += p.vx
				p.y += p.vy
				p.life -= 1
				if p.life > 0:
					next_particles.append(p)
			self.particles = next_particles

	def explode(self):
		self.exploded = True
		for _ in range(PARTICLES_PER_BURST):
			ang = random.uniform(0, 2 * math.pi)
			spd = random.uniform(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX)
			vx = math.cos(ang) * spd
			vy = math.sin(ang) * spd
			life = random.randint(PARTICLE_LIFE_MIN, PARTICLE_LIFE_MAX)
			col = random.choice(self.palette)
			size = random.uniform(1.4, 2.2)
			self.particles.append(Particle(self.x, self.y, vx, vy, life, col, size))

	def is_done(self):
		return self.exploded and len(self.particles) == 0

	def draw(self, surface):
		if not self.exploded:
			pygame.draw.circle(surface, (255, 240, 200), (int(self.x), int(self.y)), 3)
		else:
			for p in self.particles:
				alpha_scale = max(0.0, min(1.0, p.life / PARTICLE_LIFE_MAX))
				r, g, b = p.color
				col = (int(r * alpha_scale), int(g * alpha_scale), int(b * alpha_scale))
				pygame.draw.circle(surface, col, (int(p.x), int(p.y)), max(1, int(p.size)))


def main():
	ensure_deps()
	os.environ["SDL_VIDEO_CENTERED"] = "1"
	pygame.init()
	pygame.display.set_caption("YANHUA Fireworks")
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	clock = pygame.time.Clock()

	# For motion blur, we keep an offscreen surface and blend
	trail = pygame.Surface((WIDTH, HEIGHT), flags=pygame.SRCALPHA)

	# Prepare video writer (H.264)
	fourcc = cv2.VideoWriter_fourcc(*"avc1")
	out_path = os.path.join(os.path.dirname(__file__), "YANHUA_fireworks.mp4")
	writer = cv2.VideoWriter(out_path, fourcc, FPS, (WIDTH, HEIGHT))

	fireworks = []
	start_time = time.time()
	next_schedule_index = 0

	running = True
	frames = 0
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False

		elapsed = time.time() - start_time
		# schedule launches
		while (
			next_schedule_index < len(SCHEDULE)
			and elapsed >= SCHEDULE[next_schedule_index]
		):
			x = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
			target_y = random.uniform(HEIGHT * 0.20, HEIGHT * 0.45)
			fw = Firework(x=x, y=HEIGHT - 10, target_y=target_y)
			fireworks.append(fw)
			next_schedule_index += 1

		# background + trail fade
		screen.fill(BACKGROUND)
		trail.fill((0, 0, 0, BLUR_ALPHA))  # alpha-only fade
		screen.blit(trail, (0, 0))

		# update & draw
		alive = []
		for fw in fireworks:
			fw.update()
			fw.draw(screen)
			if not fw.is_done():
				alive.append(fw)
		fireworks = alive

		# copy to trail to leave motion traces
		trail.blit(screen, (0, 0))

		# flip
		pygame.display.flip()
		clock.tick(FPS)
		frames += 1

		# write frame to mp4
		# Convert pygame surface (RGB) to BGR numpy array for OpenCV
		array = pygame.surfarray.array3d(screen)
		frame = np.rot90(array, 3)  # rotate to match orientation
		frame = np.fliplr(frame)
		frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
		writer.write(frame_bgr)

		if elapsed >= DURATION_SEC:
			break

	# drain a little to let the last particles fade (optional)
	for _ in range(int(0.25 * FPS)):
		clock.tick(FPS)

	writer.release()
	pygame.quit()
	print(f"[DONE] 动画完成并导出: {out_path}")


if __name__ == "__main__":
	try:
		main()
	except RuntimeError as e:
		print(str(e))
		sys.exit(1)
