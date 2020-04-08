import logging
import cv2
import numpy as np
import os
import yaml

from gomrade.transformations import order_points
from utils.images_utils import avg_images, get_pt_color, fill_buffer
from gomrade.classifier import closest_color
from gomrade.gomrade_model import GomradeModel

# todo move to config?
NUM_BLACK_POINTS = 2
NUM_WHITE_POINTS = 2
NUM_BOARD_POINTS = 6
PTPXL = 9


class ImageClicker:
    def __init__(self, clicks):
        self.pts_clicks = []
        self.clicks = clicks

    def _click_and_crop(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pts_clicks.append((x, y))

    def get_points_of_interest(self, cap, image_title):

        cv2.namedWindow(image_title)
        cv2.setMouseCallback(image_title, self._click_and_crop)

        while True:
            _, frame = cap.read()

            # display the image and wait for a keypress
            cv2.imshow(image_title, frame)
            key = cv2.waitKey(1) & 0xFF

            if len(self.pts_clicks) == self.clicks:
                cv2.destroyWindow(image_title)
                break
        return self.pts_clicks


class ManualBoardStateClassifier(GomradeModel):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.black_colors = []
        self.white_colors = []
        self.board_colors = []
        self.x_grid = None
        self.y_grid = None

    def _get_pt_area(self, frame, i, j):
        # c = classify_brightness(res[i, j, :], dominant_color)
        start_i = i - PTPXL
        if start_i < 0:
            start_i = 0
        stop_i = i + PTPXL
        if stop_i > frame.shape[0]:
            stop_i = frame.shape[0]

        start_j = j - PTPXL
        if start_j < 0:
            start_j = 0
        stop_j = j + PTPXL
        if stop_j > frame.shape[1]:
            stop_j = frame.shape[1]

        return frame[start_i: stop_i, start_j: stop_j, :]

    def dump(self, exp_dir):
        with open(os.path.join(exp_dir, 'board_color_data.yml'), 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)

    def fit(self, config, cap):

        num_neighbours = config['board_state_classifier']['num_neighbours']

        if config["board_analysis"] is not None:
            logging.info('Using saved board analysis')
            return config["board_analysis"]

        clicker = ImageClicker(clicks=10)
        pts_clicks = clicker.get_points_of_interest(cap, image_title='2 black, 2 white, 4 board clicks')

        buf = fill_buffer(cap, config["buffer_size"])
        frame = avg_images(buf)

        if config['board_analysis'] is not None:
            raise NotImplementedError()
            black_colors = [content[0], content[1]]
        else:
            black_colors = get_pt_color(frame, pts_clicks[:2], num_neighbours=num_neighbours)
            white_colors = get_pt_color(frame, pts_clicks[:4], num_neighbours=num_neighbours)
            board_colors = get_pt_color(frame, pts_clicks[4:], num_neighbours=num_neighbours)

        # Create grid coords
        x_grid = np.floor(np.linspace(0, self.width - 1, config['board_size'])).astype(int)
        y_grid = np.floor(np.linspace(0, self.height - 1, config['board_size'])).astype(int)

        self.black_colors = black_colors
        self.white_colors = white_colors
        self.board_colors = board_colors
        self.x_grid = x_grid
        self.y_grid = y_grid

    def read_board(self, frame):
        # frame = cv2.blur(frame, ksize=(10, 10))

        stones_state = []
        for i in self.x_grid:
            for j in self.y_grid:
                area = self._get_pt_area(frame, i, j)
                mean_rgb = np.mean(np.mean(area, axis=0), axis=0)

                c = closest_color(mean_rgb, self.board_colors, self.black_colors, self.white_colors)
                stones_state.append(c)
                frame[i: i, j: j, :] = 0

        return stones_state


class ManualBoardExtractor(GomradeModel):
    def __init__(self):
        self.M = None
        self.max_width = None
        self.max_height = None
        self.pts_clicks = None
        self.width = None
        self.height = None

    def dump(self, exp_dir):
        with open(os.path.join(exp_dir, 'board_corners_data.yml'), 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)

    def fit(self, config, cap):

        clicker = ImageClicker(clicks=4)
        pts_clicks = clicker.get_points_of_interest(cap, image_title='Click corners: left upper, right upper, '
                                                                     'right bottom, left bottom')

        _, frame = cap.read()
        M, max_width, max_height = order_points(np.array(pts_clicks).astype(np.float32))

        self.M = M
        self.max_width = max_width
        self.max_height = max_height
        self.pts_clicks = pts_clicks

        transformed_frame = self.read_board(frame)

        width = transformed_frame.shape[0]
        height = transformed_frame.shape[1]

        self.width = width
        self.height = height

        return width, height

    def read_board(self, frame):
        # compute the perspective transform matrix and then apply it
        return cv2.warpPerspective(frame, self.M, (self.max_width, self.max_height))