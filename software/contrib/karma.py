from europi import *
from europi_script import EuroPiScript
from experimental.knobs import LockableKnob
from random import randint
from time import ticks_diff, ticks_ms


# Extend EuroPiScript to allow for each output to manage its own state, the main class is Karma
class KarmaOutput(EuroPiScript):
    """
    A class that performs the output logic, each output being independent
    """

    BEGIN_AT_START = 0
    BEGIN_AT_END = 1

    def __init__(self, cv: Output):
        super().__init__()

        # Config variables
        self._cv = cv
        self._id = cvs.index(cv)
        self._global_state = self.load_state_json()
        self._state = self._global_state.get(f'{self._id}', {
            'beginning': 0,
            'delay': 0,
            'duration': 100,
            'divisions': 1,
            'repetitions': 0,
            'probability': 100,
            'division_probability': 100,
        })

        # When to begin the output
        # 0 = output starts when trigger starts
        # 1 = output starts when trigger stops
        # Whatever is chosen, the output is reset if a new trigger starts while the output is still being performed
        self._beginning = self._state['beginning']

        # How long should we wait before starting the output (in ms)
        self._delay = self._state['delay']

        # How long should the output go for (in ms)
        self._duration = self._state['duration']

        # How many sub-output should the output be divided into
        # Useful to output bursts of triggers, sounds great on MI Rings for instance
        self._divisions = self._state['divisions']

        # How many times should the output be repeated
        self._repetitions = self._state['repetitions']

        # The percentage of probability for an output to happen
        self._probability = self._state['probability']

        # The percentage of probability for an output division to happen
        self._division_probability = self._state['division_probability']

        # Runtime variables
        self.output = LOW
        self._previous_output = LOW
        self._trigger_started_at = None
        self._output_started_at = None
        self._output_ended_at = None
        self._division_started_at = None
        self._occurrences = 0
        self._division_occurrences = 0

    # Override parent method to allow each output to manage its own state inside a single file
    @property
    def _state_filename(self) -> str:
        return 'saved_state_Karma.txt'

    @property
    def beginning(self) -> int:
        return self._beginning

    @beginning.setter
    def beginning(self, value: int):
        if value not in [self.BEGIN_AT_START, self.BEGIN_AT_END]:
            raise ValueError(
                f"Beginning can only be set to {self.BEGIN_AT_START} or {self.BEGIN_AT_END}, {value} received")

        self._beginning = value
        self._save_setting('beginning', value)

    @property
    def delay(self) -> int:
        return self._delay

    @delay.setter
    def delay(self, value: int):
        if not isinstance(value, int) or not 0 <= value <= 10000:
            raise ValueError(f"Delay can only be set to an integer between 0 and 10000, {value} received")

        self._delay = value
        self._save_setting('delay', value)

    @property
    def duration(self) -> int:
        return self._duration

    @duration.setter
    def duration(self, value: int):
        if not isinstance(value, int) or not 10 <= value <= 10000:
            raise ValueError(f"Duration can only be set to an integer between 10 and 10000, {value} received")

        self._duration = value
        self._save_setting('duration', value)

    @property
    def divisions(self) -> int:
        return self._divisions

    @divisions.setter
    def divisions(self, value: int):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Divisions can only be set to an integer between 1 and 100, {value} received")

        self._divisions = value
        self._save_setting('divisions', value)

    @property
    def repetitions(self) -> int:
        return self._repetitions

    @repetitions.setter
    def repetitions(self, value: int):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError(f"Repetitions can only be set to an integer between 0 and 100, {value} received")

        self._repetitions = value
        self._save_setting('repetitions', value)

    @property
    def probability(self) -> int:
        return self._probability

    @probability.setter
    def probability(self, value: int):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(f"Probability can only be set to an integer between 1 and 100, {value} received")

        self._probability = value
        self._save_setting('probability', value)

    @property
    def division_probability(self) -> int:
        return self._division_probability

    @division_probability.setter
    def division_probability(self, value: int):
        if not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError(
                f"Probability per division can only be set to an integer between 1 and 100, {value} received")

        self._division_probability = value
        self._save_setting('division_probability', value)

    def _save_setting(self, key: str, value: int):
        """Saves the output configuration in the global state"""
        self._state[key] = value
        self._global_state[self._id] = self._state
        self.save_state_json(self._global_state)

    @classmethod
    def _can_output(cls, probability: int) -> bool:
        """Checks if the trigger can be output based on its probability setting"""
        if probability == 100:
            return True

        return randint(1, 100) <= probability

    def _get_division_duration(self) -> float:
        """Returns the duration of a division based on the number of division and total output duration"""
        if self._divisions == 1:
            return self._duration

        return self._duration / (self._divisions * 2)

    def _start(self):
        """Starts the trigger output"""
        if not self._can_output(self._probability):
            return

        self._trigger_started_at = time.ticks_ms()

    def _reset(self):
        """Reset the output state as if it hadn't been triggered"""
        self.output = LOW
        self._trigger_started_at = None
        self._output_started_at = None
        self._division_started_at = None
        self._division_occurrences = 0

    def start(self):
        """An input trigger has started, triggers the output if set to begin at input start"""
        self._reset()

        if self._beginning == self.BEGIN_AT_START:
            self._start()

    def end(self):
        """An input trigger has ended, triggers the output if set to begin at input end"""
        if self._beginning == self.BEGIN_AT_END:
            self._start()

    def main(self):
        if not self._trigger_started_at:
            self.output = LOW
        else:
            # Start the output
            if not self._output_started_at and time.ticks_diff(time.ticks_ms(), self._trigger_started_at) >= self._delay:
                self._output_started_at = time.ticks_ms()

            # End the output run
            elif self._output_started_at and time.ticks_diff(time.ticks_ms(), self._output_started_at) >= self._duration:
                if self._repetitions > 0 and self._occurrences < self._repetitions:
                    if not self._output_ended_at:
                        self._output_ended_at = time.ticks_ms()
                    elif time.ticks_diff(time.ticks_ms(), self._output_ended_at) >= self._duration:
                        self._occurrences += 1
                        self._reset()
                        self._start()
                else:
                    self._occurrences = 0
                    self._output_ended_at = None
                    self._reset()

            # Handle the current division
            if self._output_started_at:
                if not self._division_started_at and self._division_occurrences < self._divisions:
                    self._division_started_at = time.ticks_ms()

                    if self._can_output(self._division_probability):
                        self.output = HIGH
                else:
                    division_running_time = time.ticks_diff(time.ticks_ms(), self._division_started_at)
                    division_duration = self._get_division_duration()
                    full_division_duration = division_duration * 2

                    if division_duration <= division_running_time < full_division_duration:
                        self.output = LOW
                    elif division_running_time >= full_division_duration:
                        self._division_occurrences += 1
                        self._division_started_at = None
            else:
                self.output = LOW

        # Change the output only if it actually changed
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
    SETTING_SELECTION_CHECK_DELAY = 100

    """
    Sets the delay in ms before which the menu is closed.
    The menu is constantly checking for Knobs positions which is impacting the script performances,
    by closing the menu after some time allows for the script to goes back to a faster run time.
    Pixels can also burn if they stay active for an extended period of time.
    """
    MENU_DELAY = 1000 * 10

    DIRECTION_LEFT = 0
    DIRECTION_RIGHT = 1
    DIRECTION_TOP = 2
    DIRECTION_BOTTOM = 3

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
                'name': 'division_probability',
                'options': list(range(0, 100, 10)),
                'fine': list(range(0, 10 + 1)),
            },
        ]

        self._pages_knob = LockableKnob(k1, threshold_percentage=0)
        self._pages_knob.request_unlock()
        self._settings_knob = LockableKnob(k2)
        self._settings_knob.request_unlock()

        self._pages = pages
        self._current_page = 0
        self._current_setting = None
        self._current_value = None
        self._current_state = ''
        self._previous_state = ''
        self._selected_setting = self.settings[0]
        self._selected_setting_last_check = ticks_ms()
        self._is_menu_opened = True
        self._quit_settings = False
        self._menu_last_action = ticks_ms()

    def open_menu(self):
        """Marks the menu as opened for the display to go/stay awake"""
        self._is_menu_opened = True
        self._menu_last_action = time.ticks_ms()

    def quit_settings(self):
        """Exits the current setting edition"""
        self._quit_settings = False
        self._current_setting = None
        self._current_value = None

        # Unlock the page selection and setting knobs when not editing a setting anymore
        self._pages_knob.request_unlock()
        self._settings_knob.request_unlock()

    def handle_button1(self):
        """Handles the button 1 functionalities"""
        menu_state = self._is_menu_opened

        self.open_menu()

        if not menu_state:
            return

        # If no setting is being edited: Select highlighted setting
        if not self._current_setting:
            self._current_setting = self._settings_knob.choice(self.settings)
            return

        # If a setting is being edited: Cancel setting edit
        self._quit_settings = True

    def handle_button2(self):
        """Handles the button 2 functionalities"""
        menu_state = self._is_menu_opened

        self.open_menu()

        # If the menu was previously not opened (screen in sleep state),
        # open the menu but do not select the current setting
        if not menu_state:
            return

        # If no setting is being edited: Select highlighted setting
        if not self._current_setting:
            self._current_setting = self._settings_knob.choice(self.settings)
            return

        # If a setting is being edited: Save currently edited setting
        value = self._current_value

        # The "beginning" setting is the only one displayed as a string instead of an integer
        # It needs to be interpreted before being saved
        if self._current_setting['name'] == 'beginning':
            value = KarmaOutput.BEGIN_AT_START if self._current_value == 'Start' else KarmaOutput.BEGIN_AT_END

        # Update the setting in the selected KarmaOutput
        setattr(self._pages[self._current_page]['cv'], self._current_setting['name'], value)

        self._quit_settings = True

    def centred_text_line(self, text: str, y: int, colour: int = 1):
        """Displays the given text horizontally centered on its line."""
        x_offset = int((oled.width - ((len(text) + 1) * 7)) / 2) - 1
        oled.text(text, x_offset, y, colour)

    def arrow(self, x: int, y: int, direction: int = None, size: int = 4, colour: int = 1):
        """Displays an arrow of the desired size and colour pointing left, right, top or bottom.
        Use the class constants DIRECTION_LEFT, DIRECTION_RIGHT, DIRECTION_TOP and DIRECTION_BOTTOM
        to set the direction."""
        direction = self.DIRECTION_LEFT if direction is None else direction

        if direction in [self.DIRECTION_LEFT, self.DIRECTION_RIGHT]:
            for i in range(size):
                xi = x + i if direction == self.DIRECTION_LEFT else oled.width - x - i - 1
                oled.line(xi, y - i, xi, y + i, colour)

            return

        for i in range(size):
            yi = y + i if direction == self.DIRECTION_TOP else oled.height - y - i - 1
            oled.line(x + i, yi, x - i, yi, colour)

    def _display_menu(self):
        """Displays the menu based on the current state"""
        current_page = self._pages[self._current_page]
        selected_setting = self._current_setting if self._current_setting else self._selected_setting

        oled.fill(0)

        # Show currently selected page
        oled.fill_rect(0, 1, oled.width, CHAR_HEIGHT + 1, 1)
        if self._current_page != 0:
            self.arrow(2, 5, self.DIRECTION_LEFT, colour=0)

        if self._current_page != len(self._pages) - 1:
            self.arrow(2, 5, self.DIRECTION_RIGHT, colour=0)

        self.centred_text_line(f'{current_page["input"]}', 2, 0)

        # Show currently hovered or selected setting
        if not self._current_setting:
            if self._selected_setting != self.settings[0]:
                self.arrow(2, 16, self.DIRECTION_LEFT)

            if self._selected_setting != self.settings[-1]:
                self.arrow(2, 16, self.DIRECTION_RIGHT)

        self.centred_text_line(f'{selected_setting["display"]}', 13)

        # Show setting value
        if self._current_value is not None:
            if self._current_value != selected_setting['options'][0]:
                self.arrow(2, 26, self.DIRECTION_LEFT)

            if self._current_value != selected_setting['options'][-1]:
                self.arrow(2, 26, self.DIRECTION_RIGHT)

            self.centred_text_line(f'{self._current_value}', 23)
        else:
            value = getattr(self._pages[self._current_page]['cv'], selected_setting['name'])

            if selected_setting['name'] == 'beginning':
                value = 'Start' if value == KarmaOutput.BEGIN_AT_START else 'End'

            self.centred_text_line(f'{value}', 23)

        oled.show()

    def main(self):
        # If the display is in sleep mode, directly exit this method to save resources
        if not self._is_menu_opened:
            return

        # If no action has been performed since MENU_DELAY, switch the display in sleep mode
        if ticks_diff(time.ticks_ms(), self._menu_last_action) >= self.MENU_DELAY:
            self.quit_settings()
            self._previous_state = 'screensaver'
            self._is_menu_opened = False

            oled.fill(0)
            oled.show()
            return

        # If the button 1 has been pressed during the edit of a setting, exit the edition without saving the value
        if self._quit_settings:
            self.quit_settings()

        # If a setting is currently being edited
        if self._current_setting is not None:
            # Lock the page selection knob during settings edit
            if self._pages_knob.state != LockableKnob.STATE_UNLOCKED:
                self._pages_knob.lock()

            # Lock the setting selection knob during settings edit
            if self._settings_knob.state != LockableKnob.STATE_UNLOCKED:
                self._settings_knob.lock()

            self._current_value = k2.choice(self._current_setting['options'])

            if 'fine' in self._current_setting:
                self._current_value += k1.choice(self._current_setting['fine'])

        # Only check for the setting selection every SETTING_SELECTION_CHECK_DELAY to save resources
        elif ticks_diff(ticks_ms(), self._selected_setting_last_check) > self.SETTING_SELECTION_CHECK_DELAY:
            self._current_page = self._pages_knob.range(len(self._pages))
            self._selected_setting = self._settings_knob.choice(self.settings)
            self._selected_setting_last_check = ticks_ms()

        current_setting = self._current_setting["name"] if self._current_setting else self._selected_setting['name']
        self._current_state = f'{self._current_page},{current_setting},{self._current_value}'

        # Update the display only if the state changed to save resources
        if self._current_state != self._previous_state:
            self.open_menu()
            self._display_menu()
            self._previous_state = self._current_state


class Karma(EuroPiScript):
    ANALOG_THRESHOLD = 0.3

    def __init__(self):
        super().__init__()

        self._ain_current_state = LOW
        self._ain_previous_state = LOW
        self._previous_mix = [LOW, LOW, LOW, LOW]

        self._output = [
            KarmaOutput(cv1),
            KarmaOutput(cv4),
        ]

        self._display = KarmaDisplay([
            {'cv': self._output[0], 'input': 'din'},
            {'cv': self._output[1], 'input': 'ain'},
        ])

        @b1.handler_falling
        def b1_pressed():
            self._display.handle_button1()

        @b2.handler_falling
        def b2_pressed():
            self._display.handle_button2()

        @din.handler
        def din_started():
            self._output[0].start()

        @din.handler_falling
        def din_ended():
            self._output[0].end()

    def main(self):
        while True:
            # Emulate din.handler and din.handler_falling for ain so that it can be used as a din2
            self._ain_current_state = HIGH if ain.percent() > self.ANALOG_THRESHOLD else LOW

            if self._ain_current_state == HIGH and self._ain_previous_state == LOW:
                self._output[1].start()

            if self._ain_current_state == LOW and self._ain_previous_state == HIGH:
                self._output[1].end()

            self._ain_previous_state = self._ain_current_state

            # Let each output do their thing
            for output in self._output:
                output.main()

            # Output different mix
            # CV2 = generated output 1 OR gate 1
            # CV3 = generated output 1 OR generated output 2
            # CV5 = generated output 2 OR gate 2
            # CV6 = generated output 1 XOR generated output 2
            mix = [
                self._output[0].output or din.value(),
                self._output[0].output or self._output[1].output,
                self._output[1].output or self._ain_current_state,
                self._output[0].output != self._output[1].output,
            ]

            if mix != self._previous_mix:
                self._previous_mix = mix
                
                for index, cv in enumerate([cv2, cv3, cv5, cv6]):
                    cv.value(HIGH if mix[index] else LOW)

            self._display.main()


if __name__ == '__main__':
    Karma().main()

