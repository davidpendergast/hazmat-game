import pathlib


def write_lines_to_file(lines, filepath):
    with open(filepath, "w") as file:
        for l in lines:
            file.write(l + "\n")


def read_lines_from_file(filepath):
    with open(filepath, "r") as file:
        lines = []
        line = file.readline()
        while line:
            if line.endswith("\n"):
                line = line[:-1]
            lines.append(line)
            line = file.readline()
        return lines


def exists(filepath):
    my_file = pathlib.Path(filepath)
    return my_file.is_file()


def dir_exists(path_to_dir):
    my_dir = pathlib.Path(path_to_dir)
    return my_dir.is_dir()
