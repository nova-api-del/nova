#!/usr/bin/env python3
"""Nova GTA 6 Short preset: cinematic five-scene Vice City/GTA VI story."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cinematic_shorts as cs

cs.TOPICS[:] = [{
    "title": "GTA 6: The Vice City Details Everyone Missed",
    "hook": "GTA 6 is coming, and these five details make Vice City look absolutely insane.",
    "facts": [
        "Vice City returns with a massive modern map built around Leonida, with dense city streets and huge open landscapes.",
        "Jason and Lucia are at the center of the story, giving the game a criminal duo with a Bonnie-and-Clyde-style dynamic.",
        "The world is packed with social-media-era details, wildlife, traffic, crowds, and environmental moments designed to feel alive.",
        "Rockstar's trailer footage shows a huge range of locations, from neon nightlife and highways to beaches, swamps, and small-town areas.",
        "The biggest question is how much of that world will actually be explorable when players finally get their hands on the game."
    ],
    "details": [
        "The setting stretches far beyond the familiar Vice City streets and gives Leonida a much broader identity.",
        "Their relationship is a major part of the premise, with crime constantly pushing them into bigger trouble.",
        "Small animations and background activity make the world feel less like a backdrop and more like a living place.",
        "That contrast between glamorous Vice City and the wider state creates room for very different kinds of missions.",
        "If Rockstar delivers on the scale shown in the trailers, this could become one of the most detailed open worlds ever made."
    ],
    "queries": [
        "GTA 6 trailer Vice City gameplay Rockstar",
        "GTA VI Jason Lucia trailer",
        "GTA 6 Vice City night gameplay trailer",
        "GTA 6 Leonida swamp highway trailer",
        "GTA 6 Vice City beach trailer"
    ]
}]

if __name__ == "__main__":
    cs.main()
