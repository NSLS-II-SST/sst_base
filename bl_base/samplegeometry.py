class GeometryBase:
    def __init__(self, sides):
        self.sides = sides

    def get_sample_frame(side, position):
        x1, y1, x2, y2 = position
        p1 = vec(x1, y1, t)
        p2 = vec(x1, y2, t)
        p3 = vec(x2, y1, t)
        width = x2 - x1
        height = y2 - y1

        frame = Panel(p1, p2, p3, height=height, width=width,
                      parent=self.sides[side - 1])
        return frame

    
