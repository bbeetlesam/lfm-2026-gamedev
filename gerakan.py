"""
Simulasi manual untuk mempelajari posisi, kecepatan, percepatan,
dan delta time.

Kontrol:
WASD / Tombol panah : memberikan percepatan pada objek
+ / -               : mengubah besar percepatan
SPACE               : jeda / lanjutkan simulasi
R                   : reset posisi dan kecepatan
C                   : hapus trail pergerakan
ESC                 : keluar
"""

import math
import sys

import pygame

pygame.init()

# Jendela diperbesar agar area simulasi dan informasi lebih leluasa.
WIDTH, HEIGHT = 1440, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kinematika Playground")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 20)
SMALL = pygame.font.SysFont("consolas", 16)
TITLE = pygame.font.SysFont("consolas", 30, bold=True)

BG = (19, 22, 29)
PANEL = (29, 34, 44)
GRID = (42, 49, 61)
WHITE = (235, 239, 245)
MUTED = (155, 166, 181)
CYAN = (80, 205, 220)
GREEN = (115, 220, 145)
ORANGE = (255, 183, 90)
YELLOW = (245, 220, 115)

# Area tempat simulasi ditampilkan.
VIEW = pygame.Rect(32, 135, WIDTH - 64, 610)
CENTER = VIEW.center
PIXELS_PER_UNIT = 1.0


# ---------------------------------------------------------------------------
# Variabel keadaan simulasi
# ---------------------------------------------------------------------------

# Satuan yang digunakan bersifat ilustratif: satuan dunia dan detik.
# Posisi menyimpan koordinat objek pada dunia simulasi.
position = [0.0, 0.0]

# Kecepatan menyimpan perubahan posisi per detik.
velocity = [0.0, 0.0]

# Percepatan menyimpan perubahan kecepatan per detik.
acceleration = [0.0, 0.0]

acceleration_rate = 520.0
paused = False

# History posisi digunakan untuk menggambar trail pergerakan objek.
trail = []
MAX_TRAIL = 700
radius = 21


def reset():
    """Mengembalikan posisi, kecepatan, percepatan, dan trail ke kondisi awal."""
    global position, velocity, acceleration, trail
    position = [0.0, 0.0]
    velocity = [0.0, 0.0]
    acceleration = [0.0, 0.0]
    trail = []


def draw_text(value, x, y, color=WHITE, font=FONT):
    """Menggambar teks pada layar."""
    screen.blit(font.render(str(value), True, color), (x, y))


def draw_arrow(start, end, color, width=4):
    """Menggambar panah dari titik awal menuju titik akhir."""
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy)

    # Arrow yang terlalu pendek tidak akan terlihat dengan jelas.
    if length < 3:
        return

    pygame.draw.line(screen, color, (int(sx), int(sy)), (int(ex), int(ey)), width)

    # Menghitung arah satuan untuk membentuk kepala panah.
    ux, uy = dx / length, dy / length
    head = min(17, length * 0.35)
    perp_x, perp_y = -uy, ux
    base_x, base_y = ex - ux * head, ey - uy * head
    half = head * 0.55

    pygame.draw.polygon(
        screen,
        color,
        [
            (int(ex), int(ey)),
            (int(base_x + perp_x * half), int(base_y + perp_y * half)),
            (int(base_x - perp_x * half), int(base_y - perp_y * half)),
        ],
    )


def draw_grid():
    """Menggambar kisi koordinat yang bergerak mengikuti kamera."""
    pygame.draw.rect(screen, (23, 27, 35), VIEW, border_radius=14)
    screen.set_clip(VIEW)

    spacing = 60
    offset_x = int(position[0] * PIXELS_PER_UNIT) % spacing
    offset_y = int(position[1] * PIXELS_PER_UNIT) % spacing

    for x in range(VIEW.left - spacing, VIEW.right + spacing, spacing):
        screen_x = x - offset_x
        pygame.draw.line(screen, GRID, (screen_x, VIEW.top), (screen_x, VIEW.bottom))

    for y in range(VIEW.top - spacing, VIEW.bottom + spacing, spacing):
        screen_y = y - offset_y
        pygame.draw.line(screen, GRID, (VIEW.left, screen_y), (VIEW.right, screen_y))

    # Menampilkan sumbu dunia jika posisinya masih berada di area simulasi.
    origin_x = CENTER[0] - position[0] * PIXELS_PER_UNIT
    origin_y = CENTER[1] - position[1] * PIXELS_PER_UNIT

    if VIEW.left <= origin_x <= VIEW.right:
        pygame.draw.line(
            screen,
            (95, 105, 122),
            (int(origin_x), VIEW.top),
            (int(origin_x), VIEW.bottom),
            2,
        )

    if VIEW.top <= origin_y <= VIEW.bottom:
        pygame.draw.line(
            screen,
            (95, 105, 122),
            (VIEW.left, int(origin_y)),
            (VIEW.right, int(origin_y)),
            2,
        )

    screen.set_clip(None)
    pygame.draw.rect(screen, (48, 56, 70), VIEW, 2, border_radius=14)


def draw_world():
    """Menggambar kisi, trail pergerakan, vektor, dan objek simulasi."""
    draw_grid()
    screen.set_clip(VIEW)

    # trail disimpan dalam koordinat dunia, lalu digambar relatif terhadap kamera.
    if len(trail) > 1:
        points = []

        for point in trail:
            screen_x = CENTER[0] + (point[0] - position[0]) * PIXELS_PER_UNIT
            screen_y = CENTER[1] + (point[1] - position[1]) * PIXELS_PER_UNIT

            if (
                VIEW.left - 10 <= screen_x <= VIEW.right + 10
                and VIEW.top - 10 <= screen_y <= VIEW.bottom + 10
            ):
                points.append((int(screen_x), int(screen_y)))

        if len(points) > 1:
            pygame.draw.lines(screen, (76, 117, 137), False, points, 3)

    # Kamera mengikuti objek sehingga objek selalu berada di tengah area simulasi.
    cx, cy = CENTER

    # Panjang panah diskalakan agar mudah dilihat, bukan ukuran fisik sebenarnya.
    panjang_vektor_kecepatan = 0.13
    panjang_vektor_percepatan = 0.035

    draw_arrow(
        (cx, cy),
        (
            cx + velocity[0] * panjang_vektor_kecepatan,
            cy + velocity[1] * panjang_vektor_kecepatan,
        ),
        CYAN,
    )

    draw_arrow(
        (cx, cy),
        (
            cx + acceleration[0] * panjang_vektor_percepatan,
            cy + acceleration[1] * panjang_vektor_percepatan,
        ),
        ORANGE,
    )

    # Menggambar objek utama dan penanda titik pusatnya.
    pygame.draw.circle(screen, (10, 12, 17), (cx + 3, cy + 4), radius + 3)
    pygame.draw.circle(screen, GREEN, (cx, cy), radius)
    pygame.draw.circle(screen, WHITE, (cx - 6, cy - 6), 5)

    # Garis kecil di sekitar objek membantu menunjukkan titik pusat.
    pygame.draw.line(screen, WHITE, (cx - 34, cy), (cx - 27, cy))
    pygame.draw.line(screen, WHITE, (cx + 27, cy), (cx + 34, cy))
    pygame.draw.line(screen, WHITE, (cx, cy - 34), (cx, cy - 27))
    pygame.draw.line(screen, WHITE, (cx, cy + 27), (cx, cy + 34))

    screen.set_clip(None)


def draw_hud(raw_dt, sim_dt, fps):
    """Menggambar judul, petunjuk kontrol, dan data simulasi."""
    draw_text("KINEMATIKA PLAYGROUND", 34, 20, WHITE, TITLE)
    draw_text(
        "Posisi  |  Kecepatan  |  Percepatan  |  Delta Time", 37, 65, MUTED, SMALL
    )

    status = "DIJEDA" if paused else "BERJALAN"
    status_color = ORANGE if paused else GREEN
    draw_text(
        f"{status}  |  FPS: {fps:5.1f}  |  Delta time: {raw_dt * 1000:6.2f} ms",
        940,
        38,
        status_color,
        SMALL,
    )

    # Petunjuk kontrol diletakkan di atas area simulasi.
    draw_text("WASD / PANAH: percepat objek", 36, 108, MUTED, SMALL)
    draw_text("+ / -: ubah percepatan", 390, 108, MUTED, SMALL)
    draw_text("SPACE: jeda", 700, 108, MUTED, SMALL)
    draw_text("R: reset   C: hapus trail   ESC: keluar", 900, 108, MUTED, SMALL)

    # Panel data dibagi menjadi empat kolom agar setiap besaran mudah dibaca.
    panel_rect = pygame.Rect(32, 765, WIDTH - 64, 112)
    pygame.draw.rect(screen, PANEL, panel_rect, border_radius=12)

    columns = (55, 390, 725, 1060)
    x1, x2, x3, x4 = columns

    draw_text("POSISI (satuan dunia)", x1, 780, GREEN, SMALL)
    draw_text(f"x: {position[0]:10.2f}", x1, 810)
    draw_text(f"y: {position[1]:10.2f}", x1, 840)

    draw_text("KECEPATAN (satuan/detik)", x2, 780, CYAN, SMALL)
    draw_text(f"vx: {velocity[0]:9.2f}", x2, 810)
    draw_text(f"vy: {velocity[1]:9.2f}", x2, 840)

    draw_text("PERCEPATAN (satuan/detik²)", x3, 780, ORANGE, SMALL)
    draw_text(f"ax: {acceleration[0]:9.2f}", x3, 810)
    draw_text(f"ay: {acceleration[1]:9.2f}", x3, 840)

    draw_text("SIMULASI", x4, 780, YELLOW, SMALL)
    draw_text(f"Delta time dipakai: {sim_dt * 1000:6.2f} ms", x4, 810, WHITE, SMALL)
    draw_text(f"Besar percepatan: {acceleration_rate:.0f}", x4, 840, WHITE, SMALL)

    # Legenda warna untuk kedua panah vektor.
    pygame.draw.line(
        screen,
        CYAN,
        (VIEW.left + 22, VIEW.bottom - 25),
        (VIEW.left + 55, VIEW.bottom - 25),
        4,
    )
    draw_text("Kecepatan", VIEW.left + 65, VIEW.bottom - 35, CYAN, SMALL)

    pygame.draw.line(
        screen,
        ORANGE,
        (VIEW.left + 205, VIEW.bottom - 25),
        (VIEW.left + 238, VIEW.bottom - 25),
        4,
    )
    draw_text("Percepatan", VIEW.left + 248, VIEW.bottom - 35, ORANGE, SMALL)


# ---------------------------------------------------------------------------
# Perulangan utama aplikasi
# ---------------------------------------------------------------------------

running = True

while running:
    # clock.tick() menghasilkan waktu dalam milidetik.
    # Dibagi 1000 agar delta time menggunakan satuan detik.
    raw_dt = clock.tick(120) / 1000.0

    # Membatasi delta time untuk mencegah objek meloncat terlalu jauh
    # ketika aplikasi sempat tersendat atau kehilangan fokus.
    dt = min(raw_dt, 0.05)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key == pygame.K_r:
                reset()

            elif event.key == pygame.K_c:
                trail.clear()

            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                acceleration_rate = min(1500.0, acceleration_rate + 40.0)

            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                acceleration_rate = max(40.0, acceleration_rate - 40.0)

    if not paused:
        keys = pygame.key.get_pressed()

        # Input menghasilkan arah percepatan pada sumbu X dan Y.
        # Pada koordinat layar, nilai Y positif mengarah ke bawah.
        input_x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        input_y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )

        # Normalisasi menjaga besar percepatan diagonal tetap sama
        # dengan percepatan ketika bergerak lurus.
        panjang_input = math.hypot(input_x, input_y)

        if panjang_input > 0:
            input_x /= panjang_input
            input_y /= panjang_input

        acceleration[0] = input_x * acceleration_rate
        acceleration[1] = input_y * acceleration_rate

        # Integrasi semi-implicit Euler:
        # 1. Kecepatan baru = kecepatan lama + percepatan * delta time.
        # 2. Posisi baru = posisi lama + kecepatan baru * delta time.
        velocity[0] += acceleration[0] * dt
        velocity[1] += acceleration[1] * dt

        position[0] += velocity[0] * dt
        position[1] += velocity[1] * dt

        # Simpan posisi ketika objek bergerak agar trailnya dapat digambar.
        if input_x != 0 or input_y != 0 or math.hypot(*velocity) > 1:
            trail.append(position.copy())

            if len(trail) > MAX_TRAIL:
                trail.pop(0)

    else:
        # Saat simulasi dijeda, tidak ada percepatan input yang diberikan.
        acceleration[0] = 0.0
        acceleration[1] = 0.0

    screen.fill(BG)
    draw_world()
    draw_hud(raw_dt, dt, clock.get_fps())
    pygame.display.flip()


pygame.quit()
sys.exit()
