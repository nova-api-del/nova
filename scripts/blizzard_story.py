#!/usr/bin/env python3
"""Build the 10-minute illustrated blizzard mystery episode."""
import asyncio, json, re, subprocess
from pathlib import Path
import edge_tts

OUT=Path("output/blizzard_episode")
ASSETS=OUT/"assets"
OUT.mkdir(parents=True,exist_ok=True)
ASSETS.mkdir(parents=True,exist_ok=True)
W,H,FPS=1920,1080,30
TOTAL=600.0
VOICE="en-US-GuyNeural"
IMAGES=[
"https://dnznrvs05pmza.cloudfront.net/8fcbf4a5-d53f-43d4-b813-280955b268a0.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNTJmMTFlY2YzNzgxZmYwYSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NzM3NX0.VUbXZPqvSXLctaze8VCrNzgZgHQpCPrsAuxeOfyWL8c",
"https://dnznrvs05pmza.cloudfront.net/396bc8c5-02fa-4d8d-94f1-b2bb1ddaa6da.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNGNkYzQ5ZmQ0YzIxOWMyMiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM3NzI3N30.w4X-QxM-fLXMNMyD77FesTkSTVZtgVsh-yoMRllqVyY",
"https://dnznrvs05pmza.cloudfront.net/0cf18ea6-d6ab-4e83-b1de-eccb7ce97ce1.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYTIzZjkxODhmODJmNzkxMCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0ODYxNn0.lWUQo2Wl2lbxl7CP9ySsd_zgCFKoMLaaRBthZJHiedY",
"https://dnznrvs05pmza.cloudfront.net/da6dfbd0-ceca-437b-8fd7-8c2279a5f884.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNGJmY2Y1YjY5MTIxNjRiZCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0Mjc3NH0.zYH2ExVw8MtOJl0T1BDLy8FuLtXQ54MymcMYQU9LdRw",
"https://dnznrvs05pmza.cloudfront.net/332a972f-f43f-4758-a02b-f51c0e5ee4f3.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYmY3NTgwYjdkYzAzZWIxZiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2MTcxOX0.G_IFpVGuxQq6E58xZCwK0cqtbMv4XSAlITHzyTQcZw0",
"https://dnznrvs05pmza.cloudfront.net/c79cb114-4bba-48fa-8e5f-983f72bbc405.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiY2YxZTNmYjY3MTZmNGZiNyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNjUwMn0.ps0FzLjMP6i-JmsUOjFch9ytV89NjPfJPVSzGLzAzGQ",
"https://dnznrvs05pmza.cloudfront.net/25851e70-f7ba-40b2-b138-017921799fd6.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNzcwODc0MDY4ODRiMDYxZSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM4NTA5NH0.OLeqyc994WNlQJsp71q_3sYi36yqk07APv-jS64nyrw",
"https://dnznrvs05pmza.cloudfront.net/187e9195-74f9-4849-8c2f-2cbf62e25f6d.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMTljNGFiNTk5MmQzNTc1ZiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NTcyMX0.Qiqf5EVKkYBg2eUXc9KTUxjefyIz5XuWKiLGM0KYGWs",
"https://dnznrvs05pmza.cloudfront.net/de8c2ed4-9cdd-4f3a-91eb-da199f2bf8c4.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOGVjM2M0NGQxNmFmNDMxZCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxOTI0NX0.WXhwYRmvtDiNvVeUi35DNm8Rgg0ljMzqSReorwMWlBM",
"https://dnznrvs05pmza.cloudfront.net/5fa48273-d8a5-4ed2-bf0c-fbcbb3f94f65.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOTAyMTEzOGFkOWFiOWQ1NiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxNTU5NH0.4_BE_KYVG6uPDXaV9XGcTOuZ2DiTXQxvGkrKRzcq518",
"https://dnznrvs05pmza.cloudfront.net/3cee1a0e-6585-4c2c-a0c8-7fbed1eb7bf8.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMGM0MGIxYzllYjYxMDZhYiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMyNjQwOX0.Qr4foVZY5QaDSDEbwpq3NGPu6vfqG4RQlYpBE7Yu1t8",
"https://dnznrvs05pmza.cloudfront.net/81381c37-5f7b-4527-94d1-b7311b233c5f.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOWY5OWYwZGZiY2JjOGNhZiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0OTIxNX0.Ftz_2HYWRZHuIWOZPksdtrjuVmj2QTso0XvXN1N2uQ4",
"https://dnznrvs05pmza.cloudfront.net/00993cc9-a77d-4b8f-b446-125719d3463c.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZjgwN2NkYjI3NjJhNTQ5YyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2OTc3OH0.09JJ0Z2uSx6hUxz49xSIqmcZ1BFaHhHR-I5jezgZyms",
"https://dnznrvs05pmza.cloudfront.net/47b3dd49-5c35-462d-9716-47d0a9b6c46b.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMWVlMjQyZDdlYmIyMjdhMyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMwOTUyN30.WwmOpl9BuFY3VdCGaxb1f38RENOve6yDIYmZjal6Grg",
"https://dnznrvs05pmza.cloudfront.net/be62e82c-e723-4fb9-b486-3441331ef69b.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMmI0MGUwMDE0NzFiNjM0MSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM5MDMzN30.AO-knDpAsjdCfxLrQoRExoesQIUqnPZvhT0WvgDEJZ4",
"https://dnznrvs05pmza.cloudfront.net/86ade143-3251-443a-982a-4ac71e1f1122.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMDU0YWFjYTkyNDVkM2I5OCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1Mjc0NX0.SisYoL8tLUhFg2_Pw8xXiq6cI9svPRrS85Pj8jyCjBI",
"https://dnznrvs05pmza.cloudfront.net/27acd3ec-ea85-47e2-9615-c3dfc390814e.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYzEzNDNmODQwODcxOWI4NiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1MDAyMH0.QtAsxmjAiApeCIghdlvlU23iw7UZTY1-zKWIqckIZ2M",
"https://dnznrvs05pmza.cloudfront.net/08f70822-44cc-4eac-9c2f-f096ea6bccfd.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjUyOGZmMjE1NjA3M2I1YyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNTk2OX0.eQGHJsP3SZFktbMMhkWhY5cocnQkDZc_sH7P_9TI0Kc",
"https://dnznrvs05pmza.cloudfront.net/f042a095-81c0-4e03-915b-fcae3056d73b.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNDM4ZDBiNzAyZjg0OTA1NiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxMzc3Nn0.B2z_d8mKzN4L-JnhBOwV1w-IJawSq5xZ_RzrON5HSYA",
"https://dnznrvs05pmza.cloudfront.net/dcc80042-1403-4099-b523-48014b0359cf.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiN2U4ZGRjNDEyMTQ1N2Y4OCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzODE3N30.9WtyEsX7kXeTiCqKcou4kQuFU8brPjYzxSpwsH-AfYM",
"https://dnznrvs05pmza.cloudfront.net/36ce1102-e8a8-47f4-9a84-44c947374758.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMGE5OGEwZjljMzhhMmY2MCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1NTY0MX0.U_iakjE3KscaSH5k1khgQvz5E9dYEsJWMlCeoHxt19I",
"https://dnznrvs05pmza.cloudfront.net/50993704-e756-4635-9f99-8877285c3fa8.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMGE2NzUxNDRiNzM1YTYwZiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMyMDc3Mn0.mAExmFQ2ql0CnUOMWEwsjwFX9oBEDWVOG2KeZm_f3rA",
"https://dnznrvs05pmza.cloudfront.net/023938b1-259c-4c03-ac01-f8e40207f48d.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMjc1Yjg3NzZlODI5MGE1NCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0NjY3OH0.pVYlp4nbg6bngqry6tSg8svsLco7oYB_M7EED5Q4QKo",
"https://dnznrvs05pmza.cloudfront.net/22b3aa04-0b6c-46da-b13c-97cfb50e3d77.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNmRkYzk5M2RmZjBmNDcxNiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMwODA5M30.Q5sOvLyHoTTC8A_zRPTNjV91EO37iR5CA99vZS8vro8"
]
THUMB="https://dnznrvs05pmza.cloudfront.net/6d211f3b-0f4c-48e4-b81e-10f685fd1d96.png?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiODVkMzZmYjBkZmY5ZGFiZSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0MTYxNn0.QiIish3eXW5IVsykqgwlSKRk9X7ZHsoxK-yhZbIDRA4"
NARRATION = r"""The first thing I learned about being lost in a blizzard is that the snow does not have to bury you to kill you. It only has to make you stop moving. I understood that on the first night, when the wind erased my footprints before I had even finished looking back at them.

My name is Daniel. I was supposed to be driving home before sunset. The forecast said light snow, nothing unusual for the mountains. But the storm arrived early, swallowed the road, and turned the world outside my windshield into a white wall. My car slid into a ditch. The engine died. My phone showed one bar, then none.

I waited for headlights. I waited for the sound of another car. I waited until the cold began to creep through the floorboards and into my boots. When the windows started frosting from the edges, I knew staying there was no longer an option. I took my backpack, a flashlight, a bottle of water, and the small emergency blanket from the trunk.

I walked toward what I thought was a line of pine trees. The wind pushed against my chest as if someone were leaning on me. Snow struck my face like handfuls of sand. Every few steps I stopped, turned around, and tried to memorize the direction of the car. Within minutes, it disappeared.

The first night was a lesson in distance. Objects that looked close were impossibly far away. A dark shape on the horizon became a tree. A tree became a rock. A rock became nothing at all. I kept moving because stopping felt like surrender. Then, through the storm, I saw a warm amber light.

It came from a cabin tucked between black pine trees. Smoke rose from the chimney, thin and steady. I knocked until my fingers hurt. No one answered. The door was unlocked. Inside, there was a wood stove, a table, two chairs, and a radio that hissed with static. I told myself someone would return. I told myself I was lucky.

The cabin smelled of wet timber and old smoke. A blanket lay folded on the sofa. A lantern sat on the table, already filled with oil. There were fresh boot prints near the fireplace, but no footprints leading away from the front door. I tried the radio. A voice came through in broken fragments, then vanished beneath the static.

I found a map pinned to the wall. The nearest ranger station was marked beyond a ridge, perhaps six miles away. In daylight, that might have been manageable. In a blizzard, it was a gamble. I decided to wait until morning, fed a few pieces of wood into the stove, and listened to the wind scrape the roof.

At 2:17 a.m., three knocks sounded from the front door.

I froze. The knocks were slow and evenly spaced. Not the frantic pounding of someone caught in the storm. Three careful taps. I waited for a voice. Nothing came. Then the radio clicked on by itself.

A man's voice whispered, "Do not open the door."

I stared at the radio. The signal crackled. The voice repeated the warning, clearer this time. "Whatever you hear outside, do not open the door."

Then something on the porch said my name.

Not "help." Not "please." It said, "Daniel," in the exact voice of my older brother, who had been dead for six years.

I backed away from the door. The voice outside sounded tired, almost embarrassed. It asked me to let it in because it had lost its gloves. It said it knew I was frightened. It said it could see the light under the door.

I reached for the radio. "Who is this?" I whispered.

The answer came immediately. "Stay away from the windows."

A shadow crossed the frost-covered glass. It was too tall to be a person standing on the porch. Its head nearly reached the top of the frame. I watched it move from one window to the next without making a sound in the snow.

I did not sleep. I sat with my back against the stove and kept the flashlight in my hand. Every few minutes, the porch boards creaked. Once, I heard slow footsteps circling the cabin. They stopped beneath the bedroom window. Then came a soft scratching, like a fingernail being dragged across the glass.

At dawn, the storm weakened. I opened the door just far enough to look outside. There were footprints in the snow. They formed a perfect circle around the cabin. Every print pointed toward the walls. None pointed away.

I should have left then. I know that now. But the radio was quiet, the sky was brighter, and I had convinced myself that fear had made the night seem stranger than it was. I followed the map toward the ridge, using the cabin chimney as a marker until the trees swallowed it.

The second day was harder. The snow reached my knees in places. My water bottle was freezing. I found a narrow trail and followed it downhill, hoping it would lead to a road. Instead, it brought me to another clearing and another building: a smaller cabin, half collapsed, with a roof buried under snow.

Inside, the air was colder than outside. The walls were blackened by an old fire. A metal box sat beneath a broken table. Inside it were photographs, a rusted key, and a folded newspaper. One photograph showed the cabin I had slept in. In front of it stood a young man wearing a green parka, a blue scarf, and a brown backpack.

He looked exactly like me.

I turned the photograph over. On the back, someone had written a date from twelve years earlier. Beneath it were four words: "He came back again."

I dropped the picture. My hands were shaking so badly I could barely pick it up. I searched the newspaper. The headline described a winter disappearance. A hiker named Daniel Mercer had vanished during a blizzard. Search teams found his car, but no body. The last known sighting was near the old cabin.

My full name is Daniel Mercer.

I ran. I ran until my lungs burned and the trees blurred into dark streaks. I did not know where I was going. I only knew the photograph had been taken twelve years before I was born. At the edge of the clearing, I saw a ranger marker and a trail sign pointing toward the station.

Then I heard the radio voice again. It was not coming from the cabin. It was coming from the small handheld radio clipped to my backpack. I had never owned a radio like that. I had never put it there.

"Daniel," the voice said. "You found the photograph."

I threw the radio into the snow. It kept speaking.

"Do not trust the first person who finds you."

The second night fell before I reached the ridge. The storm returned, stronger than before. I found a shallow rock shelter and wrapped myself in the emergency blanket. The wind howled through the trees. At some point, I heard a rescue helicopter. Its lights moved between the clouds, then disappeared.

I shouted until my throat hurt. No one answered.

Near midnight, a beam of light swept across the snow. A man in a ranger jacket stood at the edge of the shelter. He carried a lantern and wore a calm, familiar expression. He called himself Officer Hale. He said a search team had been looking for me since yesterday.

I almost cried with relief. Then I noticed his boots. They were completely dry.

Snow covered his shoulders, his hat, and his gloves. But his boots were dry, as if he had stepped out of a warm room instead of walking through a blizzard. I remembered the radio warning. Do not trust the first person who finds you.

I asked him where the station was. He pointed into the trees. I asked him what day it was. He smiled and said, "The day you came home."

I stepped backward. Hale did not move. He only tilted his head and looked past me, toward the dark trees. For a moment, his face seemed to flicker, like a reflection disturbed by water.

Then the radio crackled again. "Run."

I ran.

Behind me, the lantern light did not follow. The snow around my boots glowed faintly blue. I heard the ranger call my name, but the voice changed halfway through the word. It became my brother's voice. Then my own.

I reached the ridge just before sunrise. Below it, I saw the real road, a line of orange markers, and a rescue truck moving slowly through the snow. I waved my flashlight. The driver stopped. Two real rescue workers climbed out and ran toward me.

They wrapped me in a blanket and asked how long I had been missing. I told them three nights. They exchanged a look. One of them said the storm had lasted less than twenty hours.

At the ranger station, they showed me a photograph from the search camera. It showed me standing outside the cabin at 2:17 a.m. My hand was raised toward the door. Behind the frosted window stood a second figure, wearing my clothes and smiling.

The rescue team said the cabin had burned down twelve years ago. There had been no standing structure there for more than a decade. They said the old trail was closed. They said no one named Officer Hale worked in the district.

I asked about the photograph. The ranger searched the evidence bag, but it was empty. He asked me to describe it. When I did, his expression changed. He opened a locked drawer and took out an older photograph.

It showed the same cabin. The same snow. The same young man in the green parka. But this time, the man was standing behind the glass, looking out.

The ranger said the picture had been found in the pocket of a missing hiker twelve years ago. The hiker's name was Daniel Mercer.

I told him that was my name. He did not answer. He only asked me to look at the date printed on the back.

It was tomorrow's date.

They let me go home after sunrise. I did not sleep. I kept every light on. I checked the locks twice, then a third time. At 2:17 a.m., a package appeared on my doorstep. There was no delivery van on the street. No footsteps in the snow. Just a small black box with my name written across the top.

Inside was a memory card and a note: "You were not rescued. You were returned."

I watched the footage on an old laptop. It showed the cabin from outside, filmed through the trees. The camera slowly moved toward the porch. The door opened. A man stepped out wearing my green parka and blue scarf.

He looked directly into the camera.

Then he smiled and whispered, "Don't trust the rescue team."

The screen went black. A final line appeared: "The storm is not over."

I looked toward the window. Beyond the glass, the street was empty. The snow had stopped falling. But on the other side of the window, from the outside, a finger slowly traced three words into the frost.

"LET ME IN."

I stepped away. The radio on my kitchen counter clicked on, though I had thrown it into the snow. A voice whispered, "Daniel, you left the door open."

And then, from somewhere inside my own house, three careful knocks answered."""
def run(cmd):
    print("+"," ".join(map(str,cmd[:7])),flush=True)
    subprocess.run(cmd,check=True)
def ass_time(t):
    n=round(t*100); return f"{n//360000}:{(n//6000)%60:02d}:{(n//100)%60:02d}.{n%100:02d}"
async def make_voice():
    audio=ASSETS/"narration.mp3"; words=[]
    comm=edge_tts.Communicate(NARRATION,VOICE,rate="-7%",volume="+0%",pitch="-1Hz",boundary="WordBoundary")
    with audio.open("wb") as f:
        async for c in comm.stream():
            if c["type"]=="audio": f.write(c["data"])
            elif c["type"]=="WordBoundary":
                words.append((c["offset"]/10_000_000,(c["offset"]+c["duration"])/10_000_000,c["text"]))
    if not words: raise RuntimeError("No speech timings returned")
    return audio,words
def make_ass(words,path):
    lines=["[Script Info]","ScriptType: v4.00+","PlayResX: 1920","PlayResY: 1080","[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
    "Style: Nova,DejaVu Sans,52,&H00FFFFFF,&H0000D7FF,&H00000000,&HAA000000,-1,0,0,0,100,100,0,0,1,5,2,2,100,100,95,1","[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for i in range(0,len(words),6):
        g=words[i:i+6]; chunks=[]
        for a,b,w in g:
            k=max(1,round((b-a)*100))
            safe=w.replace("{",r"\{").replace("}",r"\}")
            chunks.append("{\\kf"+str(k)+"}"+safe)
        lines.append(f"Dialogue: 0,{ass_time(g[0][0])},{ass_time(g[-1][1]+0.12)},Nova,,0,0,0,,{' '.join(chunks)}")
    path.write_text("\n".join(lines),encoding="utf-8")
def download(url,path):
    import urllib.request
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=120) as r: data=r.read()
    if len(data)<10000: raise RuntimeError(f"Asset too small: {path.name}")
    path.write_bytes(data)
def main():
    audio,words=asyncio.run(make_voice())
    audio_len=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(audio)],text=True).strip())
    total=max(TOTAL,audio_len+2)
    clip_len=total/len(IMAGES)
    clips=[]
    for i,url in enumerate(IMAGES):
        img=ASSETS/f"scene_{i+1:02d}.png"
        if not img.exists():
            print(f"Fetching still image {i+1}/{len(IMAGES)}",flush=True); download(url,img)
        clip=ASSETS/f"clip_{i+1:02d}.mp4"; clips.append(clip)
        frames=round(clip_len*FPS)
        zoom="min(zoom+0.00012,1.085)" if i%2==0 else "max(zoom-0.00012,1.0)"
        x="iw/2-(iw/zoom/2)" if i%2==0 else "iw/2-(iw/zoom/2)+12*sin(on/85)"
        y="ih/2-(ih/zoom/2)"
        vf=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},zoompan=z='{zoom}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},fade=t=in:st=0:d=0.55,fade=t=out:st={clip_len-0.6:.3f}:d=0.55,format=yuv420p"
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-i",str(img),"-vf",vf,"-frames:v",str(frames),"-r",str(FPS),"-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(clip)])
    concat=ASSETS/"clips.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
    silent=ASSETS/"silent.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    ass=OUT/"captions.ass"; make_ass(words,ass)
    # Quiet blizzard ambience plus a low cinematic drone under the narration.
    fc=f"[1:a]volume=1.0,apad=whole_dur={total:.3f}[voice];anoisesrc=color=pink:duration={total:.3f}:sample_rate=48000,lowpass=f=520,volume=0.025[wind];sine=frequency=54:duration={total:.3f}:sample_rate=48000,volume=0.018[drone];[voice][wind][drone]amix=inputs=3:duration=longest:weights=1 0.45 0.25[a]"
    mp4=OUT/"blizzard_story_10min.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),"-filter_complex",fc,"-map","0:v:0","-map","[a]","-vf",f"subtitles={ass}:fontsdir=/usr/share/fonts/truetype/dejavu","-t",f"{total:.3f}","-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(mp4)])
    thumb=ASSETS/"thumbnail.png"; download(THUMB,thumb)
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(mp4)],text=True).strip())
    meta={"title":"I Was Lost in a Blizzard for 3 Nights… Then I Saw Something Outside","thumbnail_text":"IT WAS WATCHING ME!","duration_seconds":round(duration,2),"narration_seconds":round(audio_len,2),"scenes":len(IMAGES),"resolution":"1920x1080","format":"16:9","captions":"word-highlighted English karaoke captions, lower-middle","audio":"English narration + subtle cinematic blizzard ambience","render":"FFmpeg still-image montage with slow Ken Burns motion"}
    (OUT/"metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("BLIZZARD_RENDER_SUCCESS "+json.dumps(meta),flush=True)
if __name__=="__main__": main()
