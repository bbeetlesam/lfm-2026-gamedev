import sys

import pygame

# Visualisasi AABB (Axis-Aligned Bounding Box / Kotak Pembatas Sejajar Sumbu)
# Kontrol:
#   WASD / tombol panah: menggerakkan persegi panjang A
#   IJKL: menggerakkan persegi panjang B
#   Klik kiri lalu seret: memindahkan salah satu persegi panjang
#   Gunakan panel kiri untuk memasukkan lebar dan tinggi secara manual
#   ESC: keluar dari program

pygame.init()

INITIAL_WIDTH, INITIAL_HEIGHT = 1000, 700
MIN_WIDTH, MIN_HEIGHT = 560, 380
FPS = 60

BG = (16, 20, 26)  # #10141a
BLUE = (56, 182, 255)  # #38b6ff
RED = (255, 40, 40)  # #ff2828
WHITE = (235, 241, 247)
MUTED = (145, 158, 173)
GRID = (28, 35, 44)
GREEN = (111, 220, 160)  # Digunakan untuk status saat tidak terjadi tabrakan
PANEL_BG = (21, 27, 35)
PANEL_LINE = (45, 55, 67)

screen: pygame.Surface = pygame.display.set_mode(
    (INITIAL_WIDTH, INITIAL_HEIGHT),
    pygame.RESIZABLE,
)
pygame.display.set_caption("AABB Collision Visualiser")
clock = pygame.time.Clock()

# Koordinat persegi panjang dihitung relatif terhadap area permainan di kanan panel samping.
# Dunia permainan mengikuti ukuran area tersebut; tidak ada penskalaan atau ruang kosong akibat letterboxing.
WORLD_PLAY_TOP = 48
WORLD_MARGIN = 0
GRID_SPACING = 40

font = pygame.font.SysFont("consolas", 17)
small_font = pygame.font.SysFont("consolas", 14)
title_font = pygame.font.SysFont("consolas", 22, bold=True)


class Box:
    def __init__(self, name, x, y, w, h, color):
        self.name = name
        self.x, self.y = float(x), float(y)
        self.w, self.h = float(w), float(h)
        self.color = color

    @property
    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), round(self.w), round(self.h))

    def contains(self, pos):
        return self.rect.collidepoint(pos)


a = Box("A", 170, 220, 230, 155, BLUE)
b = Box("B", 490, 315, 210, 170, BLUE)
boxes = [a, b]
dragging = None
drag_offset = (0.0, 0.0)
speed = 4


def aabb_intersects(one, two):
    """Memeriksa apakah dua AABB saling tumpang tindih.

    Setiap kotak direpresentasikan oleh x, y, lebar (w), dan tinggi (h).
    Tabrakan terjadi hanya jika kedua kotak saling bertumpang tindih pada
    sumbu horizontal DAN vertikal. Sisi yang sekadar bersentuhan tidak dihitung.
    """
    # Operator pertidaksamaan ketat berarti dua sisi yang hanya bersentuhan tidak dihitung bertabrakan.
    return (
        one.x < two.x + two.w
        and one.x + one.w > two.x
        and one.y < two.y + two.h
        and one.y + one.h > two.y
    )


SIDEBAR_WIDTH = 290
SIDEBAR_MIN_WIDTH = 250
SIDEBAR_BG = (21, 27, 35)
INPUT_BG = (12, 16, 22)
INPUT_BORDER = (65, 79, 95)
INPUT_FOCUS = BLUE
BUTTON_BG = (35, 46, 58)
BUTTON_HOVER = (47, 61, 76)

# Menyimpan keadaan input teks pada panel kiri.
input_values = {
    ("A", "w"): str(int(a.w)),
    ("A", "h"): str(int(a.h)),
    ("B", "w"): str(int(b.w)),
    ("B", "h"): str(int(b.h)),
}
active_input = None
input_rects = {}
apply_button_rects = {}


def current_layout():
    """Mengembalikan batas dunia terkini yang memenuhi seluruh area di kanan panel samping."""
    window_w, window_h = screen.get_size()
    sidebar_w = sidebar_width()
    world_w = max(1, window_w - sidebar_w)
    world_h = max(1, window_h)
    return 1.0, sidebar_w, 0, world_w, world_h


def sidebar_width():
    window_w, _ = screen.get_size()
    return min(SIDEBAR_WIDTH, max(SIDEBAR_MIN_WIDTH, window_w // 3))


def draw_sidebar(colliding):
    """Menggambar panel informasi, kontrol, status tabrakan, dan kolom ukuran."""
    global input_rects, apply_button_rects
    _, window_h = screen.get_size()
    side_w = sidebar_width()
    pygame.draw.rect(screen, SIDEBAR_BG, (0, 0, side_w, window_h))
    pygame.draw.line(screen, PANEL_LINE, (side_w - 1, 0), (side_w - 1, window_h), 1)

    pad = 16
    y = 16
    title = pygame.font.SysFont("consolas", 19, bold=True)
    section = pygame.font.SysFont("consolas", 16, bold=True)
    body = pygame.font.SysFont("consolas", 13)
    tiny = pygame.font.SysFont("consolas", 11)

    draw_text(screen, "AABB VISUALISER", pad, y, WHITE, title)
    y += 31
    draw_text(screen, "AXIS-ALIGNED BOUNDING BOX", pad, y, MUTED, tiny)
    y += 28

    status = "COLLISION: TRUE" if colliding else "COLLISION: FALSE"
    status_color = RED if colliding else GREEN
    status_rect = pygame.Rect(pad, y, side_w - 2 * pad, 34)
    pygame.draw.rect(screen, INPUT_BG, status_rect, border_radius=5)
    pygame.draw.rect(screen, status_color, status_rect, width=1, border_radius=5)
    draw_text(
        screen,
        status,
        status_rect.centerx,
        status_rect.centery,
        status_color,
        body,
        "center",
    )
    y += 49

    draw_text(screen, "KONTROL", pad, y, WHITE, section)
    y += 25
    for line in (
        "A  gerak: WASD / arrow keys",
        "B  gerak: IJKL",
        "Mouse: click + drag salah satu box",
        "ESC: keluar program",
    ):
        draw_text(screen, line, pad, y, MUTED, body)
        y += 20

    y += 12
    pygame.draw.line(screen, PANEL_LINE, (pad, y), (side_w - pad, y), 1)
    y += 13
    draw_text(screen, "UKURAN KOTAK", pad, y, WHITE, section)
    y += 24
    draw_text(screen, "Masukkan integer positif.", pad, y, MUTED, tiny)
    y += 24

    input_rects = {}
    apply_button_rects = {}
    field_gap = 10
    field_w = (side_w - 2 * pad - field_gap) // 2
    field_h = 31
    label_h = 18

    for box in boxes:
        draw_text(screen, f"KOTAK {box.name}", pad, y, BLUE, body)
        y += 23
        for idx, (key, label) in enumerate((("w", "LEBAR"), ("h", "TINGGI"))):
            x = pad + idx * (field_w + field_gap)
            draw_text(screen, label, x, y, MUTED, tiny)
            rect = pygame.Rect(x, y + label_h, field_w, field_h)
            input_rects[(box.name, key)] = rect
            focused = active_input == (box.name, key)
            pygame.draw.rect(screen, INPUT_BG, rect, border_radius=4)
            pygame.draw.rect(
                screen,
                INPUT_FOCUS if focused else INPUT_BORDER,
                rect,
                width=2 if focused else 1,
                border_radius=4,
            )
            value = input_values[(box.name, key)]
            draw_text(
                screen, value or "", rect.x + 8, rect.centery, WHITE, body, "midleft"
            )
        y += label_h + field_h + 8

        button_rect = pygame.Rect(pad, y, side_w - 2 * pad, 29)
        apply_button_rects[box.name] = button_rect
        pygame.draw.rect(screen, BUTTON_BG, button_rect, border_radius=4)
        pygame.draw.rect(screen, INPUT_BORDER, button_rect, width=1, border_radius=4)
        draw_text(
            screen,
            f"Apply {box.name} size",
            button_rect.centerx,
            button_rect.centery,
            WHITE,
            body,
            "center",
        )
        y += 43

    draw_text(screen, "TES AABB", pad, y, WHITE, section)
    y += 23
    for line in (
        "A.kiri < B.kanan",
        "A.kanan > B.kiri",
        "A.atas < B.bawah",
        "A.bawah > B.atas",
    ):
        draw_text(screen, line, pad, y, MUTED, tiny)
        y += 17


def apply_box_size(box):
    """Memvalidasi input lebar/tinggi, lalu menerapkannya ke persegi panjang.

    Input harus berupa bilangan bulat positif. Jika tidak valid, nilainya
    diganti menjadi 200. Ukuran kemudian dibatasi agar sesuai dengan dunia.
    """
    for key, attr in (("w", "w"), ("h", "h")):
        raw = input_values[(box.name, key)].strip()
        try:
            # Hanya menerima bilangan asli: digit ASCII dengan nilai lebih besar dari 0.
            if not raw or not raw.isascii() or not raw.isdigit() or int(raw) <= 0:
                value = 200
            else:
                value = int(raw)
        except (ValueError, OverflowError):
            value = 200

        # Batasi ukuran agar tetap berada dalam batas dunia yang tersedia saat ini.
        world_w, world_h = world_size()
        max_value = world_w if attr == "w" else max(30, world_h - WORLD_PLAY_TOP)
        value = max(30, min(value, max_value))
        setattr(box, attr, float(value))
        input_values[(box.name, key)] = str(value)

    clamp_box(box)


def world_to_screen(pos, layout):
    scale, vx, vy, *_ = layout
    return round(vx + pos[0] * scale), round(vy + pos[1] * scale)


def screen_to_world(pos, layout):
    scale, vx, vy, *_ = layout
    if scale <= 0:
        return 0.0, 0.0
    return (pos[0] - vx) / scale, (pos[1] - vy) / scale


def in_viewport(pos, layout):
    _, vx, vy, vw, vh = layout
    return vx <= pos[0] < vx + vw and vy <= pos[1] < vy + vh


def draw_text(target, text, x, y, color, font_obj, anchor="topleft"):
    image = font_obj.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, (round(x), round(y)))
    target.blit(image, rect)


def draw_corner_label(target, text, pos, color, anchor, scale):
    # Sesuaikan ukuran teks label dan latar belakangnya dengan area tampilan.
    font_size = max(9, round(14 * scale))
    label_font = pygame.font.SysFont("consolas", font_size)
    image = label_font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, (round(pos[0]), round(pos[1])))
    pad = max(2, round(3 * scale))
    pygame.draw.rect(target, BG, rect.inflate(pad * 2, pad * 2))
    target.blit(image, rect)


def draw_box(target, box, colliding, layout):
    """Menggambar kotak, penanda asal, label koordinat, dan dimensinya.

    Warna garis menjadi merah ketika fungsi AABB mendeteksi tabrakan;
    jika tidak, garis tetap biru.
    """
    scale, vx, vy, *_ = layout
    r = box.rect
    screen_rect = pygame.Rect(
        round(vx + r.x * scale),
        round(vy + r.y * scale),
        max(1, round(r.width * scale)),
        max(1, round(r.height * scale)),
    )
    color = RED if colliding else BLUE
    line_width = max(1, round(2 * scale))
    marker_radius = max(2, round(4 * scale))

    pygame.draw.rect(target, color, screen_rect, width=line_width)

    # Penanda titik asal berada di sudut kiri atas, yaitu koordinat (x, y).
    pygame.draw.circle(target, color, screen_rect.topleft, marker_radius)
    pygame.draw.circle(target, BG, screen_rect.topleft, max(1, round(scale)))

    # Label koordinat mengikuti posisi sudut persegi panjang.
    label_gap = max(4, round(9 * scale))
    draw_corner_label(
        target,
        f"x={int(box.x)}",
        (screen_rect.left, screen_rect.top - label_gap),
        color,
        "bottomleft",
        scale,
    )
    draw_corner_label(
        target,
        f"y={int(box.y)}",
        (screen_rect.left + round(54 * scale), screen_rect.top - label_gap),
        color,
        "bottomleft",
        scale,
    )
    draw_corner_label(
        target,
        f"x={int(box.x + box.w)}",
        (screen_rect.right + round(8 * scale), screen_rect.top),
        color,
        "topleft",
        scale,
    )
    draw_corner_label(
        target,
        f"y={int(box.y + box.h)}",
        (screen_rect.right + round(8 * scale), screen_rect.bottom),
        color,
        "bottomleft",
        scale,
    )

    # Tampilkan nama dan dimensi persegi panjang di bagian tengahnya.
    inner_font = pygame.font.SysFont("consolas", max(9, round(17 * scale)))
    draw_text(
        target,
        f"{box.name}  {int(box.w)} x {int(box.h)}",
        screen_rect.centerx,
        screen_rect.centery,
        color,
        inner_font,
        "center",
    )


def world_size():
    """Mengambil lebar dan tinggi dunia saat ini, tanpa memasukkan lebar panel samping."""
    _, _, _, world_w, world_h = current_layout()
    return world_w, world_h


def clamp_box(box):
    world_w, world_h = world_size()
    box.w = max(30, min(box.w, world_w))
    box.h = max(30, min(box.h, max(30, world_h - WORLD_PLAY_TOP)))
    box.x = max(0, min(box.x, world_w - box.w))
    box.y = max(WORLD_PLAY_TOP, min(box.y, world_h - box.h))


def draw_scene():
    """Menggambar kisi dan kedua kotak pada area dunia di sebelah panel kiri."""
    layout = current_layout()
    _, vx, vy, vw, vh = layout
    screen.fill(BG)

    # Permukaan dunia permainan memenuhi seluruh area yang tersedia di kanan panel samping.
    # Koordinat, sel kisi, bentuk untuk deteksi tabrakan, dan pemetaan mouse memakai skala 1:1.
    scene = pygame.Surface((vw, vh))
    scene.fill(BG)

    for gx in range(0, vw, GRID_SPACING):
        pygame.draw.line(scene, GRID, (gx, 0), (gx, vh), 1)
    for gy in range(0, vh, GRID_SPACING):
        pygame.draw.line(scene, GRID, (0, gy), (vw, gy), 1)

    colliding = aabb_intersects(a, b)
    world_layout = (1.0, 0, 0, vw, vh)
    draw_box(scene, a, colliding, world_layout)
    draw_box(scene, b, colliding, world_layout)

    formula = (
        "A.kiri < B.kanan  AND  A.kanan > B.kiri  AND  "
        "A.atas < B.bawah  AND  A.bawah > B.atas"
    )
    draw_text(scene, formula, vw // 2, 18, MUTED, small_font, "midtop")

    screen.blit(scene, (vx, vy))
    draw_sidebar(colliding)
    return layout


running = True
while running:
    # Alur setiap frame: baca input, perbarui posisi, hitung tabrakan,
    # gambar ulang dunia dan panel, lalu tampilkan frame ke layar.
    clock.tick(FPS)
    layout = current_layout()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            pass

        elif event.type == pygame.KEYDOWN:
            if active_input is not None:
                if event.key == pygame.K_BACKSPACE:
                    input_values[active_input] = input_values[active_input][:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    target = a if active_input[0] == "A" else b
                    apply_box_size(target)
                    active_input = None
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_ESCAPE:
                    active_input = None
                    pygame.key.stop_text_input()
            elif event.key == pygame.K_ESCAPE:
                running = False

        elif event.type == pygame.TEXTINPUT and active_input is not None:
            # Simpan teks apa adanya agar input yang tidak valid dapat diperiksa saat diterapkan.
            input_values[active_input] += event.text

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < sidebar_width():
                # Fokuskan kolom input atau terapkan ukuran persegi panjang.
                active_input = None
                for field_key, rect in input_rects.items():
                    if rect.collidepoint(event.pos):
                        active_input = field_key
                        break
                if active_input is not None:
                    pygame.key.start_text_input()
                else:
                    pygame.key.stop_text_input()
                for box_name, rect in apply_button_rects.items():
                    if rect.collidepoint(event.pos):
                        target = a if box_name == "A" else b
                        apply_box_size(target)
                        active_input = None
                        pygame.key.stop_text_input()
                        break
            elif in_viewport(event.pos, layout):
                world_pos = screen_to_world(event.pos, layout)
                for box in reversed(boxes):
                    if box.contains(world_pos):
                        dragging = box
                        drag_offset = (box.x - world_pos[0], box.y - world_pos[1])
                        break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging = None

        elif event.type == pygame.MOUSEMOTION and dragging is not None:
            world_pos = screen_to_world(event.pos, layout)
            dragging.x = world_pos[0] + drag_offset[0]
            dragging.y = world_pos[1] + drag_offset[1]
            clamp_box(dragging)

    keys = pygame.key.get_pressed()
    if dragging is None and active_input is None:
        # Rectangle A always uses WASD / arrow keys.
        dx_a = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        dy_a = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        a.x += dx_a * speed
        a.y += dy_a * speed
        clamp_box(a)

        # Persegi panjang B selalu digerakkan dengan IJKL.
        dx_b = int(keys[pygame.K_l]) - int(keys[pygame.K_j])
        dy_b = int(keys[pygame.K_k]) - int(keys[pygame.K_i])
        b.x += dx_b * speed
        b.y += dy_b * speed
        clamp_box(b)

    # Ambil ulang Surface tampilan setelah ukuran jendela diubah oleh compositor.
    # pygame-ce / SDL memperbarui Surface tampilan ketika ukuran jendela berubah.
    display_surface = pygame.display.get_surface()
    if display_surface is not None:
        screen = display_surface
    draw_scene()
    pygame.display.flip()

pygame.quit()
sys.exit()
