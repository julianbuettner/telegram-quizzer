from collections import namedtuple

# 🌱🌿🌻🌳

class emojis:
    # Symbols:
    green_check = '✅'
    red_cross = '❌'
    small_orange_diamond = '🔸'
    grey_questionmark = '❔'
    green_star = '❇️'
    red_circle = '⭕️'
    arrow_forward = '▶️'
    arrows_anti_clockwards = '🔄'
    warning = '⚠️'
    grey_dash = '➖'

    # Plants:
    seedling = '🌱'
    branch = '🌿'
    sunflower = '🌻'
    tree = '🌳'

    # Nature:
    cloud = '☁️'
    sun = '☀️'
    volcano = '🌋'

    # Transportation:
    scooter = '🛴'
    bike = '🚲'
    motor_scooter = '🛵'
    truck = '🚛'
    car = '🚗'
    motor_bike = '🏍'
    race_car = '🏎'
    helicopter = '🚁'
    plane = '✈️'
    rocket = '🚀'
    ufo = '🛸'

    plane_starting = '🛫'
    plane_landing = '🛬'

    # Everyday objects
    clipboard = '📋'
    fountain_pen = '🖋'
    stop_watch = '⏱'
    celebrate = '🎉'

efm = emojis().__dict__  # emoji format dict


progress_nature = [
    emojis.seedling,
    emojis.branch,
    emojis.sunflower,
    emojis.tree,
]

progress_machine = [
    emojis.scooter,
    emojis.bike,
    emojis.motor_scooter,
    emojis.truck,
    emojis.car,
    emojis.motor_bike, 
    emojis.race_car,
    emojis.helicopter, 
    emojis.plane,
    emojis.rocket, 
    emojis.ufo,
]


def _pr(per, emoji_string):
    for i in range(len(emoji_string)):
        if per <= (i+1) / len(emoji_string):
            return emoji_string[i]
    return emoji_string[-1]

def progress_to_nature_emoji(per):
    return _pr(per, progress_nature)

def progress_to_machine_emoji(per):
    return _pr(per, progress_machine)



ClipElement = namedtuple('ClipElement', ['emoji', 'position_list'])


class VolcanoFlight:
    def __init__(self):
        frame_count = 10
        self.counter = 0
        self.elements = [
            # position: (y, x)
            ClipElement(emoji=emojis.volcano,
                position_list=[(3, 12)]*frame_count
            ),
            ClipElement(emoji=emojis.helicopter, 
                position_list=[(3,15), (2,15), (2,14), (1, 12), (1, 10), (1, 8), (1,6), (1, 5), (2, 4), (3,3)]
            ),
            ClipElement(emoji=emojis.cloud, position_list=[(0, 3)] * frame_count),
            ClipElement(emoji=emojis.cloud, position_list=[(0, 9)] * frame_count),
            ClipElement(emoji=emojis.cloud, position_list=[(1, 19)] * frame_count),
            ClipElement(emoji=emojis.cloud, position_list=[(0, 18)] * frame_count),
            ClipElement(emoji=emojis.sun, position_list=[(1, 0)] * frame_count),
            ClipElement(emoji=emojis.tree, position_list=[(3, 1)] * frame_count),
        ]
        
    def reset_grid(self):
        self.grid = []
        for _i in range(4):
            line = []
            for _j in range(20):
                line.append(' ')
            self.grid.append(line)

    def build_next(self):
        if self.counter >= len(self.elements[0].position_list):
            return False
        self.reset_grid()
        for element in self.elements:
            position = element.position_list[self.counter]
            if not position:
                continue
            self.grid[position[0]][position[1]] = element.emoji
        self.counter += 1
        return True

    def get_render(self):
        s = ''
        for line in self.grid:
            s += ''.join(line) + '\n'
        res = s.format(
            cl=emojis.cloud,
            pl_start=emojis.plane_starting,
            pl_land=emojis.plane_landing,
            volcano=emojis.volcano
        )
        return '```' + res + '```'  # Markdown!

