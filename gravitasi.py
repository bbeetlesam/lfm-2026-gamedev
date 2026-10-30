"""
GRAVITY PLAYGROUND
==================

Tujuan
------
Program ini memperlihatkan bagaimana gravitasi memengaruhi gerak vertikal
sebuah karakter dalam platformer sederhana. Fokus utama simulasi adalah:

1. Gravitasi merupakan percepatan konstan yang arahnya ke bawah.
2. Percepatan gravitasi mengubah velocity vertikal setiap frame.
3. Velocity vertikal mengubah posisi vertikal karakter.
4. Ketika karakter menyentuh lantai, collision response menghentikan gerak
   jatuhnya. Saat jump, karakter diberi velocity awal ke atas dan gravitasi
   langsung kembali memengaruhi gerakannya.

Persamaan yang digunakan
------------------------
    a_y = g
    v_y = v_y + a_y * dt
    y   = y + v_y * dt

Dalam koordinat layar Pygame, sumbu Y positif mengarah ke bawah. Karena itu,
nilai GRAVITY positif membuat karakter mengalami percepatan ke bawah.
Saat jump, velocity_y diberi nilai negatif agar karakter bergerak ke atas.

Collision dengan floor
----------------------
Floor merupakan sebuah rectangle horizontal panjang. Karakter dan floor
direpresentasikan sebagai AABB (Axis-Aligned Bounding Box).

Untuk mendarat, kita tidak hanya memeriksa apakah kedua rectangle sedang
overlap. Kita memeriksa apakah bagian bawah karakter MELINTASI permukaan atas
floor pada frame ini:

    previous_bottom <= floor.top
    current_bottom  >= floor.top
    velocity_y      >= 0

Syarat tersebut penting. Ketika karakter tepat menyentuh lantai, kedua AABB
hanya bersinggungan dan tidak memiliki overlap area. Fungsi colliderect()
menganggap kondisi bersinggungan seperti itu bukan collision. Jika status
grounded hanya bergantung pada overlap, statusnya dapat flicker.

Setelah crossing terdeteksi, posisi karakter di-snap ke atas floor dan
velocity_y diatur menjadi nol. Ini adalah collision response. Pada frame
berikutnya gravitasi kembali diterapkan, tetapi crossing check akan menjaga
karakter tetap berada di permukaan lantai.

Kontrol
-------
A / D atau panah kiri / kanan : bergerak horizontal
SPACE / W / panah atas        : jump
R                             : reset ke posisi awal
ESC                           : keluar

Tidak ada physics engine atau modul physics bawaan. Integrasi gerak,
gravitasi, pemeriksaan AABB, dan collision response ditulis manual.
"""

import sys

import pygame

# ===========================================================================
# 1. INISIALISASI DAN KONFIGURASI VISUAL
# ===========================================================================

pygame.init()

WIDTH, HEIGHT = 1280, 800
FPS = 120

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Playground")
CLOCK = pygame.time.Clock()

TITLE_FONT = pygame.font.SysFont("dejavusans", 28, bold=True)
FONT = pygame.font.SysFont("dejavusans", 17)
SMALL_FONT = pygame.font.SysFont("dejavusans", 14)
VALUE_FONT = pygame.font.SysFont("dejavusans", 23, bold=True)

BG = (19, 22, 29)
WORLD_BG = (24, 29, 38)
GRID = (37, 44, 56)
PANEL = (29, 35, 46)
PANEL_BORDER = (62, 73, 91)
WHITE = (238, 241, 247)
MUTED = (157, 169, 188)
CYAN = (95, 211, 226)
ORANGE = (255, 174, 91)
ORANGE_DARK = (92, 58, 31)
GREEN = (120, 220, 150)
BLUE = (105, 176, 255)
BLUE_LIGHT = (190, 220, 255)
FLOOR_COLOR = (79, 91, 110)

WORLD = pygame.Rect(32, 145, WIDTH - 64, 545)


# ===========================================================================
# 2. OBJEK DAN PARAMETER SIMULASI
# ===========================================================================

PLAYER_WIDTH = 48
PLAYER_HEIGHT = 64

# Posisi awal karakter, disimpan sebagai float agar perhitungan physics
# tidak kehilangan presisi akibat pembulatan koordinat pixel.
SPAWN_X = 150.0
SPAWN_Y = 250.0

# Floor adalah satu AABB panjang. Bagian atasnya merupakan permukaan tempat
# karakter mendarat.
FLOOR = pygame.Rect(WORLD.left, 625, WORLD.width, 44)

# Parameter gerakan horizontal dan jump.
MOVE_SPEED = 330.0  # pixel/detik
JUMP_SPEED = 650.0  # pixel/detik; negatif berarti ke atas

# GRAVITY adalah percepatan, bukan kecepatan jatuh.
# Satuannya pixel/detik². Nilai positif berarti percepatan ke bawah
# karena koordinat layar Pygame memiliki sumbu Y positif ke bawah.
GRAVITY = 1500.0

# Batas ini mencegah velocity jatuh terus membesar tanpa batas.
MAX_FALL_SPEED = 1100.0

player_x = SPAWN_X
player_y = SPAWN_Y
velocity_x = 0.0
velocity_y = 0.0

# is_grounded adalah status hasil pemeriksaan kontak dengan floor pada
# update physics sebelumnya. Status ini dipakai untuk mengizinkan jump.
is_grounded = False

# Mencegah jump dipicu berulang kali selama tombol ditahan.
jump_was_pressed = False


# ===========================================================================
# 3. FUNGSI BANTUAN
# ===========================================================================


def draw_text(surface, text, font, color, x, y):
    """Menggambar teks dengan titik koordinat kiri-atas."""
    image = font.render(text, True, color)
    surface.blit(image, (x, y))


def draw_grid(surface, rect, spacing=40):
    """Menggambar grid sebagai referensi visual pergerakan karakter."""
    for x in range(rect.left, rect.right, spacing):
        pygame.draw.line(surface, GRID, (x, rect.top), (x, rect.bottom), 1)

    for y in range(rect.top, rect.bottom, spacing):
        pygame.draw.line(surface, GRID, (rect.left, y), (rect.right, y), 1)


def get_player_rect():
    """
    Membuat AABB karakter untuk rendering dan pemeriksaan collision.

    Posisi physics tetap berupa float. Pembulatan hanya dilakukan ketika
    mengubahnya menjadi pygame.Rect untuk kebutuhan geometri pixel.
    """
    return pygame.Rect(
        round(player_x),
        round(player_y),
        PLAYER_WIDTH,
        PLAYER_HEIGHT,
    )


def horizontal_overlap(player_left, player_right, floor_rect):
    """
    Memeriksa overlap pada sumbu X.

    Untuk mendarat di floor, karakter harus memiliki irisan horizontal
    dengan floor. Tidak perlu ada overlap vertikal terlebih dahulu karena
    kita akan mendeteksi apakah karakter melintasi permukaan atas floor.
    """
    return player_left < floor_rect.right and player_right > floor_rect.left


def reset_simulation():
    """Mengembalikan posisi, velocity, dan status karakter ke kondisi awal."""
    global player_x, player_y, velocity_x, velocity_y
    global is_grounded, jump_was_pressed

    player_x = SPAWN_X
    player_y = SPAWN_Y
    velocity_x = 0.0
    velocity_y = 0.0
    is_grounded = False
    jump_was_pressed = False


# ===========================================================================
# 4. COLLISION DETECTION DAN RESPONSE
# ===========================================================================


def resolve_floor_collision(previous_bottom, current_bottom):
    """
    Mendeteksi karakter yang sedang mendarat pada floor dan menyelesaikan
    collision response.

    Mengapa tidak cukup memakai pygame.Rect.colliderect()?
    ------------------------------------------------------
    colliderect() hanya bernilai True jika dua rectangle memiliki area
    overlap. Saat karakter tepat berdiri di atas floor, bottom karakter
    sama dengan top floor. Keduanya hanya bersinggungan, sehingga
    colliderect() bernilai False.

    Karena itu, untuk platform satu arah (karakter mendarat dari atas), kita
    memakai metode crossing test:
    - sebelumnya kaki karakter belum melewati permukaan floor;
    - sekarang kaki karakter sudah mencapai/melewati permukaan floor;
    - karakter sedang bergerak ke bawah atau diam secara vertikal;
    - karakter memiliki overlap horizontal dengan floor.

    Jika semua syarat terpenuhi, karakter di-snap ke permukaan floor.
    """
    global player_y, velocity_y, is_grounded

    player_left = player_x
    player_right = player_x + PLAYER_WIDTH

    crossed_floor_top = previous_bottom <= FLOOR.top and current_bottom >= FLOOR.top

    is_over_floor = horizontal_overlap(
        player_left,
        player_right,
        FLOOR,
    )

    is_falling_or_landing = velocity_y >= 0

    if crossed_floor_top and is_over_floor and is_falling_or_landing:
        # Koreksi posisi agar kaki karakter tepat sejajar dengan permukaan.
        player_y = float(FLOOR.top - PLAYER_HEIGHT)

        # Hentikan gerak vertikal. Gravitasi akan diterapkan lagi pada
        # frame berikutnya, lalu crossing test menjaga karakter tetap di
        # permukaan floor tanpa membuat status grounded berkedip.
        velocity_y = 0.0
        is_grounded = True
        return

    is_grounded = False


# ===========================================================================
# 5. MAIN LOOP
# ===========================================================================

running = True

while running:
    # -----------------------------------------------------------------------
    # A. Delta time
    # -----------------------------------------------------------------------
    # dt adalah waktu yang berlalu sejak frame sebelumnya, dalam detik.
    # Perkalian velocity dan acceleration dengan dt membuat simulasi berbasis
    # waktu, bukan sekadar jumlah frame.
    #
    # dt dibatasi agar jeda frame yang sangat panjang tidak menghasilkan
    # perpindahan posisi yang ekstrem.
    raw_dt = CLOCK.tick(FPS) / 1000.0
    dt = min(raw_dt, 0.05)

    # -----------------------------------------------------------------------
    # B. Input
    # -----------------------------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                reset_simulation()

    keys = pygame.key.get_pressed()

    move_direction = 0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        move_direction -= 1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        move_direction += 1

    # Gerakan horizontal dibuat langsung dari input.
    velocity_x = move_direction * MOVE_SPEED

    # -----------------------------------------------------------------------
    # C. Jump
    # -----------------------------------------------------------------------
    # Jump memberikan initial velocity negatif pada sumbu Y. Gravitasi tidak
    # dimatikan ketika karakter naik. Justru gravitasi yang terus mengurangi
    # kecepatan naik sampai karakter mencapai puncak lompatan, lalu membuat
    # karakter jatuh kembali.
    jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]

    if jump_pressed and not jump_was_pressed and is_grounded:
        velocity_y = -JUMP_SPEED
        is_grounded = False

    jump_was_pressed = jump_pressed

    # -----------------------------------------------------------------------
    # D. Simpan posisi kaki sebelum physics update
    # -----------------------------------------------------------------------
    # Nilai ini diperlukan untuk mengetahui apakah karakter MELINTASI
    # permukaan floor selama frame berjalan. Tanpa posisi sebelumnya, kita
    # sulit membedakan karakter yang baru mendarat dari karakter yang sudah
    # berada di bawah permukaan floor.
    previous_bottom = player_y + PLAYER_HEIGHT

    # -----------------------------------------------------------------------
    # E. Terapkan gravitasi: acceleration -> velocity
    # -----------------------------------------------------------------------
    # Gravitasi adalah percepatan konstan ke bawah.
    #
    # a_y = GRAVITY
    # v_y = v_y + a_y * dt
    #
    # Saat karakter melompat, velocity_y bernilai negatif. Penambahan
    # GRAVITY * dt membuatnya perlahan mendekati nol. Setelah melewati nol,
    # velocity_y menjadi positif dan karakter bergerak jatuh.
    velocity_y += GRAVITY * dt

    # Batasi kecepatan jatuh maksimum.
    velocity_y = min(velocity_y, MAX_FALL_SPEED)

    # -----------------------------------------------------------------------
    # F. Terapkan velocity: velocity -> position
    # -----------------------------------------------------------------------
    # Posisi berubah berdasarkan velocity saat ini.
    #
    # y = y + v_y * dt
    #
    # Ini adalah semi-implicit Euler: velocity diperbarui lebih dahulu,
    # kemudian dipakai untuk memperbarui posisi.
    player_x += velocity_x * dt
    player_y += velocity_y * dt

    # Batasi gerakan horizontal agar karakter tetap di dalam area simulasi.
    player_x = max(
        float(WORLD.left),
        min(player_x, float(WORLD.right - PLAYER_WIDTH)),
    )

    # -----------------------------------------------------------------------
    # G. AABB floor collision dan collision response
    # -----------------------------------------------------------------------
    current_bottom = player_y + PLAYER_HEIGHT

    # Status grounded ditentukan ulang dari hasil pemeriksaan frame ini.
    # Crossing test tetap mendeteksi kontak meskipun karakter hanya
    # bersinggungan dengan floor tanpa overlap area.
    resolve_floor_collision(previous_bottom, current_bottom)

    # -----------------------------------------------------------------------
    # H. Rendering
    # -----------------------------------------------------------------------
    SCREEN.fill(BG)

    draw_text(SCREEN, "GRAVITY PLAYGROUND", TITLE_FONT, WHITE, 34, 27)
    draw_text(
        SCREEN,
        "Perhatikan bagaimana gravitasi mengubah velocity vertikal karakter",
        FONT,
        MUTED,
        35,
        68,
    )

    # Panel konsep gravitasi dibuat menonjol karena gravitasi adalah fokus
    # pembelajaran. AABB hanya menjadi mekanisme pendukung agar karakter
    # dapat mendarat pada floor.
    gravity_panel = pygame.Rect(WIDTH - 330, 22, 292, 98)
    pygame.draw.rect(SCREEN, ORANGE_DARK, gravity_panel, border_radius=10)
    pygame.draw.rect(SCREEN, ORANGE, gravity_panel, 2, border_radius=10)
    draw_text(
        SCREEN,
        "GRAVITASI (a_y)",
        SMALL_FONT,
        ORANGE,
        gravity_panel.x + 16,
        gravity_panel.y + 12,
    )
    draw_text(
        SCREEN,
        f"{GRAVITY:.0f} px/s²",
        VALUE_FONT,
        WHITE,
        gravity_panel.x + 16,
        gravity_panel.y + 34,
    )
    draw_text(
        SCREEN,
        "Percepatan konstan ke bawah",
        SMALL_FONT,
        MUTED,
        gravity_panel.x + 16,
        gravity_panel.y + 70,
    )

    # Area simulasi dan grid.
    pygame.draw.rect(SCREEN, WORLD_BG, WORLD, border_radius=10)
    draw_grid(SCREEN, WORLD)
    pygame.draw.rect(SCREEN, PANEL_BORDER, WORLD, 2, border_radius=10)

    # Floor. Rectangle ini dipakai sebagai batas tempat karakter mendarat.
    pygame.draw.rect(SCREEN, FLOOR_COLOR, FLOOR, border_radius=5)
    pygame.draw.line(
        SCREEN,
        (145, 160, 183),
        (FLOOR.left, FLOOR.top),
        (FLOOR.right, FLOOR.top),
        3,
    )
    draw_text(
        SCREEN,
        "FLOOR",
        SMALL_FONT,
        WHITE,
        FLOOR.left + 14,
        FLOOR.top + 13,
    )

    # Karakter.
    player_rect = get_player_rect()
    pygame.draw.rect(SCREEN, BLUE, player_rect, border_radius=8)
    pygame.draw.rect(SCREEN, BLUE_LIGHT, player_rect, 2, border_radius=8)

    eye_x = player_rect.centerx + (8 if move_direction >= 0 else -8)
    pygame.draw.circle(SCREEN, (20, 31, 48), (eye_x, player_rect.y + 22), 4)

    # Panah gravitasi: menunjukkan arah percepatan, bukan arah velocity.
    arrow_x = WORLD.right - 65
    arrow_top = WORLD.top + 48
    arrow_bottom = arrow_top + 82

    pygame.draw.line(
        SCREEN,
        ORANGE,
        (arrow_x, arrow_top),
        (arrow_x, arrow_bottom),
        5,
    )
    pygame.draw.polygon(
        SCREEN,
        ORANGE,
        [
            (arrow_x, arrow_bottom + 11),
            (arrow_x - 10, arrow_bottom - 5),
            (arrow_x + 10, arrow_bottom - 5),
        ],
    )
    draw_text(
        SCREEN,
        "g",
        VALUE_FONT,
        ORANGE,
        arrow_x - 8,
        arrow_top - 34,
    )

    # -----------------------------------------------------------------------
    # I. Panel status physics
    # -----------------------------------------------------------------------
    panel_rect = pygame.Rect(32, 710, WIDTH - 64, 72)
    pygame.draw.rect(SCREEN, PANEL, panel_rect, border_radius=9)
    pygame.draw.rect(SCREEN, PANEL_BORDER, panel_rect, 1, border_radius=9)

    state_text = "MENYENTUH LANTAI" if is_grounded else "DI UDARA"
    state_color = GREEN if is_grounded else ORANGE

    draw_text(SCREEN, "VELOCITY Y", SMALL_FONT, MUTED, 50, 721)
    draw_text(SCREEN, f"{velocity_y:,.2f} px/s", FONT, CYAN, 50, 744)

    draw_text(SCREEN, "PERCEPATAN GRAVITASI", SMALL_FONT, MUTED, 300, 721)
    draw_text(SCREEN, f"{GRAVITY:,.0f} px/s²", FONT, ORANGE, 300, 744)

    draw_text(SCREEN, "KONDISI KARAKTER", SMALL_FONT, MUTED, 600, 721)
    draw_text(SCREEN, state_text, FONT, state_color, 600, 744)

    draw_text(
        SCREEN,
        "A/D: gerak   SPACE: jump   R: reset   ESC: keluar",
        SMALL_FONT,
        MUTED,
        875,
        746,
    )

    pygame.display.flip()

pygame.quit()
sys.exit()
