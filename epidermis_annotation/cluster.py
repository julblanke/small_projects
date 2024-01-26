import numpy as np
from skimage.measure import label


class Cluster:
    """ Class to find and count cluster; defines a walker who tracks edge of inner epidermis.

    Attributes:
        orig_img (3d array): Original image (rgb)
        inner_epi (list): Coordinates of inner epidermis edge
        pixel_width (int): User defined pixel width left and right to inner epidermis edge for cluster window
        green_threshold (int): User defined value for green value threshold concerning clustering
    """
    def __init__(self, orig_img, inner_epi, pixel_width, green_threshold):
        self.orig_img = orig_img
        self.inner_epi = inner_epi
        self.pixel_width = pixel_width
        self.green_threshold = green_threshold

    def get_cluster_amount(self) -> tuple(int, list(list(tuple))):
        """ Returns cluster amount after creating cluster window and searching for clusters

        Returns:
             cluster_amount (int): Amount of clusters in window
             inner_epi_windows_coordinates (list(list(tuples)): Contains coordinates of window; used for visualization
        """
        inner_epi_windows, inner_epi_windows_coordinates = self._append_coordinates()
        cluster_amount = self._find_clusters(inner_epi_windows=inner_epi_windows)
        return cluster_amount, inner_epi_windows_coordinates

    def _append_coordinates(self) -> tuple(list, list(list(tuple))):
        """ Append edge with pixel left and right to coordinates; width is defined by user.

        Returns:
            inner_epi_green_windows (list): Thresholded green values in window used for clustering
            inner_epi_windows_coordinates (list(list(tuples)): Contains coordinates of window; used for visualization
        """
        inner_epi_green_windows = []
        inner_epi_windows_coordinates = []
        for coordinate in self.inner_epi:
            green_channel_window = []
            window_coordinates = []
            x = coordinate[1]
            y = coordinate[0]

            # handles border; continues if pixel_width overshoots border
            if (x - self.pixel_width) < 0 or (x + self.pixel_width + 1) > (self.orig_img.shape[1] - 1):
                continue

            for i in range(x - self.pixel_width, x + self.pixel_width + 1):
                img_ = self.orig_img[:, :, 1]
                green_channel = img_[y][i]
                if green_channel > self.green_threshold:
                    green_channel_window.append(green_channel)
                else:
                    green_channel_window.append(0)
                window_coordinates.append([y, i])

            inner_epi_green_windows.append(green_channel_window)
            inner_epi_windows_coordinates.append(window_coordinates)
        return inner_epi_green_windows, inner_epi_windows_coordinates

    def _find_clusters(self, inner_epi_windows) -> int:
        """ Finds clusters using skimage label function.

        Returns:
            counts (int): Amount of clusters found in window
        """
        inner_epi_windows_ = np.array(inner_epi_windows)
        labeled_array, counts = label(inner_epi_windows_, return_num=True)
        return counts

