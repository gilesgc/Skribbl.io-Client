from math import floor, ceil
from google_images_download import google_images_download
import hitherdither
from PIL import Image
import random

class SkribblGame(object):
    def __init__(self, data):
        self.name = data['name']
        self.key = data['key']
        self.language = data['language']
        self.slots = data['slots']
        self.drawingID = data['drawingID']
        self.myID = data['myID']
        self.ownerID = data['ownerID']
        self.round = data['round']
        self.roundMax = data['roundMax']
        self.time = data['time']
        self.timeMax = data['timeMax']
        self.inGame = data['inGame']
        self.players = dict()
        for p in data['players']:
            self.players[p['id']] = self.Player(p)

    def addPlayer(self, data):
        p = self.Player(data)
        self.players[p.id] = p

    class Player:
        def __init__(self, data):
            self.__dict__ = data

    class Canvas:
        colors = [
            (255, 255, 255),
            (0, 0, 0),
            (193, 193, 193),
            (76, 76, 76),
            (239, 19, 11),
            (116, 11, 7),
            (255, 113, 0),
            (194, 56, 0),
            (255, 228, 0),
            (232, 162, 0),
            (0, 204, 0),
            (0, 85, 16),
            (0, 178, 255),
            (0, 86, 158),
            (35, 31, 211),
            (14, 8, 101),
            (163, 0, 186),
            (85, 0, 105),
            (211, 124, 170),
            (167, 85, 116),
            (160, 82, 45),
            (99, 48, 13)
        ]

        #copied from javascript - not sure what some stuff does but it works
        @classmethod
        def parseDrawCommand(cls, data, canvasWidth, canvasHeight):
            def i(t, e, n):
                if t < e:
                    return e
                elif t > n:
                    return n
                else:
                    return t

            #paintbrush
            if data[0] == 0:
                size = floor(data[2])
                n = floor(ceil(size / 2))
                x = i(floor(data[3]), -n, canvasWidth + n)
                y = i(floor(data[4]), -n, canvasHeight + n)
                end_x = i(floor(data[5]), -n, canvasWidth + n)
                end_y = i(floor(data[6]), -n, canvasHeight + n)
                color = cls.colors[data[1]]
                return cls.Line(x, y, end_x, end_y, size, color)

            #eraser
            elif data[0] == 1:
                size = floor(data[1])
                n = floor(ceil(size / 2))
                x = i(floor(data[2]), -n, canvasWidth + n)
                y = i(floor(data[3]), -n, canvasHeight + n)
                end_x = i(floor(data[4]), -n, canvasWidth + n)
                end_y = i(floor(data[5]), -n, canvasHeight + n)
                return cls.Line(x, y, end_x, end_y, size, (255, 255, 255))

            #floodfill (not finished)
            else:
                u = cls.colors[data[1]]
                h = i(floor(data[2]), 0, canvasWidth)
                l = i(floor(data[3]), 0, canvasHeight)
                print("someone used fill tool")
                return cls.Line(h, l, h, l, 4, (0, 0, 0))

        @classmethod
        def getColorNumber(cls, color: tuple):
            for i in range(0, len(cls.colors)):
                if(cls.colors[i] == color):
                    return i

        class Line:
            def __init__(self, x, y, end_x, end_y, size, color):
                self.x = x
                self.y = y
                self.end_x = end_x
                self.end_y = end_y
                self.size = size
                self.r = color[0]
                self.g = color[1]
                self.b = color[2]

            def data(self):
                return [0, SkribblGame.Canvas.getColorNumber((self.r, self.g, self.b)),
                    self.size, self.x, self.y, self.end_x, self.end_y]

    class AutoDraw:
        palette = hitherdither.palette.Palette(
            [0xFFFFFF, 0x000000, 0xC1C1C1, 0x4C4C4C,
             0xEF130B, 0x740B07, 0xFF7100, 0xC23800,
             0xFFE400, 0xE8A200, 0x00CC00, 0x005510,
             0x00B2FF, 0x00569E, 0x231FD3, 0x0E0865,
             0xA300BA, 0x550069, 0xD37CAA, 0xA75574,
             0xA0522D, 0x63300D]
        )

        class DrawMethod:
            random = 'random'
            scan = 'scan'

        @classmethod
        def drawImage(cls, client, paintbox, image, method):
            img_rgb = cls.formatImage(image)
            lines = list()
            for x in range(0, img_rgb.width, 3):
                new_y = 0
                for y in range(img_rgb.height):
                    if y != new_y:
                        continue
                    color = img_rgb.getpixel((x, y))
                    new_y = cls.continueToDifferentColor(img_rgb, (x, y))
                    lines.append(SkribblGame.Canvas.Line(x, y, x, new_y, 6, color).data())
            if method == cls.DrawMethod.scan:
                while len(lines) > 0:
                    if len(lines) <= 8:
                        client.socket.emit("drawCommands", lines)
                        paintbox.addUnparsedCommands(lines)
                        paintbox.update()
                        lines.clear()
                    else:
                        client.socket.emit("drawCommands", lines[:8])
                        paintbox.addUnparsedCommands(lines[:8])
                        paintbox.update()
                        for i in range(9):
                            del(lines[0])
            elif method == cls.DrawMethod.random:
                while len(lines) > 0:
                    if len(lines) >= 16:
                        randomindex = random.randint(0, len(lines) - 8)
                        linestosend = lines[randomindex:randomindex + 8]
                        client.socket.emit("drawCommands", linestosend)
                        paintbox.addUnparsedCommands(linestosend)
                        paintbox.update()
                        for l in linestosend:
                            lines.remove(l)
                    else:
                        client.socket.emit("drawCommands", lines[:8])
                        client.socket.emit("drawCommands", lines[8:])
                        lines.clear()

        def continueToDifferentColor(image, coord):
            original_pixel = image.getpixel(coord)
            for y in range(coord[1] + 1, image.height):
                if image.getpixel((coord[0], y)) != original_pixel:
                    return y
            return image.height

        def formatImage(image):
            image_dithered = hitherdither.ordered.cluster.cluster_dot_dithering(image.resize((400, 300)).convert('RGB'), SkribblGame.AutoDraw.palette, [1, 1, 1], 4)
            return image_dithered.convert('RGB').resize((800, 600))

        def getGoogleImage(query):
            gid = google_images_download.googleimagesdownload()
            arguments = {"keywords": query, "limit":1, "silent_mode": True, "output_directory": "images"}
            return Image.open(gid.download(arguments)[0][query][0])
