


"""
python run_webcam_example.py --use_region -b obj_000014 -m <path/to/obj/dir>
"""

import cv2
import time
import argparse
import numpy as np
import quaternion

from single_view_tracker import setup_single_object_tracker, ExecuteTrackingStepSingleObject

def parse_script_input():
    parser = argparse.ArgumentParser(
        prog='run_webcam_example',
        description='Run the m3t tracker from webcam video stream'
    )

    parser.add_argument('-b', '--body_name',  dest='body_name',  type=str, required=True, help='Name of the object to track. need to match')
    parser.add_argument('-m', '--models_dir', dest='models_dir', type=str, required=True, help='Path to directory where object model file {body_name}.obj is stored')
    parser.add_argument('--fov',              dest='fov', type=float, default=50.0, help='Approximate horizontal field of view of the webcam in degrees')
    parser.add_argument('--scale_geometry',   dest='scale_geometry', default=0.001, type=float, required=False, help='Scale factor to convert model geometry to meters.')
    parser.add_argument('--tmp_dir',          dest='tmp_dir',    type=str, default='tmp', help='Directory to store preprocessing files generated by the tracker.')
    parser.add_argument('--use_region',       dest='use_region', action='store_true', default=False)

    return parser.parse_args()

args = parse_script_input()

# revover one image to get the camera resolution
vid = cv2.VideoCapture(0) 
ret, frame = vid.read()
height, width, _ = frame.shape

# Idea from https://learnopencv.com/approximate-focal-length-for-webcams-and-cell-phone-cameras/
f_approx = (width/2)/np.tan(np.deg2rad(args.fov)/2)
intrinsics_approx = {
    'fu': f_approx,
	'fv': f_approx,
	'ppu': width/2,
	'ppv': height/2,
	'width': width,
	'height': height,
}

cam_intrinsics = {
	'intrinsics_color': intrinsics_approx,
	'quat_d_c_xyzw': [0,0,0,1],
    'trans_d_c': [0,0,0],
}

# Setup tracker and all related objects
tracker, optimizer, body, link, color_camera, color_viewer = setup_single_object_tracker(args, cam_intrinsics)

#----------------
# Initialize object pose
body2world_pose = np.array([ 1, 0,  0, 0,
                             0, 0, -1, 0,
                             0, 1,  0, 0.456,
                             0, 0,  0, 1 ]).reshape((4,4))
dR_l = quaternion.as_rotation_matrix(quaternion.from_rotation_vector([0.2,0,0.0]))
body2world_pose[:3,:3] = body2world_pose[:3,:3] @ dR_l
#----------------

#----------------------
# TODO: tweak tikhonov regularization to observe effect on tracking stability 
scale_t = 1
scale_r = 1
optimizer.tikhonov_parameter_translation *= scale_t
optimizer.tikhonov_parameter_rotation *= scale_r
optimizer.SetUp()
#----------------------

first = True
tracking = False
i = 0
print('\n------\nPress q to quit during execution')
print('Press d to reset object pose (and stop tracking)')
print('Press x to start tracking')
while True: 
	ret, frame = vid.read()
	color_camera.image = frame
	ok = tracker.UpdateCameras(True)  # poststep verifying the images have been properly setup
	if not ok:
		raise ValueError('Something is wrong with the provided images')
      
	k = cv2.waitKey(1)
	if first or k == ord('d'):
		body.body2world_pose = body2world_pose  # simulate external initial pose
		first = False
		tracking = False
	if k == ord('x'):
		tracking = True
		print('StartTracking')
	if k == ord('q'):
		break
	if tracking:
		t = time.time()
		#----------------------
		# TODO: uncomment/comment to replace by simplified implementation 
		tracker.ExecuteTrackingStep(i)
		# ExecuteTrackingStepSingleObject(tracker, link, body, i, optimizer.tikhonov_parameter_translation, optimizer.tikhonov_parameter_rotation)
		print('ExecuteTrackingCycle (ms)', 1000*(time.time() - t))
		print('body.body2world_pose\n',body.body2world_pose)
		#----------------------

	i += 1
	color_viewer.UpdateViewer(i)

vid.release() 
cv2.destroyAllWindows() 
