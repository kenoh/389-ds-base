# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2019 Red Hat, Inc.
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

import json
import ldap
from lib389.plugins import (PassThroughAuthenticationPlugin, PAMPassThroughAuthPlugin,
                            PAMPassThroughAuthConfigs, PAMPassThroughAuthConfig)

from lib389.cli_conf import add_generic_plugin_parsers, generic_object_edit, generic_object_add

arg_to_attr_pam = {
    'exclude_suffix': 'pamExcludeSuffix',
    'include_suffix': 'pamIncludeSuffix',
    'missing_suffix': 'pamMissingSuffix',
    'filter': 'pamFilter',
    'id_attr': 'pamIDAttr',
    'id_map_method': 'pamIDMapMethod',
    'fallback': 'pamFallback',
    'secure': 'pamSecure',
    'service': 'pamService'
}


def pta_list(inst, basedn, log, args):
    log = log.getChild('pta_list')
    plugin = PassThroughAuthenticationPlugin(inst)
    result = []
    urls = plugin.get_urls()
    if args.json:
        log.info(json.dumps({"type": "list", "items": urls}))
    else:
        if len(urls) > 0:
            for i in result:
                log.info(i)
        else:
            log.info("No Pass Through Auth URLs were found")


def pta_add(inst, basedn, log, args):
    log = log.getChild('pta_add')
    plugin = PassThroughAuthenticationPlugin(inst)
    urls = list(map(lambda url: url.lower(), plugin.get_urls()))
    if args.URL.lower() in urls:
        raise ldap.ALREADY_EXISTS("Entry %s already exists" % args.URL)
    plugin.add("nsslapd-pluginarg%s" % len(urls), args.URL)


def pta_edit(inst, basedn, log, args):
    log = log.getChild('pta_edit')
    plugin = PassThroughAuthenticationPlugin(inst)
    urls = list(map(lambda url: url.lower(), plugin.get_urls()))
    old_url_l = args.OLD_URL.lower()
    if old_url_l not in urls:
        log.info("Entry %s doesn't exists. Adding a new value." % args.OLD_URL)
        url_num = len(urls)
    else:
        url_num = urls.index(old_url_l)
        plugin.remove("nsslapd-pluginarg%s" % url_num, old_url_l)
    plugin.add("nsslapd-pluginarg%s" % url_num, args.NEW_URL)


def pta_del(inst, basedn, log, args):
    log = log.getChild('pta_del')
    plugin = PassThroughAuthenticationPlugin(inst)
    urls = list(map(lambda url: url.lower(), plugin.get_urls()))
    old_url_l = args.URL.lower()
    if old_url_l not in urls:
        raise ldap.NO_SUCH_OBJECT("Entry %s doesn't exists" % args.URL)

    plugin.remove_all("nsslapd-pluginarg%s" % urls.index(old_url_l))
    log.info("Successfully deleted %s", args.URL)


def pam_pta_list(inst, basedn, log, args):
    log = log.getChild('pam_pta_list')
    configs = PAMPassThroughAuthConfigs(inst)
    result = []
    result_json = []
    for config in configs.list():
        if args.json:
            result_json.append(config.get_all_attrs_json())
        else:
            result.append(config.rdn)
    if args.json:
        log.info(json.dumps({"type": "list", "items": result_json}))
    else:
        if len(result) > 0:
            for i in result:
                log.info(i)
        else:
            log.info("No PAM Pass Through Auth plugin config instances")


def pam_pta_add(inst, basedn, log, args):
    log = log.getChild('pam_pta_add')
    plugin = PAMPassThroughAuthPlugin(inst)
    props = {'cn': args.NAME}
    generic_object_add(PAMPassThroughAuthConfig, inst, log, args, arg_to_attr_pam, basedn=plugin.dn, props=props)


def pam_pta_edit(inst, basedn, log, args):
    log = log.getChild('pam_pta_edit')
    configs = PAMPassThroughAuthConfigs(inst)
    config = configs.get(args.NAME)
    generic_object_edit(config, log, args, arg_to_attr_pam)


def pam_pta_show(inst, basedn, log, args):
    log = log.getChild('pam_pta_show')
    configs = PAMPassThroughAuthConfigs(inst)
    config = configs.get(args.NAME)

    if not config.exists():
        raise ldap.NO_SUCH_OBJECT("Entry %s doesn't exists" % args.name)
    if args and args.json:
        o_str = config.get_all_attrs_json()
        log.info(o_str)
    else:
        log.info(config.display())


def pam_pta_del(inst, basedn, log, args):
    log = log.getChild('pam_pta_del')
    configs = PAMPassThroughAuthConfigs(inst)
    config = configs.get(args.NAME)
    config.delete()
    log.info("Successfully deleted the %s", config.dn)


def _add_parser_args_pam(parser):
    parser.add_argument('--exclude-suffix', nargs='+',
                        help='Specifies a suffix to exclude from PAM authentication (pamExcludeSuffix)')
    parser.add_argument('--include-suffix', nargs='+',
                        help='Sets a suffix to include for PAM authentication (pamIncludeSuffix)')
    parser.add_argument('--missing-suffix', choices=['ERROR', 'ALLOW', 'IGNORE'],
                        help='Identifies how to handle missing include or exclude suffixes (pamMissingSuffix)')
    parser.add_argument('--filter',
                        help='Sets an LDAP filter to use to identify specific entries within '
                             'the included suffixes for which to use PAM pass-through authentication (pamFilter)')
    parser.add_argument('--id-attr', nargs='+',
                        help='Contains the attribute name which is used to hold the PAM user ID (pamIDAttr)')
    parser.add_argument('--id_map_method',
                        help='Gives the method to use to map the LDAP bind DN to a PAM identity (pamIDMapMethod)')
    parser.add_argument('--fallback', choices=['TRUE', 'FALSE'], type=str.upper,
                        help='Sets whether to fallback to regular LDAP authentication '
                             'if PAM authentication fails (pamFallback)')
    parser.add_argument('--secure', choices=['TRUE', 'FALSE'], type=str.upper,
                        help='Requires secure TLS connection for PAM authentication (pamSecure)')
    parser.add_argument('--service',
                        help='Contains the service name to pass to PAM (pamService)')


def create_parser(subparsers):
    passthroughauth_parser = subparsers.add_parser('pass-through-auth',
                                                   help='Manage and configure Pass-Through Authentication plugins '
                                                        '(URLs and PAM)')
    subcommands = passthroughauth_parser.add_subparsers(help='action')
    add_generic_plugin_parsers(subcommands, PassThroughAuthenticationPlugin)

    list = subcommands.add_parser('list', help='List pass-though plugin URLs or PAM configurations.')
    subcommands_list = list.add_subparsers(help='action')
    list_urls = subcommands_list.add_parser('urls', help='List URLs.')
    list_urls.set_defaults(func=pta_list)
    list_pam = subcommands_list.add_parser('pam-configs', help='List PAM configurations.')
    list_pam.set_defaults(func=pam_pta_list)

    url = subcommands.add_parser('url', help='Manage PTA URL configurations.')
    subcommands_url = url.add_subparsers(help='action')

    add_url = subcommands_url.add_parser('add', help='Add the config entry')
    add_url.add_argument('URL',
                         help='The full LDAP URL in format '
                              '"ldap|ldaps://authDS/subtree maxconns,maxops,timeout,ldver,connlifetime,startTLS". '
                              'If one optional parameter is specified the rest should be specified too')
    add_url.set_defaults(func=pta_add)

    edit_url = subcommands_url.add_parser('modify', help='Edit the config entry')
    edit_url.add_argument('OLD_URL', help='The full LDAP URL you get from the "list" command')
    edit_url.add_argument('NEW_URL',
                          help='The full LDAP URL in format '
                               '"ldap|ldaps://authDS/subtree maxconns,maxops,timeout,ldver,connlifetime,startTLS". '
                               'If one optional parameter is specified the rest should be specified too')
    edit_url.set_defaults(func=pta_edit)

    delete_url = subcommands_url.add_parser('delete', help='Delete the config entry')
    delete_url.add_argument('URL', help='The full LDAP URL you get from the "list" command')
    delete_url.set_defaults(func=pta_del)

    pam = subcommands.add_parser('pam-config', help='Manage PAM PTA configurations.')
    pam.add_argument('NAME', help='The PAM PTA configuration name')
    subcommands_pam = pam.add_subparsers(help='action')

    add = subcommands_pam.add_parser('add', help='Add the config entry')
    add.set_defaults(func=pam_pta_add)
    _add_parser_args_pam(add)
    edit = subcommands_pam.add_parser('set', help='Edit the config entry')
    edit.set_defaults(func=pam_pta_edit)
    _add_parser_args_pam(edit)
    show = subcommands_pam.add_parser('show', help='Display the config entry')
    show.set_defaults(func=pam_pta_show)
    delete = subcommands_pam.add_parser('delete', help='Delete the config entry')
    delete.set_defaults(func=pam_pta_del)