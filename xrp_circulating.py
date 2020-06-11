#!/usr/bin/env python3

# Copyright (c) 2020 Mark Travis (mtravis15432+os@gmail.com).
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose  with  or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE  SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH  REGARD  TO  THIS  SOFTWARE  INCLUDING  ALL  IMPLIED  WARRANTIES  OF
# MERCHANTABILITY  AND  FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY  SPECIAL,  DIRECT,  INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER  RESULTING  FROM  LOSS  OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION  OF  CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import argparse
import json
import http.client
import sys
import textwrap
import urllib.parse


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-r', '--rippled', type=str, required=True,
                            help='rippled JSON-RPC URL.')
    arg_parser.add_argument('-i', '--index', type=int,
                            help='Ledger index number.')
    arg_parser.add_argument('--hash', type=str,
                            help='Ledger hash.')
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

    total_drops = 0
    marker = None
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
        if portion['validated'] is not True:
            sys.stderr.write('Ledger is not validated.\n')
            return 1
        if 'marker' not in portion:
            break
        marker = portion['marker']

        for obj in portion['state']:
            if obj['LedgerEntryType'] == 'AccountRoot':
                total_drops += int(obj['Balance'])

    total_drops = str(total_drops)
    if len(total_drops) < 7:
        sys.stderr.write('Error: total XRP is less than 1.\n')
        return 1
    if args.index is not None:
        ledger = args.index
    else:
        ledger = args.hash
    for line in textwrap.wrap(
            'Total circulating XRP in all accounts as of ledger '
            '{} is {}.{}.'.format(ledger, total_drops[:-6],
                                  total_drops[-6:])):
        sys.stdout.write(line + '\n')


if __name__ == "__main__":
    sys.exit(main())
