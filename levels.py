import images
import entities

ALL_LEVELS = {}  # name -> level

LEVELS_DIR = "levels/"
LEVEL_EXT = ".txt"
WALLS_HEADER = "##  WALLS  ##"
DECOR_HEADER = "##  DECORATIONS  ##"
GROUND_HEADER = "##  GROUND  ##"
REF_HEADER = "##  REFERENCES  ##"
ALL_HEADERS = [WALLS_HEADER, DECOR_HEADER, GROUND_HEADER, REF_HEADER]


def get_level(level_id):
    if level_id not in ALL_LEVELS:
        raise ValueError("No level exists for id: " + str(level_id))
    else:
        return ALL_LEVELS[level_id]


class Level:
    def __init__(self, level_id):
        self.level_id = level_id
        ALL_LEVELS[level_id] = self

    def get_id(self):
        return self.level_id

    def build(self, world):
        refs = load_from_level_file(world, self.get_id())
        self.build_refs(refs, world)


class _SampleLevel(Level):
    def __init__(self):
        Level.__init__(self, "default_level")

    def build_refs(self, refs, world):
        pass


_SampleLevel()


def load_from_level_file(world, filename):
    with open(LEVELS_DIR + filename + LEVEL_EXT, "r") as file:
        refs = {}  # ref_id -> (x, y)
        last_header = None
        line = file.readline()
        cnt = 1
        while line:
            if line.endswith("\n"):
                line = line[:-1]
            try:
                if line in ALL_HEADERS:
                    last_header = line
                    print("Loading from section: ", last_header)
                elif line == "":
                    pass
                elif last_header is None or line.startswith("#"):
                    print("skipping line: ", line)
                else:
                    items = line.split(", ")
                    if last_header == REF_HEADER:
                        xy = (int(items[1]), int(items[2]))
                        refs[items[0]] = xy

                    elif last_header == WALLS_HEADER:
                        anim_id = items[0]
                        animation = images.get_animation(anim_id)
                        x, y, w, h = int(items[1]), int(items[2]), int(items[3]), int(items[4])
                        world.add_entity(entities.Wall(x, y, w=w, h=h, sprite=animation))

                    elif last_header == DECOR_HEADER:
                        dec_id = items[0]
                        x = int(items[1])
                        y = int(items[2])
                        # TODO - dec = decorations.get_decoration(dec_id)
                        # TODO - dec.set_xy(x, y)
                        # TODO - world.add_entity(dec)

                    elif last_header == GROUND_HEADER:
                        x = int(items[1])
                        y = int(items[2])
                        world.add_entity(entities.Ground(x, y, 0))

            except ValueError:
                print("Error on line ", cnt, ":\t", line)

            line = file.readline()
            cnt += 1
        return refs


def save_to_level_file(world, filename):
    with open(LEVELS_DIR + filename + LEVEL_EXT, "w") as file:
        walls = []
        decorations = []
        ground = []
        references = []

        for e in world.get_entities_with(not_category="actor"):
            if e.get_ref_id() is not None:
                references.append(e)
            if e.is_("wall"):
                walls.append(e)
            elif e.is_("ground"):
                ground.append(e)
            elif e.is_("decoration"):
                decorations.append(e)
            else:
                print("discarding entity: ", e)

        lines = list()
        lines.append(REF_HEADER)
        for ref in references:
            lines.append("{}, {}, {}".format(ref.get_ref_id(), ref.get_x(), ref.get_y()))
        lines.append("")

        lines.append(DECOR_HEADER)
        for dec in decorations:
            lines.append("{}, {}, {}".format(dec.get_dec_id(), dec.get_x(), dec.get_y()))
        lines.append("")

        lines.append(WALLS_HEADER)
        for wall in walls:
            anim_id = wall.sprite().get_id()
            r = wall.get_rect()
            lines.append("{}, {}, {}, {}, {}".format(anim_id, r[0], r[1], r[2], r[3]))
        lines.append("")

        lines.append(GROUND_HEADER)
        for gr in ground:
            lines.append("{}, {}, {}".format(gr.get_dec_id(), gr.get_x(), gr.get_y()))
        lines.append("")

        for l in lines:
            file.write(l + "\n")












