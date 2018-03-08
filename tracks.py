import entities
import cool_math
import images


class TrackPiece(entities.Entity):
    def __init__(self):
        entities.Entity.__init__(self, 16, 16)
        self.categories.update(["track"])
        self.has_neighbor = [False]*len(cool_math.Dir.ALL_DIRS)

    def has_neighbor_track(self, direction):
        idx = cool_math.dir_idx(direction)
        return self.has_neighbor[idx]

    def set_has_neighbor_track(self, direction, val):
        idx = cool_math.dir_idx(direction)
        self.has_neighbor[idx] = val

    def update(self, input_state, world):
        for i in range(0, len(self.has_neighbor)):
            self.has_neighbor[i] = False
        search_space = self.get_rect().inflate(2, 2)
        relevant_tracks = world.get_entities_in_rect(search_space, category="track")
        for track in relevant_tracks:
            if track is not self:
                diff = cool_math.sub(track.center(), self.center())
                diff_dir = (0 if diff[0] == 0 else int(diff[0] / abs(diff[0])),
                            0 if diff[1] == 0 else int(diff[1] / abs(diff[1])))
                if diff_dir != cool_math.Dir.ZERO:
                    self.set_has_neighbor_track(diff_dir, True)

    def sprite(self):
        return images.TRACK_JOINT

    def draw(self, screen, offset=(0, 0), modifier=None):
        dest = self.get_rect().move(offset[0], offset[1])
        num_neighbors = 0
        for i in range(0, len(self.has_neighbor)):
            direction = cool_math.get_dir(i)
            if self.has_neighbor_track(direction):
                num_neighbors += 1
                track_sprite = images.TRACKS[direction]
                images.draw_animated_sprite(screen, dest, track_sprite)

        if num_neighbors < 2:
            images.draw_animated_sprite(screen, dest, images.TRACK_JOINT)




