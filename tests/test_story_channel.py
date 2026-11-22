import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "story_channel"))
import render_story, write_story  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
