# Karma

author: Arthur LAURENT (github.com/atulrnt)

date: 01/10/2022

labels: gates, triggers, randomness, probability, utility

#### What goes around, comes around

Two independent triggers/gates manipulators.

Delay, stretch, multiply, divide, and add a touch of randomness to your triggers/gate.

    digital_in: Trigger/Gate 1 in
    analog_in: Trigger/Gate 2 in (analog is used as a fake digital)
    output_1 and 4: Output manipulation result for trigger 1
    output_3 and 6: Output manipulation result for trigger 2
    output_2: Output mix of output_1 and output_3 (OR logic)
    output_5: Output mix of output_4 and output_6 (OR logic)

    knob_1: 
      - If no setting is being edited: Cycle through output pages
      - If a setting is being edited: Fine change the setting value

    knob_2: 
      - If no setting is being edited: Cycle through the settings of the selected output
      - If a setting is being edited: Change the setting value

    button_1:
      - If screen is off: Switch screen on
      - If screen is on: Cancel setting edit

    button_2:
      - If screen is off: Switch screen on
      - If screen is on: 
        - If no setting is being edited: Select highlighted setting
        - If a setting is being edited: Save currently edited setting

# Usage

The settings are constantly displayed, there is no other output than the settings page.

Both input are used as digital input, the analogue input might a bit less precise than the digital output since it hasn't been made to handle digital signals as well the digital input.

## Settings

Use the Knob 1 to select a different setting to edit.

Use the Knob 2 to change the value of the setting to edit that you've selected with the Knob 1.

Use the buttons to the next / previous output settings.

### Beginning

The "beginning" setting define when the output starts.

Two options are available:
- At start: the output will be triggered as soon as the input trigger is received
- At end; the output will be triggered once the input trigger has stopped

Default: At start.

### Delay

The "delay" settings defines how long it should wait to output a gate once the output has been triggered.

The delay is set in milliseconds with a range between 0ms to 10s.

Default: 0ms.

### Duration

The "duration" setting defines for how long the output should stay on.

The duration is set in milliseconds with a range between 10ms to 10s.

Default: 100ms.

### Divisions

The "divisions" setting defines in how many trigger/gates there should in a triggered output.

For instance, if an output is set to last for 1s and to have 4 divisions, the actual output will be 4 shorter output of 125ms each separated by 4 delays of 125ms.
1s / 4 divisions, each division having an equally long high and low state.

If too many divisions are set in a short output, you might get less divisions than expected.

The number of divisions can be within a range of 1 (single output) to 100 (high number of divisions only make sense in long output).

Default: 1.

### Repetitions

The "repetitions" setting defines how many times the output should be repeated.

Each repetition will be separated by a delay as long as the output.

For instance, if an output is set to last for 1s and have 2 repetitions, there will be 3 similar output on the course of 5s.
3 output * 1s + 2 output separations * 1s.

The number of repetitions can be within a range of 0 (single output without repetition) to 100 (high number of repetitions would mostly make sense for short output).

The divisions and the repetitions mostly differ when used with the probability settings defined below.

Default: 0.

### Probability

The "probability" setting defines what are the chances for an output to happen.

The probability is a percentage of chance between 1 and 100%.

If an output is set to have some repetitions, each repetition will have its probability calculated individually.
So for instance, an output set to have 1 repetitions and a probability of 50% will most likely be output only once.

Default: 100%.

### Probability per division

The "probability per division" setting defines what are the chances for an output division to happen.

Exactly the same as the probability setting but applied to the divisions.

For instance, if an output is set to have 10 divisions and have a probability per division of 50%, it will most likely output only 5 divisions.

Default: 100%.

# Patch ideas

## Mutable Instruments Rings

I've made this script specifically to use it with MI Rings in my setup.

My goal was to trigger burst of random triggers to Rings' strum input at specific steps of my sequence.

## Self patching

It can be interesting to self patch the module, sending one output of the first trigger input into the second input to have some sort of cascading effect.

## Add probability to basic triggers

This script can also be used to simply add probability to any trigger by using the following settings for instance:
- Beginning: At start
- Delay: 0ms
- Duration: 10ms
- Divisions: 1
- Repetitions: 0
- Probability: 50%
- Probability per division: 100%