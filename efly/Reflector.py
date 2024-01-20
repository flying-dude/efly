#!/usr/bin/env python3

# Ignore the invalid snake-case error for the module name and the number of
# lines.
# pylint: disable=invalid-name,too-many-lines

# Copyright (C) 2012-2020  Xyne
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# (version 2) as published by the Free Software Foundation.
#
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''
Retrieve Arch Linux mirrors.
'''

import argparse
import base64
import calendar
import datetime
import http.client
import itertools
import json
import logging
import multiprocessing
import os
import re
import shlex
import socket
import subprocess
import signal
import sys
import tempfile
import time
import urllib.error
import urllib.request

# -------------------------------- Constants --------------------------------- #

NAME = 'Reflector'

URL = 'https://archlinux.org/mirrors/status/json/'

DISPLAY_TIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC'
PARSE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
PARSE_TIME_FORMAT_WITH_USEC = '%Y-%m-%dT%H:%M:%S.%fZ'

DB_SUBPATH = 'extra/os/x86_64/extra.db'

MIRROR_URL_FORMAT = '{0}{1}/os/{2}'
MIRRORLIST_ENTRY_FORMAT = "Server = " + MIRROR_URL_FORMAT + "\n"

DEFAULT_CONNECTION_TIMEOUT = 5
DEFAULT_DOWNLOAD_TIMEOUT = 5
DEFAULT_CACHE_TIMEOUT = 300

SORT_TYPES = {
    'age': 'last server synchronization',
    'rate': 'download rate',
    'country': 'country name, either alphabetically or in the order given by the --country option',
    'score': 'MirrorStatus score',
    'delay': 'MirrorStatus delay',
}


# ------------------------------- IO Functions ------------------------------- #

def get_cache_file(name='mirrorstatus.json'):
    '''
    Get a nearly XDG-compliant cache directory. PyXDG is not used to  avoid the
    external dependency. It is not fully compliant because it omits the
    application name, but the mirror status file can be reused by other
    applications and this stores no other files.
    '''
    cache_dir = os.getenv('XDG_CACHE_HOME', default=os.path.expanduser('~/.cache'))
    path = os.path.join(cache_dir, name)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    # Raised by makedirs if permissions do not match umask
    except FileExistsError:
        pass
    return path


def get_mirrorstatus(
    connection_timeout=DEFAULT_CONNECTION_TIMEOUT,
    cache_timeout=DEFAULT_CACHE_TIMEOUT,
    url=URL
):
    '''
    Retrieve the mirror status JSON object. The downloaded data will be cached
    locally and re-used within the cache timeout period. Returns the object and
    the local cache's modification time.
    '''
    if url == URL:
        cache_path = get_cache_file()
    else:
        name = base64.urlsafe_b64encode(url.encode('utf-8')).decode('utf-8') + '.json'
        name = os.path.join(NAME, name)
        cache_path = get_cache_file(name=name)

    try:
        mtime = os.path.getmtime(cache_path)
        invalid = (time.time() - mtime) > cache_timeout
    except FileNotFoundError:
        mtime = None
        invalid = True

    try:
        if invalid:
            with urllib.request.urlopen(url, None, connection_timeout) as handle:
                obj = json.loads(handle.read().decode())
            with open(cache_path, 'w', encoding='utf-8') as handle:
                json.dump(obj, handle, sort_keys=True, indent=2)
            mtime = time.time()
        else:
            with open(cache_path, 'r', encoding='utf-8') as handle:
                obj = json.load(handle)

        return obj, mtime
    except (IOError, urllib.error.URLError, socket.timeout) as err:
        raise MirrorStatusError(
            f'failed to retrieve mirrorstatus data: {err.__class__.__name__}: {err}'
        ) from err


# ------------------------------ Miscellaneous ------------------------------- #

def get_logger():
    '''
    Get the logger used by this module. Use this to be sure that the right logger
    is used.
    '''
    return logging.getLogger(NAME)


def format_last_sync(mirrors):
    '''
    Parse and format the "last_sync" field.
    '''
    for mirror in mirrors:
        last_sync = calendar.timegm(time.strptime(mirror['last_sync'], PARSE_TIME_FORMAT))
        mirror.update(last_sync=last_sync)
        yield mirror


def count_countries(mirrors):
    '''
    Count the mirrors in each country.
    '''
    countries = {}
    for mirror in mirrors:
        k = (mirror['country'], mirror['country_code'])
        if not any(k):
            continue
        try:
            countries[k] += 1
        except KeyError:
            countries[k] = 1
    return countries


def country_sort_key(priorities):
    '''
    Return a sort key function based on a list of country priorities.

    Args:
        priorities:
            The list of countries in the order of priority. Any countries not in
            the list will be sorted alphabetically after the countries in the
            list. The countries may be specified by name or country code.

    Returns:
        A key function to pass to sort().
    '''
    priorities = [country.upper() for country in priorities]
    try:
        default_priority = priorities.index('*')
    except ValueError:
        default_priority = len(priorities)

    def key_func(mirror):
        country = mirror['country'].upper()
        code = mirror['country_code'].upper()

        try:
            return (priorities.index(country), country)
        except ValueError:
            pass

        try:
            return (priorities.index(code), country)
        except ValueError:
            pass

        return (default_priority, country)

    return key_func


# ------------------------ download timeout handling ------------------------- #

class DownloadTimeout(Exception):
    '''
    Download timeout exception raised by DownloadContext.
    '''


class DownloadTimer():
    '''
    Context manager for timing downloads with timeouts.
    '''
    def __init__(self, timeout=DEFAULT_DOWNLOAD_TIMEOUT):
        '''
        Args:
            timeout:
                The download timeout in seconds. The DownloadTimeout exception
                will be raised in the context after this many seconds.
        '''
        self.time = None
        self.start_time = None
        self.timeout = timeout
        self.previous_handler = None
        self.previous_timer = None

    def raise_timeout(self, signl, frame):
        '''
        Raise the DownloadTimeout exception.
        '''
        raise DownloadTimeout(f'Download timed out after {self.timeout} second(s).')

    def __enter__(self):
        self.start_time = time.time()
        if self.timeout > 0:
            self.previous_handler = signal.signal(signal.SIGALRM, self.raise_timeout)
            self.previous_timer = signal.alarm(self.timeout)
        return self

    def __exit__(self, typ, value, traceback):
        time_delta = time.time() - self.start_time
        signal.alarm(0)
        self.time = time_delta
        if self.timeout > 0:
            signal.signal(signal.SIGALRM, self.previous_handler)

            previous_timer = self.previous_timer
            if previous_timer > 0:
                remaining_time = int(previous_timer - time_delta)
                # The alarm should have been raised during the download.
                if remaining_time <= 0:
                    signal.raise_signal(signal.SIGALRM)
                else:
                    signal.alarm(remaining_time)
        self.start_time = None


# --------------------------------- Sorting ---------------------------------- #

def sort(mirrors, by=None, key=None, **kwargs):  # pylint: disable=invalid-name
    '''
    Sort mirrors by different criteria.

    Args:
        mirrors:
            The iterable of mirrors to sort. This will be converted to a list.

        by:
            A mirrorstatus field by which to sort the mirrors, or one of the
            following:

            * age - Sort the mirrors by their last synchronization.
            * rate - Sort the mirrors by download rate.

        key:
            A custom sorting function that accepts mirrors and returns a sort
            key. If given, it will override the "by" parameter.

        **kwargs:
            Keyword arguments that are passed through to rate() when "by" is
            "rate".

    Returns:
        The sorted mirrors as a list.
    '''
    # Ensure that "mirrors" is a list that can be sorted.
    if not isinstance(mirrors, list):
        mirrors = list(mirrors)

    if by == 'age':
        mirrors.sort(key=lambda m: m['last_sync'], reverse=True)

    elif by == 'rate':
        rates = rate(mirrors, **kwargs)
        mirrors = sorted(mirrors, key=lambda m: rates[m['url']], reverse=True)

    else:
        if key is None:
            def key(mir):
                return mir[by]
        try:
            mirrors.sort(key=key)
        except KeyError as err:
            raise MirrorStatusError(
                f'attempted to sort mirrors by unrecognized criterion: "{by}"'
            ) from err

    return mirrors


# ---------------------------------- Rating ---------------------------------- #

def rate_rsync(
    db_url,
    connection_timeout=DEFAULT_CONNECTION_TIMEOUT,
    download_timeout=DEFAULT_DOWNLOAD_TIMEOUT
):
    '''
    Download a database via rsync and return the time and rate of the download.
    '''
    rsync_cmd = [
        'rsync',
        '-avL', '--no-h', '--no-motd',
        f'--contimeout={connection_timeout}',
        db_url
    ]
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with DownloadTimer(timeout=download_timeout) as timer:
                subprocess.check_call(
                    rsync_cmd + [tmpdir],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            time_delta = timer.time
            size = os.path.getsize(
                os.path.join(tmpdir, os.path.basename(DB_SUBPATH))
            )
            ratio = size / time_delta
            return time_delta, ratio
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        DownloadTimeout
    ) as err:
        logger = get_logger()
        logger.warning('failed to rate rsync download (%s): %s', db_url, err)
        return 0, 0


def rate_http(
    db_url,
    connection_timeout=DEFAULT_CONNECTION_TIMEOUT,
    download_timeout=DEFAULT_DOWNLOAD_TIMEOUT
):
    '''
    Download a database via any protocol supported by urlopen and return the time
    and rate of the download.
    '''
    req = urllib.request.Request(url=db_url)
    try:
        with urllib.request.urlopen(req, None, connection_timeout) as handle, \
                DownloadTimer(timeout=download_timeout) as timer:
            size = len(handle.read())
        time_delta = timer.time
        ratio = size / time_delta
        return time_delta, ratio
    except (
        OSError,
        urllib.error.HTTPError,
        http.client.HTTPException,
        DownloadTimeout
    ) as err:
        logger = get_logger()
        logger.warning('failed to rate http(s) download (%s): %s', db_url, err)
        return 0, 0


def _rate_unthreaded(mirrors, fmt, kwargs):
    '''
    Rate mirrors without using threads.
    '''
    logger = get_logger()
    rates = {}
    for mir in mirrors:
        url = mir['url']
        db_url = url + DB_SUBPATH
        scheme = urllib.parse.urlparse(url).scheme

        if scheme == 'rsync':
            time_delta, ratio = rate_rsync(db_url, **kwargs)
        else:
            time_delta, ratio = rate_http(db_url, **kwargs)

        kibps = ratio / 1024.0
        logger.info(fmt.format(url, kibps, time_delta))
        rates[url] = ratio
    return rates


def _rate_wrapper(func, url, kwargs):
    '''
    Wrapper function for multithreaded rating.
    '''
    time_delta, ratio = func(url + DB_SUBPATH, **kwargs)
    return url, time_delta, ratio


def _rate_threaded(mirrors, fmt, n_threads, kwargs):  # pylint: disable=too-many-locals
    '''
    Rate mirrors using threads.
    '''
    args = []
    for mir in mirrors:
        url = mir['url']
        scheme = urllib.parse.urlparse(url).scheme
        rfunc = rate_rsync if scheme == 'rsync' else rate_http
        args.append((rfunc, url, kwargs))

    logger = get_logger()
    rates = {}
    with multiprocessing.Pool(n_threads) as pool:
        for url, time_delta, ratio in pool.starmap(_rate_wrapper, args):
            kibps = ratio / 1024.0
            logger.info(fmt.format(url, kibps, time_delta))
            rates[url] = ratio
    return rates


def rate(
    mirrors,
    n_threads=0,
    **kwargs
):
    '''
    Rate mirrors by timing the download of the community repo's database from
    each one. Keyword arguments are passed through to rate_rsync and rate_http.
    '''
    # Ensure that mirrors is not a generator so that its length can be determined.
    if not isinstance(mirrors, tuple):
        mirrors = tuple(mirrors)

    if not mirrors:
        return None

    logger = get_logger()
    logger.info('rating %s mirror(s) by download speed', len(mirrors))

    url_len = max(len(mir['url']) for mir in mirrors)
    header_fmt = f'{{:{url_len:d}s}}  {{:>14s}}  {{:>9s}}'
    logger.info(header_fmt.format('Server', 'Rate', 'Time'))
    fmt = f'{{:{url_len:d}s}}  {{:8.2f}} KiB/s  {{:7.2f}} s'

    if n_threads > 0:
        return _rate_threaded(mirrors, fmt, n_threads, kwargs)
    return _rate_unthreaded(mirrors, fmt, kwargs)


# -------------------------------- Exceptions -------------------------------- #

class MirrorStatusError(Exception):
    '''
    Common base exception raised by this module.
    '''

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


# ---------------------------- MirrorStatusFilter ---------------------------- #

class MirrorStatusFilter():  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    '''
    Filter mirrors by different criteria.
    '''

    def __init__(
        self,
        min_completion_pct=1.0,
        countries=None,
        protocols=None,
        include=None,
        exclude=None,
        age=None,
        delay=None,
        isos=False,
        ipv4=False,
        ipv6=False
    ):  # pylint: disable=too-many-arguments
        self.min_completion_pct = min_completion_pct
        self.countries = tuple(c.upper() for c in countries) if countries else tuple()
        self.protocols = protocols
        self.include = tuple(re.compile(r) for r in include) if include else tuple()
        self.exclude = tuple(re.compile(r) for r in exclude) if exclude else tuple()
        self.age = age
        self.delay = delay
        self.isos = isos
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def filter_mirrors(self, mirrors):
        '''
        Filter the mirrors.
        '''
        # Filter unsynced mirrors.
        mirrors = (m for m in mirrors if m['last_sync'])

        # Parse the last sync time.
        mirrors = format_last_sync(mirrors)

        # Filter by completion "percent" [0-1].
        mirrors = (m for m in mirrors if m['completion_pct'] >= self.min_completion_pct)

        # Filter by countries.
        countries = self.countries
        if countries and '*' not in countries:
            mirrors = (
                m for m in mirrors
                if m['country'].upper() in countries or m['country_code'].upper() in countries
            )

        # Filter by protocols.
        if self.protocols:
            mirrors = (m for m in mirrors if m['protocol'] in self.protocols)

        # Filter by include expressions.
        if self.include:
            mirrors = (m for m in mirrors if any(r.search(m['url']) for r in self.include))

        # Filter by exclude expressions.
        if self.exclude:
            mirrors = (m for m in mirrors if not any(r.search(m['url']) for r in self.exclude))

        # Filter by age. The age is given in hours and converted to seconds. Servers
        # with a last refresh older than the age are omitted.
        if self.age and self.age > 0:
            tim = time.time()
            age = self.age * 60**2
            mirrors = (m for m in mirrors if (m['last_sync'] + age) >= tim)

        # Filter by delay. The delay is given as a float of hours and must be
        # converted to seconds.
        if self.delay is not None:
            delay = self.delay * 3600
            mirrors = (m for m in mirrors if m['delay'] <= delay)

        # Filter by ISO hosing.
        if self.isos:
            mirrors = (m for m in mirrors if m['isos'])

        # Filter by IPv4 support.
        if self.ipv4:
            mirrors = (m for m in mirrors if m['ipv4'])

        # Filter by IPv6 support.
        if self.ipv6:
            mirrors = (m for m in mirrors if m['ipv6'])

        yield from mirrors


# -------------------------------- Formatting -------------------------------- #

def format_mirrorlist(
    mirror_status,
    mtime,
    include_country=False,
    command=None,
    url=URL
):  # pylint: disable=too-many-locals
    '''
    Format the mirrorlist.
    '''
    if command is None:
        command = '?'
    else:
        command = 'reflector ' + ' '.join(shlex.quote(x) for x in command)

    last_check = mirror_status['last_check']
    # For some reason the "last_check" field included microseconds.
    try:
        parsed_last_check = datetime.datetime.strptime(
            last_check,
            PARSE_TIME_FORMAT_WITH_USEC,
        ).timetuple()
    except ValueError:
        parsed_last_check = datetime.datetime.strptime(
            last_check,
            PARSE_TIME_FORMAT,
        ).timetuple()

    width = 80
    colw = 11
    header = '# Arch Linux mirrorlist generated by Reflector #'.center(width, '#')
    border = '#' * len(header)
    mirrorlist = f'{border}\n{header}\n{border}\n\n' + \
        '\n'.join(
            f'# {{:<{colw:d}s}} {{}}'.format(k, v) for k, v in (
                ('With:', command),
                ('When:', time.strftime(DISPLAY_TIME_FORMAT, time.gmtime())),
                ('From:', url),
                ('Retrieved:', time.strftime(DISPLAY_TIME_FORMAT, time.gmtime(mtime))),
                ('Last Check:', time.strftime(DISPLAY_TIME_FORMAT, parsed_last_check))
            )
        ) + \
        '\n\n'

    country = None

    mirrors = mirror_status['urls']
    for mirror in mirrors:
        # Include country tags. This is intended for lists that are sorted by
        # country.
        if include_country:
            ctry = f'{mirror["country"]} [{mirror["country_code"]}]'
            if ctry != country:
                if country:
                    mirrorlist += '\n'
                mirrorlist += f'# {ctry}\n'
                country = ctry
        mirrorlist += MIRRORLIST_ENTRY_FORMAT.format(mirror['url'], '$repo', '$arch')

    if mirrors:
        return mirrorlist
    return None


# -------------------------- MirrorStatus Retriever -------------------------- #

class MirrorStatus():
    '''
    This is a legacy class that will likely be removed in the future. It
    previously held most of this module's functionality until it was refactored
    into more modular functions. Seemingly pointless code is still used by
    importers of this module.
    '''

    # TODO:
    # Move these to another module or remove them completely Related:
    # https://bugs.archlinux.org/task/32895
    REPOSITORIES = (
        'core',
        'core-testing',
        'extra',
        'extra-testing',
        'multilib',
        'multilib-testing'
    )
    # Officially supported system architectures.
    ARCHITECTURES = ['x86_64']

    MIRROR_URL_FORMAT = MIRROR_URL_FORMAT
    MIRRORLIST_ENTRY_FORMAT = MIRRORLIST_ENTRY_FORMAT

    def __init__(
        self,
        connection_timeout=DEFAULT_CONNECTION_TIMEOUT,
        download_timeout=DEFAULT_DOWNLOAD_TIMEOUT,
        cache_timeout=DEFAULT_CACHE_TIMEOUT,
        min_completion_pct=1.0,
        n_threads=0,
        url=URL
    ):  # pylint: disable=too-many-arguments
        self.connection_timeout = connection_timeout
        self.download_timeout = download_timeout
        self.cache_timeout = cache_timeout
        self.min_completion_pct = min_completion_pct
        self.url = url

        self.mirror_status = None
        self.ms_mtime = 0
        self.n_threads = n_threads

    def retrieve(self):
        '''
        Retrieve the mirrorstatus data.
        '''
        self.mirror_status, self.ms_mtime = get_mirrorstatus(
            connection_timeout=self.connection_timeout,
            cache_timeout=self.cache_timeout,
            url=self.url
        )

    def get_obj(self):
        '''
        Get the JSON mirror status.
        '''
        t = time.time()  # pylint: disable=invalid-name
        if (t - self.ms_mtime) > self.cache_timeout:
            self.retrieve()
        return self.mirror_status

    def get_mirrors(self):
        '''
        Get the mirror from the mirror status.
        '''
        obj = self.get_obj()
        try:
            return obj['urls']
        except KeyError as err:
            raise MirrorStatusError('no mirrors detected in mirror status output') from err

    def filter(self, mirrors=None, **kwargs):
        '''
        Filter mirrors by various criteria.
        '''
        if mirrors is None:
            mirrors = self.get_mirrors()
        msf = MirrorStatusFilter(min_completion_pct=self.min_completion_pct, **kwargs)
        yield from msf.filter_mirrors(mirrors)

    def sort(self, mirrors, **kwargs):
        '''
        Sort mirrors by various criteria.
        '''
        if mirrors is None:
            mirrors = self.get_mirrors()
        kwargs.setdefault('connection_timeout', self.connection_timeout)
        kwargs.setdefault('download_timeout', self.download_timeout)
        yield from sort(mirrors, n_threads=self.n_threads, **kwargs)

    def rate(self, mirrors=None, **kwargs):
        '''
        Sort mirrors by download speed.
        '''
        yield from self.sort(mirrors, by='rate', n_threads=self.n_threads, **kwargs)

    def get_mirrorlist(self, mirrors=None, include_country=False, cmd=None):
        '''
        Get a Pacman-formatted mirrorlist.
        '''
        obj = self.get_obj().copy()
        if mirrors is not None:
            if not isinstance(mirrors, list):
                mirrors = list(mirrors)
            obj['urls'] = mirrors
        return format_mirrorlist(
            obj,
            self.ms_mtime,
            include_country=include_country,
            command=cmd,
            url=self.url
        )

    def list_countries(self):
        '''
        List countries along with a server count for each one.
        '''
        mirrors = self.get_mirrors()
        return count_countries(mirrors)


# ----------------------------- argparse Actions ----------------------------- #

class ListCountries(argparse.Action):
    '''
    Action to list countries along with the number of mirrors in each.
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        ms = MirrorStatus(url=namespace.url)  # pylint: disable=invalid-name
        countries = ms.list_countries()
        headers = ('Country', 'Code', 'Count')
        widths = [len(h) for h in headers]
        widths[0] = max(widths[0], max(len(c) for c, cc in countries))
        widths[2] = max(widths[2], len(str(max(countries.values()))))
        fmt = '{{:{:d}s}} {{:>{:d}s}} {{:{:d}d}}'.format(*widths)
        hdr_fmt = fmt.replace('d', 's')
        print(hdr_fmt.format(*headers))
        print(' '.join('-' * w for w in widths))
        for (ctry, count), nmbr in sorted(countries.items(), key=lambda x: x[0][0]):
            print(fmt.format(ctry, count, nmbr))
        sys.exit(0)


def print_mirror_info(mirrors, time_fmt=DISPLAY_TIME_FORMAT):
    '''
    Print information about each mirror to STDOUT.
    '''
    if mirrors:
        #  mirrors = format_last_sync(mirrors)
        if not isinstance(mirrors, list):
            mirrors = list(mirrors)
        keys = sorted(k for k in mirrors[0].keys() if k != 'url')
        length = max(len(k) for k in keys)
        fmt = f'{{:{length:d}s}} : {{}}'
        for mir in mirrors:
            print(f'{mir["url"]}$repo/os/$arch')
            for key in keys:
                value = mir[key]
                if key == 'last_sync':
                    value = time.strftime(time_fmt, time.gmtime(value))
                print(fmt.format(key, value))
            print()


def add_arguments(parser):
    '''
    Add reflector arguments to the argument parser.
    '''
    parser.add_argument(
        '--connection-timeout', type=int, metavar='n', default=DEFAULT_CONNECTION_TIMEOUT,
        help='The number of seconds to wait before a connection times out. Default: %(default)s'
    )

    parser.add_argument(
        '--download-timeout', type=int, metavar='n', default=DEFAULT_DOWNLOAD_TIMEOUT,
        help='The number of seconds to wait before a download times out. Default: %(default)s'
    )

    parser.add_argument(
        '--list-countries', action=ListCountries, nargs=0,
        help='Display a table of the distribution of servers by country.'
    )

    parser.add_argument(
        '--cache-timeout', type=int, metavar='n', default=DEFAULT_CACHE_TIMEOUT,
        help=(
            '''The cache timeout in seconds for the data retrieved from the Arch
            Linux Mirror Status API. The default is %(default)s. '''
        )
    )

    parser.add_argument(
        '--url', default=URL,
        help=(
            '''The URL from which to retrieve the mirror data in JSON format. If
            different from the default, it must follow the same format. Default:
            %(default)s'''
        )
    )

    parser.add_argument(
        '--save', metavar='<filepath>',
        help='Save the mirrorlist to the given path.'
    )

    sort_help = '; '.join(f'"{k}": {v}' for k, v in SORT_TYPES.items())
    parser.add_argument(
        '--sort', choices=SORT_TYPES,
        help=f'Sort the mirrorlist. {sort_help}.'
    )

    parser.add_argument(
        '--threads', metavar='n', type=int, default=0,
        help=(
            '''Use n threads for rating mirrors. This option will speed up the
            rating step but the results will be inaccurate if the local
            bandwidth is saturated at any point during the operation. If rating
            takes too long without this option then you should probably apply
            more filters to reduce the number of rated servers before using this
            option.'''
        )
    )

    parser.add_argument(
        '--verbose', action='store_true',
        help='Print extra information to STDERR. Only works with some options.'
    )

    parser.add_argument(
        '--info', action='store_true',
        help='Print mirror information instead of a mirror list. Filter options apply.'
    )

    filters = parser.add_argument_group(
        'filters',
        '''The following filters are inclusive, i.e. the returned list will only
        contain mirrors for which all of the given conditions are met.'''
    )

    filters.add_argument(
        '-a', '--age', type=float, metavar='n',
        help=(
            '''Only return mirrors that have synchronized in the last n hours. n
            may be an integer or a decimal number.'''
        )
    )

    filters.add_argument(
        '--delay', type=float, metavar='n',
        help=(
            '''Only return mirrors with a reported sync delay of n hours or
            less, where n is a float. For example. to limit the results to
            mirrors with a reported delay of 15 minutes or less, pass 0.25.'''
        )
    )

    filters.add_argument(
        '-c', '--country', dest='countries', action='append', metavar='<country name or code>',
        help=(
            '''Restrict mirrors to selected countries. Countries may be given by
            name or country code, or a mix of both. The case is ignored.
            Multiple countries may be selected using commas (e.g. --country
            France,Germany) or by passing this option multiple times (e.g.  -c
            fr -c de). Use "--list-countries" to display a table of available
            countries along with their country codes. When sorting by country,
            this option may also be used to sort by a preferred order instead of
            alphabetically. For example, to select mirrors from Sweden, Norway,
            Denmark and Finland, in that order, use the options "--country
            se,no,dk,fi --sort country". To set a preferred country sort order
            without filtering any countries.  this option also recognizes the
            glob pattern "*", which will match any country. For example, to
            ensure that any mirrors from Sweden are at the top of the list and
            any mirrors from Denmark are at the bottom, with any other countries
            in between, use "--country \'se,*,dk\' --sort country". It is
            however important to note that when "*" is given along with other
            filter criteria, there is no guarantee that certain countries will
            be included in the results. For example, with the options "--country
            \'se,*,dk\' --sort country --latest 10", the latest 10 mirrors may
            all be from the United States. When the glob pattern is present, it
            only ensures that if certain countries are included in the results,
            they will be sorted in the requested order.'''
        )
    )

    filters.add_argument(
        '-f', '--fastest', type=int, metavar='n',
        help=(
            '''Return the n fastest mirrors that meet the other criteria. Do not
            use this option without other filtering options.'''
        )
    )

    filters.add_argument(
        '-i', '--include', metavar='<regex>', action='append',
        help='Include servers that match <regex>, where <regex> is a Python regular express.'
    )

    filters.add_argument(
        '-x', '--exclude', metavar='<regex>', action='append',
        help='Exclude servers that match <regex>, where <regex> is a Python regular express.'
    )

    filters.add_argument(
        '-l', '--latest', type=int, metavar='n',
        help='Limit the list to the n most recently synchronized servers.'
    )

    filters.add_argument(
        '--score', type=int, metavar='n',
        help='Limit the list to the n servers with the highest score.'
    )

    filters.add_argument(
        '-n', '--number', type=int, metavar='n',
        help='Return at most n mirrors.'
    )

    filters.add_argument(
        '-p', '--protocol', dest='protocols', action='append', metavar='<protocol>',
        help=(
            '''Match one of the given protocols, e.g. "https" or "ftp". Multiple
            protocols may be selected using commas (e.g. "https,http") or by
            passing this option multiple times.'''
        )
    )

    filters.add_argument(
        '--completion-percent', type=float, metavar='[0-100]', default=100.,
        help=(
            '''Set the minimum completion percent for the returned mirrors.
            Check the mirrorstatus webpage for the meaning of this parameter.
            Default value: %(default)s.'''
        )
    )

    filters.add_argument(
        '--isos', action='store_true',
        help='Only return mirrors that host ISOs.'
    )

    filters.add_argument(
        '--ipv4', action='store_true',
        help='Only return mirrors that support IPv4.'
    )

    filters.add_argument(
        '--ipv6', action='store_true',
        help='Only return mirrors that support IPv6.'
    )

    return parser


def split_list_args(args):
    '''
    Split comma-separated list arguments into separate list elements.
    '''
    if not args:
        return
    for arg in args:
        yield from arg.split(',')


class MyArgumentParser(argparse.ArgumentParser):
    '''
    Custom argument parser to support a more readable format in argument files.
    '''
    def convert_arg_line_to_args(self, arg_line):
        # Support comments and blank lines.
        #  content = arg_line.strip()
        #  if not content or content.startswith('#'):
        #      return list()
        return shlex.split(arg_line, comments=True)


def parse_args(args=None):
    '''
    Parse command-line arguments.
    '''
    parser = MyArgumentParser(
        description='retrieve and filter a list of the latest Arch Linux mirrors',
        fromfile_prefix_chars='@'
    )
    parser = add_arguments(parser)
    options = parser.parse_args(args)
    for list_arg in ('countries', 'protocols'):
        setattr(options, list_arg, list(split_list_args(getattr(options, list_arg))))
    return options


# Process options
def process_options(options, mirrorstatus=None, mirrors=None):
    '''
    Process options.

    Optionally accepts a MirrorStatus object and/or the mirrors as returned by
    the MirrorStatus.get_mirrors method.
    '''
    if not mirrorstatus:
        mirrorstatus = MirrorStatus(
            connection_timeout=options.connection_timeout,
            download_timeout=options.download_timeout,
            cache_timeout=options.cache_timeout,
            min_completion_pct=(options.completion_percent / 100.),
            url=options.url,
            n_threads=options.threads
        )

    if mirrors is None:
        mirrors = mirrorstatus.get_mirrors()

    # Filter
    mirrors = mirrorstatus.filter(
        mirrors,
        countries=options.countries,
        include=options.include,
        exclude=options.exclude,
        age=options.age,
        delay=options.delay,
        protocols=options.protocols,
        isos=options.isos,
        ipv4=options.ipv4,
        ipv6=options.ipv6
    )

    if options.latest and options.latest > 0:
        mirrors = mirrorstatus.sort(mirrors, by='age')
        mirrors = itertools.islice(mirrors, options.latest)

    if options.score and options.score > 0:
        mirrors = mirrorstatus.sort(mirrors, by='score')
        mirrors = itertools.islice(mirrors, options.score)

    if options.fastest and options.fastest > 0:
        mirrors = mirrorstatus.sort(mirrors, by='rate')
        mirrors = itertools.islice(mirrors, options.fastest)

    if options.sort and not (options.sort == 'rate' and options.fastest):
        if options.sort == 'country' and options.countries:
            mirrors = mirrorstatus.sort(mirrors, key=country_sort_key(options.countries))
        else:
            mirrors = mirrorstatus.sort(mirrors, by=options.sort)

    if options.number:
        mirrors = list(mirrors)[:options.number]

    return mirrorstatus, mirrors


def main(args=None, configure_logging=False):  # pylint: disable=too-many-branches
    '''
    Process command-line arguments and generate a mirror list.
    '''
    if args:
        cmd = tuple(args)
    else:
        cmd = sys.argv[1:]

    options = parse_args(args)

    # Configure logging.
    logger = get_logger()

    if configure_logging:
        if options.verbose:
            level = logging.INFO
        else:
            level = logging.WARNING

        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt='[{asctime:s}] {levelname:s}: {message:s}',
            style='{',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    try:
        mirrorstatus, mirrors = process_options(options)
        if mirrors is not None and not isinstance(mirrors, list):
            mirrors = list(mirrors)
        if not mirrors:
            sys.exit('error: no mirrors found')
        include_country = options.sort == 'country'
        # Convert the generator object to a list for re-use later.
        if options.info:
            print_mirror_info(mirrors)
            return
        mirrorlist = mirrorstatus.get_mirrorlist(mirrors, include_country=include_country, cmd=cmd)
        if mirrorlist is None:
            sys.exit('error: no mirrors found')
    except MirrorStatusError as err:
        sys.exit(f'error: {err.msg}')

    if options.save:
        try:
            with open(options.save, 'w', encoding='utf-8') as handle:
                handle.write(mirrorlist)
        except IOError as err:
            sys.exit(f'error: {err.strerror}')
    else:
        print(mirrorlist)


def run_main(args=None, **kwargs):
    '''
    Wrapper around main to handler keyboard interrupts. I don't remember why I
    added this instead of catching the error under the "if __name__" block.
    '''
    try:
        main(args, **kwargs)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_main(configure_logging=True)
