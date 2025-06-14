from flask import Flask, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import uuid
import os

app = Flask(__name__)
mp_face_mesh = mp.solutions.face_mesh

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        print("❌ No image file in request.")
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if file.filename == '':
        print("❌ Image file has an empty filename.")
        return jsonify({"error": "Empty filename"}), 400

    temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
    file.save(temp_filename)
    print(f"📸 Received image: {file.filename}, saved as: {temp_filename}")

    try:
        image = cv2.imread(temp_filename)
        if image is None:
            print("❌ Failed to read image using OpenCV.")
            return jsonify({"error": "Invalid image file"}), 400

        h, w = image.shape[:2]

        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1,refine_landmarks=True) as face_mesh:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_image)

            if not results.multi_face_landmarks:
                print("❌ No face landmarks detected.")
                return jsonify({"error": "No face detected"}), 422

            landmarks = results.multi_face_landmarks[0].landmark

            if len(landmarks) <= 473:
                print("❌ Incomplete landmarks: Less than 474 points.")
                return jsonify({"error": "Incomplete facial landmarks detected"}), 422

            # Pupillary distance (between landmark 468 and 473)
            left = np.array([landmarks[468].x * w, landmarks[468].y * h])
            right = np.array([landmarks[473].x * w, landmarks[473].y * h])
            dp = np.linalg.norm(right - left)

            # Pupil height (from eye center to top of face)
            eye_center = (left + right) / 2
            top_of_face = np.array([landmarks[10].x * w, landmarks[10].y * h])
            height = np.linalg.norm(eye_center - top_of_face)

            # Placeholder face shape estimation
            face_shape = "Oval"

            print(f"✅ Face processed. DP: {dp:.1f} mm, AP: {height:.1f} mm")

            return jsonify({
                "Distância Pupilar (DP)": f"{dp:.1f} mm",
                "Altura Pupilar (AP)": f"{height:.1f} mm",
                "Distância Naso-Pupilar (DPN)": {
                    "Olho Esquerdo": f"{dp/2:.1f} mm",
                    "Olho Direito": f"{dp/2:.1f} mm"
                },
                "Formato do Rosto": face_shape,
                "Mensagem": "Estas medidas foram calculadas usando tecnologia de visão computacional. Para confirmação, recomendamos consulta com um profissional."
            })

    except Exception as e:
        print(f"🔥 Error during image processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print(f"🧹 Temporary file deleted: {temp_filename}")

if __name__ == '__main__':
    app.run(port=5000, debug=True)
