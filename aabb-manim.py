from collections.abc import Callable
from functools import cache
from typing import Any

import numpy as np
from manim import (
    BOLD,
    DOWN,
    LEFT,
    NORMAL,
    ORIGIN,
    UP,
    Animation,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    ManimColor,
    Rectangle,
    Scene,
    Text,
    ValueTracker,
    VGroup,
    VMobject,
    Write,
    always_redraw,
    config,
    smooth,
)

# Video edukasi tentang AABB (Axis-Aligned Bounding Box), berdasarkan aabb.py.
# Render pratinjau:
#   uv run manim -pql aabb-manim.py AABBExplainer
# Render kualitas tinggi:
#   uv run manim -pqh aabb-manim.py AABBExplainer

BG = "#10141a"
BLUE = "#38b6ff"
RED = "#ff2828"
WHITE = "#f0f3f6"
MUTED = "#a1adba"
GRID = "#202832"
GREEN = "#6fdca0"

config.background_color = ManimColor(BG)

Box = dict[str, float]

# Data kotak menggunakan koordinat dunia: (x, y) adalah sudut kiri atas.
A: Box = {"x": 1.0, "y": 1.0, "w": 4.0, "h": 3.0}
B: Box = {"x": 7.0, "y": 2.0, "w": 4.0, "h": 3.0}

# Pemetaan koordinat dunia ke layar Manim.
# Di dunia 2D game, y bertambah ke bawah; di Manim, y bertambah ke atas.
SCALE = 0.62
ORIGIN_X = -5.8
ORIGIN_Y = 2.15

# Panel penjelasan di sisi kanan layar.
PANEL_X = 1.95
EPSILON = 1e-6


def screen_point(x: float, y: float) -> np.ndarray:
    """Membuat titik 3D Manim dari koordinat layar."""
    return np.array([x, y, 0.0])


def world_point(x: float, y: float) -> np.ndarray:
    """Mengubah titik koordinat dunia menjadi titik di layar Manim."""
    return screen_point(ORIGIN_X + x * SCALE, ORIGIN_Y - y * SCALE)


def box_center(box: Box) -> np.ndarray:
    """Menghitung titik tengah kotak pada layar Manim."""
    return world_point(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)


def intersects_aabb(one: Box, two: Box) -> bool:
    """Tes AABB yang sama dengan aabb.py: sisi yang hanya bersentuhan tidak dihitung."""
    return (
        one["x"] < two["x"] + two["w"]
        and one["x"] + one["w"] > two["x"]
        and one["y"] < two["y"] + two["h"]
        and one["y"] + one["h"] > two["y"]
    )


def touches_aabb(one: Box, two: Box) -> bool:
    """Benar jika kotak hanya bersentuhan di sisi (tidak bertumpang tindih)."""
    if intersects_aabb(one, two):
        return False
    return (
        one["x"] <= two["x"] + two["w"]
        and one["x"] + one["w"] >= two["x"]
        and one["y"] <= two["y"] + two["h"]
        and one["y"] + one["h"] >= two["y"]
    )


def conditions(one: Box, two: Box) -> list[tuple[str, float, str, float, bool]]:
    """Empat kondisi AABB: (nama, nilai kiri, operator, nilai kanan, terpenuhi?)."""
    one_left, one_right = one["x"], one["x"] + one["w"]
    one_top, one_bottom = one["y"], one["y"] + one["h"]
    two_left, two_right = two["x"], two["x"] + two["w"]
    two_top, two_bottom = two["y"], two["y"] + two["h"]
    return [
        ("A.kiri < B.kanan", one_left, "<", two_right, one_left < two_right),
        ("A.kanan > B.kiri", one_right, ">", two_left, one_right > two_left),
        ("A.atas < B.bawah", one_top, "<", two_bottom, one_top < two_bottom),
        ("A.bawah > B.atas", one_bottom, ">", two_top, one_bottom > two_top),
    ]


def resolve(value: Any) -> Any:
    """Mengembalikan nilai langsung, atau hasil pemanggilan jika berupa fungsi."""
    return value() if callable(value) else value


@cache
def cached_text(content: str, size: float, color: str, weight: str) -> Text:
    """Membuat Text sekali per kombinasi isi/gaya; membuat Text (Pango) cukup mahal."""
    return Text(content, font_size=size, color=color, weight=weight)


def live_text(
    content: Callable[[], str] | str,
    position: Callable[[], np.ndarray] | np.ndarray,
    size: float,
    color: Callable[[], str] | str = WHITE,
    edge: np.ndarray = ORIGIN,
    weight: str = NORMAL,
) -> VMobject:
    """Teks yang digambar ulang setiap frame agar mengikuti keadaan animasi."""
    return always_redraw(
        lambda: (
            cached_text(resolve(content), size, resolve(color), weight)
            .copy()
            .move_to(resolve(position), aligned_edge=edge)
        )
    )


class AABBExplainer(Scene):
    def construct(self):
        # Kisi latar sebagai panduan visual posisi dan pergerakan kotak.
        grid = VGroup()
        for x in np.arange(-6.5, 7.0, 0.5):
            grid.add(
                Line(
                    screen_point(x, -3.6),
                    screen_point(x, 3.1),
                    stroke_color=GRID,
                    stroke_width=0.6,
                )
            )
        for y in np.arange(-3.5, 3.5, 0.5):
            grid.add(
                Line(
                    screen_point(-6.7, y),
                    screen_point(6.7, y),
                    stroke_color=GRID,
                    stroke_width=0.6,
                )
            )
        self.add(grid)

        judul = Text(
            "Memahami Deteksi Tabrakan AABB", font_size=30, color=WHITE, weight=BOLD
        ).to_edge(UP, buff=0.22)
        subjudul = Text(
            "Axis-Aligned Bounding Box • Visualisasi 2D", font_size=16, color=MUTED
        ).next_to(judul, DOWN, buff=0.08)
        self.play(Write(judul), FadeIn(subjudul))
        self.wait(0.4)

        # ValueTracker mengendalikan posisi kotak B selama animasi.
        # Nilai dibulatkan agar galat floating point tidak memicu kedipan status.
        pos_bx = ValueTracker(B["x"])
        pos_by = ValueTracker(B["y"])

        def kotak_a() -> Box:
            return A

        def kotak_b() -> Box:
            return {
                **B,
                "x": round(pos_bx.get_value(), 6),
                "y": round(pos_by.get_value(), 6),
            }

        def tabrakan() -> bool:
            return intersects_aabb(kotak_a(), kotak_b())

        def warna_kotak() -> str:
            return RED if tabrakan() else BLUE

        def buat_kotak(get_box: Callable[[], Box]) -> VMobject:
            return always_redraw(
                lambda: Rectangle(
                    width=get_box()["w"] * SCALE,
                    height=get_box()["h"] * SCALE,
                    stroke_color=warna_kotak(),
                    stroke_width=3,
                    fill_color=BLUE,
                    fill_opacity=0.06,
                ).move_to(box_center(get_box()))
            )

        def buat_titik(get_box: Callable[[], Box]) -> VMobject:
            # Titik asal setiap kotak terletak di sudut kiri atas.
            return always_redraw(
                lambda: Dot(
                    world_point(get_box()["x"], get_box()["y"]),
                    radius=0.055,
                    color=warna_kotak(),
                )
            )

        def buat_label_tepi(get_box: Callable[[], Box], di_atas: bool) -> VGroup:
            """Label x kiri/kanan dan y atas/bawah di sekitar kotak.

            Label x diletakkan di atas (kotak A) atau di bawah (kotak B), dan label y
            di kiri (A) atau kanan (B), sehingga tidak saling menimpa saat kotak
            bertumpang tindih.
            """
            arah = -1 if di_atas else 1

            def x_label(tepi_kanan: bool) -> VMobject:
                return live_text(
                    lambda: (
                        f"x={get_box()['x'] + (get_box()['w'] if tepi_kanan else 0):.1f}"
                    ),
                    lambda: world_point(
                        get_box()["x"] + (get_box()["w"] if tepi_kanan else 0),
                        get_box()["y"]
                        + (0 if di_atas else get_box()["h"])
                        + arah * 0.35,
                    ),
                    13,
                    warna_kotak,
                )

            def y_label(tepi_bawah: bool) -> VMobject:
                return live_text(
                    lambda: (
                        f"y={get_box()['y'] + (get_box()['h'] if tepi_bawah else 0):.1f}"
                    ),
                    lambda: world_point(
                        get_box()["x"]
                        + (0 if di_atas else get_box()["w"])
                        + arah * 0.9,
                        get_box()["y"] + (get_box()["h"] if tepi_bawah else 0),
                    ),
                    13,
                    warna_kotak,
                )

            return VGroup(
                x_label(False),
                x_label(True),
                y_label(False),
                y_label(True),
            )

        rect_a, rect_b = buat_kotak(kotak_a), buat_kotak(kotak_b)
        titik_a, titik_b = buat_titik(kotak_a), buat_titik(kotak_b)
        label_a = buat_label_tepi(kotak_a, di_atas=True)
        label_b = buat_label_tepi(kotak_b, di_atas=False)
        nama_a = live_text(
            "KOTAK A", lambda: box_center(kotak_a()), 16, WHITE, weight=BOLD
        )
        nama_b = live_text(
            "KOTAK B", lambda: box_center(kotak_b()), 16, WHITE, weight=BOLD
        )

        # Panel kanan menjelaskan aturan tabrakan.
        panel_judul = Text("Prinsip AABB", font_size=22, color=WHITE, weight=BOLD)
        panel_judul.move_to(screen_point(PANEL_X, 1.85), aligned_edge=LEFT)

        penjelasan = VGroup(
            Text("Kedua kotak harus tumpang tindih", font_size=14, color=MUTED),
            Text("pada sumbu X DAN sumbu Y.", font_size=14, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        penjelasan.move_to(screen_point(PANEL_X, 1.25), aligned_edge=LEFT)

        # Setiap kondisi dievaluasi langsung: hijau jika terpenuhi, merah jika tidak.
        def baris_kondisi(indeks: int) -> VMobject:
            def isi() -> str:
                nama, kiri, op, kanan, _ = conditions(kotak_a(), kotak_b())[indeks]
                return f"{nama}   ({kiri:.1f} {op} {kanan:.1f})"

            def warna() -> str:
                return GREEN if conditions(kotak_a(), kotak_b())[indeks][4] else RED

            return live_text(
                isi, screen_point(PANEL_X, 0.4 - indeks * 0.36), 14, warna, LEFT
            )

        kondisi = VGroup(*[baris_kondisi(i) for i in range(4)])

        status = live_text(
            lambda: "TABRAKAN TERDETEKSI" if tabrakan() else "BELUM BERTABRAKAN",
            screen_point(PANEL_X, -1.35),
            16,
            lambda: RED if tabrakan() else GREEN,
            LEFT,
            BOLD,
        )

        def isi_catatan() -> str:
            if tabrakan():
                return "Keempat kondisi terpenuhi."
            if touches_aabb(kotak_a(), kotak_b()):
                return "Sisi bersentuhan tidak dihitung (pakai < dan >)."
            return "Masih ada kondisi yang belum terpenuhi."

        catatan = live_text(isi_catatan, screen_point(PANEL_X, -1.75), 12, MUTED, LEFT)

        self.play(
            Create(rect_a),
            Create(rect_b),
            FadeIn(titik_a),
            FadeIn(titik_b),
            FadeIn(label_a),
            FadeIn(label_b),
            FadeIn(nama_a),
            FadeIn(nama_b),
            run_time=1.3,
        )
        self.play(
            FadeIn(panel_judul),
            FadeIn(penjelasan),
            LaggedStart(*[FadeIn(k) for k in kondisi], lag_ratio=0.12),
            FadeIn(status),
            FadeIn(catatan),
        )
        self.wait(1)

        # Keterangan fase animasi di bagian bawah panel.
        keterangan: list[Text] = []

        def tampilkan_keterangan(teks: str | None) -> list[Animation]:
            animasi: list[Animation] = [FadeOut(k) for k in keterangan]
            keterangan.clear()
            if teks is not None:
                baru = Text(teks, font_size=15, color=WHITE)
                baru.move_to(screen_point(PANEL_X, -2.5), aligned_edge=LEFT)
                keterangan.append(baru)
                animasi.append(FadeIn(baru))
            return animasi

        # Fase 1: B mendekat dari kanan sampai tepat bersentuhan dengan A.
        self.play(
            *tampilkan_keterangan("Kotak B bergerak ke kiri..."),
            pos_bx.animate.set_value(A["x"] + A["w"]),
            run_time=2.5,
            rate_func=smooth,
        )
        self.wait(1.8)

        # Fase 2: B masuk lebih dalam; keempat kondisi terpenuhi.
        self.play(
            *tampilkan_keterangan("B masuk ke A: tumpang tindih di X dan Y."),
            pos_bx.animate.set_value(3.2),
            run_time=2,
            rate_func=smooth,
        )
        self.wait(1.5)

        # Fase 3: B turun; sumbu X masih tumpang tindih tetapi sumbu Y tidak.
        self.play(
            *tampilkan_keterangan("B turun: sumbu Y tidak lagi tumpang tindih."),
            pos_by.animate.set_value(5.5),
            run_time=2.5,
            rate_func=smooth,
        )
        self.wait(1.8)

        # Kembalikan B ke posisi awal.
        self.play(
            *tampilkan_keterangan(None),
            pos_bx.animate.set_value(B["x"]),
            pos_by.animate.set_value(B["y"]),
            run_time=2.5,
            rate_func=smooth,
        )
        self.wait(1)

        penutup = Text(
            "AABB: metode sederhana dan cepat untuk deteksi tabrakan 2D.",
            font_size=17,
            color=WHITE,
        ).to_edge(DOWN, buff=0.2)
        self.play(FadeIn(penutup, shift=UP * 0.1))
        self.wait(2)
