import os
import cv2
import numpy as np
from walker import Walker
from cluster import Cluster


def run():
    """ Run pathology image segmentation finding clusters and length of inner epidermis. """

    # read all images in defined image directory
    img_dir = "put_dir_here"
    images_paths = os.listdir(img_dir)
    file_pairs = _get_file_pairs(images_paths=images_paths)

    # get clusters and length of inner epidermis for every image pair (original image, annotation)
    for file_pair in file_pairs:
        annot_file = file_pair[0]
        orig_file = file_pair[1]

        # define src file
        annot = os.path.join(img_dir, annot_file)
        orig_img = os.path.join(img_dir, orig_file)

        # read images
        annot_img = cv2.imread(annot, cv2.IMREAD_GRAYSCALE)
        orig_img = cv2.imread(orig_img, cv2.IMREAD_COLOR)

        # get annotation edges coordinates with Walker class
        walker = Walker(annotation_img=annot_img)
        annotation_edges, img_canny = walker.get_annotation_edges()

        # define which edge is inner epidermis
        inner_epidermis = _get_inner_epidermis(annotation_edges=annotation_edges)
        inner_epidermis_length = len(inner_epidermis)

        # find clusters and get count
        cluster = Cluster(orig_img=orig_img, inner_epi=inner_epidermis, pixel_width=50, green_threshold=200)
        cluster_amount, inner_epi_windows_coordinates = cluster.get_cluster_amount()

        _visualize(orig_img=orig_img, annot_img=annot_img, img_canny=img_canny,
                   inner_epi_windows_coordinates=inner_epi_windows_coordinates,
                   inner_epidermis_length=inner_epidermis_length, cluster_amount=cluster_amount, name=orig_file)


def _get_file_pairs(images_paths) -> list(tuple):
    """ Read images in directory and sort files to pairs (original image, annotation).

    Args:
        images_paths (list): Path to images

    Returns:
        file_pairs (list(tuple)): Each entry contains the corresponding file path to subject's
                                  original image and annotation
    """
    file_pairs = list()
    for file in images_paths:
        pair = list()
        if "Annotation" in file:
            subject_nr = file.split("_")[0]
            pair.append(file)
            for file in images_paths:
                if subject_nr in file and not "Annotation" in file:
                    pair.append(file)
        if not len(pair) == 0:
            file_pairs.append(pair)
    return file_pairs


def _get_inner_epidermis(annotation_edges) -> list:
    """ Returns inner epidermis (this is decided by start- and endpoint of edges in x-direction).
        If startpoint is smaller than endpoint, then the annotation has a curve to the right, meaning
        the second edge is the inner epidermis.
        If startpoint is bigger than endpoint, then the annotation has a curve to the left, meaning
        the first edge is the inner epidermis.

    Args:
        annotation_edges (list(list(tuple))): Contains coordinates of inner epidermis using annotation edges

    Returns:
        (list): Returns inner epidermis edge
    """
    start_x_first_edge = annotation_edges[0][0][1]
    end_x_first_edge = annotation_edges[0][-1][1]
    if start_x_first_edge < end_x_first_edge:
        return annotation_edges[1]
    else:
        return annotation_edges[0]


def _visualize(orig_img, annot_img, img_canny, inner_epi_windows_coordinates,
               inner_epidermis_length, cluster_amount, name):
    """ Visualize data.

    Args:
        orig_img (3d array): Original image (rgb)
        annot_img (2d array): Annotation (grayscale)
        img_canny (2d array): Canny edge filtered annotation image (grayscale)
        inner_epi_windows_coordinates (list(list(tuples)): Contains coordinates of inner epidermis edge with a window-
                                                           size of user defined pixels left and right to edge coordinate
        cluster_amount (int): Amount of cluster in edge window
        name (str): Name of original image file for saving purposes
    """
    # create filtered original image with edge window
    height, width, channels = orig_img.shape
    filtered_orig_img = np.zeros((height, width, channels), dtype=np.uint8)
    for window in inner_epi_windows_coordinates:
        for y, x in window:
            filtered_orig_img[y][x][:] = orig_img[y][x][:]

    # convert the grayscale images to RGB images
    annot_img = cv2.cvtColor(annot_img, cv2.COLOR_GRAY2BGR)
    img_canny = cv2.cvtColor(img_canny, cv2.COLOR_GRAY2BGR)
    images = [orig_img, annot_img, img_canny, filtered_orig_img]

    # concatenate the images into a single large image
    h_concat = np.concatenate(images[:2], axis=0)
    result = np.concatenate([h_concat, np.concatenate(images[2:], axis=0)], axis=1)

    # display the large image in a single window
    img_resized = cv2.resize(result, (1024, 1024))

    # define the title to be added to the image
    title = 'clusters: {}, pixel amount of inner epidermis edge: {}'.format(cluster_amount, inner_epidermis_length)

    # define the font to be used
    font = cv2.FONT_HERSHEY_SIMPLEX

    # define the font scale and color
    font_scale = 1
    font_color = (255, 255, 255)

    # define the thickness of the font
    thickness = 3

    # det the size of the text
    (text_width, text_height), baseline = cv2.getTextSize(title, font, font_scale, thickness)

    # set the position to put the text
    text_x = int(0)
    text_y = int(550)

    # add the title to the image
    cv2.putText(img_resized, title, (text_x, text_y), font, font_scale, font_color, thickness)

    # show image with user input
    cv2.imshow("pathologie", img_resized)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # save file
    cv2.imwrite('{}.jpg'.format(name), img_resized)


if __name__ == '__main__':
    run()
