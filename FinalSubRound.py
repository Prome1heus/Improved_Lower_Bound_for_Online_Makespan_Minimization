from SubRound import SubRound


class FinalSubRound(SubRound):

    def cost_on_different_machines(self, rounds, index, sub_round_index):
        jobs_to_consider = [round.sub_rounds[0].get_identifier() for (i, round) in enumerate(rounds) if i < index]
        min_cost = sum([round.sub_rounds[0].job_size for (i, round) in enumerate(rounds) if i < index])
        return " + ".join(jobs_to_consider) + " = $" + str(float(min_cost)) + " > " + str(
            float(self.c * self.get_makespan())) + \
               " = " + str(float(self.c)) + "\\cdot " + str(float(self.get_makespan())) + "$"

    def get_analysis(self, use_images, index, sub_round_index, rounds):
        result = "By the example schedule below, the optimum makespan is at most {0}. ".format(
            str(float(self.get_makespan())))
        result += "No matter where A schedules the last job, "
        result += "its makespan is at least " + self.cost_on_different_machines(rounds, index, sub_round_index)
        result += ". \\newline \n "
        result += self.get_assignment_per_machine(rounds)
        if use_images:
            result += self.get_image()
        else:
            result += self.get_latex_table()
        return result
