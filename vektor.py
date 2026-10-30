"""
VECTOR PLAYGROUND
=================

Tujuan
------
Program ini membantu memahami vektor melalui contoh karakter yang bergerak
menuju target menggunakan Pygame.

Konsep yang divisualisasikan:
1. Posisi (position): lokasi karakter dan target pada bidang 2D.
2. Displacement vector: selisih posisi target dengan posisi karakter.
3. Magnitude: panjang vektor displacement.
4. Unit vector: vektor arah dengan panjang 1.
5. Velocity vector: unit vector dikalikan speed yang diinginkan.
6. Komponen X dan Y: kontribusi horizontal dan vertikal dari sebuah vektor.

Alur perhitungan
----------------
Misalkan posisi karakter P = (Px, Py) dan posisi target T = (Tx, Ty).

    displacement = T - P
                 = (Tx - Px, Ty - Py)

Magnitude displacement:

    distance = sqrt(dx * dx + dy * dy)

Unit vector:

    direction = displacement / distance

Velocity vector dengan speed tertentu:

    velocity = direction * speed

Posisi karakter kemudian diperbarui setiap frame:

    position = position + velocity * dt

Catatan koordinat layar
-----------------------
Pada koordinat layar Pygame, X positif mengarah ke kanan dan Y positif
mengarah ke bawah. Karena itu, displacement dengan komponen Y positif
menunjuk ke bawah layar.

Kontrol
-------
Klik kiri pada area simulasi : pindahkan target
SPACE                        : jeda / lanjutkan gerakan karakter
R                            : reset posisi karakter dan target
+ / -                        : naikkan / turunkan speed
ESC                          : keluar

Pygame hanya digunakan untuk input, waktu, dan rendering. Perhitungan vektor,
normalisasi, magnitude, velocity, dan perpindahan ditulis manual tanpa
physics engine atau pygame.math.Vector2.
"""

import math
import sys

import pygame

# ===========================================================================
# 1. INISIALISASI DAN KONFIGURASI
# ===========================================================================

pygame.init()

WIDTH, HEIGHT = 1280, 850
FPS = 120

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vector Playground")
CLOCK = pygame.time.Clock()

TITLE_FONT = pygame.font.SysFont("dejavusans", 28, bold=True)
FONT = pygame.font.SysFont("dejavusans", 17)
SMALL_FONT = pygame.font.SysFont("dejavusans", 14)
MONO_FONT = pygame.font.SysFont("dejavusansmono", 15)
VALUE_FONT = pygame.font.SysFont("dejavusans", 21, bold=True)

BG = (19, 22, 29)
WORLD_BG = (24, 29, 38)
GRID = (38, 45, 57)
PANEL = (29, 35, 46)
PANEL_BORDER = (62, 73, 91)
WHITE = (238, 241, 247)
MUTED = (157, 169, 188)
CYAN = (95, 211, 226)  # displacement vector
ORANGE = (255, 174, 91)  # komponen vektor
GREEN = (120, 220, 150)  # unit vector
PURPLE = (183, 145, 255)  # velocity vector
BLUE = (105, 176, 255)  # karakter
BLUE_LIGHT = (190, 220, 255)
YELLOW = (245, 218, 112)

WORLD = pygame.Rect(32, 145, 850, 655)

# Posisi awal karakter dan target.
SPAWN_PLAYER = (210.0, 470.0)
SPAWN_TARGET = (650.0, 300.0)

PLAYER_RADIUS = 17
TARGET_RADIUS = 11

# Speed adalah magnitude velocity yang diinginkan, dalam pixel/detik.
MOVE_SPEED = 220.0
MIN_SPEED = 40.0
MAX_SPEED = 600.0
SPEED_STEP = 20.0

player_x, player_y = SPAWN_PLAYER
target_x, target_y = SPAWN_TARGET
is_moving = True


# ===========================================================================
# 2. FUNGSI VEKTOR MANUAL
# ===========================================================================


def vector_subtract(vector_a, vector_b):
    """
    Mengurangi dua vektor secara komponen.

    Contoh:
        (10, 8) - (3, 2) = (7, 6)

    Dalam simulasi ini, target - posisi karakter menghasilkan displacement
    vector yang menunjuk dari karakter menuju target.
    """
    return (
        vector_a[0] - vector_b[0],
        vector_a[1] - vector_b[1],
    )


def vector_magnitude(vector):
    """
    Menghitung magnitude atau panjang sebuah vektor.

    Rumus Pythagoras:
        |v| = sqrt(vx² + vy²)
    """
    return math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])


def vector_normalize(vector):
    """
    Mengubah vektor menjadi unit vector tanpa mengubah arahnya.

    Unit vector memiliki magnitude 1. Jika magnitude vektor awal adalah
    nol, normalisasi tidak dilakukan karena pembagian dengan nol tidak valid.
    """
    magnitude = vector_magnitude(vector)

    if magnitude == 0:
        return (0.0, 0.0)

    return (
        vector[0] / magnitude,
        vector[1] / magnitude,
    )


def vector_scale(vector, scalar):
    """Mengalikan setiap komponen vektor dengan sebuah scalar."""
    return (
        vector[0] * scalar,
        vector[1] * scalar,
    )


def vector_add(vector_a, vector_b):
    """Menjumlahkan dua vektor secara komponen."""
    return (
        vector_a[0] + vector_b[0],
        vector_a[1] + vector_b[1],
    )


# ===========================================================================
# 3. FUNGSI GAMBAR
# ===========================================================================


def draw_text(surface, text, font, color, x, y):
    """Menggambar teks dari koordinat kiri-atas."""
    image = font.render(text, True, color)
    surface.blit(image, (x, y))


def draw_grid(surface, rect, spacing=40):
    """Menggambar grid koordinat pada area simulasi."""
    for x in range(rect.left, rect.right, spacing):
        pygame.draw.line(surface, GRID, (x, rect.top), (x, rect.bottom), 1)
    for y in range(rect.top, rect.bottom, spacing):
        pygame.draw.line(surface, GRID, (rect.left, y), (rect.right, y), 1)


def draw_arrow(surface, start, end, color, width=3, head_size=11):
    """
    Menggambar garis berujung panah.

    Arah panah ditentukan dari start menuju end. Perhitungan arah panah
    menggunakan normalisasi vektor secara manual.
    """
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length < 1:
        return

    direction = (dx / length, dy / length)
    perpendicular = (-direction[1], direction[0])

    base = (
        end[0] - direction[0] * head_size,
        end[1] - direction[1] * head_size,
    )

    left = (
        base[0] + perpendicular[0] * head_size * 0.55,
        base[1] + perpendicular[1] * head_size * 0.55,
    )
    right = (
        base[0] - perpendicular[0] * head_size * 0.55,
        base[1] - perpendicular[1] * head_size * 0.55,
    )

    pygame.draw.line(surface, color, start, end, width)
    pygame.draw.polygon(surface, color, [end, left, right])


def draw_dashed_line(surface, color, start, end, dash_length=8, gap_length=6):
    """Menggambar garis putus-putus untuk menunjukkan komponen X dan Y."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length == 0:
        return

    direction = (dx / length, dy / length)
    distance = 0.0

    while distance < length:
        segment_end = min(distance + dash_length, length)

        p1 = (
            start[0] + direction[0] * distance,
            start[1] + direction[1] * distance,
        )
        p2 = (
            start[0] + direction[0] * segment_end,
            start[1] + direction[1] * segment_end,
        )

        pygame.draw.line(surface, color, p1, p2, 2)
        distance += dash_length + gap_length


def reset_simulation():
    """Mengembalikan karakter dan target ke posisi awal."""
    global player_x, player_y, target_x, target_y, is_moving

    player_x, player_y = SPAWN_PLAYER
    target_x, target_y = SPAWN_TARGET
    is_moving = True


# ===========================================================================
# 4. MAIN LOOP
# ===========================================================================

running = True

while running:
    # Delta time membuat perpindahan berbasis waktu, bukan jumlah frame.
    raw_dt = CLOCK.tick(FPS) / 1000.0
    dt = min(raw_dt, 0.05)

    # -----------------------------------------------------------------------
    # A. INPUT DAN EVENT
    # -----------------------------------------------------------------------

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                is_moving = not is_moving

            elif event.key == pygame.K_r:
                reset_simulation()

            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                MOVE_SPEED = min(MAX_SPEED, MOVE_SPEED + SPEED_STEP)

            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                MOVE_SPEED = max(MIN_SPEED, MOVE_SPEED - SPEED_STEP)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos

            # Target hanya dapat dipindahkan di dalam area simulasi.
            if WORLD.collidepoint(mouse_x, mouse_y):
                target_x = float(mouse_x)
                target_y = float(mouse_y)

    # -----------------------------------------------------------------------
    # B. HITUNG DISPLACEMENT VECTOR
    # -----------------------------------------------------------------------
    # Posisi karakter P = (player_x, player_y)
    # Posisi target   T = (target_x, target_y)
    #
    # displacement = T - P
    #
    # Hasilnya adalah vektor yang menunjuk dari karakter menuju target.
    player_position = (player_x, player_y)
    target_position = (target_x, target_y)

    displacement = vector_subtract(
        target_position,
        player_position,
    )

    distance = vector_magnitude(displacement)

    # -----------------------------------------------------------------------
    # C. NORMALISASI: DISPLACEMENT -> UNIT VECTOR
    # -----------------------------------------------------------------------
    # Displacement memiliki panjang yang sama dengan jarak karakter-target.
    # Kita normalisasi agar hanya memperoleh informasi arah.
    #
    # direction = displacement / |displacement|
    #
    # Jika karakter sudah sangat dekat dengan target, hindari pembagian
    # dengan nol dan hentikan gerakan.
    if distance > 1.0:
        direction = vector_normalize(displacement)
    else:
        direction = (0.0, 0.0)

    # -----------------------------------------------------------------------
    # D. UNIT VECTOR -> VELOCITY VECTOR
    # -----------------------------------------------------------------------
    # Unit vector memiliki magnitude 1. Dengan mengalikannya dengan speed,
    # kita memperoleh velocity dengan magnitude yang kita tentukan.
    #
    # velocity = direction * MOVE_SPEED
    #
    # Karena direction sudah dinormalisasi, karakter bergerak dengan speed
    # yang sama walaupun target berada pada jarak atau sudut berbeda.
    velocity = vector_scale(direction, MOVE_SPEED)

    # -----------------------------------------------------------------------
    # E. PERBARUI POSISI
    # -----------------------------------------------------------------------
    # position = position + velocity * dt
    #
    # Gerakan dilakukan hanya jika simulasi tidak sedang dijeda dan karakter
    # belum mencapai target.
    if is_moving and distance > 1.0:
        displacement_this_frame = vector_scale(velocity, dt)
        next_position = vector_add(
            player_position,
            displacement_this_frame,
        )

        player_x, player_y = next_position

        # Cegah karakter melewati target akibat langkah frame terakhir.
        # Jika jarak tersisa lebih kecil dari perpindahan satu frame, snap
        # langsung ke target.
        if vector_magnitude(
            vector_subtract(target_position, next_position)
        ) <= vector_magnitude(displacement_this_frame):
            player_x, player_y = target_position

    # Hitung ulang data setelah posisi karakter diperbarui agar UI dan
    # visualisasi menampilkan nilai yang sesuai dengan posisi terkini.
    player_position = (player_x, player_y)
    displacement = vector_subtract(target_position, player_position)
    distance = vector_magnitude(displacement)
    direction = vector_normalize(displacement)
    velocity = vector_scale(direction, MOVE_SPEED) if distance > 1.0 else (0.0, 0.0)

    # -----------------------------------------------------------------------
    # F. RENDERING: AREA SIMULASI
    # -----------------------------------------------------------------------

    SCREEN.fill(BG)

    draw_text(SCREEN, "VECTOR PLAYGROUND", TITLE_FONT, WHITE, 32, 25)
    draw_text(
        SCREEN,
        "Arah, magnitude, displacement, unit vector, dan velocity",
        FONT,
        MUTED,
        34,
        67,
    )

    pygame.draw.rect(SCREEN, WORLD_BG, WORLD, border_radius=10)
    draw_grid(SCREEN, WORLD)
    pygame.draw.rect(SCREEN, PANEL_BORDER, WORLD, 2, border_radius=10)

    # Posisi target dan karakter.
    target_screen = (round(target_x), round(target_y))
    player_screen = (round(player_x), round(player_y))

    # Garis bantu komponen: displacement = (dx, dy).
    # Proyeksi ini menunjukkan kontribusi X dan Y secara terpisah.
    corner = (target_x, player_y)
    draw_dashed_line(SCREEN, ORANGE, player_screen, corner)
    draw_dashed_line(SCREEN, ORANGE, corner, target_screen)

    # Displacement vector dari karakter menuju target.
    if distance > 1.0:
        draw_arrow(
            SCREEN,
            player_screen,
            target_screen,
            CYAN,
            width=4,
            head_size=13,
        )

    # Unit vector divisualisasikan sebagai panah pendek dari karakter.
    # Panjang visual sengaja diperbesar agar mudah dilihat; nilai matematis
    # unit vector tetap memiliki magnitude 1.
    unit_visual_length = 75
    unit_end = (
        player_x + direction[0] * unit_visual_length,
        player_y + direction[1] * unit_visual_length,
    )
    if distance > 1.0:
        draw_arrow(
            SCREEN,
            player_screen,
            (round(unit_end[0]), round(unit_end[1])),
            GREEN,
            width=3,
            head_size=10,
        )

    # Velocity vector ditampilkan sebagai panah ungu dengan skala visual.
    # Skala gambar bukan satuan fisik; nilai velocity sebenarnya ditampilkan
    # di panel informasi.
    velocity_visual_scale = 0.22
    velocity_end = (
        player_x + velocity[0] * velocity_visual_scale,
        player_y + velocity[1] * velocity_visual_scale,
    )
    if distance > 1.0:
        draw_arrow(
            SCREEN,
            player_screen,
            (round(velocity_end[0]), round(velocity_end[1])),
            PURPLE,
            width=3,
            head_size=10,
        )

    # Target.
    pygame.draw.circle(SCREEN, (35, 70, 58), target_screen, TARGET_RADIUS + 7)
    pygame.draw.circle(SCREEN, GREEN, target_screen, TARGET_RADIUS)
    pygame.draw.circle(SCREEN, WHITE, target_screen, TARGET_RADIUS, 2)
    draw_text(
        SCREEN,
        "TARGET",
        SMALL_FONT,
        GREEN,
        target_x + 15,
        target_y - 9,
    )

    # Karakter.
    pygame.draw.circle(SCREEN, BLUE, player_screen, PLAYER_RADIUS)
    pygame.draw.circle(SCREEN, BLUE_LIGHT, player_screen, PLAYER_RADIUS, 2)
    pygame.draw.circle(SCREEN, (20, 31, 48), player_screen, 4)

    # Label komponen pada garis proyeksi.
    dx = displacement[0]
    dy = displacement[1]
    if distance > 1.0:
        draw_text(
            SCREEN,
            f"dx = {dx:.0f}",
            SMALL_FONT,
            ORANGE,
            (player_x + target_x) / 2 - 20,
            player_y + 10,
        )
        draw_text(
            SCREEN,
            f"dy = {dy:.0f}",
            SMALL_FONT,
            ORANGE,
            target_x + 8,
            (player_y + target_y) / 2 - 8,
        )

    # -----------------------------------------------------------------------
    # G. PANEL INFORMASI VEKTOR
    # -----------------------------------------------------------------------

    info = pygame.Rect(906, 145, 342, 655)
    pygame.draw.rect(SCREEN, PANEL, info, border_radius=10)
    pygame.draw.rect(SCREEN, PANEL_BORDER, info, 1, border_radius=10)

    x0 = info.x + 18
    y = info.y + 18

    draw_text(SCREEN, "DATA VEKTOR", TITLE_FONT, WHITE, x0, y)
    y += 48

    draw_text(SCREEN, "DISPLACEMENT VECTOR", SMALL_FONT, CYAN, x0, y)
    y += 24
    draw_text(
        SCREEN,
        f"({dx:7.1f}, {dy:7.1f})",
        MONO_FONT,
        WHITE,
        x0,
        y,
    )
    y += 25
    draw_text(
        SCREEN,
        f"Magnitude: {distance:.2f} px",
        FONT,
        CYAN,
        x0,
        y,
    )

    y += 48
    pygame.draw.line(SCREEN, PANEL_BORDER, (x0, y), (info.right - 18, y), 1)
    y += 16

    draw_text(SCREEN, "KOMPONEN VEKTOR", SMALL_FONT, ORANGE, x0, y)
    y += 25
    draw_text(
        SCREEN,
        f"dx (horizontal): {dx:8.2f}",
        MONO_FONT,
        WHITE,
        x0,
        y,
    )
    y += 24
    draw_text(
        SCREEN,
        f"dy (vertikal):   {dy:8.2f}",
        MONO_FONT,
        WHITE,
        x0,
        y,
    )

    y += 42
    pygame.draw.line(SCREEN, PANEL_BORDER, (x0, y), (info.right - 18, y), 1)
    y += 16

    draw_text(SCREEN, "UNIT VECTOR", SMALL_FONT, GREEN, x0, y)
    y += 25
    draw_text(
        SCREEN,
        f"({direction[0]: .3f}, {direction[1]: .3f})",
        MONO_FONT,
        WHITE,
        x0,
        y,
    )
    y += 24
    draw_text(
        SCREEN,
        f"Magnitude: {vector_magnitude(direction):.3f}",
        FONT,
        GREEN,
        x0,
        y,
    )

    y += 42
    pygame.draw.line(SCREEN, PANEL_BORDER, (x0, y), (info.right - 18, y), 1)
    y += 16

    draw_text(SCREEN, "VELOCITY VECTOR", SMALL_FONT, PURPLE, x0, y)
    y += 25
    draw_text(
        SCREEN,
        f"({velocity[0]: .1f}, {velocity[1]: .1f})",
        MONO_FONT,
        WHITE,
        x0,
        y,
    )
    y += 24
    draw_text(
        SCREEN,
        f"Speed: {vector_magnitude(velocity):.1f} px/s",
        FONT,
        PURPLE,
        x0,
        y,
    )

    y += 42
    pygame.draw.line(SCREEN, PANEL_BORDER, (x0, y), (info.right - 18, y), 1)
    y += 16

    draw_text(SCREEN, "KONTROL", SMALL_FONT, MUTED, x0, y)
    y += 23
    draw_text(SCREEN, "Klik area: pindahkan target", SMALL_FONT, WHITE, x0, y)
    y += 21
    draw_text(SCREEN, "SPACE: jeda / lanjut", SMALL_FONT, WHITE, x0, y)
    y += 21
    draw_text(SCREEN, "R: reset posisi", SMALL_FONT, WHITE, x0, y)
    y += 21
    draw_text(SCREEN, "+ / -: ubah speed", SMALL_FONT, WHITE, x0, y)
    y += 21
    draw_text(SCREEN, "ESC: keluar", SMALL_FONT, WHITE, x0, y)

    # Status gerakan dan speed aktif di bagian bawah panel.
    status = (
        "BERGERAK"
        if is_moving and distance > 1.0
        else ("DIJEDA" if not is_moving else "TARGET TERCAPAI")
    )
    status_color = GREEN if status == "BERGERAK" else ORANGE

    status_rect = pygame.Rect(x0, info.bottom - 55, info.width - 36, 36)
    pygame.draw.rect(SCREEN, (39, 48, 60), status_rect, border_radius=7)
    draw_text(
        SCREEN,
        f"{status}  |  SPEED {MOVE_SPEED:.0f} px/s",
        SMALL_FONT,
        status_color,
        status_rect.x + 10,
        status_rect.y + 10,
    )

    # Legenda warna.
    legend_y = 111
    legend_items = [
        (CYAN, "Displacement"),
        (GREEN, "Unit vector"),
        (PURPLE, "Velocity"),
        (ORANGE, "Komponen X/Y"),
    ]

    legend_x = 34
    for color, label in legend_items:
        pygame.draw.circle(SCREEN, color, (legend_x + 5, legend_y + 7), 5)
        draw_text(
            SCREEN,
            label,
            SMALL_FONT,
            MUTED,
            legend_x + 16,
            legend_y,
        )
        legend_x += 175

    pygame.display.flip()

pygame.quit()
sys.exit()
