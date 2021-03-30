#!/usr/bin/env python3

import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile

fonts = [
    {
        'id': 'sans',
        # This is a fairly standard sans-serif typeface.
        'filename': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    },
    {
        'id': 'mono',
        # This is a mono-width font, kinda like a typewriter
        'filename': '/usr/share/fonts/truetype/ttf-bitstream-vera/VeraMono.ttf'
    },
    {
        'id': 'decor',
        # This is a decorative font where letters are like balloons
        'filename': '/usr/share/fonts/truetype/aenigma/hillock.ttf'
    },
    {
        'id': 'scrawl',
        # This is a 'handwriting'/'scrawl' typeface
        'filename': '/usr/share/fonts/truetype/aenigma/aescrawl.ttf'
    },
]

# Scratch 3.0 uses double-resolution for its raster images
# (presumably for things like retina displays). So an image
# that is 60x80 will show in Scratch as being 30x40
#
# If we wanted text at greater than 100% size, then it would
# be best to make the source image a bit bigger, so we scale
# that by 4, which should lead to reasonably results looking
# at a sprite at 400% size.
#
# The printer code will need to be adjusted in its print_size
# block to adjust for this.
#
# However, when stamping, the stamped resolution is very bad;
# much worse than the sprite shown at that size. This is only
# a problem with stamping; clones do not have this problem.
#
width = 60 * 4
height = 80 * 4

# Limitation: costume names must be lower-case
# Limitation: costume names don't like characters outside of [a-z0-9-], maybe some others
#
# So we work around those limitations by generating names like sans-upper-a or sans-special-comma

characters = \
    'abcdefghijklmnopqrstuvwxyz' \
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
    '0123456789' \
    '`~!@#$€£%^&*()-_=+[{]}\\|;:\'"<,>.?/ '

replacement_font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
replacement_character = '\uFFFD'  # Unicode replacement character

label_specials = {
    ' ': 'label:\\ ',
    '\\': 'label:\\\\'
}

# These get overwritten in main with more performant and robust settings
temp_png = 'tmp.png'
temp_dir = '/tmp/'


def md5sum_file(filename):
    '''Returns an MD5 hex-formatted checksum so we can name the file as expected.'''

    with open(filename, 'rb') as f:
        h = hashlib.md5()
        h.update(f.read())
        return h.hexdigest()


def generate_glyph(font, name, label):
    '''Generate the image and costume data for a given character.

    To aid in understanding some of the terminology,
    'glyph' is the technical term for the visual representation
    of a 'character' in a given 'font'. In our case we store that
    visual representation ('glyph') as an image in PNG format.

    c(font) is the path to the filename (eg. to a TTF font).

    c(name) is the name you want to give the costume in Scratch.
    For the Printer project, we use fontid-character, such as
    'sans-a', but there are limitations in Scratch, such as
    not being able to have 'sans-A', so we leave that naming
    detail up to the caller.

    c(label) is the ImageMagick label that will be passed to
    the 'convert' program from ImageMagick.
    
    For most simple cases, label might be something like
    'label:a' to write the character 'a', but in more complex
    cases, such as backslash or space, or some Unicode characters
    we may need something a bit different.

    The responsibility of correctly formulating the label is
    left up to the caller.
    
    Returns the costume data for the resulting glyph.
    '''

    global width
    global height
    global temp_png
    global temp_dir

    argv = [
        'convert',
        '-font', font,
        '-size', f'{width}x{height}',
        '-background', 'none',
        '-gravity', 'center',
        label,
        temp_png
    ]

    subprocess.check_call(argv)

    md5hash = md5sum_file(temp_png)

    shutil.copy(temp_png, os.path.join(temp_dir, f'{md5hash}.png'))

    return {
        "assetId": md5hash,
        "name": name,
        "bitmapResolution": 2,
        "md5ext": f"{md5hash}.png",
        "dataFormat": "png",
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
    global replacement_font
    global replacement_character
    global temp_png
    global temp_dir

    # We set the currentCostume to 0, so we make the first font's
    # first costume to be the global replaceable.

    for font in fonts:
        print(f"Creating {font['id']}")

        # First create the 'replaceable' glyph for this font
        # that is show when we don't have a glyph for the
        # desired character.

        yield generate_glyph(
            replacement_font,
            f"{font['id']}-replaceable",
            f'label:{replacement_character}')

        for character in characters:
            
            yield generate_glyph(
                font['filename'],
                name_for(font['id'], character),
                label_specials.get(character, f'label:{character}'))


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
    global temp_png

    with tempfile.TemporaryDirectory(prefix='printer-costumes-') as temp_dir:

        print(f"Using temporary directory {temp_dir}")

        temp_png = os.path.join(temp_dir, 'tmp.png')

        sprite = load_sprite_code('../input/Printer.sprite3')
        for costume in generate_glyphs():
            sprite['costumes'].append(costume)
        assemble_sprite(sprite, '../output/Printer.sprite3')

        print("New sprite is ready for upload, available it the output directory")

if __name__ == '__main__':
    main()
