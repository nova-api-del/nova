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
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/f81222ab-39ca-4d23-a900-13b18c80f051/aae3b77f-85e6-43fb-85d4-bc9d1a1a9b1a/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZWE0MmQ5ZDkwMDgxNzI1NyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMwNTY4OX0.T4jcbwI-6xofAUcNgQyyJzwmtw12ISysZxhRR9we1FM",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/233bf657-bbc6-4af3-9785-76327db24396/cfb78ce5-2e97-46c9-9e04-df14cea71ae7/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYWZlZDY4OWM5ODEzMWVjMSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NjgxMn0.Ugft5jo_m-RioQa09hnt6Tzg43kYOcugUb0edblmA6Y",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/23676bc1-9a69-4e85-b055-60da6e0221cc/2dd53251-af51-4d0f-80a3-249a2508efb2/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiM2MyYjk4YjFhYWJlZDQ4ZSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM4NDQ5N30.xXhZYDSvRLeg5Bf9qIM97UZmvz-AaV6NgO8B9vbFSD8",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/78b43983-806e-4059-865b-164d75e269af/10a141ee-667a-4f7d-b6e9-bae8c29e5efa/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOWVkNWZlYWVmNTcxZTIyZiIsImJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM4MTI5NH0.5JpSMbyb5N0g2sTxJ8Sd9aC20_Rh8lm7OqpBGLAS3V0",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/7f1a100c-bd7e-473d-9c24-dc380f1a849b/1b49a7a0-a167-44ec-9db8-94699bd05800/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMzA3NDBjMDMyYTQ0NzNiNyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NjAxOX0.hYYDPh8uGPTyyNSp2tXzC5Q6pFXNFm_dzIWCqP3SY0E",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/1814ba68-40f8-480f-af66-a7aab42b9c7c/41574b29-92f0-4e55-b4a0-617f8f6bc5f0/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNmZiMzRlNjRlYmZhMjBkYyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxMTU4OH0.Cc1uLHJw7KP15X3eqXZISqbbACAy1-uchTmUYtTTwtA",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/a015ef5b-984b-4ed8-a944-ef316fc1393d/a8e46fdd-f829-4589-b4b4-13d807e77b97/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiODhhYjBmMWYzNDFiMWJlYyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNDMwM30.k1DfFvZnz1cp57XTfTZQK-j66tbf8Pn_L7YYgeYefp0",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/0ca55704-3711-4f76-a645-9216293c56e4/b710ba8b-bf7d-40ff-8328-dab05d21e3fd/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZTZkYzU2MjllMTQ3NzRjYiIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NjA1N30.IstgBDPiJPOHtOA8gXSfapDxziw5N36cXDRQ-uMnAKk",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/da4c8469-f811-4722-802e-63ce7b03143c/c80ff591-3c1c-4553-b473-c8718d428d10/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjcyNDM1NDM4NzI0MDQwOCIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxMjU3OX0.ixyeXA63uALtRKi6-iK3yFczkoq-FdiX66zW07KBIGw",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/a9e45897-6a61-4bac-b5b6-da01d9d3e604/e64762aa-3397-4e05-aed4-1804bd738064/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNmE3YWQ0ZjdiYThiNjA4MiIsImJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzNDAwN30.D0ue-j4OtJ7ereyRVZH-1Y-PPA2dsRHqpvGufLqvcjM",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/8bbb65af-f657-4aaa-90ea-fa8a19badb19/51aad27e-f10c-44ff-bc36-fa83fece94ef/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOTY2ZjVjMmYyYTkzNzE3YyIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1NTY5NX0.ZTp-_YGGe2QZJ-nrnwCcL1dabmcI_TEjXH6uHSe_uJg",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/b5f9dba9-d57c-4358-820d-73d10884b95f/d7428323-5704-440b-b88d-f407dccb426c/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiOTRhNDM3MjUxYzI0MTZkYSIsImJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMzMjM4OX0.9DsGaIxdrTRmUm5rSAXjXtkQGv6mVA8bpxiC0VTD3vE",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/05e8a30b-9f00-4645-8446-7b95e457c2b8/36076096-14dd-4ca8-82bc-2aa6b13869bd/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNjVlYjE1NThiM2I4MWI3MSIsImJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM1NDg0MH0.iladqggrJ23XswVTn4OgZTG2K3Ytq834iAgnKfjJ35M",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/da34733b-1a4e-4de6-9157-683883ee1c2d/f7df4f50-2424-4493-b1b2-f6104386dbea/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMjYyZTdkZGJlYzUxYWYzNSIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxNzA4M30.AFUcoMJtII2QpnNOhh7mhZm2VwuLXZWRsf4yNT4_EUw",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/3a4a9e3b-bd1a-452e-9522-ced2e6eec512/71b6f5a1-16ce-452a-9501-070d003d716c/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiODhjY2ZlMGE3ZDdlMGU3ZiIsImJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxMTc1NH0.miCGFBeM0-Z_UcpaxlLjemzbfhpZ0ucCYBVxD3yd078",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/395bd588-1ba6-4fbc-a47c-c55612ca7462/8cb312f6-af45-487d-8092-12f2cd381e7f/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYWU0OTU3M2M0NTI1ZDI1ZSIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxMjQ0NH0.vVHoFpAmtJ0iyu1JfOxROs9gNfSVYsKe9oAEyVWnrSs",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/48f96b49-00b8-47d3-9ea2-9ef1a6bd57f8/0c0e9558-c46f-43ff-9192-41326ad1be02/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYzdmYTJjMWRmZmUzZWQ4YiIsImJ1Y2tldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2ODQ3N30.6a9_IzqaBu35uLidx0f8Gk0NIApw-0medoq6VxpRqek",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/b6a3777e-1267-4a96-85ae-cc3143c51a33/76631b6d-e0ee-44c6-9137-3784436011d3/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiNDU1ZjViNzVlYzg2MWM4MyIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM3NDgzN30.ICVp0fsJEFm9BvKKMNHYH45gMY_i6PzprxouCP094ss",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/fae441a8-d66c-4da2-a4f5-48f60ad1a30e/0e0ffda2-cbff-4a2d-9ae0-9b2f6dc43725/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMjRmYWQ2NmFmZmRiYjcxYiIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM3MjI2Nn0.-A8T7l4LKSgyn6fhe0DjRTP8TCEKQDIQVZEcz2qx_io",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/ffaacdd9-602d-45ce-86a7-7b21b710a640/534492ec-fc46-4e5d-8807-ae22693f78c9/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYzZiM2I1YzdjNGNlNWU2YSIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMxNDI0N30.7i7YYFH2TjNjv08jcykoRq3HYP534ZrMZSCb-50efoc",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/e4170850-e322-488d-ab97-7cd85403d612/8064b8e6-8aad-4dc9-a58c-ebebf11025ae/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYjFiOTgwNDY4NTQxY2ZiYyIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM2NTgzMH0.Aql6oEBw15q21ZQQIt8a7vUaIhGglZ5VBfJrmEj-KIc",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/53c3ae17-543d-42ea-9343-6ba70480ddfc/bab6e2f5-de9c-42dc-97c6-c3e919aa30dc/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiYTAyZDkwMjIxOTY0ZDliMiIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0Njk3OH0.Zb1QL2TiNC4EPQ0MRozeFirL5gcRApYTKHv745Tuty8",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/83f9bbf7-c888-485b-93a3-cc1dbbe20549/5d7b0f45-83dc-4fe0-99c7-241e5bd0f968/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiMjJhOTM1YWJjOWEyN2EzZSIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTM0ODI2N30.P80baXzwAnLJYZk7-eAIhCv9bJ8gyOeRprQsYd8dVhI",
"https://dnznrvs05pmza.cloudfront.net/gemini/gemini-3.1-flash-lite-image/images/0677d0dc-7f1d-4f3e-903a-b9eee7831ac7/bcb06473-1d5f-490b-8234-a1cb5f736ecb/Keep_the_exact_same_single_protagonist_as_the_reference_imag.jpg?_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXlIYXNoIjoiZTQ4YTc1Yzc2NGFhZmFmYyIsImJ1bmtldCI6InJ1bndheS10YXNrLWFydGlmYWN0cyIsInN0YWdlIjoicHJvZCIsImV4cCI6MTc5NTMyNTc2N30.Ilkx6VvnPqpYZzeA0BhJFAiQqQgtl8ysXr7izi3bMoA"
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
