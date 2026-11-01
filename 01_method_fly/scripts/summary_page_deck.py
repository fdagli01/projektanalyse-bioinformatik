"""Deck-styled version of the stage 1 overview page (same content as summary_page.py):
light background, white cards, blue accents and a blue pipeline band, like the title and Data slides."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

plt.rcParams["font.family"] = ["Montserrat", "Avenir Next", "Helvetica Neue", "Arial", "DejaVu Sans"]

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")
SUMMARY = os.path.join(HERE, "figures", "summary")
BG, NAVY, BLUE, ORANGE, GREY = "#DDEAF8", "#0F1B3D", "#1862D6", "#E4694F", "#5A6478"

steps = [
    ("Pose tracking", "1_skeleton.png",
     "Keypoints on every video frame\n(fly: 32 points, 100 fps)"),
    ("Egocentric representation", "2_angles.png",
     "Joint angles instead of x/y positions: independent of\nwhere the animal is or faces (32 points → 22 angles)"),
    ("PCA", "3_pca.png",
     "Angles that move together are merged\n22 angles → 13 main movement patterns (95% of variance)"),
    ("Wavelet transform", "4_wavelet.png",
     "Posture over time → how much slow and fast movement\n13 patterns × 25 frequencies = 325 numbers per frame"),
    ("UMAP embedding", "5_umap.png",
     "325 numbers → one point on a 2-D map\nSimilar movement = nearby points; peaks = frequent behaviors"),
    ("Watershed regions", "6_regions.png",
     "Map cut into 12 regions = candidate behaviors\nEach frame gets a region label → time per behavior, ethogram"),
]

W, H = 19.2, 10.8
fig = plt.figure(figsize=(W, H), facecolor=BG)
bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, 1); bg.set_ylim(0, 1); bg.axis("off")

fig.text(0.04, 0.935, "Notebook 01: from video to behavior map", fontsize=34, weight="bold", color=NAVY, va="center")
fig.text(0.04, 0.885, "MotionMapper pipeline  ·  No manual labels: behaviors are discovered from the movement itself,"
         " then named by watching example clips", fontsize=15, color=GREY, va="center")
bg.add_patch(FancyBboxPatch((0.04, 0.855), 0.07, 0.006, boxstyle="round,pad=0,rounding_size=0.003", fc=ORANGE, ec="none"))

mx, gap, top, ch, rgap = 0.04, 0.018, 0.835, 0.335, 0.025
cw = (1 - 2 * mx - 2 * gap) / 3
for i, (title, img, cap) in enumerate(steps):
    r, c = divmod(i, 3)
    x = mx + c * (cw + gap)
    y = top - ch - r * (ch + rgap)
    bg.add_patch(FancyBboxPatch((x + 0.002, y - 0.004), cw, ch, boxstyle="round,pad=0,rounding_size=0.012",
                                fc="#BFD0E6", ec="none"))                      # soft shadow
    bg.add_patch(FancyBboxPatch((x, y), cw, ch, boxstyle="round,pad=0,rounding_size=0.012", fc="white", ec="none"))
    cx, cy = x + 0.022, y + ch - 0.037
    bg.add_patch(Circle((cx, cy), 0.0155, fc=BLUE, ec="none", transform=bg.transData))
    fig.text(cx, cy, str(i + 1), color="white", fontsize=15, weight="bold", ha="center", va="center")
    fig.text(cx + 0.024, cy, title, color=NAVY, fontsize=18, weight="bold", va="center")
    ax = fig.add_axes([x + 0.012, y + 0.085, cw - 0.024, ch - 0.145])
    ax.imshow(plt.imread(os.path.join(SUMMARY, img))); ax.axis("off"); ax.set_anchor("C")
    fig.text(x + 0.016, y + 0.04, cap, fontsize=11.5, color=GREY, va="center", linespacing=1.45)

bg.add_patch(FancyBboxPatch((0.04, 0.025), 0.92, 0.075, boxstyle="round,pad=0,rounding_size=0.02", fc=BLUE, ec="none"))
fig.text(0.5, 0.0625, "32 keypoints  →  22 angles  →  13 PCA modes  →  325 wavelet features  →  2-D map  →  12 behavior regions",
         fontsize=18, weight="bold", color="white", ha="center", va="center")
fig.savefig(os.path.join(OUT, "21_overview_deck_blue.png"), dpi=100, facecolor=BG)
print("saved 21_overview_deck_blue.png")
