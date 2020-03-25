import numpy as np
import cv2


imgA = cv2.imread('image.jpg')

imgx2 = cv2.resize(imgA, None, fx=1/2, fy=1/2, interpolation=cv2.INTER_CUBIC)
imgx4 = cv2.resize(imgA, None, fx=1/4, fy=1/4, interpolation=cv2.INTER_CUBIC)


img2d = cv2.Canny(imgx2, 50, 400)
imgB = cv2.cvtColor(img2d, cv2.COLOR_GRAY2BGR)

imgC = cv2.blur(imgx4, (5, 5))

imgD = cv2.GaussianBlur(imgx4, (7,7), 0)

kernel = np.random.randint(-5, 10, (5, 5))/25
imgE = cv2.filter2D(imgx4, -1, kernel)

imgF = np.random.randint(100, 250, imgx4.shape)

row1 = np.concatenate((imgE, imgF), axis=1)
row2 = np.concatenate((imgC, imgD), axis=1)
row3 = np.concatenate((row2, row1), axis=0)
row4 = np.concatenate((imgB, row3), axis=0)
res = np.concatenate((imgA, row4), axis=1)

cv2.imwrite('res.jpg', res)