import pycolmap
import os
import open3d as o3d

images_dir="images" #Zdjęcia
workspace_dir="output"

#Rzadka rekonstrukcja
def sparse_reconstruction(workspace_dir,images_dir):
    database_dir=workspace_dir+"/database.db"
    sparse_dir=workspace_dir+"/sparse"
    ply_dir=workspace_dir+"/ply"
    os.makedirs(workspace_dir, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(ply_dir,exist_ok=True)
    pycolmap.extract_features(database_path=database_dir,image_path=images_dir)
    pycolmap.match_exhaustive(database_path=database_dir)
    maps=pycolmap.incremental_mapping(database_path=database_dir,image_path=images_dir,output_path=sparse_dir)
    maps[0].write(sparse_dir)
    reconstruction = pycolmap.Reconstruction(sparse_dir)
    reconstruction.export_PLY(ply_dir+"/sparse.ply")

#Gesta rekonstrukcja(Wymaga CUDA i zainstalowania pycolmapa recznie)
def dense_reconstruction(workspace_dir,images_dir):
    sparse_dir=workspace_dir+"/sparse"
    ply_dir = workspace_dir + "/ply"
    dense_dir = workspace_dir+"/dense"
    os.makedirs(dense_dir, exist_ok=True)
    undistorted_ops=pycolmap.UndistortCameraOptions(max_image_size=1500)
    patch_match_ops=pycolmap.PatchMatchOptions(cache_size=48,max_image_size=1500)
    pycolmap.undistort_images(dense_dir, sparse_dir, images_dir,undistort_options=undistorted_ops)
    pycolmap.patch_match_stereo(dense_dir,options=patch_match_ops)
    pycolmap.stereo_fusion(ply_dir + "/dense.ply", dense_dir)


sparse_reconstruction(workspace_dir,images_dir)
dense_reconstruction(workspace_dir,images_dir)

#Odczyt
pcd1 = o3d.io.read_point_cloud(workspace_dir + "/ply/sparse.ply")
pcd2 = o3d.io.read_point_cloud(workspace_dir + "/ply/dense.ply")

pcd2.translate((1.0, 0, 0))

o3d.visualization.draw_geometries([pcd1, pcd2])