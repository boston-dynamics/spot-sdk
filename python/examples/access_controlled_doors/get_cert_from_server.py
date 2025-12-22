# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
from ssl import _SSLMethod, get_server_certificate


def main():
    parser = argparse.ArgumentParser(description="Make API calls using provided configuration.")
    parser.add_argument('--hostname', required=True, help='Server to retrieve cert from')
    parser.add_argument('--port', type=int, default=443, help='Port to connect to (default: 443)')
    parser.add_argument('--cert', required=True, help='Path to where to store to certificate file')
    parser.add_argument(
        '--protocol-version',
        type=lambda s: _SSLMethod[s]._name_,  # enum to string
        choices=list(_SSLMethod.__members__.keys()),  # string
        default='PROTOCOL_TLS',
        help='Protocol version to use when attempting connection to server.')
    try:
        args = parser.parse_args()
    except KeyError as e:
        # This is unlikely to happen as only the supported protocol versions are displayed in the choices.
        # But, if the user's server uses an unsupported protocol version, we let them know.
        print(
            'Protocol version argument unsupported by installed SSL version). Get the certificate manually.'
        )
        exit(1)

    if not args.cert.lower().endswith('.cer'):
        print(
            "Spot expects certificate files to have a .cer extension. Please update the --cert argument accordingly. Exiting."
        )
        exit(1)

    cert_pem = get_server_certificate(
        (args.hostname, args.port),
        ssl_version=_SSLMethod[args.protocol_version]  # string to enum
    )

    # Save the certificate to a file
    with open(args.cert, 'w') as f:
        f.write(cert_pem)
        print(f"Certificate saved to {args.cert}")


if __name__ == "__main__":
    main()
