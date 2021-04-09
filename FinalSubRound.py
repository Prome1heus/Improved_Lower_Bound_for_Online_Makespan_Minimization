from SubRound import SubRound


class FinalSubRound(SubRound):

    def cost_on_different_machines(self, rounds, index, sub_round_index):
        jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if i < index]
        min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index])
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " > " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"
