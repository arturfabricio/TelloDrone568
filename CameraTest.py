import cv2.cv2 as cv2
import threading
import imutils
from imutils.video import VideoStream

class Stitcher:
    def __init__(self):
        # Determine the version of opencv we are using, and initialize the homography matrix.
        self.isv3 = imutils.is_cv3()
        self.cachedH = None

    def stitch(self, images, ratio=0.75, reprojThresh=4.0):
        #Unpacking images:
        (imageB, imageA) = images
        if self.cachedH is None:
            #If the homography matrix is None, we need to apply keypoint matching for contructing.
            (kpsA, featuresA) = self.detectAndDescribe(imageA)
            (kpsB, featuresB) = self.detectAndDescribe(imageB)

            #Match features between two images
            M = self.matchKeypoints(kpsA, kpsB,
			featuresA, featuresB, ratio, reprojThresh)

            if M is None:
                return None

            self.cachedH = M[1]
        result = cv2.warpPerspective(imageA, self.cachedH, (imageA.shape[1] + imageB.shape[1], imageA.shape[0]))
        result[0:imageB.shape[0], 0:imageB.shape[1]] = imageB
        return result


class camThread(threading.Thread):
    def __init__(self, previewName, camID):
        threading.Thread.__init__(self)
        self.previewName = previewName
        self.camID = camID
    def run(self):
        print("Starting " + self.previewName)
        camPreview(self.previewName, self.camID)

def camPreview(previewName, camID):
    cv2.namedWindow(previewName)
    cam = cv2.VideoCapture(camID, cv2.CAP_DSHOW)
    if cam.isOpened():  # try to get the first frame
        rval, frame = cam.read()
    else:
        rval = False

    while rval:
        cv2.imshow(previewName, frame)
        rval, frame = cam.read()
        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break
    cv2.destroyWindow(previewName)

# Create two threads as follows
thread1 = camThread("Camera 1", 2)
thread2 = camThread("Camera 2", 1)
thread1.start()
thread2.start()