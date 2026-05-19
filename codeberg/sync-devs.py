#!/usr/bin/env python
# vim:fileencoding=utf-8
# Sync developers team on Codeberg (invite or remove)
# 2-clause BSD licensed

import json
import os
import os.path
import sys

from codebergapi import CodebergAPI


ORG = "gentoo"


def main(devs_json="devs.json"):
    with open(devs_json) as devs_f:
        devs = json.load(devs_f)

    with open(os.path.expanduser("~/.codeberg-token")) as f:
        api_token = f.read().strip()

    with CodebergAPI("gentoo", "gentoo", api_token) as cb:
        for t in cb.teams(ORG):
            if t["name"] == "developers":
                break
        else:
            raise RuntimeError("Unable to find developers team")

        team_id = t["id"]
        members = frozenset(m["login"] for m in cb.team_members(team_id))
        remaining = set(m["login"] for m in cb.org_members(ORG))
        revmap = dict((v, k) for k, v in devs.items())

        for t in cb.teams(ORG):
            if t["name"] == "Owners":
                protected = frozenset(m["login"] for m in cb.team_members(t["id"]))
                break

        for cbdev, dev in revmap.items():
            if not cbdev:
                continue
            if cbdev in members:
                remaining.discard(cbdev)
            else:
                print(f"INVITE {cbdev} ({dev})")
                cb.team_add_member(team_id, cbdev)
        for m in remaining:
            if m in protected:
                # Never remove owners during automatic ldap sync. Messing up here can
                # lock everyone out.
                raise RuntimeError(f'!!!refusing to remove organization owner {m}!!!\n\n'
                                   'Double-check that no mistake was made, and if necessary, manually '
                                   'remove via the web UI before continuing.')
            print(f"REMOVE {m}")
            cb.org_remove_member(ORG, m)

    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
