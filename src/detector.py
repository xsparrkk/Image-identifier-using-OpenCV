import os
import cv2
import numpy as np


class ReferenceObject:
    """Holds metadata and feature descriptors for a single reference object."""

    def __init__(self, name: str, image_path: str, detector):
        self.name = name
        self.path = image_path
        self.img = cv2.imread(image_path)
        if self.img is None:
            raise FileNotFoundError(f"Could not load image at {image_path}")

        self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        self.h, self.w = self.gray.shape
        self.kp, self.des = detector.detectAndCompute(self.gray, None)


class MultiObjectVerifier:
    """Detects and tracks multiple reference objects in a live video feed."""

    def __init__(self, reference_dir: str = "reference_images", min_match_count: int = 15, method: str = "SIFT"):
        self.min_match_count = min_match_count
        self.method = method.upper()

        if self.method == "SIFT":
            self.detector = cv2.SIFT_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_L2)
        elif self.method == "ORB":
            self.detector = cv2.ORB_create(nfeatures=1000)
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        else:
            raise ValueError("Unsupported method. Use 'SIFT' or 'ORB'.")

        self.ref_objects = []
        self._load_reference_images(reference_dir)

    def _load_reference_images(self, reference_dir: str):
        if not os.path.exists(reference_dir):
            os.makedirs(reference_dir)
            raise FileNotFoundError(f"Created '{reference_dir}' folder. Please place reference images inside it.")

        valid_exts = (".png", ".jpg", ".jpeg", ".bmp", ".webp")
        for file in os.listdir(reference_dir):
            if file.lower().endswith(valid_exts):
                full_path = os.path.join(reference_dir, file)
                obj_name = os.path.splitext(file)[0].capitalize()
                try:
                    ref_obj = ReferenceObject(obj_name, full_path, self.detector)
                    if ref_obj.des is not None and len(ref_obj.kp) >= self.min_match_count:
                        self.ref_objects.append(ref_obj)
                        print(f"Loaded reference object: '{obj_name}' ({len(ref_obj.kp)} features)")
                    else:
                        print(f"Skipping '{file}': Not enough feature points found.")
                except Exception as e:
                    print(f"Error loading '{file}': {e}")

        if not self.ref_objects:
            raise ValueError(f"No valid reference images found in '{reference_dir}'.")

    @staticmethod
    def get_dynamic_color(match_ratio: float):
        """Generates a BGR color gradient transitioning from Red (0%) -> Yellow (50%) -> Green (100%)."""
        ratio = np.clip(match_ratio, 0.0, 1.0)
        if ratio <= 0.5:
            green = int(255 * (ratio * 2))
            red = 255
        else:
            green = 255
            red = int(255 * (2 * (1.0 - ratio)))
        return (0, green, red)

    @staticmethod
    def is_valid_polygon(pts, frame_shape):
        """Validates if projected points form a convex, non-collapsed 4-sided polygon."""
        if not cv2.isContourConvex(pts):
            return False

        area = cv2.contourArea(pts)
        frame_area = frame_shape[0] * frame_shape[1]
        if area < 1000 or area > (frame_area * 0.95):
            return False

        return True

    def verify_frame(self, frame: np.ndarray):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Extract features from current camera frame ONCE for efficiency
        kp_frame, des_frame = self.detector.detectAndCompute(frame_gray, None)

        detections = []
        best_match_pct = 0.0

        if des_frame is not None and len(des_frame) >= 2:
            # Check frame features against EVERY reference object
            for ref_obj in self.ref_objects:
                matches = self.matcher.knnMatch(ref_obj.des, des_frame, k=2)

                good_matches = []
                for match in matches:
                    if len(match) == 2:
                        m, n = match
                        if m.distance < 0.70 * n.distance:
                            good_matches.append(m)

                if len(good_matches) >= self.min_match_count:
                    src_pts = np.float32([ref_obj.kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                    if M is not None and mask is not None:
                        inlier_count = int(np.sum(mask))

                        if inlier_count >= self.min_match_count:
                            pts = np.float32([[0, 0], [0, ref_obj.h - 1], [ref_obj.w - 1, ref_obj.h - 1], [ref_obj.w - 1, 0]]).reshape(-1, 1, 2)
                            dst = cv2.perspectiveTransform(pts, M)
                            dst_int = np.int32(dst)

                            if self.is_valid_polygon(dst_int, frame.shape):
                                polygon_area = cv2.contourArea(dst_int)
                                frame_area = frame.shape[0] * frame.shape[1]
                                coverage_pct = min(100.0, (polygon_area / frame_area) * 100.0)

                                target_inliers = min(len(ref_obj.kp), 60)
                                match_pct = min(100.0, (inlier_count / target_inliers) * 100.0)
                                dynamic_color = self.get_dynamic_color(match_pct / 100.0)

                                if match_pct > best_match_pct:
                                    best_match_pct = match_pct

                                # Draw bounding box around detected object
                                cv2.polylines(frame, [dst_int], True, dynamic_color, 3, cv2.LINE_AA)

                                # Draw object label badge over polygon
                                label_x, label_y = dst_int[0][0][0], dst_int[0][0][1] - 10
                                label_text = f"{ref_obj.name} ({match_pct:.0f}%)"
                                cv2.putText(frame, label_text, (max(10, label_x), max(20, label_y)),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, dynamic_color, 2)

                                detections.append({
                                    "name": ref_obj.name,
                                    "inliers": inlier_count,
                                    "match_pct": match_pct,
                                    "coverage_pct": coverage_pct,
                                    "color": dynamic_color
                                })

        overall_color = self.get_dynamic_color(best_match_pct / 100.0)
        return frame, detections, best_match_pct, overall_color