from europi import *
import machine
from time import ticks_diff, ticks_ms
from random import randint, uniform
from europi_script import EuroPiScript


'''
Karma
author: Arthur LAURENT (github.com/atulrnt)
date: 2022-09-30

What goes around comes around.

A script to delay, repeat, divide, add probability etc. to two independent triggers.
Output 1 to 3 have separate settings to manipulate the triggers coming in the trigger input 1.
Output 4 to 6 have separate settings to manipulate the triggers coming in the trigger input 2.

digital_in: trigger 1 in
analog_in: trigger 2 in (analog is used as a fake digital)

knob_1: go over the settings for the selected output for trigger 1
knob_2: go over the settings for the selected output for trigger 2

button_1 + knob_1: switch between the settings page of output 1 to 3
button_2 + knob_2: switch between the settings page of output 4 to 6

button_1: send a manual trigger to trigger 1
button_2: send a manual trigger to trigger 2

output_1 to 6: generated triggers
'''


class Karma(EuroPiScript):
    def __init__(self):
        super().__init__()

        self.ain_previous_state = LOW
        self.ain_current_state = LOW

        self.sections = [
            [KarmaOutput(cv1), KarmaOutput(cv2), KarmaOutput(cv3)],
            [KarmaOutput(cv4), KarmaOutput(cv5), KarmaOutput(cv6)],
        ]

        @din.handler
        def trigger_started():
            self.send_start_trigger(0)

        @din.handler_falling
        def trigger_ended():
            self.send_end_trigger(0)

    def main(self):
        # Emulate din.handler and din.handler_falling for ain so that the analogue input can be used as a digital input
        self.ain_current_state = HIGH if ain.percent() > 1 else LOW

        if self.ain_current_state == HIGH and self.ain_previous_state == LOW:
            self.send_start_trigger(1)

        if self.ain_current_state == LOW and self.ain_previous_state == HIGH:
            self.send_end_trigger(1)

        self.ain_previous_state = self.ain_current_state

        # Let each output do their thing
        for section in self.sections:
            for cv in section:
                cv.main()

    def send_start_trigger(self, section):
        for cv in self.sections[section]:
            cv.input_started()

    def send_end_trigger(self, section):
        for cv in self.sections[section]:
            cv.input_ended()

    def display_menu(self):
        pass


class KarmaOutput:
    BEGIN_AT_START = 0
    BEGIN_AT_END = 1

    def __init__(
            self,

            # The EuroPi output used by this output class
            cv: Output,

            # When to begin the output
            # 0 = output starts when trigger starts
            # 1 = output starts when trigger stops
            # Whatever is chosen, the output is reset if a new trigger starts while the output is still being performed
            beginning=BEGIN_AT_END,

            # How long should we wait before starting the output (in ms)
            delay=0,

            # How long should the output go for (in ms)
            duration=100,

            # How many sub-output should the output be divided into
            # Useful to output bursts of triggers, sounds great on MI Rings for instance
            divisions=1,

            # How many times should the output be repeated
            repetitions=0,

            # The percentage of probability for an output to happen
            probability=100,

            # The percentage of probability for an output division to happen
            probability_per_division=100,
    ):
        self.cv = cv
        self.beginning = beginning
        self.delay = delay
        self.duration = duration
        self.divisions = divisions
        self.repetitions = repetitions
        self.probability = probability
        self.probability_per_division = probability_per_division

        self.output = LOW
        self.previous_output = LOW
        self.output_started_at = 0
        self.karma_started_at = 0
        self.division_started = False
        self.division_started_at = 0

        self.occurrences = 0

    def input_started(self):
        self.reset()

        if self.beginning == self.BEGIN_AT_START:
            self.start()

    def input_ended(self):
        if self.beginning == self.BEGIN_AT_END:
            self.start()

    def start(self):
        if not self.can_output(self.probability):
            return

        self.karma_started_at = time.ticks_ms()

    def reset(self):
        self.karma_started_at = 0
        self.division_started = False
        self.division_started_at = 0
        self.output = LOW
        self.output_started_at = 0
        self.occurrences = 0

    def can_output(self, probability):
        return randint(1, 100) <= probability

    def get_division_duration(self):
        return self.duration / ((self.divisions * 2) - 1)

    def main(self):
        if self.karma_started_at == 0:
            self.output = LOW
        else:
            current_time = time.ticks_ms()
            time_since_karma_beginning = time.ticks_diff(current_time, self.karma_started_at)

            # Start the output
            if self.output_started_at == 0 and time_since_karma_beginning >= self.delay:
                self.output_started_at = current_time

            # End the karma run
            elif self.output_started_at == 1 and time_since_karma_beginning >= self.duration:
                self.occurrences += 1
                self.reset()

                if self.repetitions > 0 and self.occurrences < self.repetitions:
                    self.start()
                else:
                    self.occurrences = 0

            # Handle the current division
            # A complete division is the HIGH + the LOW except for the last division as Karma always ends with a HIGH
            # (if probability is set to 100)
            if self.output_started_at > 0:
                if not self.division_started:
                    self.division_started = True
                    self.division_started_at = current_time

                    if self.can_output(self.probability_per_division):
                        self.output = HIGH

                else:
                    division_running_time = time.ticks_diff(current_time, self.division_started_at)
                    division_duration = self.get_division_duration()
                    full_division_duration = division_duration * 2

                    if division_duration <= division_running_time < full_division_duration:
                        self.output = LOW

                    elif division_running_time >= full_division_duration:
                        self.division_started = False
                        self.division_started_at = 0

        if self.output != self.previous_output:
            self.previous_output = self.output
            self.cv.value(self.output)


if __name__ == '__main__':
    Karma().main()
