#!/usr/bin/env python3

import json
import time
import requests
import pathlib

class Transmitter:

    def __init__(self, frequency : float, mode : str, description : str ):
        self.frequency = frequency
        self.mode = mode
        self.description = description

    def json(self):
        return {
            "frequency": self.frequency,
            "mode": self.mode,
            "description": self.description
        }


class Satellite:

    def __init__(self, name, tle1, tle2, norad):
        self.name = name.strip()
        self.tle1 = tle1
        self.tle2 = tle2
        self.norad = norad

        self.transmitters = [ ]

    def json(self):
        return {
            "name": self.name,
            "tle1": self.tle1,
            "tle2": self.tle2,
            "norad": self.norad,
            "transmitters": [ t.json() for t in self.transmitters ]
        }




def process(transmitters, active):
    """
    Converts a transmitters file and an active tle file into a json file
    that contains satellites and transmitters.
    """

    # Create a dictionary mapping norad number to Satellite.

    satellites = { }

    lines = active.split("\n")

    for l1, l2, l3 in zip(lines[::3], lines[1::3], lines[2::3]):
        norad = int(l2[2:7])
        satellites[norad] = Satellite(l1, l2, l3, norad)

    # Add the transmitters to the satellites.

    for d in transmitters:

        if not d["alive"]:
            continue

        if not d["status"] == "active":
            continue

        if not d["norad_cat_id"]:
            continue

        frequency = d["downlink_low"]

        if "drift" in d:
            drift = d["drift"] / 1.0e9
            frequency *= (1.0 + drift)

        norad = int(d["norad_cat_id"])
        mode = d["mode"]
        description = d["description"]

        t = Transmitter(frequency, mode, description)

        if norad in satellites:
            satellites[norad].transmitters.append(t)

    json_data = {
        "timestamp" : int(time.time() * 1000),
        "satellites": [ s.json() for s in satellites.values() if s.transmitters ]
    }

    return json.dumps(json_data, indent=2)


if __name__ == "__main__":



    transmitters = requests.get("https://db.satnogs.org/api/transmitters/?format=json").json()
    active = requests.get("https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle").content.decode("utf-8")

    data = process(transmitters, active)

    base = pathlib.Path(__file__).parent

    if (base / "static").exists():
        with open(base / "static" / "data.json", "w") as f:
            f.write(data)

    if (base / "root").exists():
        with open(base / "root" / "data.json", "w") as f:
            f.write(data)
