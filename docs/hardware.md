# Hardware

General overview only. Parts, wiring and mechanics are not published.

- small computer running this code
- servos for eyes, eyelids, jaw and neck, driven by a PWM board
- camera, microphone, amplifier and speaker
- separate power for the computer and the servos

Tips from building it:

- keep servo power separate, or the computer will reset
- limit every joint in software
- move smoothly, it looks much more alive
- face tracking depends a lot on where the camera is mounted
