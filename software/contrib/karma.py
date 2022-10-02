from europi import *
from time import ticks_diff, ticks_ms
from random import randint
from europi_script import EuroPiScript


class KarmaMenu:
    """
    Sets the delay between each check of k2 to define on which setting the user is
    Decreasing it will make the menu more responsive at the expense of performances
    """
    SETTING_SELECTION_CHECK_DELAY = 200

    def __init__(self, pages):
        duration_options = list(range(0, 10000, 100))
        duration_options[0] = 10

        self.settings = [
            {
                'display': 'Begin at',
                'name': 'beginning',
                'options': [
                    'Start', 'End'
                ],
            },
            {
                'display': 'Delay (ms)',
                'name': 'delay',
                'options': list(range(0, 10000, 100)),
                'fine': list(range(0, 100, 10)),
            },
            {
                'display': 'Duration (ms)',
                'name': 'duration',
                'options': duration_options,
                'fine': list(range(0, 100, 10)),
            },
            {
                'display': 'Divisions',
                'name': 'divisions',
                'options': list(range(0, 100 + 1)),
            },
            {
                'display': 'Repetitions',
                'name': 'repetitions',
                'options': list(range(0, 100 + 1)),
            },
            {
                'display': 'Probability',
                'name': 'probability',
                'options': list(range(0, 100 + 1, 10)),
                'fine': list(range(0, 10)),
            },
            {
                'display': 'Proba / div',
                'name': 'probability_per_division',
                'options': list(range(0, 100 + 1, 10)),
                'fine': list(range(0, 10)),
            },
        ]

        self._pages = pages
        self._current_page = 0
        self._current_setting = None
        self._current_value = None
        self._current_state = ''
        self._previous_state = ''
        self._selected_setting = k2.choice(self.settings)
        self._selected_setting_last_check = 0

    @classmethod
    def _centered_text(cls, s, y, color=1):
        """Displays the given text centered on its line"""
        x_offset = int((oled.width - ((len(s) + 1) * 7)) / 2) - 2
        oled.text(s, x_offset, y, color)

    @classmethod
    def _arrow(cls, y, direction='left', size=4, color=1):
        """Display an array of the desired size pointing left or right"""
        for i in range(size):
            x = 2 + i if direction == 'left' else oled.width - 2 - i
            oled.line(x, y - i, x, y + i, color)

    def _get_current_state(self):
        """Generate a string representing the current state of the menu"""
        current_setting = self._current_setting["name"] if self._current_setting["name"] else self._selected_setting
        return f'{self._current_page},{current_setting},{self._current_value}'

    def handle_button1(self, press_time):
        # Cancel setting edit on long press
        if press_time > 3000:
            self._current_setting = None
            self._current_value = None
            return

        # Switch page if shorter press
        if self._current_page == len(self._pages):
            self._current_page = 0
            return

        self._current_page += 1

    def handle_button2(self):
        # If no setting is being edited: Select highlighted setting
        if not self._current_setting:
            self._current_setting = k2.choice(self.settings)
            return

        # If a setting is being edited: Save currently edited setting
        value = self._current_value

        if self._current_page == 0:
            value = KarmaOutput.BEGIN_AT_START if self._current_value == 'Start' else KarmaOutput.BEGIN_AT_END

        setattr(self._pages[self._current_page]['cv'], self._current_setting['name'], value)

        self._current_setting = None
        self._current_value = None

    def _display(self):
        current_page = self._pages[self._current_page]
        selected_setting = self._current_setting if self._current_setting else self._selected_setting

        oled.fill(0)

        # Show header
        oled.fill_rect(0, 0, oled.width, CHAR_HEIGHT + 2, 1)
        self._centered_text(f'IN[{current_page["input"]}] OUT[{current_page["output"]}]', 2, 0)

        # Show currently hovered or selected setting
        if not self._current_setting:
            if self._selected_setting != self.settings[0]:
                self._arrow(16)

            if self._selected_setting != self.settings[-1]:
                self._arrow(16, 'right')

        self._centered_text(f'{selected_setting["display"]}', 13)

        # Show setting value
        if self._current_value:
            if self._current_value != selected_setting['options'][0]:
                self._arrow(26)

            if self._current_value != selected_setting['options'][-1]:
                self._arrow(26, 'right')

            self._centered_text(f'{self._current_value}', 23)
        else:
            value = getattr(self._pages[self._current_page]["cv"], selected_setting["name"])

            if self._current_page == 0:
                value = 'Start' if value == KarmaOutput.BEGIN_AT_START else 'End'

            self._centered_text(f'{value}', 23)

        oled.show()

    def main(self):
        # Check the value of k1 and k2 to change the selected setting
        if self._current_setting:
            self._current_value = k2.choice(self._current_setting['options'])

            if 'fine' in self._current_setting:
                self._current_value += k1.choice(self._current_setting['fine'])
        elif ticks_diff(ticks_ms(), self._selected_setting_last_check) > self.SETTING_SELECTION_CHECK_DELAY:
            self._selected_setting = k2.choice(self.settings)
            self._selected_setting_last_check = ticks_ms()

        self._current_state = self._get_current_state()

        if self._current_state != self._previous_state:
            self._display()
            self._previous_state = self._current_state


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

        self._menu = KarmaMenu([
            {'cv': self._sections[0][0], 'output': '1', 'input': 1},
            {'cv': self._sections[0][1], 'output': '4', 'input': 1},
            {'cv': self._sections[1][0], 'output': '3', 'input': 2},
            {'cv': self._sections[1][1], 'output': '6', 'input': 2},
        ])

        @b1.handler_falling
        def b1_pressed():
            press_time = ticks_diff(ticks_ms(), b1.last_pressed())
            if press_time > 300:
                self._menu.handle_button1(press_time)
            else:
                self.start_section(0)
                self.end_section(0)

        @b2.handler_falling
        def b2_pressed():
            if ticks_diff(ticks_ms(), b2.last_pressed()) > 300:
                self._menu.handle_button2()
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

    def start_section(self, section):
        for cv in self._sections[section]:
            cv.start()

    def end_section(self, section):
        for cv in self._sections[section]:
            cv.end()

    def manually_start_section(self, section):
        for cv in self._sections[section]:
            cv.manual_start()

    def main(self):
        # Emulate din.handler and din.handler_falling for ain so that the analogue input can be used as a digital input
        self._ain_current_state = HIGH if ain.percent() > 0.9 else LOW

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
            mix = mixer['mix'][0].output or mixer['mix'][1].output

            if mix != mixer['previous_mix']:
                mixer['cv'].value(mix)
                mixer['previous_mix'] = mix


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

    @property
    def beginning(self):
        return self._beginning

    @beginning.setter
    def beginning(self, value):
        if value not in [self.BEGIN_AT_START, self.BEGIN_AT_END]:
            raise ValueError(f"Beginning can only be set to {self.BEGIN_AT_START} or {self.BEGIN_AT_END}")

        self._beginning = value

    @property
    def delay(self):
        return self._delay

    @delay.setter
    def delay(self, value):
        if not isinstance(value, int) or not 0 <= value <= 10000:
            raise ValueError(f"Delay can only be set to an integer between 0 and 10000")

        self._delay = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        if not isinstance(value, int) or not 10 <= value <= 10000:
            raise ValueError(f"Duration can only be set to an integer between 10 and 10000")

        self._duration = value

    @property
    def divisions(self):
        return self._divisions

    @divisions.setter
    def divisions(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Divisions can only be set to an integer between 1 and 100")

        self._divisions = value

    @property
    def repetitions(self):
        return self._repetitions

    @repetitions.setter
    def repetitions(self, value):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError(f"Repetitions can only be set to an integer between 0 and 100")

        self._repetitions = value

    @property
    def probability(self):
        return self._probability

    @probability.setter
    def probability(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Probability can only be set to an integer between 1 and 100")

        self._probability = value

    @property
    def probability_per_division(self):
        return self._probability_per_division

    @probability_per_division.setter
    def probability_per_division(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Probability per division can only be set to an integer between 1 and 100")

        self._probability_per_division = value

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
