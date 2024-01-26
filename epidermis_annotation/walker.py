import cv2


class Walker:
    """ Class to filter annotation image with canny and run a walker function to get coordinates of inner
        and outer epidermis edges.

    Attributes:
        annotation_img (2d array): Annotation (grayscale)
    """
    def __init__(self, annotation_img):
        self.annotation_img = annotation_img

    def get_annotation_edges(self) -> tuple(list(list(tuple)), np.array):
        """ Returns coordinates of inner epidermis using annotation edges with canny filter.

        Returns:
            annotation_edges (list(list(tuple))): Contains coordinates of inner epidermis using annotation edges
            img_canny (2d array): Canny edge filtered annotation image (grayscale)
        """
        img_canny = self._get_img_canny()
        annotation_edges = self._run_walker(img_canny=img_canny)
        return annotation_edges, img_canny

    def _get_img_canny(self):
        """ returns canny filtered image """
        return cv2.Canny(self.annotation_img, 50, 150)

    def _run_walker(self, img_canny) -> list(list(tuple)):
        """ Runs a walker through canny filtered image of annotation; tracks the edges of epidermis and save coordinates.

        Parameters:
            img_canny (2d array): Canny edge filtered annotation image (grayscale)

        Returns:
            annotation_edges (list(list(tuple))): Contains coordinates of inner epidermis using annotation edges
        """
        # get starting point from bottom of picture
        starting_coord_walker = []
        k = 1
        while len(starting_coord_walker) == 0:

            for i in range(img_canny.shape[1] - 1):
                if img_canny[img_canny.shape[1] - k][i] > 128:
                    starting_coord_walker.append([img_canny.shape[1] - k, i])
            k += 1

        # define the steps the walker will take
        dy_orth = [1, 0, -1, 0]
        dx_orth = [0, 1, 0, -1]

        dy_diag = [1, -1, -1, 1]
        dx_diag = [1, 1, -1, -1]

        # define the initial direction the walker will take
        current_direction = 0

        # direction counter to make sure the orthogonal directions are check first
        direction_counter = 0

        # run walker
        annotation_edges = list()
        for starting_point in starting_coord_walker:
            coordinates = [starting_point]

            reached_end = False
            steps_counter = 0
            max_steps = 200000
            while not reached_end:
                # breaks if no border is present by reaching max steps
                if steps_counter > max_steps:
                    break

                # makes sure to check orthogonal pixel first, then diagonal
                if direction_counter > 4:
                    y = coordinates[-1][0] + dy_diag[current_direction]
                    x = coordinates[-1][1] + dx_diag[current_direction]
                else:
                    y = coordinates[-1][0] + dy_orth[current_direction]
                    x = coordinates[-1][1] + dx_orth[current_direction]

                # handles artifacts
                if direction_counter > 8:
                    dy_orth_artifact = [2, 0, -2, 0]
                    dx_orth_artifact = [0, 2, 0, -2]
                    y = coordinates[-1][0] + dy_orth_artifact[current_direction]
                    x = coordinates[-1][1] + dx_orth_artifact[current_direction]

                if direction_counter > 12:
                    dy_diag_artifact = [2, -2, -2, 2]
                    dx_diag_artifact = [2, 2, -2, -2]
                    y = coordinates[-1][0] + dy_diag_artifact[current_direction]
                    x = coordinates[-1][1] + dx_diag_artifact[current_direction]

                # checks for border of image
                if y < 0 or y > (self.annotation_img.shape[0] - 1) or x < 0 or x > (self.annotation_img.shape[1] - 1):
                    current_direction = (current_direction + 1) % 4
                    direction_counter += 1
                    if not len(coordinates) == 1:  # handles first coordinate is at border -> breaks while loop
                        reached_end = True
                    continue

                if img_canny[y][x] != 0 and not [y, x] in coordinates:
                    coordinates.append([y, x])
                    current_direction = 0
                    direction_counter = 0
                else:
                    # If the next step is not along an edge, try the next direction
                    current_direction = (current_direction + 1) % 4
                    direction_counter += 1

                steps_counter += 1
            annotation_edges.append(coordinates)

        return annotation_edges
