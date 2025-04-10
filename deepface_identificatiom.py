import cv2
import os
from deepface import DeepFace
def get_user_id(face_roi):
    try:
        # Set a flag to control the flow and prevent continuing the loop until DeepFace result is ready
        result = DeepFace.find(img_path=face_roi, db_path='dataset/', enforce_detection=False, align=True)
        print(result)
        if result is not None:
        # Find the best match in the results
            best_match = None
            min_distance = float('inf')

            if isinstance(result, list) and len(result) > 0:
                for res in result:
                    if not res.empty:
                        # Filter results with distances less than 0.6
                        filtered_results = res[res['distance'] < 0.48]
                        # threeshold=res['threshold']
                        # print(threeshold)
                        if not filtered_results.empty:
                            # Find the image with the smallest distance
                            closest_match = filtered_results.loc[filtered_results['distance'].idxmin()]
                            if closest_match['distance'] < min_distance:
                                min_distance = closest_match['distance']
                                best_match = closest_match

        if best_match is not None:
            # Extract and print the best match's file name
            matched_file = os.path.basename(best_match['identity']).split('.')[1]
            print(f"Best Match: {matched_file}, Distance: {best_match['distance']}")
            return matched_file
        else:
            print("No Match Found")
            return None
    except Exception as e:
        print(f"Error during DeepFace matching: {e}")