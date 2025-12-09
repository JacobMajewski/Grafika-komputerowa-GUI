import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import pycolmap
import open3d as o3d

# --- Rekonstrukcja rzadka ---
def sparse_reconstruction(workspace_dir, images_dir):
    database_dir = os.path.join(workspace_dir, "database.db")
    sparse_dir = os.path.join(workspace_dir, "sparse")
    ply_dir = os.path.join(workspace_dir, "ply")

    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(ply_dir, exist_ok=True)

    pycolmap.extract_features(database_path=database_dir, image_path=images_dir)
    pycolmap.match_exhaustive(database_path=database_dir)
    maps = pycolmap.incremental_mapping(database_path=database_dir, image_path=images_dir, output_path=sparse_dir)
    maps[0].write(sparse_dir)
    reconstruction = pycolmap.Reconstruction(sparse_dir)
    reconstruction.export_PLY(os.path.join(ply_dir, "sparse.ply"))

# --- Rekonstrukcja gęsta ---
def dense_reconstruction(workspace_dir, images_dir):
    sparse_dir = os.path.join(workspace_dir, "sparse")
    ply_dir = os.path.join(workspace_dir, "ply")
    dense_dir = os.path.join(workspace_dir, "dense")

    os.makedirs(dense_dir, exist_ok=True)

    undistorted_ops = pycolmap.UndistortCameraOptions(max_image_size=1500)
    patch_match_ops = pycolmap.PatchMatchOptions(cache_size=48, max_image_size=1500)

    pycolmap.undistort_images(dense_dir, sparse_dir, images_dir, undistort_options=undistorted_ops)
    pycolmap.patch_match_stereo(dense_dir, options=patch_match_ops)
    pycolmap.stereo_fusion(os.path.join(ply_dir, "dense.ply"), dense_dir)

# --- Okno GUI ---
def run_reconstruction():
    images_dir = img_path_var.get()
    workspace_dir = out_path_var.get()

    if not images_dir or not workspace_dir:
        messagebox.showerror("Błąd", "Podaj oba foldery!")
        return

    def worker():
        try:
            sparse_reconstruction(workspace_dir, images_dir)
            dense_reconstruction(workspace_dir, images_dir)

            pcd1 = o3d.io.read_point_cloud(os.path.join(workspace_dir, "ply/sparse.ply"))
            pcd2 = o3d.io.read_point_cloud(os.path.join(workspace_dir, "ply/dense.ply"))
            pcd2.translate((1.0, 0, 0))

            o3d.visualization.draw_geometries([pcd1, pcd2])
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    threading.Thread(target=worker).start()


def select_images():
    folder = filedialog.askdirectory()
    if folder:
        img_path_var.set(folder)


def select_output():
    folder = filedialog.askdirectory()
    if folder:
        out_path_var.set(folder)


root = tk.Tk()
root.title("Interfejs Rekonstrukcji 3D — PyCOLMAP")
root.geometry("450x220")

img_path_var = tk.StringVar()
out_path_var = tk.StringVar()

# GUI layout
tk.Label(root, text="Folder ze zdjęciami:").pack()
tk.Entry(root, textvariable=img_path_var, width=50).pack()
tk.Button(root, text="Wybierz", command=select_images).pack(pady=5)

tk.Label(root, text="Folder wyjściowy:").pack()
tk.Entry(root, textvariable=out_path_var, width=50).pack()
tk.Button(root, text="Wybierz", command=select_output).pack(pady=5)

tk.Button(root, text="Start rekonstrukcji", command=run_reconstruction, bg="#4CAF50", fg="white").pack(pady=10)

root.mainloop()
