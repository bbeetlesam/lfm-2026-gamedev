# larut-gamedev2026

Materi visualisasi untuk **Larut for Maba 2026**.

Proyek ini terdiri dari dua bagian:

| File            | Keterangan                                                                                                                       |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `aabb.py`       | Aplikasi interaktif berbasis [pygame-ce](https://pyga.me/). Gerakkan dua kotak dan lihat hasil tes AABB berubah secara langsung. |
| `aabb-manim.py` | Animasi [Manim](https://www.manim.community/) yang menjelaskan aturan AABB langkah demi langkah.                                 |

## Requirements

| Alat                                        | Dibutuhkan untuk      | Catatan                                                                                                                                                                                                                                                                                              |
| ------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Python](https://www.python.org/) **3.14+** | semuanya              | Dideklarasikan di `pyproject.toml` (`requires-python = ">=3.14"`). `uv` dapat memasangkannya untukmu.                                                                                                                                                                                                |
| [uv](https://docs.astral.sh/uv/)            | mengelola environment | Direkomendasikan. Memasang Python, membuat `.venv`, dan memasang dependensi sesuai lockfile.                                                                                                                                                                                                         |
| [FFmpeg](https://ffmpeg.org/)               | animasi Manim         | Harus tersedia di `PATH` untuk meng-encode video.                                                                                                                                                                                                                                                    |
| System library Cairo dan Pango              | animasi Manim         | Dipakai untuk menggambar dan merender teks. Wheel bawaan sudah mencukupi di kebanyakan sistem. Jika instalasi gagal, pasang dari package manager sistem operasimu (misalnya `pango`, `cairo`, dan `pkg-config` di Arch, atau `libpango1.0-dev`, `libcairo2-dev`, dan `pkg-config` di Debian/Ubuntu). |

Paket Python (dikelola oleh `uv`, versinya dikunci di `uv.lock`):

- `pygame-ce` untuk game interaktif
- `manim` untuk animasi

> **Jangan memasang `pygame` atau `manimce`.**
> `pygame` dan `pygame-ce` sama-sama menyediakan modul `pygame` sehingga saling
> menimpa (timpa teks jir). `manimce` adalah paket usang yang merusak `import manim`.
> Gunakan hanya `pygame-ce` dan `manim`.

LaTeX **tidak** dibutuhkan karena animasi hanya memakai teks biasa.

## Instalasi

```sh
# 1. Clone repositori lalu masuk ke foldernya
git clone https://github.com/bbeetlesam/lfm-2026-gamedev.git
cd larut-gamedev2026

# 2. Buat .venv dan pasang dependensi sesuai lockfile
uv sync
```

### Tanpa uv (pip)

```sh
python3.14 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` dihasilkan dari `uv.lock`. Untuk memperbaruinya setelah
dependency berubah:

```sh
uv export --no-hashes --no-emit-project --no-header --no-annotate -o requirements.txt
```

## Menjalankan aplikasi interaktif

```sh
# Jalankan game demo AABB
uv run aabb.py
```

## Merender animasi Manim

```sh
# Pratinjau cepat berkualitas rendah (480p, 15 fps), video dibuka setelah selesai
uv run manim -pql aabb-manim.py AABBExplainer

# Kualitas menengah (720p, 30 fps)
uv run manim -pqm aabb-manim.py AABBExplainer

# Kualitas tinggi (1080p, 60 fps)
uv run manim -pqh aabb-manim.py AABBExplainer
```

Opsi: `-p` membuka video setelah render selesai, dan `-q` diikuti `l`, `m`,
atau `h` menentukan kualitas.

Hasil render disimpan di `media/videos/aabb-manim/<kualitas>/AABBExplainer.mp4`.
Folder `media/` diabaikan oleh git. Proses render memakan waktu beberapa menit.

## Struktur proyek

```text
aabb.py            visualisasi interaktif dengan pygame-ce
aabb-manim.py      animasi Manim (scene: AABBExplainer)
pyproject.toml     metadata proyek dan dependensi
uv.lock            versi dependensi yang dikunci (sertakan di commit)
requirements.txt   versi dependensi untuk pip, diekspor dari uv.lock
```
