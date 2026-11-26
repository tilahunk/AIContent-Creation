import json
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "outputs" / "the-next-page-film"
WIDTH = 1280
HEIGHT = 720
CHROME_CANDIDATES = (
    Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
)

DEFS = """
<defs>
  <linearGradient id="sky" x2="0" y2="1">
    <stop stop-color="#172b42"/><stop offset=".62" stop-color="#d47a55"/>
    <stop offset="1" stop-color="#f0bd73"/>
  </linearGradient>
  <linearGradient id="wall" x2="0" y2="1">
    <stop stop-color="#f4e3c9"/><stop offset="1" stop-color="#d8b995"/>
  </linearGradient>
  <linearGradient id="floor" x2="0" y2="1">
    <stop stop-color="#b77c52"/><stop offset="1" stop-color="#684638"/>
  </linearGradient>
  <linearGradient id="window" x2="0" y2="1">
    <stop stop-color="#f6c477"/><stop offset="1" stop-color="#b75e49"/>
  </linearGradient>
  <pattern id="tibeb" width="36" height="24" patternUnits="userSpaceOnUse">
    <rect width="36" height="24" fill="#f3eddf"/>
    <path d="M0 3H36M0 21H36" stroke="#1b6570" stroke-width="3"/>
    <path d="M6 5L12 12L6 19L0 12ZM24 5L30 12L24 19L18 12Z" fill="#b84837"/>
    <path d="M12 7L16 12L12 17L8 12ZM30 7L34 12L30 17L26 12Z" fill="#d49b3f"/>
  </pattern>
  <pattern id="gabi" width="48" height="36" patternUnits="userSpaceOnUse">
    <rect width="48" height="36" fill="#f2eddf"/>
    <path d="M0 5H48M0 10H48M0 29H48M0 33H48" stroke="#315c59" stroke-width="2"/>
    <path d="M0 17H48M0 21H48" stroke="#9e4439" stroke-width="1.5"/>
  </pattern>
  <pattern id="woven" width="32" height="24" patternUnits="userSpaceOnUse">
    <rect width="32" height="24" fill="#e8d5b6"/>
    <path d="M0 4H32M0 12H32M0 20H32" stroke="#315c59" stroke-width="2"/>
    <path d="M8 0V24M24 0V24" stroke="#a9573d" stroke-width="2"/>
  </pattern>
  <filter id="shadow" x="-30%" y="-30%" width="160%" height="170%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="7"/>
    <feOffset dy="7"/><feComponentTransfer>
      <feFuncA type="linear" slope=".24"/>
    </feComponentTransfer><feMerge>
      <feMergeNode/><feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
"""


def person(x, baseline, scale=1, kind="hana", clothing=None):
    clothing = clothing or kind
    skin = {"hana": "#814a36", "bekele": "#70412f", "sami": "#925438"}.get(kind, "#87503a")
    hair = "#241f20" if kind != "bekele" else "#403b38"
    if clothing == "hana":
        body = """
          <path d="M-31-230L-67-202L-49-150L-39-45Q0-25 39-45L49-150L67-202L31-230Z"
            fill="#f4efe2" stroke="#5b4b42" stroke-width="3"/>
          <path d="M-48-73Q0-62 48-73L43-43Q0-27-43-43Z" fill="url(#tibeb)"/>
          <path d="M-25-226Q-5-211 15-226L38-165L17-156L-1-191L-20-156L-39-166Z"
            fill="#fffaf0" stroke="#bcae99" stroke-width="2"/>
          <path d="M-38-168L-20-158L-2-194L17-157L37-167" fill="none"
            stroke="url(#tibeb)" stroke-width="9"/>
          <path d="M-61-192L-49-154M61-192L49-154" stroke="url(#tibeb)" stroke-width="9"/>
        """
    elif clothing == "bekele":
        body = """
          <path d="M-34-231L-65-205L-52-111L-44-44Q0-30 44-44L52-111L65-205L34-231Z"
            fill="#f7f2e7" stroke="#65564b" stroke-width="3"/>
          <path d="M-35-226Q-10-207 11-230L43-201L30-175L11-187L-4-143L-31-159L-48-182Z"
            fill="url(#gabi)" stroke="#8c7c69" stroke-width="2"/>
          <path d="M-11-221L0-206L12-222M0-206V-161" fill="none"
            stroke="#b49e80" stroke-width="3"/>
        """
    elif clothing == "sami":
        body = """
          <path d="M-27-230L-58-205L-45-148L-34-86L-28-43Q0-34 28-43L34-86L45-148L58-205L27-230Z"
            fill="#315c78" stroke="#273d4c" stroke-width="3"/>
          <path d="M-25-228L-8-215L10-230L26-211L9-196L-8-208L-23-195L-39-210Z"
            fill="url(#woven)" stroke="#725b49" stroke-width="2"/>
          <path d="M-31-87L0-82L31-87L27-42Q0-34-27-42Z"
            fill="#51443d" stroke="#302d2b" stroke-width="3"/>
        """
    else:
        body = """
          <path d="M-31-230L-64-205L-48-150L-38-45Q0-27 38-45L48-150L64-205L31-230Z"
            fill="url(#woven)" stroke="#57483e" stroke-width="3"/>
          <path d="M-47-74Q0-63 47-74L42-44Q0-28-42-44Z" fill="url(#gabi)"/>
        """

    hair_shape = (
        "<path d='M-34-291Q-42-326-16-333Q4-347 22-331Q45-325 36-288"
        "Q29-301 20-301Q9-290 0-302Q-14-289-24-299Z' fill='" + hair + "'/>"
    )
    face = f"""
      <ellipse cx="0" cy="-276" rx="34" ry="40" fill="{skin}"/>
      {hair_shape}
      <path d="M-22-274Q-15-280-8-274M8-274Q15-280 22-274"
        fill="none" stroke="#2c2421" stroke-width="3" stroke-linecap="round"/>
      <circle cx="-14" cy="-274" r="2.7" fill="#171817"/>
      <circle cx="14" cy="-274" r="2.7" fill="#171817"/>
      <path d="M-7-254Q0-249 8-254" fill="none" stroke="#542f2a"
        stroke-width="2.5" stroke-linecap="round"/>
      <path d="M-11-238V-224M11-238V-224" stroke="{skin}" stroke-width="13"/>
    """
    if kind == "bekele":
        face += """
          <path d="M-31-292Q-22-307-10-302M10-302Q24-308 32-291"
            fill="none" stroke="#b8aca0" stroke-width="8" stroke-linecap="round"/>
        """
    return f"""
      <g transform="translate({x} {baseline}) scale({scale})" filter="url(#shadow)">
        <ellipse cx="0" cy="-8" rx="74" ry="13" fill="#342b29" opacity=".18"/>
        {body}
        {face}
      </g>
    """


def book(x, y, width=110, height=28, color="#a64d3b"):
    return f"""
      <g transform="translate({x} {y})" filter="url(#shadow)">
        <path d="M0 0Q{width/2} -13 {width} 0V{height}Q{width/2} {height-10} 0 {height}Z"
          fill="{color}" stroke="#3d302c" stroke-width="3"/>
        <path d="M{width/2} -11V{height-4}" stroke="#ead9b9" stroke-width="3"/>
        <path d="M10 5Q{width/2} -5 {width-10} 5" fill="none"
          stroke="#e9d8bd" stroke-width="2"/>
      </g>
    """


def shelves():
    return """
      <g opacity=".96">
        <rect x="72" y="188" width="258" height="264" rx="7" fill="#76513b"/>
        <path d="M72 272H330M72 360H330M72 447H330" stroke="#d4ae7f" stroke-width="11"/>
        <path d="M94 205V261M122 198V261M151 209V261M181 196V261M214 204V261M249 194V261M284 207V261"
          stroke="#a7513e" stroke-width="17"/>
        <path d="M102 283V350M133 290V350M165 278V350M198 287V350M231 279V350M269 287V350M303 280V350"
          stroke="#315c78" stroke-width="17"/>
        <path d="M95 372V436M128 378V436M162 367V436M197 379V436M232 370V436M267 377V436M300 368V436"
          stroke="#d69c43" stroke-width="17"/>
        <path d="M86 272H316M86 360H316M86 448H316" stroke="#e8d3ad" stroke-width="4"/>
      </g>
    """


def interior():
    return """
      <rect width="1280" height="720" fill="url(#wall)"/>
      <path d="M0 550H1280V720H0Z" fill="url(#floor)"/>
      <path d="M0 552H1280" stroke="#8b5c42" stroke-width="10"/>
      <path d="M391 110Q391 80 424 80H690Q723 80 723 110V365H391Z"
        fill="#805843" stroke="#5b4438" stroke-width="8"/>
      <path d="M414 113Q414 101 431 101H682Q700 101 700 119V345H414Z"
        fill="url(#window)"/>
      <path d="M420 285Q483 236 540 286T697 277V345H420Z" fill="#45635d" opacity=".72"/>
      <path d="M559 103V346M420 235H697" stroke="#70503e" stroke-width="9"/>
      <path d="M0 478Q640 445 1280 482" fill="none" stroke="#f8e9d1" stroke-width="4" opacity=".5"/>
    """


def exterior():
    return """
      <rect width="1280" height="720" fill="url(#sky)"/>
      <circle cx="1030" cy="188" r="66" fill="#f7d18c" opacity=".9"/>
      <path d="M0 362Q150 245 310 344T640 323T980 342T1280 301V500H0Z" fill="#5a6960"/>
      <path d="M0 414Q190 310 380 402T780 378T1280 390V540H0Z" fill="#394f4a"/>
      <path d="M0 490H1280V720H0Z" fill="#59443d"/>
      <g fill="#c68e65" stroke="#493d39" stroke-width="6">
        <path d="M40 378L135 322L226 380V511H40Z"/>
        <path d="M1010 358L1102 298L1202 366V520H1010Z"/>
        <path d="M232 403L293 365L353 408V500H232Z"/>
      </g>
      <g fill="#4a3c39">
        <rect x="83" y="405" width="30" height="45"/><rect x="153" y="405" width="30" height="45"/>
        <rect x="1050" y="392" width="32" height="48"/><rect x="1130" y="392" width="32" height="48"/>
      </g>
    """


def shopfront():
    return """
      <g filter="url(#shadow)">
        <path d="M334 301L631 213L952 302V571H334Z" fill="#d6b38d"
          stroke="#473c39" stroke-width="9"/>
        <path d="M313 310L630 202L975 310" fill="none" stroke="#453b38" stroke-width="18"/>
        <rect x="390" y="344" width="186" height="227" fill="#34505a" stroke="#473c39" stroke-width="9"/>
        <path d="M403 355H562V562H403Z" fill="#263e4b"/>
        <path d="M418 364V548M438 364V548M458 364V548M478 364V548M498 364V548M518 364V548M538 364V548"
          stroke="#9d7456" stroke-width="8"/>
        <rect x="667" y="339" width="223" height="232" fill="#6b4a39" stroke="#473c39" stroke-width="9"/>
        <rect x="692" y="365" width="173" height="181" fill="#b77a51"/>
        <path d="M708 389H850M708 405H850M708 421H850M708 437H850M708 453H850M708 469H850M708 485H850M708 501H850M708 517H850"
          stroke="#e1c59c" stroke-width="5"/>
        <rect x="492" y="254" width="278" height="35" rx="8" fill="#284c52"/>
        <path d="M511 270H751" stroke="#d2a75e" stroke-width="4"/>
      </g>
      <path d="M0 574H1280V720H0Z" fill="#51413b"/>
      <path d="M0 594Q330 568 640 596T1280 584" fill="none" stroke="#b88a61" stroke-width="7"/>
    """


def scene_svg(scene_id):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">', DEFS]
    if scene_id == "shot_001":
        parts += [exterior(), shopfront(), person(555, 635, .94, "hana")]
        parts += ['<circle cx="615" cy="422" r="13" fill="#d8ad4c"/>',
                  '<path d="M615 422L632 441L623 446L609 430" fill="none" stroke="#d8ad4c" stroke-width="5"/>']
    else:
        parts += [interior(), shelves()]
        if scene_id in {"shot_002", "shot_003"}:
            parts += [person(798, 641, 1.05, "bekele"), person(450, 642, .94, "hana")]
            parts += ['<path d="M341 497H1000V535H341Z" fill="#88583d" stroke="#563d32" stroke-width="6"/>',
                      '<path d="M368 535V692M969 535V692" stroke="#664633" stroke-width="20"/>',
                      book(675, 467, 144, 33)]
            if scene_id == "shot_003":
                parts += ['<path d="M530 513L615 471L700 513V607H530Z" fill="#b9824f" stroke="#6b4936" stroke-width="5"/>',
                          '<path d="M530 513L615 555L700 513" fill="none" stroke="#e1bd8d" stroke-width="4"/>']
        elif scene_id == "shot_004":
            parts += [person(390, 642, .78, "sami"), person(755, 642, .92, "hana"),
                      person(1010, 642, .94, "bekele")]
            parts += ['<path d="M316 507H1046V545H316Z" fill="#88583d" stroke="#563d32" stroke-width="6"/>',
                      '<path d="M355 545V693M1008 545V693" stroke="#664633" stroke-width="20"/>',
                      book(477, 470, 109, 30, "#315c78")]
        elif scene_id == "shot_005":
            parts += [person(500, 705, 1.32, "bekele"), person(790, 705, 1.32, "hana")]
            parts += ['<path d="M180 510H1110V720H180Z" fill="#8f6041" stroke="#563d32" stroke-width="7"/>',
                      '<path d="M330 534H968V676H330Z" fill="#eadfc9" stroke="#695443" stroke-width="4"/>',
                      book(520, 579, 218, 45, "#9d4837"),
                      '<path d="M627 583C699 532 747 627 827 576" fill="none" stroke="#b94d39" stroke-width="5"/>']
        elif scene_id == "shot_006":
            parts += [person(285, 646, .78, "hana"), person(475, 646, .78, "neighbor", "neighbor"),
                      person(690, 646, .82, "sami"), person(885, 646, .78, "bekele"),
                      person(1080, 646, .78, "neighbor", "neighbor")]
            parts += ['<path d="M218 510H1160V548H218Z" fill="#88583d" stroke="#563d32" stroke-width="6"/>',
                      '<path d="M255 548V695M1125 548V695" stroke="#664633" stroke-width="20"/>',
                      book(474, 473, 105, 28), book(734, 474, 114, 28, "#315c78"),
                      '<rect x="930" y="469" width="72" height="52" rx="4" fill="#e4d1aa" stroke="#705642" stroke-width="4"/>',
                      '<path d="M941 508Q960 473 991 503" fill="none" stroke="#52605a" stroke-width="4"/>']
        elif scene_id == "shot_007":
            parts += [person(266, 653, .77, "neighbor", "neighbor"), person(500, 638, .77, "bekele"),
                      person(745, 646, .73, "sami"), person(1006, 653, .77, "hana"),
                      '<path d="M441 504Q620 475 796 504" fill="none" stroke="#8b5d43" stroke-width="18"/>',
                      book(692, 451, 105, 28, "#315c78")]
        elif scene_id == "shot_008":
            parts += [person(708, 645, .94, "hana"), person(947, 645, .92, "bekele")]
            parts += ['<path d="M337 505H1058V539H337Z" fill="#88583d" stroke="#563d32" stroke-width="6"/>',
                      '<path d="M364 539V695M1030 539V695" stroke="#664633" stroke-width="20"/>',
                      book(624, 465, 133, 31),
                      '<path d="M855 412V486" stroke="#695344" stroke-width="8"/><circle cx="855" cy="488" r="14" fill="#d8ad4c"/>']
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    browser = next((path for path in CHROME_CANDIDATES if path.is_file()), None)
    if browser is None:
        browser_name = shutil.which("chrome") or shutil.which("msedge")
        if browser_name is None:
            raise RuntimeError("Chrome or Edge is required to render the local SVG artwork")
        browser = Path(browser_name)

    frames = PACKAGE / "outputs" / "keyframes"
    vectors = PACKAGE / "illustrations"
    frames.mkdir(parents=True, exist_ok=True)
    vectors.mkdir(parents=True, exist_ok=True)
    for index in range(1, 9):
        shot_id = f"shot_{index:03}"
        svg_path = vectors / f"{shot_id}.svg"
        png_path = frames / f"{shot_id}.png"
        svg_path.write_text(scene_svg(shot_id), encoding="utf-8")
        subprocess.run(
            [
                str(browser), "--headless=new", "--disable-gpu", "--no-first-run",
                "--disable-extensions", "--hide-scrollbars",
                f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={png_path}",
                svg_path.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=30,
        )
        for _ in range(50):
            if png_path.is_file() and png_path.stat().st_size:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"Browser did not render illustration: {svg_path}")

    source_storyboard = ROOT / "outputs" / "script" / "storyboard-proposal.json"
    target_storyboard = PACKAGE / "storyboard.json"
    target_storyboard.write_text(
        json.dumps(json.loads(source_storyboard.read_text(encoding="utf-8")),
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    schema_source = ROOT / "schema" / "storyboard.schema.json"
    schema_target = PACKAGE / "schema" / "storyboard.schema.json"
    schema_target.parent.mkdir(parents=True, exist_ok=True)
    schema_target.write_bytes(schema_source.read_bytes())
    print(f"Rendered 8 original illustrated frames into {frames}")


if __name__ == "__main__":
    main()
