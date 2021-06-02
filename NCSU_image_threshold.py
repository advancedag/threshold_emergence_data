#NCSU Image Threshold for Plant Height Measurement
import cv2 
import numpy as np
from sklearn import cluster
import time
import glob 
image_names = sorted(glob.glob("pictures/*.JPG"))
images = [cv2.imread(file) for file in image_names]

IS_MANUAL = False
## CHANGE THIS TO TRUE TO SET VALUES MANUALLY
#Note: manual mode can take a long time to load

AUTO_PROCESS = True
#CHANGE THIS TO TRUE TO AUTOMATICALLY PROCESS ALL IMAGES 

def nothing(ignore):
    pass

# Function that handles the mouseclicks
def process_click(event, x, y,flags, params):
    # check if the click is within the dimensions of the button
    global is_set
    if event == cv2.EVENT_LBUTTONDOWN:
        if y > button[0] and y < button[1] and x > button[2] and x < button[3]:   
            # print('Clicked on Button!')
            is_set = True

#default thresholds
lower_HSV = np.array([20,100,50])
upper_HSV = np.array([80, 250, 200])

# button dimensions (y1,y2,x1,x2)
button = [20,60,50,375]
is_set = False

if IS_MANUAL:
    #create trackbars to use to adjust hsv values of mask
    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("Lower Hue", "Trackbars", 0, 179, nothing)
    cv2.createTrackbar("Lower Saturation", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("Lower Light", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("Upper Hue", "Trackbars", 0, 179, nothing)
    cv2.createTrackbar("Upper Saturation", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("Upper Light", "Trackbars", 0, 255, nothing)
    cv2.setMouseCallback('Trackbars', process_click)

    #create button image
    control_image = np.zeros((80,400), np.uint8)
    control_image[button[0]:button[1],button[2]:button[3]] = 180
    cv2.putText(control_image, 'Click to Save',(100,50),cv2.FONT_HERSHEY_COMPLEX, 1,(0),2)
    cv2.imshow('Trackbars', control_image)

    while is_set != True: 
        #get values from trackbars
        l_h = cv2.getTrackbarPos("Lower Hue", "Trackbars")
        l_s = cv2.getTrackbarPos("Lower Saturation", "Trackbars")
        l_v = cv2.getTrackbarPos("Lower Light", "Trackbars")
        u_h = cv2.getTrackbarPos("Upper Hue", "Trackbars")
        u_s = cv2.getTrackbarPos("Upper Saturation", "Trackbars")
        u_v = cv2.getTrackbarPos("Upper Light", "Trackbars")

        #set mask of image based on trackbar values, using HSV (Hue, Saturation, Lightness)
        hsv = cv2.cvtColor(images[0], cv2.COLOR_BGR2HSV)
        lower_HSV = np.array([l_h,l_s,l_v])
        upper_HSV = np.array([u_h, u_s, u_v])
        HSV_mask = cv2.inRange(hsv, lower_HSV, upper_HSV)

        #show seperate window with the values from trackbars
        cv2.namedWindow("Values")
        text_image = np.zeros((50, 600,3), np.uint8)
        cv2.imshow("masked", HSV_mask)
        text = "Hue: " + str(l_h) + " - " + str(u_h) + "  Sat: " + str(l_s) + " - " + str(u_s) + "  Light(V): " + str(l_v) + " - " + str(u_v)
        cv2.putText(text_image, text, (10,40), cv2.FONT_HERSHEY_COMPLEX, 0.6,(255,255,255),1)
        cv2.imshow('Values', text_image)

        key = cv2.waitKey(1)
        if key == 27:
            break

cv2.destroyAllWindows()

# Function that handles clicking on the image
clicked = False
def process_image_click(event, x, y,flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        global clicked
        clicked = True
        # print("cclicked")
        for data in data_array:
            # print(x, y)
            if (abs(data[0] - y)) < 20 and (abs(data[2] - x)) < 20:
                # print("Data to remove", data)
                data_array.remove([data[0], data[1], data[2]])
                return
                
            
        data_array.append([y, y, x])
        # print("Data to add", [y, y, x])

def sort_in_rows(keypoints_to_search):
    #Sort the array of data from upper left to bottom right
    points = []
    while len(keypoints_to_search) > 1:
        # Find the top left point: min(x+y)
        a = sorted(keypoints_to_search, key=lambda p: (p[2]) + (p[0]))[0]
        # Find the top right point: max(x-y)
        b = sorted(keypoints_to_search, key=lambda p: (p[2]) - (p[0]))[-1] 
        # Create a straight line from the points.
        if not (b[2] - a[2]) == 0: m = (b[0]- a[0])/(b[2] - a[2])
        else: m = (b[0]- a[0])
        intercept = b[0] - m*b[2]
        end_value = m*width + intercept
        cv2.line(original_img, (int(0), int(intercept)), (int(width), int(end_value)), (255, 0, 0), 1)

        # convert opencv keypoint to numpy 3d point
        a = np.array([0, intercept, 0])
        b = np.array([width, end_value, 0])
        row_points = []
        remaining_points = []
        for k in keypoints_to_search:
            p = np.array([k[2], k[0], 0])
            d = 200  # diameter of the keypoint (might be a threshold)
            # Calculate the distance of all points to the line
            dist = np.linalg.norm(np.cross(np.subtract(p, a), np.subtract(b, a))) / np.linalg.norm(b)   # distance between keypoint and line a->b
            # If it is smaller than the radius of the circle (or a threshold): point is in the top line.
            if d/2 > dist:
                row_points.append(k)
            # Otherwise: point is in the rest of the block.
            else:
                remaining_points.append(k)
        # Sort points of the top line by x value and save.
        points.extend(sorted(row_points, key=lambda h: h[2]))
        # Repeat until there are no points left.
        keypoints_to_search = remaining_points
    return points

print("Click on image to add or remove plant.")
print("Press enter to go to next image.")
print("Click delete to skip.")

img_num = 0
processed = False
while img_num < len(image_names) - 1:

    original_img = images[img_num].copy()
    height, width, channels = original_img.shape

    if not processed:

        #set default mask or use values from manual mode
        hsv = cv2.cvtColor(original_img, cv2.COLOR_BGR2HSV)
        HSV_mask = cv2.inRange(hsv, lower_HSV, upper_HSV)

        #HSV_mask is an array of either 0s or 255s
        #threshold pixels is an array of the indexes of the points that are white (255)
        threshold_pixels = []
        for x in range(len(HSV_mask)):
                for y in range(len(HSV_mask[0])):
                    if HSV_mask[x][y] == 255:
                        #elements in threshold pixels are in the format [x pixel, y pixel]
                        threshold_pixels.append([x, y])


        clustering = cluster.DBSCAN(eps=3, min_samples=2).fit(threshold_pixels)
        #https://github.com/scikit-learn/scikit-learn/blob/15a949460/sklearn/cluster/_dbscan.py#L148

        #creates array of each cluster's height max, height min, and horizontal center
        data_array = []
        for a in range(np.amax(clustering.labels_)):
            max_value = 0     #default values
            min_value = 100000000
            box_center = 0
            for j in range(len(threshold_pixels)):
                if clustering.labels_[j] == a:
                    if threshold_pixels[j][1] > max_value:
                        max_value = threshold_pixels[j][0]
                    if threshold_pixels[j][1] < min_value:
                        min_value = threshold_pixels[j][0]
                        box_center = threshold_pixels[j][1]
            data_array.append([max_value, min_value, box_center])
        processed = True

    sorted_clusters = sort_in_rows(data_array)
    sorted_clusters = np.array(sorted_clusters)
    height_array = [abs(a[0]-a[1]) for a in sorted_clusters]
    spacing_array = [sorted_clusters[i+1][2]-sorted_clusters[i][2] for i in range(len(sorted_clusters)-1)]
    
    
    for i in range(len(sorted_clusters)):
        #draw squares around each cluster and label with index
        height = abs(sorted_clusters[i][0]-sorted_clusters[i][1])
        img = cv2.rectangle(original_img, (sorted_clusters[i][2] - int(height/2), sorted_clusters[i][0]), (sorted_clusters[i][2] + int(height/2), sorted_clusters[i][1]), (0, 0, 255), thickness=2)
        cv2.putText(img, str(i), (sorted_clusters[i][2], sorted_clusters[i][0] + 40), 0, 1, (0, 0, 255), thickness= 2) # lineType=None, bottomLeftOrigin=None)

    #[Optional] save pictures
    # filename = str(image_names[i])
    # cv2.imwrite("example_image.JPG", img)

    #iterate to next image and reset click 
    img_num = img_num + 1
    clicked = False

    if AUTO_PROCESS:
        print(image_names[img_num])
        print("Heights: " + str(height_array))
        print("Average Height: " + str(int(np.average(height_array))))
        print("Spacing: " + str(spacing_array))
        print("Average Spacing: " + str(int(np.average(spacing_array))))
        processed = False
        continue

    while True:
        cv2.imshow("original", img)
        cv2.setMouseCallback('original', process_image_click)
        key = cv2.waitKey(1)


        #If user clicks on screen, rerun analysis on same picture
        if clicked:
            cv2.destroyAllWindows()
            img_num = img_num - 1
            break
        
        #If user presses delete, move to next image without printing
        if key == 127:
            processed = False
            cv2.destroyAllWindows()
            break

        #If user presses enter, print results and move to next image
        if key == 13:
            print(image_names[img_num])
            print("Heights: " + str(height_array))
            print("Average Height: " + str(int(np.average(height_array))))
            print("Spacing: " + str(spacing_array))
            print("Average Spacing: " + str(int(np.average(spacing_array))))
            processed = False
            cv2.destroyAllWindows()
            break
print("Done!")

