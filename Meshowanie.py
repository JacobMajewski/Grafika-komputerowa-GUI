import open3d as o3d
import numpy as np
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def point_cloud_to_mesh_alpha_refined(input_file_path, output_file_path):
    if not os.path.exists(input_file_path):
        print(f"Błąd: Plik {input_file_path} nie istnieje.")
        return None

    print(f"Wczytywanie chmury: {input_file_path}")
    pcd = o3d.io.read_point_cloud(input_file_path)

    if not pcd.has_points():
        print("Błąd: Chmura jest pusta.")
        return None

    # 1. Czyszczenie danych
    pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=25, std_ratio=2.5)

    # 2. Rekonstrukcja Alpha Shapes
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    alpha = avg_dist * 6.0

    print(f"Rekonstrukcja Alpha Shapes (alpha={alpha:.4f})...")
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)

    # 3. Naprawa geometrii (Kluczowe dla widoczności)
    print("Optymalizacja siatki i normalnych...")
    mesh.remove_duplicated_vertices()
    mesh.remove_duplicated_triangles()
    mesh.remove_degenerate_triangles()

    # Obliczamy normalne na nowo, aby oświetlenie działało poprawnie
    mesh.compute_vertex_normals()

    # Usuwanie małych obiektów
    triangle_clusters, cluster_n_triangles, _ = mesh.cluster_connected_triangles()
    triangle_clusters = np.asarray(triangle_clusters)
    cluster_n_triangles = np.asarray(cluster_n_triangles)

    if len(cluster_n_triangles) > 0:
        largest_cluster_idx = cluster_n_triangles.argmax()
        mesh.remove_triangles_by_mask(triangle_clusters != largest_cluster_idx)

    # 4. Zapis
    print(f"Zapisywanie: {output_file_path}")
    o3d.io.write_triangle_mesh(output_file_path, mesh)

    return mesh

if __name__ == "__main__":
    # Rekonstrukcja w oparciu o Dense Cloud Point
    input_ply = os.path.join("output", "ply", "dense.ply")
    output_ply = os.path.join("output", "mesh", "dense_mesh_alpha.ply")

    os.makedirs(os.path.dirname(output_ply), exist_ok=True)

    final_mesh = point_cloud_to_mesh_alpha_refined(input_ply, output_ply)

    if final_mesh:
        print("Uruchamianie zaawansowanej wizualizacji...")

        # Tworzymy wizualizator, który automatycznie ustawi kamerę na obiekt
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name="Wynik Rekonstrukcji", width=1280, height=720)

        # Dodajemy mesh
        vis.add_geometry(final_mesh)

        # Opcje renderowania - pokaż obie strony ścian i popraw oświetlenie
        opt = vis.get_render_option()
        opt.mesh_show_back_face = True
        opt.background_color = np.asarray([0.2, 0.2, 0.2]) # Ciemnoszare tło zamiast

        # Reset kamery, aby objęła cały model
        vis.reset_view_point(True)
        vis.run()
        vis.destroy_window()