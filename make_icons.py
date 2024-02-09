#!/usr/bin/env python3


import os
import sys
import shutil
import argparse


def make_icon_name(size: int, factor: int) -> str:
    scale = '@2x' if factor == 2 else ''
    return f'icon_{size}x{size}{scale}.png'


SIZES = [
    (16, 2),
    (32, 1),
    (32, 2),
    (64, 1),
    (128, 2),
    (256, 1),
    (256, 2),
    (512, 1),
    (512, 2),
    (1024, 1),
]


def make_iconset(input_file: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=False)
    for size, factor in SIZES:
        name = make_icon_name(size, factor)
        actual_size = size * factor
        os.system(f'sips -z {actual_size} {actual_size} '
                  f'{input_file} --out {output_dir}/{name}')
    os.system(f'iconutil --convert icns {output_dir}')
    shutil.rmtree(output_dir)
    return output_dir[:-len('iconset')] + 'icns'


def main():
    parser = argparse.ArgumentParser(description='icon set generator')
    parser.add_argument('input_file', metavar='INFILE',
                        help='input PNG file')
    parser.add_argument('output_dir', metavar='OUTDIR',
                        help='output directory to put icons into')
    args = parser.parse_args()
    output_dir = args.output_dir.rstrip('/')
    if not output_dir.endswith('.iconset'):
        output_dir += '.iconset'
    try:
        make_iconset(args.input_file, output_dir)
    except FileExistsError:
        print('Output directory already exists.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
