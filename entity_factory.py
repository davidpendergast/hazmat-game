import entities
import decorations
import images
import enemies

ALL_ENTITIES = {}  # id -> lambda: Entity
ALL_IDS_SORTED = []


def _put(factory_id, entity_builder):
    if factory_id in ALL_ENTITIES:
        print("WARN\toverwriting an entitiy with id: ", factory_id)
    ALL_ENTITIES[factory_id] = entity_builder
    ALL_IDS_SORTED.append(factory_id)


def build(factory_id):
    if factory_id in ALL_ENTITIES:
        res = ALL_ENTITIES[factory_id]()
        res.set_factory_id(factory_id)
        return res
    else:
        raise ValueError("unknown factory id: ", factory_id)


def _spawner(obj_builder):
    return lambda: entities.SpawnerEntity(obj_builder)


def init_entities():
    print("INFO\tinitializing entity factory")

    ALL_IDS_SORTED.clear()
    ALL_ENTITIES.clear()

    _put("white_wall", lambda: entities.Wall(32, 32, sprite=images.WHITE_WALL))
    _put("white_wall_fancy", lambda: entities.Wall(32, 32, images.WHITE_WALL_FANCY))
    _put("white_wall_small", lambda: entities.Wall(16, 16, images.WHITE_WALL_SMOL))
    _put("chain_wall_small", lambda: entities.Wall(16, 16, images.CHAIN_SMOL))

    _put("reference_entity", lambda: entities.ReferenceEntity(ref_id=None))

    _put("acid_top", lambda: entities.KillBlock(images.ACID_TOP_HALF, hitbox=[0, 16, 32, 16]).with_light_level(128))
    _put("acid_full", lambda: entities.KillBlock(images.ACID_FULL).with_light_level(128))

    _put("breakable_white_wall_spawner", _spawner(lambda: entities.BreakableWall(images.WHITE_WALL_CRACKED, images.WHITE_WALL_BREAKING)))
    _put("breakable_block_spawner", _spawner(lambda: entities.BreakableWall(images.BREAKABLE_WALL, images.BREAKABLE_WALL_ANIM)))

    _put("lightbulb", lambda: decorations.Decoration("lightbulb", images.LIGHT_BULB).with_light_level(160))
    _put("wire_vert", lambda: decorations.Decoration("wire_vert", images.WIRE_VERTICAL))
    _put("chalkboard", lambda: decorations.Decoration("chalkboard", images.CHALKBOARD))
    _put("ground_stone", lambda: decorations.Ground("ground_stone", images.STONE_GROUND))
    _put("ground_sand", lambda: decorations.Ground("ground_sand", images.SAND_GROUND))
    _put("ground_grass", lambda: decorations.Ground("ground_grass", images.GRASS_GROUND))
    _put("ground_purple", lambda: decorations.Ground("ground_purple", images.PURPLE_GROUND))
    _put("ground_wall", lambda: decorations.Ground("ground_wall", images.WALL_GROUND))
    _put("ground_dark", lambda: decorations.Ground("ground_dark", images.DARK_GROUND))

    _put("enemy_basic", _spawner(lambda: enemies.DumbEnemy()))
    _put("enemy_smart", _spawner(lambda: enemies.SmartEnemy()))
    _put("enemy_sticky", _spawner(lambda: enemies.StickyEnemy()))
    _put("enemy_sticky_ccw", _spawner(lambda: enemies.StickyEnemy(clockwise=False)))
    _put("enemy_dodger", _spawner(lambda: enemies.DodgeEnemy()))

    print("INFO\tfinished initializing ", len(ALL_ENTITIES), " entities")


init_entities()


