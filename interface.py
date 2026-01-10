import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
import pycolmap
import open3d as o3d

# =========================
# THREAD SAFE PROGRESS
# =========================
def set_progress(value, text=""):
    progress_bar["value"] = value
    status_label.config(text=text)
    root.update_idletasks()

# =========================
# SPARSE
# =========================
def sparse_reconstruction(workspace_dir, images_dir):
    set_progress(5, "Extracting features...")
    database_path = os.path.join(workspace_dir, "database.db")
    sparse_dir = os.path.join(workspace_dir, "sparse")
    ply_dir = os.path.join(workspace_dir, "ply")

    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(ply_dir, exist_ok=True)

    pycolmap.extract_features(database_path, images_dir)
    set_progress(20, "Matching features...")

    pycolmap.match_exhaustive(database_path)
    set_progress(40, "Incremental mapping...")

    maps = pycolmap.incremental_mapping(database_path, images_dir, sparse_dir)
    maps[0].write(sparse_dir)

    recon = pycolmap.Reconstruction(sparse_dir)
    recon.export_PLY(os.path.join(ply_dir, "sparse.ply"))
    set_progress(55, "Sparse reconstruction done")

# =========================
# DENSE
# =========================
def dense_reconstruction(workspace_dir, images_dir):
    sparse_dir = os.path.join(workspace_dir, "sparse")
    dense_dir = os.path.join(workspace_dir, "dense")
    ply_dir = os.path.join(workspace_dir, "ply")

    os.makedirs(dense_dir, exist_ok=True)

    set_progress(60, "Undistorting images...")
    pycolmap.undistort_images(dense_dir, sparse_dir, images_dir)

    set_progress(75, "PatchMatch stereo...")
    pycolmap.patch_match_stereo(dense_dir)

    set_progress(90, "Stereo fusion...")
    pycolmap.stereo_fusion(os.path.join(ply_dir, "dense.ply"), dense_dir)

    set_progress(100, "Dense reconstruction done")

# =========================
# CLOUD → MESH
# =========================
def cloud_to_mesh(workspace_dir):
    set_progress(10, "Loading point cloud...")
    ply_path = os.path.join(workspace_dir, "ply", "dense.ply")
    mesh_path = os.path.join(workspace_dir, "ply", "mesh.ply")

    pcd = o3d.io.read_point_cloud(ply_path)

    set_progress(30, "Estimating normals...")
    pcd.estimate_normals()

    set_progress(60, "Poisson meshing...")
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=9
    )

    set_progress(85, "Saving mesh...")
    mesh.compute_vertex_normals()
    o3d.io.write_triangle_mesh(mesh_path, mesh)

    set_progress(100, "Mesh ready!")
    o3d.visualization.draw_geometries([mesh])

# =========================
# GUI ACTIONS
# =========================
def run_full_pipeline():
    def worker():
        try:
            set_progress(0, "Starting pipeline...")
            sparse_reconstruction(out_path.get(), img_path.get())
            dense_reconstruction(out_path.get(), img_path.get())

            dense = o3d.io.read_point_cloud(os.path.join(out_path.get(), "ply/dense.ply"))
            o3d.visualization.draw_geometries([dense])
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
            set_progress(0, "Error")

    threading.Thread(target=worker).start()


def run_mesh_only():
    threading.Thread(target=lambda: cloud_to_mesh(out_path.get())).start()


def select_images():
    path = filedialog.askdirectory()
    if path:
        img_path.set(path)


def select_output():
    path = filedialog.askdirectory()
    if path:
        out_path.set(path)

# =========================
# GUI
# =========================
root = tk.Tk()
root.title("3D Reconstruction – Progress Demo")
root.geometry("520x360")

img_path = tk.StringVar()
out_path = tk.StringVar()

tk.Label(root, text="Folder ze zdjęciami").pack()
tk.Entry(root, textvariable=img_path, width=60).pack()
tk.Button(root, text="Wybierz", command=select_images).pack(pady=4)

tk.Label(root, text="Folder roboczy").pack()
tk.Entry(root, textvariable=out_path, width=60).pack()
tk.Button(root, text="Wybierz", command=select_output).pack(pady=4)

tk.Button(root, text="Zdjęcia → Cloud", bg="#4CAF50",
          fg="white", command=run_full_pipeline).pack(pady=6)

tk.Button(root, text="Cloud → Mesh", bg="#2196F3",
          fg="white", command=run_mesh_only).pack(pady=6)

progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Idle", fg="gray")
status_label.pack()

root.mainloop()
