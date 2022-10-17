# Karma

author: Arthur LAURENT (github.com/atulrnt)

date: 01/10/2022

labels: gates, triggers, randomness, probability, utility

## What goes around, comes around

Two independent triggers/gates manipulators.

Delay, stretch, multiply, divide, and add a touch of randomness to your triggers/gate.

    digital_in: Trigger/Gate 1 in
    analog_in: Trigger/Gate 2 in (analog is used as a fake digital)
    output_1 and 4: Output manipulation result for trigger 1
    output_3 and 6: Output manipulation result for trigger 2
    output_2: Output mix of output_1 and output_3 (OR logic)
    output_5: Output mix of output_4 and output_6 (XOR logic)

    knob_1: 
      - If no setting is being edited: Cycle through output pages
      - If a setting is being edited: Fine change the setting value

    knob_2: 
      - If no setting is being edited: Cycle through the settings of the selected output
      - If a setting is being edited: Change the setting value

    button_1:
      - If screen is off: Switch screen on
      - If screen is on:
        - If no setting is being edited: Select highlighted setting
        - If a setting is being edited: Cancel setting edit

    button_2:
      - If screen is off: Switch screen on
      - If screen is on: 
        - If no setting is being edited: Select highlighted setting
        - If a setting is being edited: Save currently edited setting

## Usage

Output 1 and 4 are triggered with the digital input.  
Output 3 and 6 are triggered with the analog input used as digital.  
Output 2 is an OR gate of output 1 and 3.  
Output 5 is a XOR gate of output 4 and 6.

### Output/Menu configuration

You can completely change the input/output arrangement if you want.  
You could have 3 output linked to the 1st input, 2 output linked to the 2nd input and a single mix outputting an AND gate of the first 2 output.

All this is configured in the first lines of `Karma.main()`.

### Mix configuration

The mixing type for the output 2 and 5 can be changed by using the different constants in the code:
- MIX_TYPE_NONE: No mixing at all, the output will always be LOW
- MIX_TYPE_OR: OR gate
- MIX_TYPE_XOR: XOR gate
- MIX_TYPE_AND: AND gate

Just change the `Karma._mixers` variable to your need.
    
## Settings

### Beginning

The "beginning" setting defines when the output starts.

Two options are available:
- At start: the output will be triggered as soon as the input trigger is received
- At end: the output will be triggered once the input trigger has stopped (mainly useful when the input receives a gate)

**Default: At start**

### Delay

The "delay" settings defines how long it should wait before starting the output once the output has been triggered (depending on the "beginning" setting).  
The delay is set in milliseconds with a range between 0ms to 10s.

**Default: 0ms**

### Duration

The "duration" setting defines for how long the output should stay on.  
The duration is set in milliseconds with a range between 10ms to 10s.

**Default: 100ms**

### Divisions

The "divisions" setting defines in how many trigger/gates the output should be divided.

For instance, if an output is set to last for 1s and to have 4 divisions, the actual output will be 4 shorter output of 125ms each separated by 4 delays of 125ms.
1s / 4 divisions, each division having an equally long high and low state.

    REGULAR OUT: _|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|_

    DIVIDED OUT: _|‾|__|‾|__|‾|__|‾|____

If too many divisions are set in a short output, you might get unexpected results.

The number of divisions can be within a range of 1 (single output) to 100 (high number of divisions only make sense in long output).

**Default: 1**

### Repetitions

The "repetitions" setting defines how many times the output should be repeated.

Each repetition will be separated by a delay of the same length as the output.

For instance, if an output is set to last for 1s and to have 2 repetitions, there will be 3 similar output on the course of 5s.
3 output * 1s + 2 output separations * 1s.

    REGULAR OUT:  _|‾‾‾|___________________

    REPEATED OUT: _|‾‾‾|____|‾‾‾|____|‾‾‾|_

The number of repetitions can be within a range of 0 (single output without repetition) to 100 (high number of repetitions would mostly make sense for short output).

The divisions and the repetitions mostly differ when used with the probability settings defined below.

**Default: 0**

### Probability

The "probability" setting defines what are the chances for an input trigger to be noticed.  
It's a percentage of chance between 1 and 100%.

If an output is set to have some repetitions, each repetition will have its probability calculated individually.
So for instance, an output set to have 1 repetitions and a probability of 50% will most likely be output only once.

**Default: 100%**

### Probability per division

The "probability per division" setting defines what are the chances for an output division to happen.  
Exactly the same as the probability setting but applied to the divisions.

For instance, if an output is set to have 10 divisions and have a probability per division of 50%, it will most likely output only 5 divisions.

**Default: 100%**

## Known limitations

### Display 

The display has to be put to sleep to save as much resource and avoid drifting in time when using short repetitions/divisions.
To make it a bit more fun than just a black screen, it's displaying a random mandala instead of shutting down completely.

### Random / Probability

Using probabilities slightly impact performances, so you might end up with imprecise triggers.  
We are talking in terms of ms but if you are dividing a relatively short output in a lot of smaller triggers (e.g. 1s divided in 100), you might see the last trigger shortened or even missed entirely.

If you need very precise triggers, you shouldn't play with randomness in this script.

### Analog input

Since the analog input is not made to be used as a digital input, you might have issue triggering it correctly.  
When the analog input is left unpatched, it can be noisy and might trigger randomly.

You can try to change the constant `Karma.ANALOG_THRESHOLD` to a number that fits your module better.

## Patch ideas

### Mutable Instruments Rings

I've made this script specifically to use it with MI Rings in my setup.

My goal was to trigger bursts of random triggers to Rings' strum input at specific steps of my sequence.

### Self patching

It can be interesting to self patch the module, sending one output of the first trigger input into the second input to have some sort of cascading effect.

### Add probability to basic triggers

This script can also be used to simply add probability to any trigger by using the following settings for instance:
- Beginning: At start
- Delay: 0ms
- Duration: 10ms
- Divisions: 1
- Repetitions: 0
- Probability: 50%
- Probability per division: 100%