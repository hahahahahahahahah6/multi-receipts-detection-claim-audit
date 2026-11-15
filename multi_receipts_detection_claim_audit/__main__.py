"""Command-line interface."""

import argparse
import json
import sys

from . import __version__
from .audit import audit


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, self.prog + ': error: ' + message + '\n')


def main(argv=None):
    parser = Parser(prog='multi-receipts-detection-claim-audit')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('audit', help='compare documentation with source evidence')
    command.add_argument('repo', nargs='?', default='.')
    command.add_argument('--json', action='store_true')
    command.add_argument('--verbose', action='store_true')
    command.add_argument('--ignore', action='append', default=[], metavar='PREFIX')
    command.add_argument('--fail-on', choices=('high', 'medium'), default='high')
    args = parser.parse_args(argv)
    try:
        report = audit(args.repo, args.ignore)
    except (OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report['verdict'])
        for finding in report['findings']:
            print(finding['severity'] + ' ' + finding['rule'] + ': ' + finding['message'])
        if args.verbose:
            for item in report['claims']:
                print('{}:{}: {} {}'.format(item['path'], item['line'], item['family'], item['phrase']))
            for item in report['evidence']:
                print('{}:{}: {}{}'.format(item['path'], item['line'], item['route'], ' (test)' if item['test'] else ''))
    return 2 if any(item['severity'] == 'HIGH' or args.fail_on == 'medium' for item in report['findings']) else 0


if __name__ == '__main__':
    sys.exit(main())
