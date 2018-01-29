import entities
import images

ALL_ENTITIES = {}  # id -> lambda: Entity


def _put(factory_id, entity_builder):
    if factory_id in ALL_ENTITIES:
        print("WARN\toverwriting an entitiy with id: ", factory_id)
    ALL_ENTITIES[factory_id] = entity_builder


def init_entities():
    print("INFO\tinitializing entity factory")
    _put("acid_top", lambda: entities.KillBlock(0, 0, images.ACID_TOP_HALF, hitbox=[0, 16, 32, 16]))
    _put("acid_full", lambda: entities.KillBlock(0, 0, images.ACID_FULL))
    print("INFO\tfinished initializing ", len(ALL_ENTITIES), " entities")


def build(factory_id):
    if factory_id in ALL_ENTITIES:
        res = ALL_ENTITIES[factory_id]()
        res.set_factory_id(factory_id)
        return res
    else:
        raise ValueError("unknown factory id: ", factory_id)


init_entities()


