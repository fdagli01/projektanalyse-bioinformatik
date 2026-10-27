"""Notebook 01, PCA: a tiny made-up example with 2 joint angles, so the idea is visible."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "calisma", "cikti")

# 2 joint angles that mostly move together (leg opening/closing) plus a little independent jitter
rng = np.random.default_rng(3)
t = np.arange(300) / 100
leg = np.sin(2 * np.pi * 1.2 * t) + 0.5 * np.sin(2 * np.pi * 0.4 * t)
A = 0.9 * leg + 0.10 * rng.standard_normal(len(t))          # angle of joint A
B = 0.6 * leg + 0.10 * rng.standard_normal(len(t))          # angle of joint B
X = np.c_[A, B]

p = PCA().fit(X)
Y = p.transform(X)
ratio = p.explained_variance_ratio_
mean = X.mean(0)

fig, ax = plt.subplots(1, 4, figsize=(19, 4.4))

ax[0].plot(t, A, color="royalblue", label="eklem A açısı")
ax[0].plot(t, B, color="darkorange", label="eklem B açısı")
ax[0].set_xlabel("zaman (s)"); ax[0].legend(loc="upper right", fontsize=8)
ax[0].set_title("1) İki açı zamanla\nhep birlikte inip çıkıyor")

ax[1].scatter(A, B, s=8, c=t, cmap="cool")
ax[1].set_xlabel("eklem A"); ax[1].set_ylabel("eklem B"); ax[1].set_aspect("equal")
ax[1].set_title("2) Her kare = bir nokta\nnoktalar eğik bir 'sosis' oluşturuyor")

ax[2].scatter(A, B, s=8, c="0.75")
for k, col, nm in [(0, "firebrick", "PC1"), (1, "seagreen", "PC2")]:
    v = p.components_[k] * 1.3 * np.sqrt(p.explained_variance_[k])
    ax[2].plot(*np.c_[mean - v, mean + v], color=col, lw=3)
    ax[2].text(*(mean + v * 1.1), nm, color=col, fontsize=12, weight="bold")
ax[2].set_xlim(-1.8, 1.8); ax[2].set_ylim(-1.3, 1.3)
ax[2].set_xlabel("eklem A"); ax[2].set_ylabel("eklem B"); ax[2].set_aspect("equal")
ax[2].set_title("3) PCA iki çizgi buluyor:\nPC1 = sosisin uzun yönü, PC2 = dik yönü")

ax[3].scatter(Y[:, 0], Y[:, 1], s=8, c=t, cmap="cool")
ax[3].set_xlim(-2.5, 2.5); ax[3].set_ylim(-2.5, 2.5); ax[3].set_aspect("equal")
ax[3].set_xlabel("PC1 değeri"); ax[3].set_ylabel("PC2 değeri")
ax[3].set_title("4) Yeni eksenlerde: PC1'de yayılım %%%.0f,\nPC2'de %%%.0f -> PC2'yi atabiliriz"
                % (100 * ratio[0], 100 * ratio[1]))

fig.tight_layout(); fig.savefig(os.path.join(OUT, "17_pca_oyuncak.png"), dpi=105); plt.close(fig)

# what is lost when we keep only PC1?
Xrec = mean + np.outer(Y[:, 0], p.components_[0])
err = np.abs(Xrec - X).mean()
fig, ax = plt.subplots(1, 2, figsize=(13, 3.6))
ax[0].plot(t, A, color="royalblue", lw=2, label="gerçek A")
ax[0].plot(t, Xrec[:, 0], "k--", lw=1.2, label="sadece PC1'den geri kurulan A")
ax[0].legend(fontsize=8, loc="upper right"); ax[0].set_xlabel("zaman (s)")
ax[0].set_title("2 sayı yerine 1 sayı (PC1) tuttuk: A neredeyse aynı")
ax[1].plot(t, Y[:, 0], color="firebrick")
ax[1].set_xlabel("zaman (s)"); ax[1].set_ylabel("PC1")
ax[1].set_title("Her kare için tek sayı: 'bacak ne kadar açık'")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "18_pca_oyuncak_kayip.png"), dpi=105); plt.close(fig)
print("explained variance:", np.round(ratio, 3), "mean abs error with PC1 only: %.3f" % err)
