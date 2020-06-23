from modules.yolo.src.yolo import Darknet
from modules.yolo.utils import parse_config, utils
from modules.sort.sort import Sort
from utils.detect import detect_image
from utils.change_coord import change_coord
from utils.visualization import visualization
from utils.k_means import pre_k_means
from utils.filter_court import PointList, onMouse, filter_court
import os, sys, time, datetime, random
sys.path.append(os.pardir)


import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torch.autograd import Variable
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn import datasets, preprocessing
from sklearn.cluster import KMeans
from PIL import Image
import cv2
from IPython.display import clear_output
import click


@click.command()
@click.option('--config_path', default='config/yolov3.cfg')
@click.option('--weights_path', default='weights/yolov3.weights')
@click.option('--class_path', default='data/coco.names')
@click.option('--img_size', default=416)
@click.option('--conf_thres', default=0.8)
@click.option('--nms_thres', default=0.4)
@click.option('--videopath', default='data/seiucchanvideo.mp4')
@click.option('--npoints', default=5)
@click.option('--wname', default='MouseEvent')
def main(config_path,
         weights_path,
         class_path,
         img_size,
         conf_thres,
         nms_thres,
         videopath,
         npoints,
         wname):

    # Load model and weights
    model = Darknet(config_path, img_size).to("cpu")
    if weights_path.endswith(".weights"):
        model.load_darknet_weights(weights_path)
    else:
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    # model.cuda()
    model.eval()
    classes = utils.load_classes(class_path)
    # Tensor = torch.cuda.FloatTensor
    Tensor = torch.Tensor

    vid = cv2.VideoCapture(videopath)
    ret, frame = vid.read()
    img = frame
    cv2.namedWindow(wname)
    ptlist = PointList(npoints)
    cv2.setMouseCallback(wname, onMouse, [wname, img, ptlist])
    cv2.waitKey()
    cv2.destroyAllWindows()
    mot_tracker = Sort()
    count_boxes = []

    while(True):
        for ii in range(4000):
            ret, frame = vid.read()
            print(0)

            if type(frame) == type(None):
                # print('ratio:', np.mean(count_boxes) / 10)
                sys.exit(0)
            pilimg = Image.fromarray(frame)
            detections = detect_image(pilimg, img_size, Tensor, model, conf_thres, nms_thres)

            if detections is not None:
                print(1)
                detections = filter_court(detections, pilimg, img_size, ptlist)
                tracked_objects = mot_tracker.update(detections.cpu())
                bbox_list_n = pre_k_means(tracked_objects, pilimg, img_size, img)

                if ii == 0:
                    print('fit')
                    # preds = KMeans(n_clusters=3).fit(bbox_list_n)
                    k_means = KMeans(n_clusters=3).fit(bbox_list_n)

                    preds = k_means.predict(bbox_list_n)

                else:
                    preds = k_means.predict(bbox_list_n)

                visualization(tracked_objects, pilimg, img_size, img, classes, frame, preds)

if __name__ == '__main__':
    main()
