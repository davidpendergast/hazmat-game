import images
import entities
import decorations
import file_stuff
import settings

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


def fetch_ref(ref_id, entity, refs):
    if ref_id not in refs:
        raise ValueError("reference doesn't exist: ", ref_id)
    else:
        position = refs[ref_id]
        entity.set_xy(position[0], position[1])
        entity.set_ref_id(ref_id)
        return entity


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
        ref_items = list()
        ref_items.append(fetch_ref("terminal_1", entities.Terminal(0, 0, "you don't belong here."), refs))
        ref_items.append(fetch_ref("puzzle_terminal_1", entities.PuzzleTerminal(0, 0), refs))
        msg = ["you'll die in this place.", "is that what you want?"]
        ref_items.append(fetch_ref("jump_tip_terminal", entities.Terminal(0, 0, msg), refs))

        for item in ref_items:
            world.add_entity(item)


_SampleLevel()


def load_from_level_file(world, filename):
    refs = {}  # ref_id -> (x, y)
    last_header = None
    cnt = 1
    levels_dir = settings.CONFIGS["level_dir"]
    lines = file_stuff.read_lines_from_file(levels_dir + filename + LEVEL_EXT)
    for line in lines:
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

                elif last_header == DECOR_HEADER or last_header == GROUND_HEADER:
                    dec_id = items[0]
                    x = int(items[1])
                    y = int(items[2])

                    dec = decorations.get_decoration(dec_id)
                    dec.set_xy(x, y)
                    world.add_entity(dec)

        except ValueError:
            print("Error on line ", cnt, ":\t", line)

        cnt += 1
    return refs


def save_to_level_file(world, filename):

        walls = []
        decorations = []
        ground = []
        references = []

        for e in world.get_entities_with(not_category="actor"):
            if e.get_ref_id() is not None:
                references.append(e)
            elif e.is_("wall"):
                walls.append(e)
            elif e.is_("ground"):
                ground.append(e)
            elif e.is_("decoration"):
                decorations.append(e)
            else:
                print("discarding entity: ", e)

        lines = list()
        lines.append(REF_HEADER)
        for ref in sorted(references, key=str):
            lines.append("{}, {}, {}".format(ref.get_ref_id(), ref.get_x(), ref.get_y()))
        lines.append("")

        lines.append(DECOR_HEADER)
        for dec in sorted(decorations, key=str):
            lines.append("{}, {}, {}".format(dec.get_dec_id(), dec.get_x(), dec.get_y()))
        lines.append("")

        lines.append(WALLS_HEADER)
        for wall in sorted(walls, key=str):
            anim_id = wall.sprite().get_id()
            r = wall.get_rect()
            lines.append("{}, {}, {}, {}, {}".format(anim_id, r[0], r[1], r[2], r[3]))
        lines.append("")

        lines.append(GROUND_HEADER)
        for gr in sorted(ground, key=str):
            lines.append("{}, {}, {}".format(gr.get_dec_id(), gr.get_x(), gr.get_y()))
        lines.append("")

        levels_dir = settings.CONFIGS["level_dir"]
        file_stuff.write_lines_to_file(lines, levels_dir + filename + LEVEL_EXT)












