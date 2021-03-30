# Print text in Scratch

Print text on screen!

See this in action on the [Scratch project page](https://scratch.mit.edu/projects/138671484/).

If you'd like to use the Scratch Offline Editor, then you can use the project file in the demo/ folder in this repository.

## Features

- lovely vector-based lettering (not so great in full-screen though)
- all the English fonts that Scratch provides
- knows about various sizes ('XS' through to 'XL')
- includes glyphs for all the US-ASCII printable characters, plus £ and €, and could support some other Unicode characters too.
- supports one colour: Black
- locate start of text using X,Y coordinates
- line-wrapping supported out the box
- '\n' can be used in a string to print a newline
- '\\' will print a '\'
- '\P1500;' will pause for 1500 milli-seconds; don't forget the terminating semi-colon
- Uses stamping for each letter; not clones, so no limits on number of letters that can be printed on screen
- (in future, cloning will be an option too, which has a different set of pros and cons)

For performance, the characters are 'stamped' on screen, although this ends up being pixelated in full-screen. This is a Scratch bug.

In a later version I hope to let the user choose to use either stamping or cloning (there is a limit of 300 clones, and each letter is a clone, so...)

The costumes have been generated using some Python code to generate *vector* images for each character. This is done using SVG Text, so is as efficient as can reasonably be done.

This has had a major rework to complete the initial version, and shows some useful Computer Science concepts and methods of problem solving in Scratch.

You can use this in your own work; just copy the 'Printer' sprite into your own project. See the examples in the 'Eric' sprite or stage to see how to use it.

Some ideas from Computer Science you will find in the code:

- There is an implementation of a Finite State Automoton (FSA, or just 'State Machine') that handles escape sequences. You'll see this in 'printer_x_y_cols_string'

- The code has been made more readable in a couple of places to avoid a lot of if-then-else-if-then-else-if... and instead uses lists of keys and matching values (eg. to translate sizes like 'XS', 'S', 'M' etc. to respective values). This is as close to an associative array (aka 'dictionary' or 'map') that you can get in Scratch. See the 'printer_sizes_init' more block as an example and its use in 'printer_calculate_size'

- It shows a way of catching errors as soon as you detect them (see the 'printer_error' more block)

- In the 'Eric' sprite, you'll find some commentary around concepts such as locks and semaphores as they relate to Scratch's broadcasts.

This project is essentially a study in working around Scratch's limitations. Probably the most obvious ones as relate to this project (March 2021, Scratch 3):

- Can't print text on screen easily (hence this demonstration)
- Code would be much cleaner and correct if we could pass a message to a different sprite and also give it arguments. It sure would be nice if Scratch implemented a proper 'Actor' model of communication between sprites (ala Erlang or Go); it would make distributed systems much easier to code correctly.

## Known issues

- stamps are pixelated in full-screen; likely a bug in Scratch.
- there is also a \Dn; escape (where n is the number of milli-seconds to wait between characters) doesn't work; presumably because the code is running inside of a block that runs without screen refresh. Works for larger values of n, but that becomes painful to watch. Do not use for now.
- \Pn; escape timings may not be effective with small values for n ? Presumably this will be similar with \Dn;
- Considering this is effectively mono-spaced text, it tends to look pretty good, but you will likely find consecutive 'm' or 'w' will run into each other.

## How to Use the Printer

You'll need to download the output/Printer.sprite3 file from this repository. Upload this as a sprite into a Scratch 3 project.

Now you're ready to use it.

Because Scratch doesn't have a mechanism by which to send a message to another sprite and pass some variable (gosh that would be nice), we have to use a bunch of global variables to communicate what we want, and then a broadcast message to say we want the printer to look at what we've put into the global variables.

You'll use a pattern of blocks of the following form, as an example:

- set (printer_size) to (M)
- set (printer_typeface) to (handwriting)
- set (printer_string) to (Text to display)
- set (printer_x_start) to (-100)
- set (printer_y_start) to (0)

You'll see examples of this in the stage, and in the Eric sprite in the demo project.

Font sizes range from XS, S, M, L, XL, XXL

Font names need to be one of (case sensitive):
- 'handwriting'
- 'sans-serif'
- 'sans'
- 'curly'
- 'marker'
- 'pixel'

If an input is detected as being invalid, the global variable printer_error will be set, the variable shown on screen, and then all sprites will be stopped.

There are some escape sequences that are understood when the printer parses 'printer_string'. Namely:

- '\n' will cause a new line to be made
- '\\' will simply cause a '\' to be printed
- '\P*nnn*;', where nnn is a positive integer representing a duration in milliseconds to wait before continuing printing. Most commonly this will be for doing things like subtitle-timing.
- '\D*nnn*;' is similar, except it's *meant* to inject a delay between each character. Do not use it.

Note that \P and \D are both useless for small durations (which makes \D useless entirely). This is presumably because the 'more' block that this runs in does so without screen refresh and only larger values (say \P500;) tend to be useful.

The (Scratch) code that parses the printer_string content does so in a Finite State Machine, so if you're wanting to extend that, you'll want to understand that concept.

## Costume Generation

The Python code in this repository (create_vector_costumes.py) will read in an exported sprite (expecting it to be found in 'input/Printer.sprite3'). It will read that, and remove all costumes (and sounds); generate all the costumes as specified, as simple SVG Text documents; and create a new output sprite into 'output/Printer.sprite3'.

Thus the development workflow tends to look something like the following:

- After making changes to the code in the Printer sprite, export the sprite into input/Printer.sprite3
- From within the src/ directory, run 'python3.9 create_vector_costumes.py' (any version of Python newer than 3.6 should work, but only 3.9 has been tested.)
- Within Scratch (Offline Editor) delete the Printer sprite and re-upload it from the output directory.

### Word of warning

Scratch's vector-based image editor doesn't seem to play nice with SVG generated from other tools. It doesn't seem to implement much of SVG, so keep it really simple. You'll notice that as soon as you even slightly edit an uploaded costume, the underlying SVG structure will change drastically.

The biggest changes it makes to costumes is to reset the viewBox and wrap it in some transforming layers... you'll notice that what is shown in the Editor does not match up with what is shown in the costume thumbnail. The thumbnail is what seems be actually represent what gets used.

