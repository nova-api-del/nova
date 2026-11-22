import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "story_channel"))
import animate_plan, render_story, write_story  # noqa: E402


def good_story(n=36, words=35):
    return {"title": "t", "description": "d", "tags": ["a"], "thumb_text": "x", "thumbnail_visual": "v",
            "scenes": [{"narration": " ".join(["word"] * words), "visual": "v", "has_character": True} for _ in range(n)]}


class ValidateTests(unittest.TestCase):
    def test_accepts_full_story(self):
        self.assertEqual(write_story.validate(good_story()), [])

    def test_rejects_short_story(self):
        self.assertTrue(write_story.validate(good_story(n=5)))

    def test_rejects_missing_fields(self):
        story = good_story()
        del story["title"]
        self.assertIn("missing title", write_story.validate(story))


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg required")
class RenderTests(unittest.TestCase):
    def test_render_two_scenes_with_fake_tts(self):
        from PIL import Image
        tmp = Path(tempfile.mkdtemp())
        frames = tmp / "frames"
        frames.mkdir()
        for n, color in ((1, (200, 60, 60)), (2, (60, 60, 200))):
            Image.new("RGB", (1024, 576), color).save(frames / f"scene_{n:02d}.png")
        story = good_story(n=2, words=8)
        story["title"] = "Test"
        out = tmp / "out"
        out.mkdir()
        (out / "story.json").write_text(json.dumps(story))

        async def fake_synth(text, mp3):
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "anullsrc=r=24000:cl=mono", "-t", "2", "-c:a", "libmp3lame", str(mp3)], check=True)
            return [{"start": i * 0.2, "end": i * 0.2 + 0.18, "text": w} for i, w in enumerate(text.split())]

        render_story.OUT, render_story.FRAMES, render_story.synth = out, frames, fake_synth
        self.assertEqual(render_story.main(), 0)
        self.assertTrue((out / "video.mp4").exists())
        self.assertTrue((out / "thumbnail.jpg").exists())
        self.assertGreater(render_story.probe_duration(out / "video.mp4"), 4.0)

    def test_missing_image_stops_build(self):
        tmp = Path(tempfile.mkdtemp())
        out = tmp / "out"
        out.mkdir()
        (out / "story.json").write_text(json.dumps(good_story(n=1, words=5)))
        render_story.OUT, render_story.FRAMES = out, tmp / "none"
        with self.assertRaises(SystemExit):
            render_story.main()


class AnimatePlanTests(unittest.TestCase):
    def test_uses_key_moments_and_always_includes_hook(self):
        story = good_story(n=36)
        for i in (9, 20, 30):
            story["scenes"][i]["key_moment"] = True
        picks = animate_plan.pick_animation_scenes(story, limit=5)
        self.assertTrue({1, 10, 21, 31} <= set(picks))  # hook + all flagged key moments are kept
        self.assertEqual(len(picks), 5)                  # one extra scene is spread in to reach the limit
        too_many = good_story(n=36)
        for i in (4, 9, 14, 20, 25, 30):
            too_many["scenes"][i]["key_moment"] = True
        self.assertEqual(animate_plan.pick_animation_scenes(too_many, limit=5), [1, 5, 10, 15, 21])

    def test_respects_limit_and_falls_back_to_even_spread(self):
        picks = animate_plan.pick_animation_scenes(good_story(n=36), limit=5)
        self.assertEqual(len(picks), 5)
        self.assertEqual(picks, sorted(set(picks)))
        self.assertEqual(picks[0], 1)
        self.assertTrue(all(1 <= n <= 36 for n in picks))

    def test_empty_story_and_zero_limit(self):
        self.assertEqual(animate_plan.pick_animation_scenes({"scenes": []}), [])
        self.assertEqual(animate_plan.pick_animation_scenes(good_story(n=5), limit=0), [])


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg required")
class AnimatedSceneRenderTests(unittest.TestCase):
    def test_scene_uses_animated_clip_when_present(self):
        from PIL import Image
        tmp = Path(tempfile.mkdtemp())
        frames = tmp / "frames"
        frames.mkdir()
        for n in (1, 2):
            Image.new("RGB", (1024, 576), (30, 60, 120)).save(frames / f"scene_{n:02d}.png")
        # scene 2 gets a 2-second animated clip (a moving test pattern stands in for a Wan clip)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "testsrc=size=832x480:rate=24:duration=2", "-pix_fmt", "yuv420p",
                        str(frames / "scene_02.mp4")], check=True)
        story = good_story(n=2, words=8)
        out = tmp / "out"
        out.mkdir()
        (out / "story.json").write_text(json.dumps(story))

        async def fake_synth(text, mp3):
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "anullsrc=r=24000:cl=mono", "-t", "5", "-c:a", "libmp3lame", str(mp3)], check=True)
            return [{"start": i * 0.2, "end": i * 0.2 + 0.18, "text": w} for i, w in enumerate(text.split())]

        render_story.OUT, render_story.FRAMES, render_story.synth = out, frames, fake_synth
        self.assertEqual(render_story.main(), 0)
        # the 2s clip was looped (ping-pong) to cover ~5.35s of narration, so the scene is longer than the clip
        scene2 = out / "work" / "scene_02.mp4"
        self.assertGreater(render_story.probe_duration(scene2), 5.0)
        self.assertTrue((out / "work" / "pingpong_02.mp4").exists())
        self.assertFalse((out / "work" / "pingpong_01.mp4").exists())  # scene 1 stayed a still image
        self.assertGreater(render_story.probe_duration(out / "video.mp4"), 10.0)


if __name__ == "__main__":
    unittest.main()
