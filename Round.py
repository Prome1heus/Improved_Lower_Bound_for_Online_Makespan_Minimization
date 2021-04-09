from SubRound import SubRound


class Round:

    def __init__(self, index, m):
        self.sub_rounds = []
        self.index = index
        self.m = m

    def add_sub_round(self, sub_round: SubRound):
        self.sub_rounds.append(sub_round)

    def get_overview(self, list_size):
        if len(self.sub_rounds) == 0:
            return ""
        elif len(self.sub_rounds) == 1:
            return "Round " + str(self.index) + ": " + self.sub_rounds[0].get_overview() + "\\newline \n"
        else:
            result = "Round " + str(self.index) + ":\\begin{itemize}\n"
            for (i, sub_round) in enumerate(self.sub_rounds):
                result += "\\item Subround " + str(self.index) + "." + str(i+1) + ": " + \
                          sub_round.get_overview() + "\n"
            result += "\\end{itemize}"
            return result

    def get_analysis(self, rounds, use_images: bool):
        if len(self.sub_rounds) == 0:
            return ""
        elif len(self.sub_rounds) == 1:
            return "Round " + str(self.index) + ": " + \
                   self.sub_rounds[0].get_analysis(use_images, self.index, 1, rounds) + "\\newline \n"
        else:
            result = ""
            for (i, sub_round) in enumerate(self.sub_rounds):
                result += "Subround " + str(self.index) + "." + str(i+1) + ": \\newline \n" + \
                          sub_round.get_analysis(use_images, self.index, (i+1), rounds) + "\n"
            return result + "\n"

    def get_number_of_jobs_left(self):
        result = self.m
        for sub_round in self.sub_rounds:
            result -= sub_round.get_multiplicity()
        return result

    def initialize_identifiers(self, list_size: int):
        round_identifier = chr(ord('z') - list_size + self.index)
        if len(self.sub_rounds) == 1:
            self.sub_rounds[0].set_identifier("$" + round_identifier + "$", self.index)
        else:
            for (i, sub_round) in enumerate(self.sub_rounds):
                sub_round.set_identifier("$" + round_identifier + "_" + str(i+1) + "$", self.index)

    def get_sub_round(self, index: int):
        return self.sub_rounds[index]
