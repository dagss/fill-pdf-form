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
import re

def get_field_info(pdf_file):
    p = Popen(['pdftk', pdf_file, 'dump_data_fields'], stdout=PIPE)
    out, err = p.communicate()
    lines = out.splitlines()
    new_lines = []
    for line in lines:
        m = re.match(r'^([A-Za-z0-9]+: )(.*)$', line)
        if m is None:
            new_lines.append(line)
        else:
            new_lines.append("%s'%s'" % m.groups())
    out = '\n'.join(new_lines)
    assert p.wait() == 0
    return list(yaml.safe_load_all(out))

def fill_pdf_form(input_pdf, entries, output_pdf, flatten=False):
    d = tempfile.mkdtemp()
    try:
        fdf_filename = pjoin(d, 'entries.fdf')
        with open(fdf_filename, 'w') as f:
            f.write(forge_fdf("", entries, [], [], []))
        args = ['pdftk', input_pdf, 'fill_form', fdf_filename, 'output', output_pdf]
        if flatten:
            args += ['flatten']
        check_call(args)
    finally:
        shutil.rmtree(d)

def explain_cmd(args):
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

def template_cmd(args):
    fields = get_field_info(args.in_pdf)
    template = {}
    for f in fields:
        template[f['FieldName']] = ''
    with open(args.out_yml, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)

def fill_cmd(args):
    if args.out_pdf is None:
        args.out_pdf = os.path.splitext(args.entries_yml)[0] + '.pdf'
        sys.stderr.write("Writing to %s\n" % args.out_pdf)
    with open(args.entries_yml) as f:
        entries = yaml.safe_load(f).items()
    fill_pdf_form(args.in_pdf, entries, args.out_pdf)

ap = argparse.ArgumentParser()
cmd_ap_group = ap.add_subparsers(title='subcommands')

explain_cmd_ap = cmd_ap_group.add_parser(name='explain')
explain_cmd_ap.add_argument('in_pdf')
explain_cmd_ap.add_argument('out_pdf', nargs='?')
explain_cmd_ap.set_defaults(func=explain_cmd)

template_cmd_ap = cmd_ap_group.add_parser(name='template')
template_cmd_ap.add_argument('in_pdf')
template_cmd_ap.add_argument('out_yml')
template_cmd_ap.set_defaults(func=template_cmd)

fill_cmd_ap = cmd_ap_group.add_parser(name='fill')
fill_cmd_ap.add_argument('in_pdf')
fill_cmd_ap.add_argument('entries_yml')
fill_cmd_ap.add_argument('out_pdf', nargs='?')
fill_cmd_ap.set_defaults(func=fill_cmd)

args = ap.parse_args()
sys.exit(args.func(args))


