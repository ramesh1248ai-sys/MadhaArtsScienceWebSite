# Madha Arts & Science College — website redesign

A static, responsive redesign of https://www.madhaarts.in/ with AI-enhanced photography.
No build step: plain HTML, one stylesheet and one small script.

## Preview

Double-click `index.html`, or serve the folder:

```
python -m http.server 8000
# open http://localhost:8000
```

## Pages

| File | Contents | Replaces (old site) |
|---|---|---|
| `index.html` | Hero, key facts, about, programme finder, principal's message, admissions + enquiry form, campus life, recent events, Madha Group | Home |
| `about.html` | The college, mission statement & values, Madha Group + sister institutions, management team, principal's full message | About Us menu (5 pages) |
| `academics.html` | All 9 programmes with filters, career training & field visits, UG/PG admission criteria, how to apply | Admissions, Courses |
| `campus-life.html` | Recent events, photo gallery with lightbox, social outreach | Gallery (was empty) |
| `contact.html` | Address, phone, emails, map, enquiry form | Contact Us |

```
assets/css/styles.css      design system + all components
assets/js/main.js          mobile menu, programme filter, lightbox, enquiry form, scroll reveal
assets/img/                enhanced photos used by the site
tools/enhance_images.py    the image enhancement pipeline
tools/prepare_photos.py    crops the college's 2025–26 event photos out of their collages
```

Design: deep navy + warm gold drawn from the college emblem, Newsreader (headings) and Inter (body) from Google Fonts,
responsive from 360px phones to wide desktops, keyboard accessible, respects reduced-motion settings.

## Photo enhancement

Every photo went through `tools/enhance_images.py`:

1. **AI super-resolution with Real-ESRGAN.** `RealESRGAN_x4plus` was used on the smallest, most degraded images (group campus, emblem) and the faster `realesr-general-x4v3` on everything else. The AI output is blended with a plain resample so textures stay natural.
2. **Photographic grade:** white balance and levels, CLAHE local contrast, vibrance, a gentle S-curve, a graduated filter on washed-out skies, and light output sharpening.
3. **Authenticity safeguards:**
   - No generative face restoration (GFPGAN/CodeFormer), because those tools change people's facial features.
   - A small building sign is masked, because the AI invented letters there.

The untouched source photos are no longer kept in the repository. To re-run, put the originals in `assets/img/originals/` and download the weights into `tools/models/`:

- https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
- https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth

then `pip install torch spandrel opencv-python-headless pillow numpy` and `python tools/enhance_images.py`.
It runs on CPU in about 10 minutes.

### Main block photo

`campus-main-block.jpg` (home page hero and the Contact page header) was supplied by the college already edited, and is used unchanged at 1600px wide.

The home page "About the college" image is `campus-foyer.jpg`, the length of the main block foyer (`mainblockentrance3.jpeg`), enhanced to 1600px.
The door signs and the painted captions on both walls are small, so each is covered by a protect box and keeps the plain resample.

The About page header uses `campus-entrance.jpg` instead: staff and students in the main block entrance hall, supplied as a single 1280px photo (`mainblockentrance0.jpeg`).
Because it fills the full page width, it is AI-enhanced like the Campus Life header: `tools/enhance_images.py` upscales it to 2000px with `realesr-general-x4v3` at half strength and a light grade.
The faces and the painted college sign on the back wall were compared against a plain resample and are unchanged apart from being sharper.

The Academics page header uses `campus-mural.jpg`, the painted mural wall in the same entrance hall (`mainblockentrance1.jpeg`), enhanced the same way from a 1040px photo.
Its captions — "Knowledge is power", the framed college name, the Tamil plaque and "Study, strive, shine" — are each covered by a protect box, so the AI cannot reshape that lettering.

The image beside "Two decades of wholesome education" on the About page is `campus-mural-stairway.jpg`, the "Learn, grow, succeed" stairway mural (`mainblockentrance4.jpeg`), enhanced to 1400px with the painted words protected.

Both of these headers carry `page-hero--flat`, which drops the blurred patch that normally sits behind the header text.
Without it the photo is unclouded, and the scrim alone keeps the text legible: measured over the glyph pixels, the worst case is 5.0:1 on Academics and 5.4:1 on About.

### Event photos (2025–26)

The photos behind **Recent events**, the newer gallery tiles and the Academics "Beyond the classroom" section came from the college as WhatsApp images.
Most were social-media collages, so `tools/prepare_photos.py` cuts a single frame out of each, trims the white collage gutters and saves a web JPEG without metadata.
They are not AI-enhanced. The photos arrived in more than one folder, so the script takes as many folders as you pass it and looks for each source file in all of them: `python tools/prepare_photos.py "<folder>" "<another folder>"`.

A second batch of single photos (not collages) fills the newer Campus Life gallery tiles: graduation day, the library, a Madha Group function, the Coast Guard cleanup day, the Meendum Manjappai campaign, a school awareness session, the two team photographs and the basketball court.
The batch also held two more school photographs and a second Manjappai one, which are left out because they repeat the tiles above.
They are used at their supplied size, between 1135px and 1600px wide, with only their metadata stripped.

Two event photos are AI-enhanced by `tools/enhance_images.py` instead, because they are shown large:

- The Campus Life page header, `event-teachers-day.jpg` (Teachers' Day, September 2026), came as a single photo rather than a collage. The 1600px WhatsApp image is upscaled to 2000px with `realesr-general-x4v3` at half strength and a light grade (source file `TeachersDay Sep 2026.jpeg`).
- `event-campus-to-corporate.jpg` fills the Academics "Beyond the classroom" image. The script cuts the 624px frame out of `CompusToCorporateTraining 2026.jpeg` and upscales it to 1600px at 60% strength. The slide text and the trainer's head keep the plain resample, because the AI invented letters on the slide.

Not used: the three admissions flyers (graphics, not photos), the event posters inside the collages, and a group photo with a burned-in camera timestamp.
Some collage frames are small (about 520–800px wide), and the vetiver-planting frame is a soft video still, so the original files would look sharper.

## Content notes: please review with the college

All names, facts, contact details, the mission statement, leadership bios and the principal's message are taken from the current site.
Things that were **removed** because they were template placeholders on the old site:

- Lorem-ipsum "Latest News" and "Upcoming Events" (e.g. "184 Main Collins Street").
- Fake statistics ("511697 Total Enrollment", "2113 Staffs").
- A testimonial for "Madha Dental College".
- A dental-clinic stock photo and a stock boardroom photo.
- The "Follow us" link, which pointed to the Madha **Dental** College Facebook page.

Things **written new** that the college should confirm:

- **Programme descriptions and durations.** These are short, generic summaries; durations follow the University of Madras norm of UG 3 years and PG 2 years.
- **Values cards** on the About page, expanded from the mission statement's own words.
- **Photo captions.** For example, the "Madha Group campus" photo appears to show a sister institution.
- **Event write-ups.** Dates, speakers, venues and partners come from the event posters. Some details were inferred from the photos and need checking:
  - the Biotechnology study tour (13 Feb 2026) was to a mushroom farm;
  - the Tamil Department's "museum" is the Government Museum;
  - the blue-T-shirt industrial visit was to an ITC factory;
  - "Assembly with flags" and "Students and faculty together" need the real occasion and venue.
- **Spelling.** "Anakaputhur" is used consistently; the old site mixed "Anagaputhur" and "Anankaputhur".

Broken links on the old site: the B.Sc Mathematics and B.Sc Hotel & Catering Management course pages return 404.
In the redesign those two cards link to the enquiry form instead of a department page.

## Before going live

- **Enquiry form:** a static site has no backend, so the form currently opens the visitor's email app with the enquiry pre-filled to info@madhaarts.in. Connect it to a form handler (the existing WordPress contact form, Formspree, Google Forms, etc.) for direct submissions.
- **Social links:** add the college's own social media links once confirmed.
- **Photos:** newer, higher-resolution originals from the college would enhance even better. Drop them in `assets/img/originals/` and re-run the script.
