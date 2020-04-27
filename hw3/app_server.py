import os
import cv2
import face_recognition
import numpy as np
from flask import Flask, flash, request, redirect, url_for, \
    send_from_directory, render_template
from werkzeug.utils import secure_filename
from face_swap import read_points, apply_affine_transform, rect_contains, \
    calculate_delaunay_triangles, warp_triangle

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def face_swap(filename2):
    (major_ver, minor_ver, subminor_ver) = cv2.__version__.split('.')

    filename1 = 'putin.jpeg'

    img1 = cv2.imread(filename1)
    img2 = cv2.imread(filename2)
    img1_warped = np.copy(img2)

    points1 = read_points(face_recognition.face_landmarks(img1)[0])
    points2 = read_points(face_recognition.face_landmarks(img2)[0])

    # Find convex hull
    hull1 = []
    hull2 = []

    hull_index = cv2.convexHull(np.array(points2), returnPoints=False)

    for i in range(0, len(hull_index)):
        hull1.append(points1[int(hull_index[i])])
        hull2.append(points2[int(hull_index[i])])

    size_img2 = img2.shape
    rect = (0, 0, size_img2[1], size_img2[0])

    dt = calculate_delaunay_triangles(rect, hull2)

    if len(dt) == 0:
        quit()

    for i in range(0, len(dt)):
        t1 = []
        t2 = []

        for j in range(0, 3):
            t1.append(hull1[dt[i][j]])
            t2.append(hull2[dt[i][j]])

        warp_triangle(img1, img1_warped, t1, t2)

    hull8U = []
    for i in range(0, len(hull2)):
        hull8U.append((hull2[i][0], hull2[i][1]))

    mask = np.zeros(img2.shape, dtype=img2.dtype)

    cv2.fillConvexPoly(mask, np.int32(hull8U), (255, 255, 255))

    r = cv2.boundingRect(np.float32([hull2]))

    center = (r[0] + int(r[2] / 2), r[1] + int(r[3] / 2))

    output = cv2.seamlessClone(np.uint8(img1_warped), img2, mask, center, cv2.NORMAL_CLONE)

    return output


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            changed_filename = "changed_" + filename
            changed_path = os.path.join(app.config['UPLOAD_FOLDER'], changed_filename)
            changed_img = face_swap(path)
            cv2.imwrite(changed_path, changed_img)
            # file.save(changed_path)
            # img = cv2.imread(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], ("changed_" + filename)), img)
            return redirect(url_for('uploaded_file', original=filename, changed=changed_filename))
    return render_template("base.html")


@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/show_images')
def uploaded_file():
    url = 'http://127.0.0.1:5000/uploads/'
    # it doesn't work with using explicit parameters, so here comes request
    img_original = url + request.args.get('original')
    img_changed = url + request.args.get('changed')
    return render_template('images.html', image1=img_original, image2=img_changed)


if __name__ == "__main__":
    app.run(debug=True)
