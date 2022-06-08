import os
import cv2
from zeno import ZenoOptions, preprocess
import numpy as np


def get_imgs(df, ops: ZenoOptions):
    ret = []
    for img in df.index:
        im = cv2.imread(os.path.join(ops.data_path, img))
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = cv2.resize(im, (224, 224))
        ret.append(im)
    return ret


@preprocess
def area(df, ops: ZenoOptions):
    ret = []
    for _, row in df.iterrows():
        label_path = os.path.join(ops.data_path, row[ops.label_column])
        label_img = cv2.imread(label_path, cv2.IMREAD_GRAYSCALE)
        label_img = cv2.resize(label_img, (224, 224))

        ret.append(np.where(label_img > 0, 1, 0).sum())
    return ret


@preprocess
def black_box_count(df, ops):
    """
    Detect if there is a black box at the bottom left
    """

    box_count = []
    imgs = get_imgs(df, ops)
    for img in imgs:
        # Get the image size
        height, width = img.shape[0:2]
        count = 0
        for x in range(0, 30):
            for y in range(200, height):
                if img[y][x][0] == 0:
                    count += 1
        if count == 720:
            box_count.append("A")
        else:
            box_count.append("B")

    return box_count
