# Pretty sure I can just download these files from their gh repo and this script is pointless,
# but I didnt know until I did this so I'm keeping it here for now

import open3d as o3d

# Load a PLY point cloud dataset
dataset = o3d.data.EaglePointCloud()

# Read the point cloud
pcd = o3d.io.read_point_cloud(dataset.path)

# Save the point cloud to a local file
o3d.io.write_point_cloud("eagle.ply", pcd)
