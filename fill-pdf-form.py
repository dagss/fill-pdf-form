#!/usr/bin/env python
import os
from os.path import join as pjoin
import sys
import yaml
import argparse
import tempfile
import shutil
from fdfgen import forge_fdf
from subprocess import check_call, Popen, PIPE

def get_field_info(pdf_file):
    p = Popen(['pdftk', pdf_file, 'dump_data_fields'], stdout=PIPE)
    out, err = p.communicate()
    assert p.wait() == 0
    return list(yaml.safe_load_all(out))

def fill_pdf_form(input_pdf, fields, output_pdf, flatten=False):
    d = tempfile.mkdtemp()
    try:
        fdf_filename = pjoin(d, 'fields.fdf')
        with open(fdf_filename, 'w') as f:
            f.write(forge_fdf("", fields, [], [], []))
        args = ['pdftk', input_pdf, 'fill_form', fdf_filename, 'output', output_pdf]
        if flatten:
            args += ['flatten']
        check_call(args)
    finally:
        shutil.rmtree(d)

def view(args):
    field_info = get_field_info(args.in_pdf)
    fields = []
    for e in field_info:
        fields.append((e['FieldName'], e['FieldName']))
    if args.out_pdf is None:
        d = tempfile.mkdtemp()
        args.out_pdf = os.path.join(d, 'output.pdf')
        view = True
    else:
        d = None
        view = False
    try:
        fill_pdf_form(args.in_pdf, fields, args.out_pdf)
        if view:
            check_call(['evince', args.out_pdf])
    finally:
        if d is not None:
            shutil.rmtree(d)
    return 0

ap = argparse.ArgumentParser()
cmd_ap_group = ap.add_subparsers(title='subcommands')
view_cmd_ap = cmd_ap_group.add_parser(name='view')
view_cmd_ap.add_argument('in_pdf')
view_cmd_ap.add_argument('out_pdf', nargs='?')
view_cmd_ap.set_defaults(func=view)

args = ap.parse_args()
sys.exit(args.func(args))


