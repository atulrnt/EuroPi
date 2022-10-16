from europi import *
from time import ticks_diff, ticks_ms
from random import randint
from europi_script import EuroPiScript
from experimental.knobs import LockableKnob
import framebuf


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
            beginning: int = 0,

            # How long should we wait before starting the output (in ms)
            delay: int = 0,

            # How long should the output go for (in ms)
            duration: int = 100,

            # How many sub-output should the output be divided into
            # Useful to output bursts of triggers, sounds great on MI Rings for instance
            divisions: int = 1,

            # How many times should the output be repeated
            repetitions: int = 0,

            # The percentage of probability for an output to happen
            probability: int = 100,

            # The percentage of probability for an output division to happen
            probability_per_division: int = 100,
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
        self._trigger_started_at = None
        self._output_started_at = None
        self._output_ended_at = None
        self._division_started_at = None
        self._occurrences = 0

    @property
    def beginning(self) -> int:
        return self._beginning

    @beginning.setter
    def beginning(self, value):
        if value not in [self.BEGIN_AT_START, self.BEGIN_AT_END]:
            raise ValueError(
                f"Beginning can only be set to {self.BEGIN_AT_START} or {self.BEGIN_AT_END}, {value} received")

        self._beginning = value

    @property
    def delay(self) -> int:
        return self._delay

    @delay.setter
    def delay(self, value):
        if not isinstance(value, int) or not 0 <= value <= 10000:
            raise ValueError(f"Delay can only be set to an integer between 0 and 10000, {value} received")

        self._delay = value

    @property
    def duration(self) -> int:
        return self._duration

    @duration.setter
    def duration(self, value):
        if not isinstance(value, int) or not 10 <= value <= 10000:
            raise ValueError(f"Duration can only be set to an integer between 10 and 10000, {value} received")

        self._duration = value

    @property
    def divisions(self) -> int:
        return self._divisions

    @divisions.setter
    def divisions(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Divisions can only be set to an integer between 1 and 100, {value} received")

        self._divisions = value

    @property
    def repetitions(self) -> int:
        return self._repetitions

    @repetitions.setter
    def repetitions(self, value):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError(f"Repetitions can only be set to an integer between 0 and 100, {value} received")

        self._repetitions = value

    @property
    def probability(self) -> int:
        return self._probability

    @probability.setter
    def probability(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Probability can only be set to an integer between 1 and 100, {value} received")

        self._probability = value

    @property
    def probability_per_division(self) -> int:
        return self._probability_per_division

    @probability_per_division.setter
    def probability_per_division(self, value):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(
                f"Probability per division can only be set to an integer between 1 and 100, {value} received")

        self._probability_per_division = value

    @classmethod
    def _can_output(cls, probability: int) -> bool:
        return randint(1, 100) <= probability

    def _get_division_duration(self) -> float:
        if self._divisions == 1:
            return self._duration

        return self._duration / ((self._divisions * 2) + 1)

    def _start(self):
        if not self._can_output(self._probability):
            return

        self._trigger_started_at = time.ticks_ms()

    def _reset(self):
        self.output = LOW
        self._occurrences = 0
        self._trigger_started_at = None
        self._division_started_at = None
        self._output_started_at = None

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
        if not self._trigger_started_at:
            self.output = LOW
        else:
            current_time = time.ticks_ms()

            # Start the output
            if not self._output_started_at and time.ticks_diff(current_time, self._trigger_started_at) >= self._delay:
                self._output_started_at = current_time

            # End the karma run
            elif self._output_started_at and time.ticks_diff(current_time, self._output_started_at) >= self._duration:
                if self._repetitions > 0 and self._occurrences < self._repetitions:
                    if self._output_ended_at:
                        self._output_ended_at = current_time
                    elif time.ticks_diff(current_time, self._output_ended_at) >= self._duration:
                        self._occurrences += 1
                        self._reset()
                        self._start()
                else:
                    self._occurrences = 0
                    self._reset()

            # Handle the current division
            if self._output_started_at and not self._output_ended_at:
                if not self._division_started_at:
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
                        self._division_started_at = None

        if self.output != self._previous_output:
            self._previous_output = self.output
            self._cv.value(self.output)


class KarmaDisplay:
    """
    A class to handle the display for the Karma script
    """

    """
    Sets the delay between each check of k2 to define on which setting the user is
    Decreasing it will make the menu more responsive at the expense of performances
    """
    SETTING_SELECTION_CHECK_DELAY = 200

    """
    Sets the delay in ms before which the menu is closed.
    The menu is constantly checking for Knobs positions which is impacting the script performances,
    by closing the menu after some time allows for the script to goes back to a faster run time.
    Pixels can also burn if they stay active for an extended period of time.
    """
    MENU_DELAY = 10000

    active_triggers = [False, False]

    def __init__(self, pages: list):
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
                'fine': list(range(0, 100 + 1, 10)),
            },
            {
                'display': 'Duration (ms)',
                'name': 'duration',
                'options': duration_options,
                'fine': list(range(0, 100 + 1, 10)),
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
                'options': list(range(0, 100, 10)),
                'fine': list(range(0, 10 + 1)),
            },
            {
                'display': 'Proba / div',
                'name': 'probability_per_division',
                'options': list(range(0, 100, 10)),
                'fine': list(range(0, 10 + 1)),
            },
        ]

        self._pages_knob = LockableKnob(k1, 0)
        self._pages_knob.request_unlock()

        self._pages = pages
        self._current_page = 0
        self._current_setting = None
        self._current_value = None
        self._current_state = ''
        self._previous_state = ''
        self._selected_setting = k2.choice(self.settings)
        self._selected_setting_last_check = ticks_ms()
        self._is_menu_opened = True
        self._menu_last_action = ticks_ms()
        self._triggers_sizes = [0, 0]

        self._quit_settings = False

        self._spaceship = framebuf.FrameBuffer(bytearray([
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x1f, 0xff,
            0xff, 0x80, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfc, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfc,
            0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfc, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00,
            0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xf0, 0x03, 0xf8, 0x00, 0x00, 0x00,
            0x0f, 0xf0, 0x03, 0xf8, 0x00, 0x00, 0x00, 0x0f, 0xf0, 0x01, 0xf8, 0x00, 0x00, 0x00, 0x01, 0xfe,
            0x00, 0xff, 0x00, 0x00, 0x00, 0x01, 0xfe, 0x00, 0xff, 0x00, 0x00, 0x03, 0xff, 0xff, 0xfc, 0xff,
            0xc0, 0x00, 0x03, 0xff, 0xff, 0xfc, 0xff, 0xc0, 0x00, 0x00, 0x3f, 0xff, 0xff, 0xff, 0xff, 0x80,
            0x00, 0x3f, 0xff, 0xff, 0xff, 0xff, 0x80, 0x00, 0x3f, 0xff, 0xff, 0xff, 0xff, 0x80, 0x03, 0xff,
            0xff, 0xfc, 0xff, 0xc0, 0x00, 0x03, 0xff, 0xff, 0xfc, 0xff, 0xc0, 0x00, 0x00, 0x01, 0xfe, 0x00,
            0xff, 0x00, 0x00, 0x00, 0x01, 0xfe, 0x00, 0xff, 0x00, 0x00, 0x00, 0x01, 0xfe, 0x00, 0xff, 0x00,
            0x00, 0x00, 0x0f, 0xf0, 0x03, 0xf8, 0x00, 0x00, 0x00, 0x0f, 0xf0, 0x03, 0xf8, 0x00, 0x00, 0x1f,
            0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff,
            0xfc, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfc, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfc, 0x00,
            0x00, 0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00, 0x1f, 0xff, 0xff, 0x80, 0x00, 0x00, 0x00
        ]), 49, 32, framebuf.MONO_HLSB)

    def open_menu(self):
        self._is_menu_opened = True
        self._menu_last_action = time.ticks_ms()

    def handle_button1(self, press_time: int):
        # Cancel setting edit on long press
        if press_time > 3000:
            self._current_setting = None
            self._current_value = None
            return

        # Switch page if shorter press
        if self._current_page == len(self._pages) - 1:
            self._current_page = 0
            return

        self._current_page += 1

    def handle_button2(self, press_time: int):
        # If no setting is being edited: Select highlighted setting
        if not self._current_setting:
            self._current_setting = k2.choice(self.settings)
            return

        # If a setting is being edited: Save currently edited setting
        value = self._current_value

        if self._current_setting['name'] == 'beginning':
            value = KarmaOutput.BEGIN_AT_START if self._current_value == 'Start' else KarmaOutput.BEGIN_AT_END

        setattr(self._pages[self._current_page]['cv'], self._current_setting['name'], value)

        self._quit_settings = True

    def _display_menu(self):
        current_page = self._pages[self._current_page]
        selected_setting = self._current_setting if self._current_setting else self._selected_setting

        oled.fill(0)

        # Show currently selected page
        oled.fill_rect(0, 1, oled.width, CHAR_HEIGHT + 1, 1)
        if self._current_page != 0:
            oled.arrow(2, 5, oled.DIRECTION_LEFT, colour=0)

        if self._current_page != len(self._pages) - 1:
            oled.arrow(2, 5, oled.DIRECTION_RIGHT, colour=0)

        oled.centred_text_line(f'IN[{current_page["input"]}] OUT[{current_page["output"]}]', 2, 0)

        # Show currently hovered or selected setting
        if not self._current_setting:
            if self._selected_setting != self.settings[0]:
                oled.arrow(2, 16, oled.DIRECTION_LEFT)

            if self._selected_setting != self.settings[-1]:
                oled.arrow(2, 16, oled.DIRECTION_RIGHT)

        oled.centred_text_line(f'{selected_setting["display"]}', 13)

        # Show setting value
        if self._current_value:
            if self._current_value != selected_setting['options'][0]:
                oled.arrow(2, 26, oled.DIRECTION_LEFT)

            if self._current_value != selected_setting['options'][-1]:
                oled.arrow(2, 26, oled.DIRECTION_RIGHT)

            oled.centred_text_line(f'{self._current_value}', 23)
        else:
            value = getattr(self._pages[self._current_page]['cv'], selected_setting['name'])

            if selected_setting['name'] == 'beginning':
                value = 'Start' if value == KarmaOutput.BEGIN_AT_START else 'End'

            oled.centred_text_line(f'{value}', 23)

        oled.show()

    def _display_screensaver(self):
        self._current_state = f'{self.active_triggers},{self._triggers_sizes}'

        if self._current_state != self._previous_state:
            self._previous_state = self._current_state
            enabled = False

            oled.fill(0)

            for i in range(0, 2):
                if self.active_triggers[i]:
                    self._triggers_sizes[i] = 32

                if self._triggers_sizes[i] < oled.width:
                    if enabled == False:
                        oled.blit(self._spaceship, 0, 0)

                    enabled = True
                    oled.rect(self._triggers_sizes[i], (3 if i == 0 else 27), 3, 2, 1)

                    accel = oled.width / 3

                    if self._triggers_sizes[i] > accel:
                        self._triggers_sizes[i] += 4
                    elif self._triggers_sizes[i] > accel * 2:
                        self._triggers_sizes[i] += 2
                    else:
                        self._triggers_sizes[i] += 1
                '''
                if self.active_triggers[i]:
                    self._triggers_sizes[i] = oled.height

                if self._triggers_sizes[i] > 0:
                    oled.arrow((10 if i == 0 else oled.width - 11), self._triggers_sizes[i] - 10, oled.DIRECTION_TOP, 10)
                    accel = oled.height / 3

                    if self._triggers_sizes[i] < accel:
                        self._triggers_sizes[i] -= 4
                    elif self._triggers_sizes[i] < accel * 2:
                        self._triggers_sizes[i] -= 2
                    else:
                        self._triggers_sizes[i] -= 1
                '''

            oled.show()

    def main(self):
        if not self._is_menu_opened:
            # self._display_screensaver()
            self._display_menu()
            return

        if ticks_diff(time.ticks_ms(), self._menu_last_action) >= self.MENU_DELAY:
            self._previous_state = 'screensaver'
            self._is_menu_opened = False
            # self._display_screensaver()
            self._display_menu()
            return

        # Check the value of k1 and k2 to change the selected setting
        if self._current_setting is not None:

            # Lock the page selection knob during settings edit
            if self._pages_knob.state != LockableKnob.STATE_UNLOCKED:
                self._pages_knob.lock()

            self._current_value = k2.choice(self._current_setting['options'])

            if 'fine' in self._current_setting:
                self._current_value += k1.choice(self._current_setting['fine'])
        elif ticks_diff(ticks_ms(), self._selected_setting_last_check) > self.SETTING_SELECTION_CHECK_DELAY:
            self._current_page = self._pages_knob.choice(list(range(0, len(self._pages))))
            self._selected_setting = k2.choice(self.settings)
            self._selected_setting_last_check = ticks_ms()

        current_setting = self._current_setting["name"] if self._current_setting else self._selected_setting['name']
        self._current_state = f'{self._current_page},{current_setting},{self._current_value}'

        if self._current_state != self._previous_state:
            self.open_menu()
            self._display_menu()
            self._previous_state = self._current_state

        if self._quit_settings:
            self._quit_settings = False
            self._current_setting = None
            self._current_value = None

            # Unlock the page selection knob
            self._pages_knob.request_unlock()


class Karma(EuroPiScript):
    def __init__(self):
        super().__init__()

        self._ain_current_state = LOW
        self._ain_previous_state = LOW

        self._sections = [
            [
                KarmaOutput(
                    cv1,
                    KarmaOutput.BEGIN_AT_START,
                    0,
                    1000,
                    1,
                    0,
                    100,
                    100
                ),
                KarmaOutput(
                    cv4,
                    KarmaOutput.BEGIN_AT_START,
                    0,
                    1000,
                    1,
                    1,
                    100,
                    100
                ),
                KarmaOutput(
                    cv3,
                    KarmaOutput.BEGIN_AT_START,
                    0,
                    1000,
                    1,
                    0,
                    100,
                    100
                ),
                KarmaOutput(
                    cv6,
                    KarmaOutput.BEGIN_AT_START,
                    0,
                    1000,
                    10,
                    0,
                    100,
                    100
                ),
            ],
            [KarmaOutput(cv3), KarmaOutput(cv6)],
        ]

        self._mixers = [
            {
                'cv': cv2,
                'mix': self._sections[0],
                'previous_mix': LOW,
                'type': 'or',
            },
            {
                'cv': cv5,
                'mix': self._sections[1],
                'previous_mix': LOW,
                'type': 'xor',
            },
        ]

        self._display = KarmaDisplay([
            {'cv': self._sections[0][0], 'output': '1', 'input': 1},
            {'cv': self._sections[0][1], 'output': '4', 'input': 1},
            {'cv': self._sections[1][0], 'output': '3', 'input': 2},
            {'cv': self._sections[1][1], 'output': '6', 'input': 2},
        ])

        buttons = [b1, b2]

        def handle_button_pressed(button: int, handler):
            press_time = ticks_diff(time.ticks_ms(), buttons[button - 1].last_pressed())

            # Manual trigger
            if press_time < 300:
                self.start_section(button - 1)
                self.end_section(button - 1)
                return

            # Access menu
            self._display.open_menu()
            handler(press_time)

        @b1.handler_falling
        def b1_pressed():
            handle_button_pressed(0, self._display.handle_button1)

        @b2.handler_falling
        def b2_pressed():
            handle_button_pressed(1, self._display.handle_button2)

        @din.handler
        def din_started():
            self.start_section(0)

        @din.handler_falling
        def din_ended():
            self.end_section(0)

    def start_section(self, section: int):
        self._display.active_triggers[section] = True

        for cv in self._sections[section]:
            cv.start()

    def end_section(self, section: int):
        self._display.active_triggers[section] = False

        for cv in self._sections[section]:
            cv.end()

    def manually_start_section(self, section: int):
        for cv in self._sections[section]:
            cv.manual_start()

    def main(self):
        while True:
            # Emulate din.handler and din.handler_falling for ain so that it can be used as a din2
            self._ain_current_state = HIGH if ain.percent() > 0.9 else LOW

            if self._ain_current_state == HIGH and self._ain_previous_state == LOW:
                self.start_section(1)

            if self._ain_current_state == LOW and self._ain_previous_state == HIGH:
                self.end_section(1)

            self._ain_previous_state = self._ain_current_state

            # Let each output do their thing
            for section in self._sections:
                for cv in section:
                    cv.main()

            # Output the mix
            for mixer in self._mixers:
                if mixer['type'] == 'or':
                    mix = mixer['mix'][0].output or mixer['mix'][1].output
                else:
                    mix = mixer['mix'][0].output != mixer['mix'][1].output

                if mix != mixer['previous_mix']:
                    mixer['cv'].value(mix)
                    mixer['previous_mix'] = mix

            self._display.main()


if __name__ == '__main__':
    Karma().main()



