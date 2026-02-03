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

def show_sparse(workspace_dir):
    ply_path = os.path.join(workspace_dir, "ply", "sparse.ply")
    pcd = o3d.io.read_point_cloud(ply_path)
    o3d.visualization.draw_geometries([pcd])import tkinter as tk
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
    undistorted_ops = pycolmap.UndistortCameraOptions(max_image_size=1500)
    patch_match_ops = pycolmap.PatchMatchOptions(cache_size=48, max_image_size=1500)

    os.makedirs(dense_dir, exist_ok=True)

    set_progress(60, "Undistorting images...")
    pycolmap.undistort_images(dense_dir, sparse_dir, images_dir,undistort_options=undistorted_ops)

    set_progress(75, "PatchMatch stereo...")
    pycolmap.patch_match_stereo(dense_dir,options=patch_match_ops)

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

def transfer_colors(pcd, mesh):
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)

    mesh_colors = []
    for v in mesh.vertices:
        _, idx, _ = pcd_tree.search_knn_vector_3d(v, 1)
        mesh_colors.append(pcd.colors[idx[0]])

    mesh.vertex_colors = o3d.utility.Vector3dVector(mesh_colors)


def cloud_to_mesh2(workspace_dir):
    set_progress(10, "Loading point cloud...")
    ply_path = os.path.join(workspace_dir, "ply", "dense.ply")
    mesh_path = os.path.join(workspace_dir, "ply", "mesh_colored.ply")

    pcd = o3d.io.read_point_cloud(ply_path)

    set_progress(30, "Estimating normals...")
    pcd.estimate_normals()

    set_progress(60, "Poisson meshing...")
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=11,linear_fit=True)
    mesh.compute_vertex_normals()
    set_progress(85, "Saving mesh...")
    o3d.io.write_triangle_mesh(
        mesh_path,
        mesh,
        write_vertex_colors=True
    )
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



def show_sparse(workspace_dir):
    ply_path = os.path.join(workspace_dir, "ply", "sparse.ply")
    pcd = o3d.io.read_point_cloud(ply_path)
    o3d.visualization.draw_geometries([pcd])

def show_dense(workspace_dir):
    ply_path = os.path.join(workspace_dir, "ply", "dense.ply")
    pcd = o3d.io.read_point_cloud(ply_path)
    o3d.visualization.draw_geometries([pcd])

def show_mesh(workspace_dir):
    mesh_path = os.path.join(workspace_dir, "ply", "mesh_colored.ply")
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    mesh.compute_vertex_normals()
    o3d.visualization.draw_geometries([mesh])
def save_mesh_and_color():
    threading.Thread(target=lambda: cloud_to_mesh2(out_path.get())).start()

def run_mesh_only():
    threading.Thread(target=lambda: cloud_to_mesh(out_path.get())).start()

def show_ply_sparse():
    threading.Thread(target=lambda: show_sparse(out_path.get())).start()
def show_ply_dense():
    threading.Thread(target=lambda: show_dense(out_path.get())).start()

def show_mesh_color():
    threading.Thread(target=lambda: show_mesh(out_path.get())).start()

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
root.geometry("640x480")
button_frame=tk.Frame(root)


img_path = tk.StringVar()
out_path = tk.StringVar()

tk.Label(root, text="Folder ze zdjęciami").pack()
tk.Entry(root, textvariable=img_path, width=60).pack()
tk.Button(root, text="Wybierz", command=select_images).pack(pady=4)

tk.Label(root, text="Folder roboczy").pack()
tk.Entry(root, textvariable=out_path, width=60).pack()
tk.Button(root, text="Wybierz", command=select_output).pack(pady=4)

button_frame.pack(pady=10)
tk.Button(button_frame, text="Zdjęcia → Cloud", bg="#4CAF50",
          fg="white", command=run_full_pipeline,width=20).grid(row=0, column=0, padx=5,pady=5)

tk.Button(button_frame, text="Cloud → Mesh", bg="#2196F3",
          fg="white", command=run_mesh_only,width=20).grid(row=0, column=1, padx=5,pady=5)
tk.Button(button_frame, text="Cloud → Mesh+Kolor", bg="#2196F3",
          fg="white", command=save_mesh_and_color,width=20).grid(row=0, column=2, padx=5,pady=5)
tk.Button(button_frame, text="Pokaz rzadka chmure", bg="#2196F3",
          fg="white", command=show_ply_sparse,width=20).grid(row=1, column=0, padx=5,pady=5)
tk.Button(button_frame, text="Pokaz gesta chmure", bg="#2196F3",
          fg="white", command=show_ply_dense,width=20).grid(row=1, column=1, padx=5,pady=5)
tk.Button(button_frame, text="Pokaz mesh", bg="#2196F3",
          fg="white", command=show_mesh_color,width=20).grid(row=1, column=2, padx=5,pady=5)


progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Idle", fg="gray")
status_label.pack()

root.mainloop()


def show_dense(workspace_dir):
    ply_path = os.path.join(workspace_dir, "ply", "dense.ply")
    pcd = o3d.io.read_point_cloud(ply_path)
    o3d.visualization.draw_geometries([pcd])


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

def show_ply_sparse():
    threading.Thread(target=lambda: show_sparse(out_path.get())).start()
def show_ply_dense():
    threading.Thread(target=lambda: show_dense(out_path.get())).start()

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
tk.Button(root, text="Pokaz rzadka chmure", bg="#2196F3",
          fg="white", command=show_ply_sparse).pack(pady=6)
tk.Button(root, text="Pokaz gesta chmure", bg="#2196F3",
          fg="white", command=show_ply_dense).pack(pady=6)

progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.pack(pady=10)

status_label = tk.Label(root, text="Idle", fg="gray")
status_label.pack()

root.mainloop()
