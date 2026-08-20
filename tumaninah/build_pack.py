#!/usr/bin/env python3
"""Expand the Tumaninah scene list into a full prompt pack and a generation manifest.

Every scene shares one style prefix and one negative prompt; only the subject
sentence, the VO line and the timing differ. Storing it that way keeps the source
small and guarantees the 116 prompts stay identical in style.
"""
import json

STYLE = (
    "hand-painted watercolour and fine ink illustration on cold-press paper, visible paper "
    "tooth and grain, soft wet-edge blooms where washes meet, loose broken ink linework that "
    "does not trace every edge, areas of bare unpainted paper left as part of the composition, "
    "soft diffused directionless light, low contrast, no harsh shadows, shallow depth of field "
    "with backgrounds dissolving into loose wash, muted palette of indigo, burnt sienna, ochre "
    "and slate grey, traditional storybook illustration feel, 16:9. "
)

NEGATIVE = (
    "3d render, cgi, photorealistic, photograph, stock photo, digital airbrush, vector art, "
    "flat vector, cel shading, cartoon, anime, comic book, glossy, plastic, thick even outlines, "
    "clip art, text, lettering, calligraphy, arabic script, handwriting, inscriptions, numerals, "
    "watermark, signature, logo, brand marks, depiction of any prophet, depiction of Muhammad, "
    "depiction of Allah, halo, religious icon, idol, statue, crucifix, church, cross, nazar "
    "amulet, hamsa, talisman, occult symbol, zodiac, neon, lens flare, hdr, oversaturated, high "
    "contrast, harsh dramatic lighting, deep black shadows, volumetric god rays, cluttered "
    "composition, busy background, crowded frame, extra fingers, distorted hands, extra limbs, "
    "blurry, low resolution"
)

# Repeated subjects, named once so re-used scenes stay pixel-identical in wording.
CARTOUCHE = ("A wide empty rectangular illuminated cartouche on cream paper, framed by a fine "
             "indigo rule and a narrow band of ochre geometric interlace, the interior completely "
             "bare unmarked paper.")
CARTOUCHE_WIDE_OCHRE = ("A wide empty rectangular illuminated cartouche on cream paper, framed by "
                        "a fine indigo rule and a wide band of ochre geometric interlace, warm "
                        "ochre dominant, very wide cream margins, the interior completely bare "
                        "unmarked paper.")
BANNER_INDIGO = ("A long horizontal empty illuminated banner across cream paper — a blank ribbon "
                 "of deep indigo wash edged top and bottom with a fine ochre rule, small verdigris "
                 "palmette finials at each end, the interior completely bare.")
BANNER_SAFFRON = ("A long horizontal empty illuminated banner across cream paper — a blank ribbon "
                  "of full saffron ochre wash edged top and bottom with a fine indigo rule, small "
                  "verdigris palmette finials at each end, the interior completely bare.")
DOORWAY = ("A bare limestone doorway in a plain wall with warm light beyond it and an empty stone "
           "floor in front, a single pair of worn sandals set down neatly to one side; nobody in "
           "the frame.")
SUJUD = ("A close low study of a forehead and folded hands resting on a reed prayer mat in sujūd, "
         "seen from the side and cropped above the brow so no face is visible, the grey-blue hijab "
         "falling to the mat, everything completely still")
HAND_IN_GLASS = ("A plain glass of river water on a bare wooden table, a hand entering the water "
                 "from above, fingers spread, the silt billowing up violently around the intrusion "
                 "in dark indigo clouds")
CAVE_MOUTH = "The view from deep inside a cave looking out toward its mouth"
WINDOW_WOMAN = ("A woman in a soft grey-blue hijab and long charcoal coat standing at a window seen "
                "from behind, one hand flat against the glass")

CHAPTERS = [
    (1,  "THE DISTURBANCE",                        "0:00",  "1:53"),
    (2,  "ṬUMAʾNĪNAH",                             "1:53",  "3:18"),
    (3,  "WHAT WE ARE WALKING TOWARD",             "3:18",  "4:15"),
    (4,  "IT IS A REQUIREMENT BEFORE IT IS A FEELING", "4:15", "5:35"),
    (5,  "THE SENTENCE NOBODY QUOTES",             "5:35",  "8:37"),
    (6,  "THE ROOT ACROSS THE QURAN",              "8:37",  "11:10"),
    (7,  "WHO THIS IS ACTUALLY ABOUT",             "11:10", "12:24"),
    (8,  "IT IS SENT DOWN",                        "12:24", "13:30"),
    (9,  "DHIKR",                                  "13:30", "15:14"),
    (10, "THE NAME AT THE END",                    "15:14", "17:28"),
    (11, "SETTLED IS NOT NUMB",                    "17:28", "19:12"),
    (12, "THE SILT",                               "19:12", "20:47"),
    (13, "THE CAVE",                               "20:47", "23:05"),
    (14, "ON A TUESDAY",                           "23:05", "25:41"),
    (15, "CLOSE",                                  "25:41", "27:17"),
]

# (id, chapter, in, out, vo, subject)   in/out empty on a B-split: it shares the parent's slot.
S = [
 ("01",1,"0:00","0:16","The āyah people put on their wall lives inside a sūrah named after the loudest thing in the sky.",
  "A vast bank of storm cloud stacked over a dark plain at dusk, seen from far below, the underside of the cloud heavy and bruised indigo, a thin band of ochre light along the horizon beneath it; no people, no buildings."),
 ("02",1,"0:16","0:32","Ar-Raʿd. The Thunder.",
  "A single fork of lightning frozen against deep indigo cloud, painted as one confident ink stroke with a soft ochre bloom around it, most of the frame left as dark wash and bare paper."),
 ("03",1,"0:32","0:48","Lightning that makes you afraid and makes you hope at the same time.", CARTOUCHE),
 ("04",1,"0:48","1:04","Clouds dragged across the sky heavy with rain.",
  "Low rain-heavy cloud being pulled across a flat desert horizon, the rain falling as a slanted grey-indigo veil that does not reach the ground, dry cracked earth below waiting for it."),
 ("05",1,"1:04","1:20","Thunder itself — which the sūrah says is exalting Allah with praise while it does it.",
  CARTOUCHE.replace("interlace, the interior", "interlace, framed slightly wider with more cream paper visible at the edges, the interior")),
 ("06",1,"1:20","1:37","So that is the room. Weather, voltage, noise… air that has gone heavy and metallic.",
  WINDOW_WOMAN + ", watching a storm break over rooftops outside; the room around her dim indigo, the storm light ochre on her sleeve."),
 ("07",1,"1:37","1:53","…the line you have seen a hundred times. Usually in a soft font. Usually over a photograph of a sunrise.",
  "A framed print hanging on a tidy pale living-room wall, the print's surface entirely blank cream with a small generic sunrise photograph motif faintly visible behind it, everything slightly too neat and flatly lit."),

 ("08",2,"1:53","2:10","Start with the thing the English cannot carry.", BANNER_INDIGO),
 ("09",2,"2:10","2:27","Its root sense is not peace. It is not calm. It is to settle.",
  "Four smooth river stones laid in a row on wet sand, each one pressed slightly into the surface so the sand has closed around it, low raking light picking out the depressions."),
 ("10",2,"2:27","2:44","The classical lexicons use it for ground. Land that lies low and level.",
  "A wide shallow salt flat at dawn, absolutely level to the horizon, the surface so still it mirrors an ochre sky; a single line of low hills far in the distance; nothing else in the frame."),
 ("10B",2,"","","The classical lexicons use it for ground. Land that lies low and level.",
  "Low-angle close study of the dry, perfectly level salt-crust surface, fine crystalline ink cracks mapping the low horizontal ground line."),
 ("11",2,"2:44","3:01","A word about something that was disturbed coming to rest. Not something never disturbed.",
  "A plain glass of cloudy river water standing on a bare wooden table, the water opaque grey-brown with suspended silt, a spoon just lifted out and still dripping."),
 ("12",2,"3:01","3:18","The English tells you the heart feels better. The Arabic tells you the heart stops moving.",
  "A plain glass of cloudy river water standing on a bare wooden table, seen from the side at eye level, the silt visibly beginning to drift downward through the water in soft indigo threads, the upper third of the water just starting to clear."),

 ("13",3,"3:18","3:37","Everything in this study grows out of that one shift.",
  "An open hand-bound manuscript on a low wooden stand seen from above, both visible pages completely blank cream paper inside an empty illuminated border of indigo and ochre interlace, a ribbon marker laid across the gutter."),
 ("13B",3,"","","Everything in this study grows out of that one shift.",
  "Close-up on the intricate ochre and indigo interlace corner border of the blank manuscript page, showing delicate hand-painted watercolor bleed on cream paper."),
 ("14",3,"3:37","3:56","Who it is describing — because it is not describing everybody.",
  "A narrow stone path forking into two in dry scrubland, one branch running toward level open ground and ochre light, the other climbing into broken rocky shadow; no figures, no signpost."),
 ("15",3,"3:56","4:15","…not as something a heart does, but as a name Allah calls somebody by.",
  "A single sealed envelope of aged cream paper lying face down on a dark wooden surface in a shaft of ochre light, completely unmarked, nothing written on it."),

 ("16",4,"4:15","4:31","Ṭumaʾnīnah is a legal requirement inside your ṣalāh.",
  "A plain reed prayer mat laid alone on a stone floor in a bare room, soft daylight from one side, the weave of the reeds picked out in fine ink line, nobody present."),
 ("16B",4,"","","Ṭumaʾnīnah is a legal requirement inside your ṣalāh.",
  "Macro texture view of the woven reed pattern on the prayer mat, rendered with broken ink linework and soft sienna washes against cold stone grey flooring."),
 ("17",4,"4:31","4:47","A man prays, comes over, and gives salām. And the Prophet ﷺ tells him: go back and pray.", DOORWAY),
 ("18",4,"4:47","5:03","He does it again. Same answer. Three times over.",
  DOORWAY + " The light across the floor has shifted noticeably further along, indicating the passage of time."),
 ("19",4,"5:03","5:19","Bow — until you are settled. Then rise. Then prostrate.",
  BANNER_INDIGO.replace("deep indigo wash", "burnt sienna wash")),
 ("20",4,"5:19","5:35","It is the half-second where every joint stops moving before you go on.", SUJUD + "."),
 ("20B",4,"","","It is the half-second where every joint stops moving before you go on.",
  "Extreme close-up detail of folded knuckles and the soft fabric fold of the grey-blue hijab resting against the fiber of the reed mat during prostration."),

 ("21",5,"5:35","5:53","Sūrah Ar-Raʿd, āyah twenty-seven. The one immediately before.", CARTOUCHE),
 ("22",5,"5:53","6:11","Why has no sign been sent down to him from his Lord?",
  "A group of robed figures standing at a distance in a sunlit stone lane, all turned away from the viewer, rendered as soft indistinct washes with no facial detail, one arm raised mid-gesture; deliberately too far away to read anyone."),
 ("23",5,"6:11","6:29","Not a garden. Not a quiet morning. A man being told publicly that the absence of a miracle proves he is a fraud.",
  "An empty flat expanse of pale sky over a low horizon, entirely featureless, with a single small dark bird crossing it far off centre; almost the whole frame is bare paper."),
 ("24",5,"6:29","6:47","The answer is not a miracle. It is a description of who actually receives guidance.",
  "A single set of footprints in sand that walks away toward the horizon, stops, turns, and comes back toward the viewer — the returning track overlapping the outgoing one."),
 ("25",5,"6:47","7:06","And then — without starting a new sentence — āyah twenty-eight continues.",
  "An open hand-bound manuscript on a low wooden stand seen from above, framed closer so a single unbroken line of empty illuminated border of indigo and ochre interlace runs from one page onto the next without a break, completely blank cream paper."),
 ("25B",5,"","","And then — without starting a new sentence — āyah twenty-eight continues.",
  "Close crop focusing strictly on the manuscript gutter where the single unbroken illuminated border line crosses smoothly from left page to right page."),
 ("26",5,"7:06","7:24","The most-quoted half of this āyah is not a standalone promise.",
  "A length of cream paper torn cleanly across the middle with only the lower half present on a dark wooden table, the upper half missing entirely; the paper is completely blank."),
 ("27",5,"7:24","7:42","It is telling you what the person who turned back looks like from the outside.",
  "A still reflecting pool of dark water in a stone courtyard, its surface perfectly flat, reflecting an ochre sky and the edge of an arch; no figure casting the reflection is visible in frame."),
 ("28",5,"7:42","8:00","Not: hearts will feel nice. Hearts settle.",
  "A cross-section view of a riverbank showing water above and dense settled silt below, the boundary between them clean and level, drawn with a fine ink line and soft indigo and sienna washes."),
 ("29",5,"8:00","8:18","Then read one more line, because the passage does not stop there either.",
  "A wide empty rectangular illuminated cartouche on cream paper, framed by a fine indigo rule and a band of ochre geometric interlace, ochre band dominant, indigo rule fine, the warmest version, the interior completely bare unmarked paper."),
 ("30",5,"8:18","8:37","The settling is not the end of the sentence. It is the middle of a journey that finishes somewhere else.",
  "A broad tree in full leaf standing alone on level ground with its roots visibly spreading into the settled soil beneath it, painted in verdigris and ochre against a pale sky."),
 ("30B",5,"","","The settling is not the end of the sentence. It is the middle of a journey that finishes somewhere else.",
  "Macro detail of thick verdigris tree roots gripping tightly into layered ochre soil, fine ink linework tracking the grain, bare unpainted paper at the edges."),

 ("31",6,"8:37","8:54","The word does not only appear here. Follow it, and the picture sharpens fast.",
  "An open manuscript page, completely blank inside its empty illuminated border, with a thin ochre thread laid across it running from top to bottom and continuing off the edge of the page."),
 ("32",6,"8:54","9:11","Ibrāhīm ؑ asks Allah to show him how the dead are given life.",
  "Four birds in flight, well separated, circling above a bare hilltop against an enormous pale sky; the hilltop itself empty, nobody standing on it."),
 ("33",6,"9:11","9:28","Yes — but so that my heart may settle.", BANNER_INDIGO),
 ("34",6,"9:28","9:45","He is not rebuked for asking. He is shown.",
  "Four birds settling down onto a bare hilltop, wings half-folded, the hilltop empty of any figure; warm ochre light across the ridge, immense pale sky."),
 ("34B",6,"","","He is not rebuked for asking. He is shown.",
  "Macro focus on the semi-folded wings of one settling bird resting against the stark horizon line of the bare stone ridge."),
 ("35",6,"9:45","10:02","Badr. The angels sent to a badly outnumbered army.",
  "A wide dry valley at first light seen from a ridge, two unequal scatters of small dark shapes facing each other across the valley floor, far too distant to resolve as people; dust hanging low."),
 ("36",6,"10:02","10:19","Not to win the battle. The angels were for the settling.",
  "A single pair of open hands held loosely at rest in a lap, palms up, fingers uncurled, cropped so no face is in frame, sienna and cream, fine ink line on the knuckles."),
 ("37",6,"10:19","10:36","In the āyah about shortening prayer in danger, the return to normal is marked by this same root.",
  "A spear and a shield set down together against a limestone wall, leaning and unattended, a prayer mat unrolled on the ground beside them."),
 ("38",6,"10:36","10:53","Sūrah Yūnus, āyah seven. Those content with the life of this world, and who have settled into it.",
  "A wide empty rectangular illuminated cartouche on cream paper, framed by a fine indigo rule and a narrow band of flat slate grey geometric interlace, visibly cold, the interior completely bare unmarked paper."),
 ("39",6,"10:53","11:10","Ṭumaʾnīnah is morally neutral. The entire question is what it comes to rest on.",
  "Two identical smooth stones side by side — one settled firmly into level packed earth, the other settled just as deeply into soft wet mud that is visibly giving way beneath it."),
 ("39B",6,"","","Ṭumaʾnīnah is morally neutral. The entire question is what it comes to rest on.",
  "Extreme close-up on the sinking stone, deep slate and wet sienna washes where the heavy mud creeps up and swallows the lower contour, no harsh black lines."),

 ("40",7,"11:10","11:29","There is a real disagreement here and you should hear it rather than have it smoothed over.",
  "Two open manuscripts lying side by side on a wooden table, both pages completely blank inside their empty illuminated borders, the two borders drawn in slightly different patterns."),
 ("41",7,"11:29","11:47","Some read it as continuous with twenty-seven. Others read the famous half as standing on its own feet.",
  "A single length of rope lying on cream paper, unbroken along most of its run, with one section where the strands separate into two parallel paths and then come back together."),
 ("42",7,"11:47","12:06","Honestly, that argument is not settled among careful readers. And both readings land in the same place.",
  "Two separate footpaths crossing a field from different directions and meeting at a single stone threshold in a low wall."),
 ("43",7,"12:06","12:24","Take the second half away and you have deleted the mechanism and kept the mood.",
  "A simple mechanical balance or hinge of dark iron mounted on a stone wall with its central pin removed and lying beside it, the mechanism hanging slack and useless."),

 ("44",8,"12:24","12:41","There is a second word in this territory — sakīnah. Different root.",
  BANNER_INDIGO.replace("deep indigo wash", "verdigris wash")),
 ("45",8,"12:41","12:57","But look at the verb attached to it every time. Anzala. Sent down.", CARTOUCHE),
 ("46",8,"12:57","13:14","It is the same verb used for rain. The same verb used for revelation.",
  "Heavy rain falling straight down into a wide still lake at dusk, seen close at water level, each drop making a small ring on the surface, indigo and ochre, the far shore dissolved into wash."),
 ("47",8,"13:14","13:30","You are not asked to manufacture calm. You are asked to be somewhere it lands.",
  "A wide shallow clay bowl set out alone on flat open ground under an overcast sky, empty, waiting, with the first few drops of rain marking its dry inner surface."),
 ("47B",8,"","","You are not asked to manufacture calm. You are asked to be somewhere it lands.",
  "Close-up macro inside the empty clay bowl, focusing on the rough porous texture of the ceramic wall where the first few droplet rings settle."),

 ("48",9,"13:30","13:47","Dhikr. Dhāl, kāf, rāʾ.", BANNER_INDIGO),
 ("49",9,"13:47","14:04","The root covers mentioning as well as remembering. Saying a thing out loud.",
  "A close study of a mouth and jaw seen from the side and cropped at the nose so the face is not readable, lips parted mid-word, warm sienna against a soft indigo ground."),
 ("50",9,"14:04","14:22","So dhikr is not primarily an event inside your skull. It has a tongue in it.",
  "Concentric rings spreading outward across still dark water from a single point, seen from directly above, the rings drawn in fine ink and catching ochre light."),
 ("51",9,"14:22","14:39","The Qurʾān uses al-Dhikr as a name for itself.",
  "An open hand-bound manuscript on a low wooden stand, framed tighter on the empty illuminated border of a single page, completely blank cream paper."),
 ("52",9,"14:39","14:56","Hearts settle by the thing you can open and read.",
  "Two hands opening a hand-bound book on a low table, the visible pages completely blank cream inside an empty illuminated border, warm ochre light falling across them, cropped at the wrists."),
 ("53",9,"14:56","15:14","Whoever turns away from My dhikr — a constricted life. Maʿīshatan ḍankā.",
  "A very narrow stone passage between two high walls, so tight that the walls nearly touch, receding into cold indigo shadow with no light at the far end."),
 ("53B",9,"","","Whoever turns away from My dhikr — a constricted life. Maʿīshatan ḍankā.",
  "Detail of the rough stone texture on the two high walls closing in, wet-edge indigo shadows pooling in the cracks, completely devoid of any light at the narrow center gap."),

 ("54",10,"15:14","15:31","There is one more place this root appears, and it changes the tone of everything.",
  "A single unsealed envelope of aged cream paper turned face up on a dark wooden table in ochre light, completely unmarked, nothing written on it, a hand just withdrawing from it."),
 ("55",10,"15:31","15:48","Sūrah Al-Fajr. Near the very end of the Qurʾān.",
  "A bare horizon before sunrise, deep indigo sky with the faintest thread of ochre lying along the very bottom edge, a single date palm silhouetted far right."),
 ("55B",10,"","","Sūrah Al-Fajr. Near the very end of the Qurʾān.",
  "Detail shot focusing on the single silhouette of the date palm on the far right against the razor-thin ochre thread of dawn bleeding into deep indigo wash."),
 ("56",10,"15:48","16:05","Nations destroyed, wealth loved with a fierce love, the earth pounded flat, level upon level.",
  "A wide field of broken masonry and collapsed columns lying flattened across level ground, everything reduced to the same height, dust settling over it in the low light."),
 ("57",10,"16:05","16:22","And then a voice turns and addresses a single soul directly.", CARTOUCHE_WIDE_OCHRE),
 ("57B",10,"","","And then a voice turns and addresses a single soul directly.",
  "Macro focus on the expansive blank cream paper margins surrounding the warm ochre interlace cartouche, highlighting the paper grain."),
 ("58",10,"16:22","16:39","Al-muṭmaʾinnah. Same root. Ṭāʾ, mīm, hamza, nūn.", BANNER_SAFFRON),
 ("59",10,"16:39","16:56","In Ar-Raʿd, settling is something a heart does. In Al-Fajr, it is what Allah calls you.",
  "Two empty illuminated cartouches side by side on one sheet, the left one bordered in indigo and the right one in ochre, both interiors completely bare, a fine ink line drawn between them."),
 ("60",10,"16:56","17:12","He does not say become settled, then return. He says: settled soul — return.",
  "A single open doorway in a limestone wall with warm ochre light flooding through it onto level ground, and a clear path of that light running out toward the viewer; nobody standing in the doorway."),
 ("61",10,"17:12","17:28","Your heart can settle because He is what is underneath it.",
  "A wide shallow salt flat relit at full ochre dawn with the level surface stretching unbroken to the horizon, perfectly still, a single set of footprints standing still on it."),
 ("61B",10,"","","Your heart can settle because He is what is underneath it.",
  "Ultra-wide panoramic view of the vast salt flat at full ochre dawn, mirror-flat surface stretching indefinitely under an expansive pale sky, absolute level horizon."),

 ("62",11,"17:28","17:45","A settled heart is not a numb heart.",
  "A lit oil lamp burning steadily inside a glass chimney while wind visibly moves the grass around it, the flame upright and unwavering, everything else in motion."),
 ("63",11,"17:45","18:02","Yaʿqūb ؑ grieves for his son until his eyes go white from it.",
  "An empty wooden chair beside a shuttered window in a dim room, a folded garment laid across its arm, dust visible in a single blade of light; nobody present."),
 ("64",11,"18:02","18:20","I complain of my anguish and my grief only to Allah.", CARTOUCHE),
 ("65",11,"18:20","18:37","The Prophet ﷺ wept when his son Ibrāhīm died… the eye sheds tears and the heart grieves.",
  "A very small square of folded white cloth resting alone on a low wooden surface in soft window light, with one adult hand laid flat beside it, not touching it."),
 ("65B",11,"","","The Prophet ﷺ wept when his son Ibrāhīm died… the eye sheds tears and the heart grieves.",
  "Close-up on the texture of the folded white cloth square resting beside the flat adult hand on the grained wooden table under soft window light."),
 ("66",11,"18:37","18:54","Mūsā's mother — Allah bound her heart. Rabaṭnā ʿalā qalbihā. Tied it down.",
  "A small boat moored to a stone bollard by a single taut rope, the water beneath it visibly moving and choppy, the boat holding its position exactly."),
 ("67",11,"18:54","19:12","Settling is what lets you move on purpose instead of being moved.",
  "A person in a charcoal coat and grey-blue hijab walking steadily away from the viewer along a level path into a strong headwind, coat and scarf streaming back, stride unbroken."),

 ("68",12,"19:12","19:28","Take a glass of river water and stir it.",
  "A plain glass of river water on a bare wooden table, a spoon turning in it, the water fully opaque grey-brown, silt whirling in visible spirals."),
 ("69",12,"19:28","19:44","You cannot see through it — not because anything was added, but because everything in it is suspended.",
  "A plain glass of cloudy opaque grey-brown river water standing on a bare wooden table, seen straight through at eye level, with a lit window behind it that is completely obscured by the cloudy water, the shape of the window unreadable."),
 ("70",12,"19:44","20:00","Stir it faster — worse. Reach in to push the silt down — worse again.", HAND_IN_GLASS + "."),
 ("71",12,"20:00","20:16","There is exactly one thing that clears that glass. You set it down. And you leave it.",
  "A plain glass of cloudy river water alone on a wooden table, the silt beginning to drift downward in soft vertical threads, the top third of the water noticeably clearer than the bottom."),
 ("71B",12,"","","There is exactly one thing that clears that glass. You set it down. And you leave it.",
  "Macro shot of the glass wall where soft indigo threads of settling silt drag downward, creating vertical watercolor blooms that fade into pure clean water at the top."),
 ("72",12,"20:16","20:32","The silt does not leave. It is still in the glass.",
  "A plain glass of river water on a bare wooden table, with a dense dark band of settled silt lying flat on the bottom and completely clear water above it, the boundary between them sharp and level."),
 ("72B",12,"","","The silt does not leave. It is still in the glass.",
  "Close macro view focusing strictly on the sharp, level boundary line between the dense settled silt band at the bottom and the clean water above."),
 ("73",12,"20:32","20:47","The offer is that you can see through the water again.",
  "A plain glass of clear river water on a bare wooden table, with a dense dark band of settled silt lying flat on the bottom, seen straight through at eye level with a lit window behind it perfectly visible and sharp through the clear water."),

 ("74",13,"20:47","21:04","Two men in a cave on Mount Thawr.",
  "A dark rocky mountainside at night under a heavy indigo sky, a small black cave opening visible partway up the slope, no light coming from it, no figures anywhere."),
 ("75",13,"21:04","21:21","Pursuers at the entrance — close enough that looking down at their own feet would have given them away.",
  CAVE_MOUTH + ", the opening a ragged bright shape against blackness, with the shadows of standing figures falling across the ground just outside it — the figures themselves out of frame."),
 ("76",13,"21:21","21:39","No weapon, no exit, no plan that anyone can see.",
  CAVE_MOUTH + ", the rough rock walls close on both sides, a spider's web strung across part of the opening catching the light, nothing else in the space."),
 ("77",13,"21:39","21:56","Lā taḥzan — inna Allāha maʿanā. Do not grieve. Allah is with us.", CARTOUCHE),
 ("78",13,"21:56","22:13","So Allah sent down His sakīnah upon him.",
  CAVE_MOUTH + ", filled with a soft warm ochre light that has no visible source and does not come from the cold pale opening, the opening a ragged bright shape against blackness."),
 ("78B",13,"","","So Allah sent down His sakīnah upon him.",
  "Detail of the rough cave wall surface catching the source-less warm ochre wash, contrasting with the dark recess corners."),
 ("79",13,"22:13","22:30","Sent down. In a cave. While the pursuers were still standing outside it.",
  CAVE_MOUTH + ", the interior filled with soft warm ochre light, the opening a ragged shape, shadows of standing figures falling across the ground just outside it exactly as before."),
 ("80",13,"22:30","22:48","You only say do not grieve to somebody who is already grieving.",
  "Two sets of footprints in cave dust, close together, both stopped and facing the opening, nobody standing in them."),
 ("81",13,"22:48","23:05","What arrived was not a correction. It was a floor.",
  "A broad flat slab of level bedrock filling the lower half of the frame inside a cave, warm ochre light lying across it, an unbroken horizontal line where it meets the wall behind."),
 ("81B",13,"","","What arrived was not a correction. It was a floor.",
  "Wider view of the inner cave sanctuary showing the complete horizontal shelf of bedrock extending across the stone wall, bathed in warm unbroken ochre light against deep slate shadows."),

 ("82",14,"23:05","23:22","So what does this actually look like on an ordinary bad day.",
  "An ordinary kitchen table at night with a cold cup of tea, a phone face down, and a chair pushed back; a single lamp lit, the rest of the room in indigo shadow."),
 ("83",14,"23:22","23:40","It does not mean you can produce calm on demand by wanting it badly enough.",
  "Two hands pressed hard against each other in a lap, knuckles pale with the effort, sleeves pulled down over the wrists, cropped well below the face."),
 ("84",14,"23:40","23:57","Dhikr has a tongue in it. When your chest is tight at two in the morning — say something.",
  "A dark bedroom seen from low beside the bed, a figure sitting on its edge in silhouette against a window with a streetlight beyond, head bowed, face not visible."),
 ("85",14,"23:57","24:14","Thinking harder about the thing that is stirring you is more stirring. It is reaching into the glass.",
  HAND_IN_GLASS.replace("A plain glass of river water on a bare wooden table, a hand", "A plain glass of river water, a hand") + ", cropped tight on the fingers."),
 ("86",14,"24:14","24:32","You already have the training built into your day, five times, and most of us rush past it.",
  "A plain reed prayer mat laid alone on a stone floor, lit with warm late-afternoon light from a low angle, nobody present."),
 ("87",14,"24:32","24:49","The one moment in twenty-four hours where you are required to stop moving.",
  SUJUD + ", framed slightly wider."),
 ("87B",14,"","","The one moment in twenty-four hours where you are required to stop moving.",
  "Slightly wider framing of the sujūd pose, capturing the soft fall of the grey-blue hijab fabric against the reed mat in complete stillness."),
 ("88",14,"24:49","25:06","The man in the ḥadīth was not told to feel more. He was told to stop rushing.",
  "A wide shallow clay bowl set out alone on flat open ground, holding a shallow pool of still rainwater with a clear reflection of ochre sky in it."),
 ("89",14,"25:06","25:24","Do not hand somebody āyah twenty-eight as a stop sign.",
  "A phone lying face up on a dark wooden surface, its screen a blank rectangle of pale ochre light with nothing on it at all, the glow spilling onto the wood."),
 ("90",14,"25:24","25:41","Sit with them. Say less than you want to say.",
  "Two people sitting side by side on a low stone step seen entirely from behind, one in a grey-blue hijab and charcoal coat, shoulders close but not touching, one open hand resting palm-up on the step between them."),

 ("91",15,"25:41","26:00","So keep the line where you can see it. Just let it be the size it actually is.",
  "A vast bank of storm cloud stacked over a dark plain, seen from far below, the underside of the cloud heavy and bruised indigo, a wide warm band of ochre light along the horizon beneath it, the cloud higher and thinner; no people, no buildings."),
 ("92",15,"26:00","26:19","It is a description of how a heart is built — spoken inside a sūrah named after thunder.", CARTOUCHE_WIDE_OCHRE),
 ("93",15,"26:19","26:39","The heavy thing does not have to leave the glass for you to see through the water.",
  WINDOW_WOMAN + "; the storm outside has passed to the far distance and the light on her sleeve is warm ochre; on the sill beside her, a clear glass of water with a dark settled band of silt at the bottom."),
 ("93B",15,"","","The heavy thing does not have to leave the glass for you to see through the water.",
  "Close-up on the window sill showing the clear glass of water with its dark settled silt band, next to the sleeve of the charcoal coat in warm ochre light."),
 ("94",15,"26:39","26:58","Yā ayyatuhā an-nafs al-muṭmaʾinnah. O settled soul.", BANNER_SAFFRON),
 ("95",15,"26:58","27:17","…May Allah make yours one of the settled ones.",
  "A bare horizon at sunrise, deep indigo sky above, a full ochre band fully risen along the level line, a single date palm silhouetted far right, the ground beneath completely flat and still."),
 ("95B",15,"","","…May Allah make yours one of the settled ones.",
  "Final wide closing frame of the flat, completely still ground beneath the fully risen ochre band at sunrise, fading smoothly into bare paper grain."),
]

chapter_name = {n: t for n, t, _, _ in CHAPTERS}


def slug(text):
    keep = "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower())
    return "-".join(keep.split()[:5])


def build():
    reqs, lines = [], []
    lines.append("=" * 80)
    lines.append("ṬUMAʾNĪNAH — AR-RAʿD 28 — IMAGE PROMPT PACK")
    lines.append("16:9 · %d images · 15 chapters · 27:17" % len(S))
    lines.append("Generated by tumaninah/build_pack.py — edit the script, not this file.")
    lines.append("=" * 80)

    seen_chapter = None
    for i, (sid, ch, tin, tout, vo, subject) in enumerate(S, start=1):
        if ch != seen_chapter:
            n, title, cin, cout = CHAPTERS[ch - 1]
            lines += ["", "=" * 80,
                      "CHAPTER %d · %s · %s–%s" % (n, title, cin, cout), "=" * 80]
            seen_chapter = ch

        is_split = sid.endswith("B")
        slot = "split of scene %s" % sid[:-1] if is_split else "%s–%s" % (tin, tout)
        fname = "%03d_scene-%s_%s.png" % (i, sid.lower(), slug(subject))

        lines += ["",
                  "--- SCENE %s · %s ---" % (sid, slot),
                  'VO: "%s"%s' % (vo, "  (continuation split)" if is_split else ""),
                  "PROMPT: " + STYLE + subject,
                  "NEGATIVE PROMPT: " + NEGATIVE]

        reqs.append({
            "index": i,
            "scene": sid,
            "chapter": ch,
            "chapter_title": chapter_name[ch],
            "file": fname,
            "in": tin or None,
            "out": tout or None,
            "split_of": sid[:-1] if is_split else None,
            "vo": vo,
            "params": {
                "model": "z_image",
                "aspect_ratio": "16:9",
                "prompt": STYLE + subject,
            },
            "negative_prompt": NEGATIVE,
        })

    manifest = {
        "title": "Ṭumaʾnīnah — Ar-Raʿd 28",
        "canvas": "16:9",
        "runtime": "27:17",
        "runtime_seconds": 1637,
        "scene_count": len([s for s in S if not s[0].endswith("B")]),
        "image_count": len(S),
        "generation": {
            "provider": "Higgsfield",
            "tool": "generate_image_batch",
            "model": "z_image",
            "credits_per_image": 0.15,
            "credits_total": round(0.15 * len(S), 2),
            "batch_note": "generate_image_batch takes 12 per call — %d calls." % -(-len(S) // 12),
            "negative_prompt_note": (
                "z_image exposes no negative-prompt field. Either fold NEGATIVE into the prompt "
                "or move to a model that takes one; the pack's negative prompt is carried here "
                "verbatim so nothing is lost either way."),
        },
        "order": [r["file"] for r in reqs],
        "requests": reqs,
    }

    with open("tumaninah/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open("tumaninah/tumaninah-prompt-pack.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    return manifest


if __name__ == "__main__":
    m = build()
    print("images:", m["image_count"], "| scenes:", m["scene_count"],
          "| credits on z_image:", m["generation"]["credits_total"])
    print("first:", m["order"][0])
    print("last :", m["order"][-1])
