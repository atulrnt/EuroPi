from europi import *
from time import ticks_diff, ticks_ms
from random import randint
from europi_script import EuroPiScript


class Karma(EuroPiScript):
    def __init__(self):
        super().__init__()

        self._ain_current_state = LOW
        self._ain_previous_state = LOW

        self._sections = [
            [KarmaOutput(cv1), KarmaOutput(cv4)],
            [KarmaOutput(cv3), KarmaOutput(cv6)],
        ]

        self._mixers = [
            {
                'cv': cv2,
                'mix': self._sections[0],
                'previous_mix': LOW,
            },
            {
                'cv': cv5,
                'mix': self._sections[1],
                'previous_mix': LOW,
            },
        ]

        @b1.handler_falling
        def b1_pressed():
            if ticks_diff(ticks_ms(), b1.last_pressed()) > 300:
                # Show next output settings
                pass
            else:
                self.start_section(0)
                self.end_section(0)
                pass

        @b2.handler_falling
        def b2_pressed():
            if ticks_diff(ticks_ms(), b2.last_pressed()) > 300:
                # Select / Save setting
                pass
            else:
                self.start_section(1)
                self.end_section(1)
                pass

        @din.handler
        def din_started():
            self.start_section(0)

        @din.handler_falling
        def din_ended():
            self.end_section(0)

    def main(self):
        # Emulate din.handler and din.handler_falling for ain so that the analogue input can be used as a digital input
        self._ain_current_state = HIGH if ain.percent() > 1 else LOW

        if self._ain_current_state == HIGH and self._ain_previous_state == LOW:
            self.start_section(1)
        elif self._ain_current_state == LOW and self._ain_previous_state == HIGH:
            self.end_section(1)

        self._ain_previous_state = self._ain_current_state

        # Let each output do their thing
        for section in self._sections:
            for cv in section:
                cv.main()

        # Output the mix of cv1 and cv3 to cv2
        # Output the mix of cv4 and cv§ to cv5
        for mixer in self._mixers:
            mix = mixer.mix[0].output or mixer.mix[1].output

            if mix != mixer.previous_mix:
                mixer.cv.value(mix)
                mixer.previous_mix = mix

    def start_section(self, section):
        for cv in self._sections[section]:
            cv.start()

    def end_section(self, section):
        for cv in self._sections[section]:
            cv.end()

    def manually_start_section(self, section):
        for cv in self._sections[section]:
            cv.manual_start()

    def display_menu(self):
        pass


class KarmaOutput:
    BEGIN_AT_START = 0
    BEGIN_AT_END = 1

    def __init__(
            self,

            # The EuroPi output used by this output class
            cv,

            # When to begin the output
            # 0 = output starts when trigger starts
            # 1 = output starts when trigger stops
            # Whatever is chosen, the output is reset if a new trigger starts while the output is still being performed
            beginning=BEGIN_AT_START,

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
        # Config variables
        self._cv = cv
        self._beginning = beginning
        self._delay = delay
        self._duration = duration
        self._divisions = divisions
        self._repetitions = repetitions
        self._probability = probability
        self._probability_per_division = probability_per_division

        # Runtime variables
        self.output = LOW
        self._previous_output = LOW
        self._trigger_started_at = 0
        self._output_started_at = 0
        self._output_ended_at = 0
        self._division_started_at = 0
        self._occurrences = 0

    @classmethod
    def _can_output(cls, probability):
        return randint(1, 100) <= probability

    def _get_division_duration(self):
        return self._duration / (self._divisions * 2)

    def _start(self):
        if not self._can_output(self._probability):
            return

        self._trigger_started_at = time.ticks_ms()

    def _reset(self):
        self._trigger_started_at = 0
        self._division_started_at = 0
        self.output = LOW
        self._output_started_at = 0
        self._occurrences = 0

    def start(self):
        self._reset()

        if self._beginning == self.BEGIN_AT_START:
            self._start()

    def end(self):
        if self._beginning == self.BEGIN_AT_END:
            self._start()

    def manual_start(self):
        self._reset()
        self._start()

    def main(self):
        if self._trigger_started_at == 0:
            self.output = LOW
        else:
            current_time = time.ticks_ms()
            time_since_karma_beginning = time.ticks_diff(current_time, self._trigger_started_at)

            # Start the output
            if self._output_started_at == 0 and time_since_karma_beginning >= self._delay:
                self._output_started_at = current_time

            # End the karma run
            elif self._output_started_at > 0 and current_time - self._output_started_at >= self._duration:
                if self._repetitions > 0 and self._occurrences < self._repetitions:
                    if self._output_ended_at > 0:
                        self._output_ended_at = current_time
                    elif time.ticks_diff(current_time, self._output_ended_at) >= self._duration:
                        self._occurrences += 1
                        self._reset()
                        self._start()
                else:
                    self._occurrences = 0
                    self._reset()

            # Handle the current division
            if self._output_started_at > 0 and self._output_ended_at == 0:
                if self._division_started_at == 0:
                    self._division_started_at = current_time

                    if self._can_output(self._probability_per_division):
                        self.output = HIGH

                else:
                    division_running_time = time.ticks_diff(current_time, self._division_started_at)
                    division_duration = self._get_division_duration()
                    full_division_duration = division_duration * 2

                    if division_duration <= division_running_time < full_division_duration:
                        self.output = LOW
                    elif division_running_time >= full_division_duration:
                        self._division_started_at = 0

        if self.output != self._previous_output:
            self._previous_output = self.output
            self._cv.value(self.output)


if __name__ == '__main__':
    Karma().main()
