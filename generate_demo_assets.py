"""
VectorScope Automated Demo Asset Pipeline
Generates:
1. 5 High-resolution targeted screenshots (assets/screenshots/)
2. Voiceover narration (assets/narration.mp3 via edge-tts)
3. Synchronized 1080p demo video (assets/vectorscope_demo.mp4)
"""

import os
import sys
import time
import asyncio
import subprocess
from pathlib import Path

import imageio_ffmpeg
import edge_tts
from selenium import webdriver
from selenium.webdriver.edge.options import Options

ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / "assets"
SCREENSHOTS_DIR = ASSETS_DIR / "screenshots"

NARRATION_TEXT = """Welcome to VectorScope, an operational epidemiological early warning and larval source reduction GIS platform engineered for Gainesville and Alachua County.

In sub-tropical ecosystems, invasive vectors like Aedes albopictus and Culex quinquefasciatus drive arboviral transmission of Dengue and West Nile Virus. VectorScope bridges space-borne Earth observations with local public health action.

Our automated data pipeline continuously queries the NASA CMR STAC API, ingesting MODIS Land Surface Temperature and GPM IMERG 72-hour precipitation data. Through non-linear Briére-1 biological kinetics, the platform computes enzymatic developmental velocity, pinpointing peak vector competence around 29.2 degrees Celsius while resolving optical canopy blindspots using NASA GLOBE citizen ground truth.

Crucially, VectorScope integrates the CDC Social Vulnerability Index, ensuring historically under-resourced communities like the East Gainesville corridor receive top dispatch priority.

Public health teams can run chronological storm surge simulations to model post-deluge larval blooms, while the embedded Google Gemini AI copilot synthesizes live environmental telemetry to prescribe precise, counterfactual Bti larvicide and civic interventions.

VectorScope: transforming satellite Earth observations into precision vector epidemiology."""


def setup_directories():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] Directories ready: {SCREENSHOTS_DIR}")


async def generate_narration():
    audio_path = ASSETS_DIR / "narration.mp3"
    print("[2/4] Synthesizing professional voiceover with edge-tts...")
    communicate = edge_tts.Communicate(NARRATION_TEXT, "en-US-ChristopherNeural", rate="+2%")
    await communicate.save(str(audio_path))
    print(f"      Narration saved to: {audio_path}")
    return audio_path


def get_audio_duration(audio_path: Path) -> float:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-i", str(audio_path)]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            # Example: Duration: 00:01:26.47, start: 0.000000
            parts = line.strip().split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            duration = int(h) * 3600 + int(m) * 60 + float(s)
            return duration
    return 86.5


def capture_screenshots():
    print("[3/4] Launching headless browser for 1080p screenshot captures...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    
    driver = webdriver.Edge(options=options)
    try:
        driver.get("http://localhost:8080")
        time.sleep(3.5)

        # Screenshot 1: Full Mission Control overview (01_overview.png)
        print("      Capturing 01_overview.png...")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1.0)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "01_overview.png"))

        # Screenshot 2: Zoomed-in GIS map highlighting the outbreak hotspot rings & telemetry (02_gis_hotspots.png)
        print("      Capturing 02_gis_hotspots.png...")
        driver.execute_script("""
            if (window.selectSector) window.selectSector('sec-east-gvl');
            if (window.map) {
                window.map.setView([29.6516, -82.3248], 13);
                window.map.invalidateSize();
            }
            window.scrollTo(0, 520);
        """)
        time.sleep(2.0)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "02_gis_hotspots.png"))

        # Screenshot 3: Environmental Drivers panel focusing on NASA LST & NDVI metrics (03_environmental_drivers.png)
        print("      Capturing 03_environmental_drivers.png...")
        driver.execute_script("""
            const el = document.getElementById('storm-surge-simulator-card');
            if (el) el.scrollIntoView({behavior: 'instant'});
            window.scrollBy(0, 220);
        """)
        time.sleep(1.5)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "03_environmental_drivers.png"))

        # Screenshot 4: Storm Surge Simulation & Larval breeding predictions (04_simulation_engine.png)
        print("      Capturing 04_simulation_engine.png...")
        driver.execute_script("""
            if (window.stepStormSurgeSimulation) {
                window.stepStormSurgeSimulation(4);
            }
            const el = document.getElementById('storm-surge-simulator-card');
            if (el) el.scrollIntoView({behavior: 'instant'});
            window.scrollBy(0, -50);
        """)
        time.sleep(1.5)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "04_simulation_engine.png"))

        # Screenshot 5: Embedded Gemini Epidemiological Copilot recommendation panel (05_ai_copilot.png)
        print("      Capturing 05_ai_copilot.png...")
        driver.execute_script("""
            if (window.runGeminiOutbreakSynthesis) {
                window.runGeminiOutbreakSynthesis();
            }
        """)
        time.sleep(3.0)
        driver.execute_script("""
            const el = document.getElementById('ai-copilot-output');
            if (el) el.scrollIntoView({behavior: 'instant', block: 'center'});
        """)
        time.sleep(1.5)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "05_ai_copilot.png"))

        print("      All 5 screenshots captured successfully!")
    finally:
        driver.quit()


def compile_video(audio_path: Path):
    print("[4/4] Compiling 1080p synchronized demo video...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    total_duration = get_audio_duration(audio_path)
    print(f"      Narration duration: {total_duration:.2f} seconds")

    # 5 slides over total_duration with smooth crossfade
    slides = [
        SCREENSHOTS_DIR / "01_overview.png",
        SCREENSHOTS_DIR / "02_gis_hotspots.png",
        SCREENSHOTS_DIR / "03_environmental_drivers.png",
        SCREENSHOTS_DIR / "04_simulation_engine.png",
        SCREENSHOTS_DIR / "05_ai_copilot.png",
    ]

    for s in slides:
        if not s.exists():
            raise FileNotFoundError(f"Missing required screenshot: {s}")

    # Calculate per-slide duration
    slide_dur = total_duration / len(slides)
    output_video = ASSETS_DIR / "vectorscope_demo.mp4"

    # Create an ffmpeg concat script with duration per image
    concat_file = ASSETS_DIR / "slides_input.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for s in slides:
            f.write(f"file '{s.as_posix()}'\n")
            f.write(f"duration {slide_dur:.3f}\n")
        # Repeat last file to satisfy ffmpeg concat demuxer convention
        f.write(f"file '{slides[-1].as_posix()}'\n")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-i", str(audio_path),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x060913",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.2f}",
        str(output_video),
    ]

    print(f"      Rendering video with ffmpeg: {output_video.name}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"FFmpeg stderr:\n{res.stderr}")
        raise RuntimeError("FFmpeg video rendering failed.")

    # Clean up temporary concat file
    if concat_file.exists():
        concat_file.unlink()

    print(f"      Demo video successfully rendered: {output_video}")
    return output_video


async def main():
    setup_directories()
    audio_path = await generate_narration()
    capture_screenshots()
    video_path = compile_video(audio_path)
    print("\n========================================================")
    print(" PIPELINE COMPLETE!")
    print(f" Screenshots: {SCREENSHOTS_DIR}")
    print(f" Narration:   {audio_path}")
    print(f" Demo Video:  {video_path}")
    print("========================================================")


if __name__ == "__main__":
    asyncio.run(main())
