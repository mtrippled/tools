#!/usr/bin/env python3


import argparse
import json
import http.client
import sys
import urllib.parse


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-r', '--rippled', type=str, required=True,
                            help='rippled JSON-RPC URL.')
    arg_parser.add_argument('-i', '--index', type=int,
                            help='Ledger index number.')
    arg_parser.add_argument('--hash', type=str,
                            help='Ledger hash.')
    arg_parser.add_argument('-p', '--pretty', action='store_true',
                            help='Pretty print output.')
    args = arg_parser.parse_args()

    if (args.index is None and args.hash is None) or \
            (args.index is not None and args.hash is not None):
        sys.stderr.write('Either of ledger sequence or hash must be specified, '
                         'but not both.\n')
        return 1

    parsed_url = urllib.parse.urlparse(args.rippled)
    if parsed_url.scheme == 'http':
        conn = http.client.HTTPConnection(parsed_url.netloc)
    elif parsed_url.scheme == 'https':
        conn = http.client.HTTPSConnection(parsed_url.netloc)
    else:
        sys.stderr.write('rippled URL must be of type http or https.\n')
        return 1
    conn.connect()

    obj = {
        'status': 'success',
        'validated': True
    }
    state = []
    marker = None
    header = True
    while True:
        request = {'method': 'ledger_data', 'params': [{}]}
        if args.index is not None:
            request['params'][0]['ledger_index'] = args.index
        else:
            request['params'][0]['ledger_hash'] = args.hash
        if marker:
            request['params'][0]['marker'] = marker
        conn.request('GET', '/', json.dumps(request).encode())
        portion = json.loads(conn.getresponse().read().decode())['result']

        if header:
            header = False
            ledger = portion['ledger']
            ledger['transactions'] = []
            try:
                ledger.pop('closed')
            except KeyError:
                pass
            obj['ledger_current_index'] = int(ledger['ledger_index'])
            obj['ledger'] = ledger

        state.extend(portion['state'])

        if 'marker' not in portion:
            break
        marker = portion['marker']

    obj['ledger']['accountState'] = state

    if args.pretty:
        sys.stdout.write(json.dumps(obj, sort_keys=True, indent=2))
    else:
        sys.stdout.write(json.dumps(obj))
    sys.stdout.write('\n')
#    sys.stdout.write('\n' + 79 * '=' + '\n')

if __name__ == "__main__":
    sys.exit(main())
