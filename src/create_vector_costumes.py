#!/usr/bin/env python3

import hashlib
import io
import json
import os
import shutil
import tempfile
import unicodedata
import zipfile

# In creating vector fonts for our printing project, we have
# two essential ways we could approach it.
#
#  1) Use a library such as Cairo that will allow us to use
#     any font we like (ie. fonts outside of scratch). Those
#     glyphs then get turned into a set of splines etc. in
#     the SVG costume. That's a lot of splines etc for
#     Scratch (and the client/server) to process and transmit.
#     This is not good from a scalability point of view.
#
#     Another issue with this approach is that we need a way
#     to set where the origin is going to be, because that
#     will decide where the glyph sits on screen versus the
#     Scratch coordinates where we asked the text to be
#     drawn.
#
#     This becomes difficult because 'g' and 'W' have quite
#     different font metrics. Scratch seems to happier if we
#     center the glyph; making it left/start justified makes
#     the resulting origin much harder to predict.
#
#  2) A better (certainly easier and more resource friendly)
#     approach is for the costume to use an SVG Text element.
#     Thus, the costume is essentially asking Scratch to
#     'please write a "g" in the "Handwriting" font at size
#     40', rather than describing a set of splines that
#     describes what a g looks like in a particular font.
#     
#     That way, the browser can make use of the much more
#     highly optimized font-technologies that the OS has.
#
#     To make it easier to locate the 'origin' of the costume,
#     we simply center the text rather than left/start align
#     it, which frees us from having to know anything about
#     font metrics... except perhaps for knowing where the
#     baseline is; but we can fudge that by providing it with
#     this program, because Scratch only supports a small
#     number of fonts, and we support only subset of that.

fonts = [
    {
        'id': 'handwriting',
        'fontname': 'Handwriting'
    },
    {
        'id': 'sans-serif',
        'fontname': 'Sans Serif'
    },
    {
        'id': 'serif',
        'fontname': 'Serif'
    },
    {
        'id': 'curly',
        'fontname': 'Curly'
    },
    {
        'id': 'marker',
        'fontname': 'Marker'
    },
    {
        'id': 'pixel',
        'fontname': 'Pixel'
    }
]

# Limitation: costume names must be lower-case
# Limitation: costume names don't like characters outside of [a-z0-9-], maybe some others
#
# So we work around those limitations by generating names like sans-upper-a or sans-special-comma

characters = \
    'abcdefghijklmnopqrstuvwxyz' \
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
    '0123456789' \
    '`~!@#$€£%^&*()-_=+[{]}\\|;:\'"<,>.?/ '

# These get overwritten in main with more performant and robust settings
temp_svg = 'tmp.svg'
temp_dir = '/tmp/'

# Essential dimentions of the resulting costume
#
# The width is wider than the height; this is just to
# capture any overflow. Doesn't really matter with SVG
# anyway as the background is transparent.
#
# Note that the Printer will want to use a different
# width when layout out the text; its just monospace
# currently, but it would be useful to have some
# level of kerning, somehow.
#
width = 40
height = 50

def svg_letter(character, font):
    '''Return an SVG document that presents a character in a given font.'''

    # This SVG content was captured by creating a vector costume
    # in Scratch containing a single letter, aligning it to suit
    # the origin, making it centered and then exporting it.
    # And then playing with it some.... no, a LOT. Really, it
    # ends up looking quite different, and the thumbnail view
    # (which is more representative of how it appears when used)
    # ends up looking different from the editor view. Very
    # hurtful to the brain... probably easier (saner) to make
    # the simplest SVG you can based on as SVG tutorial.

    # NOTE: Scrach only support some of SVG. Trying to use SVG
    # images that have been created outside of Scratch 3.0 will
    # likely end up not displaying correctly. Note that when you
    # upload a costume, it is stored verbatim. But as soon as
    # you touch it the Scratch editor will kick in and you'll
    # end up with a SVG structure that is fairly different.

    global width
    global height

    # TODO: do this better

    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;'
    }

    if character in replacements:
        character = replacements[character]

    # The 0.75 is a fudge factor for the descenders. The 'center' in terms of y is half-way between
    # the baseline and the topline. Naturally, this is something that should really take care
    # of in font metrics...

    return f'''
        <svg version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0,0,{width},{height}">
            <text x="{width/2}" y="{height*0.75}" font-size="40" xml:space="preserve" fill="#000000" fill-rule="nonzero"
                stroke="none" stroke-width="1" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="10" stroke-dasharray="" stroke-dashoffset="0"
                font-family="{font}" font-weight="normal" text-anchor="middle" style="mix-blend-mode: normal">{character}</text>
        </svg>
        '''

    # <circle cx="{width/2}" cy="{height/2}" r="1" fill="red" />


def md5sum_file(filename):
    '''Returns an MD5 hex-formatted checksum so we can name the file as expected.'''

    with open(filename, 'rb') as f:
        h = hashlib.md5()
        h.update(f.read())
        return h.hexdigest()


def generate_glyph(font, name, character):
    '''Generate the image and costume data for a given character.

    To aid in understanding some of the terminology,
    'glyph' is the technical term for the visual representation
    of a 'character' in a given 'font'. In our case we store that
    visual representation ('glyph') as an image in PNG format.

    c(font) is the name of the font as Scratch knows it
    (eg. 'Handwriting').

    c(name) is the name you want to give the costume in Scratch.
    For the Printer project, we use fontid-character, such as
    'sans-a', but there are limitations in Scratch, such as
    not being able to have 'sans-A', so we leave that naming
    detail up to the caller.

    c(character) is the character, in Unicode that will be
    displayed. It will be fed verbatim into an SVG Text
    element.
        
    Returns the costume data for the resulting glyph.
    '''

    global width
    global height
    global temp_svg
    global temp_dir

    with open(temp_svg, 'wt', encoding='utf-8') as f:
        f.write(svg_letter(character, font))

    md5hash = md5sum_file(temp_svg)

    shutil.copy(temp_svg, os.path.join(temp_dir, f'{md5hash}.svg'))

    return {
        "assetId": md5hash,
        "name": name,
        "md5ext": f"{md5hash}.svg",
        "dataFormat": "svg",
        "rotationCenterX": int(width / 2),
        "rotationCenterY": int(height / 2)
    }


def name_for(font_id, character):
    '''Return a name used for the costume for this character in this font.
    
    Result might be something like 'sans-a', 'sans-upper-a', 'sans-0' or 'sans-special-comma'

    The 'special' characters are given the names from Unicode, some of which seem rather
    odd and verbose (eg. '/' is 'SOLIDUS' and '-' is 'HYPHEN-MINUS'). We lowercase them
    and replace anything not a-z0-9 with '-'

    This needs to agree with the Scratch code in Printer in the Custom Block
    printer_special_init. It's not used by the user.
    '''

    if character in 'abcdefghijklmnopqrstuvwxyz0123456789':
        return f'{font_id}-{character}'.lower()

    if character in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        return f'{font_id}-upper-{character}'

    name = unicodedata.name(character).lower().replace('_','-').replace(' ','-')
    return f'{font_id}-special-{name}'.lower()


def generate_glyphs():

    global fonts
    global characters
    global width
    global height
    global label_specials
    global temp_svg
    global temp_dir

    # We set the currentCostume to 0, so we make the first font's
    # first costume to be the global replaceable.

    for font in fonts:
        print(f"Creating {font['id']}")

        # First create the 'replaceable' glyph for this font
        # that is show when we don't have a glyph for the
        # desired character. We do require an explicit
        # replacement character, because this is part of the
        # case-sensitivity testing.

        yield generate_glyph(
            font['fontname'],
            f'{font["id"]}-replaceable',
            '\uFFFD')

        for character in characters:
            
            yield generate_glyph(
                font['fontname'],
                name_for(font['id'], character),
                character)


def load_sprite_code(sprite3_filename):
    '''Open the sprite's data, but keep only the code.

    Discards the costumes and sounds. It is important
    that the code doesn't refer directly to any of those
    costumes or sounds.
    '''

    with zipfile.ZipFile(sprite3_filename, 'r') as archive:
        sprite = json.load(io.BytesIO(archive.read('sprite.json')))

        sprite['costumes'] = []
        sprite['current_costume'] = 0
        # At this point, its now invalid, as it has no costumes

        # Hmmm, does it need a sound? I didn't add one, but it
        # had one by default.
        sprite['sounds'] = []

        return sprite


def assemble_sprite(sprite, sprite3_filename):

    global temp_dir

    with zipfile.ZipFile(sprite3_filename, 'w') as archive:
        
        # Since the files are named after their content (MD5),
        # we end up getting duplicates when looking at characters
        # that are in fact the same set picture (and metadata)
        # such as a space. (someone might decide a space in a
        # particular font should be done a bit differently, so
        # we have a space glyph per font.)

        written_files = set()

        for costume in sprite['costumes']:

            if costume['md5ext'] not in written_files:

                archive.write(
                    os.path.join(temp_dir, costume['md5ext']),
                    arcname=costume['md5ext'],
                    compress_type=zipfile.ZIP_STORED)

                written_files.add(costume['md5ext'])
    
            else:

                print(f"Conflict found for new {costume}")

        archive.writestr('sprite.json', data=json.dumps(sprite))


def main():

    global temp_dir
    global temp_svg

    with tempfile.TemporaryDirectory(prefix='printer-costumes-') as temp_dir:

        print(f"Using temporary directory {temp_dir}")

        temp_svg = os.path.join(temp_dir, 'tmp.png')

        sprite = load_sprite_code('../input/Printer.sprite3')
        for costume in generate_glyphs():
            sprite['costumes'].append(costume)
        assemble_sprite(sprite, '../output/Printer.sprite3')

        print("New sprite is ready for upload, available it the output directory")


if __name__ == '__main__':
    main()
