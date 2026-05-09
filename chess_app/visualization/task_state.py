class TaskState:

    def __init__(self):
        self.moves = []
        self.solution = []
        self.current_index = 0

    def reset(self):
        self.moves = []
        self.solution = []
        self.current_index = 0
