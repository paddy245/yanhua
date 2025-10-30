import os
import time
import math
import random
from dataclasses import dataclass

try:
	import pygame
except Exception:
	pygame = None

# 分辨率与帧率（与手机竖屏一致）
FPS = 30
DURATION_SEC = 8.0
# 深夜天空 + 轻微蓝调
BACKGROUND = (4, 6, 10)

GRAVITY = 0.12
AIR_DRAG = 0.992
ROCKET_MIN_SPEED = 18
ROCKET_MAX_SPEED = 24
# 更密的环形菊花
PARTICLES_PER_BURST = 180
# 速度更均匀，形成干净圆环
PARTICLE_SPEED_MIN = 4.5
PARTICLE_SPEED_MAX = 5.2
PARTICLE_LIFE_MIN = 55
PARTICLE_LIFE_MAX = 82
# 加强拖尾（更低的清除强度）
BLUR_ALPHA = 22

SCHEDULE = [0.5, 1.6, 2.7, 3.8, 4.9, 6.0]


def ensure_pygame():
	if pygame is None:
		raise SystemExit("缺少 pygame，请执行: python3 -m pip install --user pygame")


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

@dataclass
class Particle:
	x: float
	y: float
	vx: float
	vy: float
	life: int
	color: tuple
	size: float

class Firework:
	def __init__(self, x, y, target_y):
		self.x = x
		self.y = y
		self.target_y = target_y
		self.vx = random.uniform(-1.2, 1.2)
		self.vy = -random.uniform(ROCKET_MIN_SPEED, ROCKET_MAX_SPEED)
		self.exploded = False
		self.particles = []
		# 偏金色/橙金调（更像视频一风格）
		base_hue = 0.12  # 约等于金色
		self.palette = [
			hsv_to_rgb((base_hue + random.uniform(-0.02, 0.02)) % 1.0, 0.8 + random.uniform(0.1, 0.2), 1.0)
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
		# 环形均匀角度分布，速度一致，产生干净的菊花环
		for i in range(PARTICLES_PER_BURST):
			ang = (2 * math.pi) * (i / PARTICLES_PER_BURST) + random.uniform(-0.01, 0.01)
			spd = random.uniform(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX)
			vx = math.cos(ang) * spd
			vy = math.sin(ang) * spd
			life = random.randint(PARTICLE_LIFE_MIN, PARTICLE_LIFE_MAX)
			col = random.choice(self.palette)
			size = random.uniform(1.6, 2.4)
			self.particles.append(Particle(self.x, self.y, vx, vy, life, col, size))

	def is_done(self):
		return self.exploded and len(self.particles) == 0

	def draw(self, surface):
		if not self.exploded:
			pygame.draw.circle(surface, (255, 240, 200), (int(self.x), int(self.y)), 3)
		else:
			for p in self.particles:
				# 闪烁衰减（更亮的金色闪烁）
				flicker = 0.85 + 0.15 * random.random()
				a = max(0.0, min(1.0, p.life / PARTICLE_LIFE_MAX)) * flicker
				r, g, b = p.color
				col = (int(r * a), int(g * a), int(b * a))
				# 核心亮点
				pygame.draw.circle(surface, col, (int(p.x), int(p.y)), max(1, int(p.size)))
				# 朦胧光晕（模拟 bloom）
				if random.random() < 0.6:
					glow = (min(255, int(col[0]*0.6)), min(255, int(col[1]*0.6)), min(255, int(col[2]*0.6)))
					pygame.draw.circle(surface, glow, (int(p.x), int(p.y)), max(2, int(p.size*2)))


def run_fullscreen():
	ensure_pygame()
	# 全屏无边框、隐藏光标
	os.environ["SDL_VIDEO_CENTERED"] = "1"
	pygame.init()
	info = pygame.display.Info()
	width, height = info.current_w, info.current_h
	flags = pygame.FULLSCREEN | pygame.NOFRAME
	screen = pygame.display.set_mode((width, height), flags)
	pygame.mouse.set_visible(False)
	clock = pygame.time.Clock()

	trail = pygame.Surface((width, height), flags=pygame.SRCALPHA)

	fireworks = []
	start_time = time.time()
	next_schedule_index = 0

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False

		elapsed = time.time() - start_time
		while next_schedule_index < len(SCHEDULE) and elapsed >= SCHEDULE[next_schedule_index]:
			x = random.uniform(width * 0.2, width * 0.8)
			target_y = random.uniform(height * 0.25, height * 0.45)
			fireworks.append(Firework(x=x, y=height - 10, target_y=target_y))
			next_schedule_index += 1

		screen.fill(BACKGROUND)
		trail.fill((0, 0, 0, BLUR_ALPHA))
		screen.blit(trail, (0, 0))

		alive = []
		for fw in fireworks:
			fw.update()
			fw.draw(screen)
			if not fw.is_done():
				alive.append(fw)
		fireworks = alive

		trail.blit(screen, (0, 0))
		pygame.display.flip()
		clock.tick(FPS)

		if elapsed >= DURATION_SEC:
			break

	pygame.mouse.set_visible(True)
	pygame.quit()


if __name__ == "__main__":
	run_fullscreen()
