import enemies
import images
import entities
import file_stuff
import settings
import puzzles
import global_state
import entity_factory

import traceback

ALL_LEVELS = {}  # name -> level

# level ids
PLATFORMER_TEST = "platformer_test"
LEVEL_VOID = "void"
LEVEL_01 = "level_01"
LEVEL_02 = "level_02"
LEVEL_02a = "level_02alt"
LEVEL_03 = "level_03"

LEVEL_SEQ = [LEVEL_01, LEVEL_02a, LEVEL_03]

LEVELS_DIR = "levels/"
LEVEL_EXT = ".txt"
WALLS_HEADER = "##  WALLS  ##"
DECOR_HEADER = "##  DECORATIONS  ##"
GROUND_HEADER = "##  GROUND  ##"
REF_HEADER = "##  REFERENCES  ##"
FACTORY_HEADER = "## FACTORY ##"
ALL_HEADERS = [WALLS_HEADER, DECOR_HEADER, GROUND_HEADER, FACTORY_HEADER, REF_HEADER]


def get_level(level_id):
    if level_id not in ALL_LEVELS:
        print("ERROR\tunrecognized level id: ", level_id)
        return ALL_LEVELS["void"]
    else:
        return ALL_LEVELS[level_id]


def get_first_level_id():
    if settings.is_debug() and settings.STARTING_LEVEL_OVERRIDE is not None:
        return settings.STARTING_LEVEL_OVERRIDE
    else:
        return LEVEL_SEQ[0]


class Level:
    def __init__(self, level_id, name, subtitle):
        """
        :param level_id: filename of level. Also used by levels to link to each other via doors.
        """
        self.level_id = level_id
        self.name = name
        self.subtitle = subtitle

        ALL_LEVELS[level_id] = self

        self._used_refs = set()

    def get_id(self):
        return self.level_id

    def get_name(self):
        return self.name

    def get_subtitle(self):
        return self.subtitle

    def get_player_start_pos(self):
        return (0, 0)

    def next_levels(self):
        """All the ids of levels that can be reached from this one."""
        # return []
        if self.get_id() in LEVEL_SEQ:
            idx = LEVEL_SEQ.index(self.get_id())
            if idx < len(LEVEL_SEQ) - 1:
                return list(LEVEL_SEQ[idx + 1])
        return []

    def fetch_ref(self, ref_id, entity, refs):
        if ref_id in self._used_refs:
            raise ValueError("reference id has already been used: ", ref_id)
        elif ref_id not in refs:
            raise ValueError("reference id doesn't exist: ", ref_id)
        else:
            self._used_refs.add(ref_id)
            position = refs[ref_id]
            entity.set_xy(position[0], position[1])
            entity.set_ref_id(ref_id)
            return entity

    def build(self, world):
        global_state.hud.set_level_title_card(self.get_name(), self.get_subtitle())

        try:
            refs = load_from_level_file(world, self.get_id())
            ref_entities = self.build_refs(refs, world)

            for e in ref_entities:
                world.add_entity(e)
        except:
            print("ERROR\tfailed to load level: ", self.get_id())
            traceback.print_exc()
            pos = self.get_player_start_pos()
            world.add_entity(entities.Wall(pos[0], pos[1] + 128))
            return

        for ref_id in refs:
            if ref_id not in self._used_refs:
                print("WARN\tdid not build reference id: ", ref_id)
                ref_entity = self.fetch_ref(ref_id, entities.ReferenceEntity(0, 0, ref_id=ref_id), refs)
                world.add_entity(ref_entity)

        self._used_refs = set()

    def build_refs(self, refs, world):
        """
        Should be overriden for level classes
        """
        raise ValueError("build_refs() isn't defined.")


class PlatformerTest(Level):
    def __init__(self):
        Level.__init__(self, PLATFORMER_TEST, "Platforming Testing", "?-?")

    def build_refs(self, refs, world):
        ref_items = list()
        ref_items.append(self.fetch_ref("slime_1", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_2", enemies.StickyEnemy(0, 0), refs))

        return ref_items


class _SampleLevel(Level):
    def __init__(self):
        Level.__init__(self, LEVEL_02, "Entry", "1-2")

    def get_player_start_pos(self):
        return (50, 50)

    def build_refs(self, refs, world):
        ref_items = list()
        ref_items.append(self.fetch_ref("terminal_1", entities.Terminal(0, 0, "you don't belong here."), refs))
        puzzle_terminal_1 = entities.PuzzleTerminal(0, 0, lambda: puzzles.DummyPuzzle())
        ref_items.append(self.fetch_ref("puzzle_terminal_1", puzzle_terminal_1, refs))
        msg = ["you'll die in this place.", "is that what you want?"]
        ref_items.append(self.fetch_ref("jump_tip_terminal", entities.Terminal(0, 0, msg), refs))

        rm_wall_1 = self.fetch_ref("rm_wall_1", entities.Wall(0, 0), refs)
        rm_wall_2 = self.fetch_ref("rm_wall_2", entities.Wall(0, 0), refs)
        puzzle2 = entities.DeathPuzzleTerminal(0, 0, lambda: puzzles.SnakePuzzle(3))
        puzzle2 = self.fetch_ref("puzzle_2", puzzle2, refs)

        def rm_walls():
            rm_wall_1.is_alive = False
            rm_wall_2.is_alive = False

        puzzle2.set_on_success(rm_walls)
        ref_items.extend([rm_wall_1, rm_wall_2, puzzle2])

        ref_items.append(self.fetch_ref("enemy_1", enemies.DodgeEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("enemy_2", enemies.DumbEnemy(0, 0), refs))

        ref_items.append(self.fetch_ref("terminal_3", entities.Terminal(0, 0, "this is only the beginning."), refs))
        ref_items.append(self.fetch_ref("health_machine", entities.HealthMachine(0, 0, 3), refs))

        ref_items.append(self.fetch_ref("finish_door_1", entities.LevelEndDoor(0, 0, self.next_levels()[0]), refs))

        ref_items.append(self.fetch_ref("door_a", entities.Door(0, 0, "door_a", "door_b"), refs))
        ref_items.append(self.fetch_ref("door_b", entities.Door(0, 0, "door_b", "door_a"), refs))
        ref_items.append(self.fetch_ref("hidden_terminal", entities.Terminal(0, 0, "this room isn't very useful, is it?"), refs))

        return ref_items


class IntroToEnemies(Level):

    def __init__(self):
        Level.__init__(self, LEVEL_02a, "Danger", "1-2")

    def build_refs(self, refs, world):
        ref_items = list()

        ref_items.append(self.fetch_ref("slime_1", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_2", enemies.StickyEnemy(0, 0, clockwise=False), refs))
        ref_items.append(self.fetch_ref("slime_3", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_4", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_5", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_6", enemies.StickyEnemy(0, 0, clockwise=False), refs))

        ref_items.append(self.fetch_ref("slime_7", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_8", enemies.StickyEnemy(0, 0, clockwise=False), refs))
        ref_items.append(self.fetch_ref("slime_9", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_10", enemies.StickyEnemy(0, 0, clockwise=False), refs))
        ref_items.append(self.fetch_ref("slime_11", enemies.StickyEnemy(0, 0), refs))
        ref_items.append(self.fetch_ref("slime_12", enemies.StickyEnemy(0, 0, clockwise=False), refs))

        #ref_items.append(self.fetch_ref("breakable_1", entities.BreakableWall(0, 0), refs))
        #ref_items.append(self.fetch_ref("breakable_2", entities.BreakableWall(0, 0), refs))
        #ref_items.append(self.fetch_ref("breakable_3", entities.BreakableWall(0, 0), refs))
        #ref_items.append(self.fetch_ref("breakable_4", entities.BreakableWall(0, 0), refs))

        txt = ""
        ref_items.append(self.fetch_ref("terminal_1", entities.Terminal(0, 0, message=txt), refs))

        return ref_items

    def get_player_start_pos(self):
        return (0, 0)


class Level12(Level):

    def __init__(self):
        Level.__init__(self, LEVEL_03, "Decay", "1-3")

    def build_refs(self, refs, world):
        ref_items = list()
        puzzle1 = entities.PuzzleTerminal(0, 0, lambda: puzzles.DummyPuzzle())
        ref_items.append(self.fetch_ref("puzzle_1", puzzle1, refs))
        terminal_1 = entities.Terminal(0, 0, ["this level is pretty boring, isn't it?",
                                              "maybe some pointless exposition would help.",
                                              "...",
                                              "i can't think of any right now..."])
        ref_items.append(self.fetch_ref("terminal_1", terminal_1, refs))

        return ref_items

    def get_player_start_pos(self):
        return (0, 0)


class Level11(Level):

    def __init__(self):
        Level.__init__(self, LEVEL_01, "Descent", "1-1")

    def get_player_start_pos(self):
        return (10, -128)

    def build_refs(self, refs, world):
        ref_items = list()

        txt = "you can move with [WASD] or [ARROW KEYS]"
        ref_items.append(self.fetch_ref("terminal_1", entities.Terminal(0, 0, txt), refs))

        wall = self.fetch_ref("breakable_walls", entities.BreakableWall(0, 0), refs)
        break_walls = [wall]
        break_walls.extend([entities.BreakableWall(wall.get_x() + i*wall.width(), wall.get_y()) for i in range(1, 4)])
        break_walls.extend([entities.BreakableWall(wall.get_x() + i*wall.width(), wall.get_y() + wall.height()) for i in range(0, 4)])
        for w in break_walls:
            w.set_ref_id("breakable_walls")
            ref_items.append(w)

        txt = "you'll die in this place, like the others"
        ref_items.append(self.fetch_ref("terminal_2", entities.Terminal(0, 0, txt), refs))

        txt = "press [J] or [X] to shoot"  # TODO - sync with actual settings
        ref_items.append(self.fetch_ref("how_to_shoot", entities.Terminal(0, 0, txt), refs))

        wall_2 = self.fetch_ref("breakable_2", entities.BreakableWall(0, 0), refs)
        wall_3 = entities.BreakableWall(wall_2.get_x(), wall_2.get_y() + wall_2.height())
        wall_3.set_ref_id("breakable_2")
        ref_items.extend([wall_2, wall_3])

        ref_items.append(self.fetch_ref("finish_door", entities.LevelEndDoor(0, 0, self.next_levels()[0]), refs))

        return ref_items


class _VoidLevel(Level):

    def __init__(self):
        Level.__init__(self, LEVEL_VOID, "Void", "?-?")

    def build(self, world):
        global_state.hud.set_level_title_card(self.get_name(), self.get_subtitle())
        world.add_all_entities([entities.Wall(i*32, 120) for i in range(0, 3)])

    def get_player_start_position(self):
        return (0, 0)

    def build_refs(self, refs, world):
        pass


def load_from_level_file(world, filename):
    if filename == LEVEL_VOID:
        print("WARN\ttried to load void level...?")
        return

    refs = {}  # ref_id -> (x, y)
    last_header = None
    cnt = 1
    levels_dir = settings.CONFIGS["level_dir"]
    lines = file_stuff.read_lines_from_file(levels_dir + filename + LEVEL_EXT)
    for line in lines:
        try:
            if line in ALL_HEADERS:
                last_header = line
                print("INFO\tloading from section: ", last_header)
            elif line == "":
                pass
            elif last_header is None or line.startswith("#"):
                print("INFO\tskipping line: ", line)
            else:
                items = line.split(", ")
                if last_header == REF_HEADER:
                    xy = (int(items[1]), int(items[2]))
                    refs[items[0]] = xy
                    world.add_entity(entities.ReferenceEntity(xy[0], xy[1], ref_id=items[0]))

                elif last_header == FACTORY_HEADER:
                    fac_id = items[0]
                    x = int(items[1])
                    y = int(items[2])

                    fac = entity_factory.build(fac_id)
                    fac.set_xy(x, y)
                    world.add_entity(fac)

        except ValueError:
            print("ERROR\t error parsing entitiy in ", (filename + LEVEL_EXT), " on line ", cnt, ":\t", line)
            traceback.print_exc()

        cnt += 1
    return refs


def save_to_level_file(world, filename):
    if filename == "void":
        print("WARN\ttried to save void level...?")
        return

    factory_created = []
    references = []

    for e in world.get_entities_with(not_category="actor"):
        if e.get_ref_id() is not None:
            if isinstance(e, entities.ReferenceEntity):
                references.append(e)
            else:
                # do nothing, this entity gets spawned by a reference entity
                pass
        elif e.get_factory_id() is not None:
            factory_created.append(e)
        else:
            print("WARN\tdiscarding entity: ", e)

    lines = list()
    lines.append(REF_HEADER)
    for ref in sorted(references, key=str):
        lines.append("{}, {}, {}".format(ref.get_ref_id(), ref.get_x(), ref.get_y()))
    lines.append("")

    lines.append(FACTORY_HEADER)
    for fac in sorted(factory_created, key=str):
        lines.append("{}, {}, {}".format(fac.get_factory_id(), fac.get_x(), fac.get_y()))
    lines.append("")

    levels_dir = settings.CONFIGS["level_dir"]
    file_stuff.write_lines_to_file(lines, levels_dir + filename + LEVEL_EXT)


print("\nINFO\tbuilding levels...")
g = globals().copy()
for level in Level.__subclasses__():
    lvl = level()
    print("INFO\tbuilt level: ", lvl.get_id())









