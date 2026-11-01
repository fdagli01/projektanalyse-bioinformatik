"""One-page overview of stage 1 (for a slide): six steps, each with its figure and a one-line caption."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 01_method_fly/
ROOT = os.path.dirname(HERE)                                         # repository root
OUT = os.path.join(HERE, "figures", "working")
SUMMARY = os.path.join(HERE, "figures", "summary")

steps = [
    ("1  Pose tracking", "1_skeleton.png",
     "Keypoints on every video frame\n(fly: 32 points, 100 fps)"),
    ("2  Egocentric representation", "2_angles.png",
     "Joint angles instead of x/y positions:\nindependent of where the animal is or faces\n(32 points → 22 angles)"),
    ("3  PCA", "3_pca.png",
     "Angles that move together are merged\n22 angles → 13 main movement patterns (95% of variance)"),
    ("4  Wavelet transform", "4_wavelet.png",
     "Posture over time → how much slow and fast movement\n13 patterns × 25 frequencies = 325 numbers per frame"),
    ("5  UMAP embedding", "5_umap.png",
     "325 numbers → one point on a 2-D map\nSimilar movement = nearby points; peaks = frequent behaviors"),
    ("6  Watershed regions", "6_regions.png",
     "Map cut into 12 regions = candidate behaviors\nEach frame gets a region label → time per behavior, timeline (ethogram)"),
]

fig = plt.figure(figsize=(20, 11.25))
fig.text(0.03, 0.955, "Notebook 01: from video to behavior map (MotionMapper pipeline)", fontsize=26, weight="bold", va="center")
fig.text(0.03, 0.915, "No manual labels: behaviors are discovered from the movement itself, then named by watching example clips",
         fontsize=15, color="0.35", va="center")

cols, rows = 3, 2
x0, cw, ch = 0.03, 0.30, 0.22
for i, (title, img, cap) in enumerate(steps):
    r, c = divmod(i, cols)
    left = x0 + c * (cw + 0.025)
    top = 0.875 - r * 0.41
    fig.text(left, top, title, fontsize=17, weight="bold", color="#1f5fd6", va="top")
    ax = fig.add_axes([left, top - 0.045 - ch, cw, ch])
    ax.imshow(plt.imread(os.path.join(SUMMARY, img))); ax.axis("off"); ax.set_anchor("N")
    fig.text(left, top - 0.055 - ch, cap, fontsize=12.5, va="top", color="0.15")

fig.text(0.03, 0.035, "32 keypoints  →  22 angles  →  13 PCA modes  →  325 wavelet features  →  2-D map  →  12 behavior regions",
         fontsize=15, weight="bold", color="firebrick", va="center")
fig.savefig(os.path.join(OUT, "19_overview.png"), dpi=100)
print("saved 19_overview.png")
