# Track 23 digit color battery — auto-generated findings

Config `a87f8ab6cb65…`.

Reference palette M tops (stage 1, digit-relative): 0: black, white, gray; 1: white, red, black; 2: yellow, green, white; 3: blue, red, pink; 4: yellow, brown, gray; 5: pink, purple, blue; 6: purple, yellow, orange; 7: purple, pink, orange; 8: orange, black, brown; 9: purple, blue, green

## instruct / sample

- parse: name 0.948 (palette 0.842), hex 0.985
- digit specificity (name): {"V": 0.29979449915875667, "null_mean": 0.14115658253457833, "null_95": 0.15740747791616794, "p": 9.999000099990002e-05}
- digit specificity (hex → nearest name): {"V": 0.20656132625512444, "null_mean": 0.1287431358410899, "null_95": 0.14454091295701763, "p": 0.0004997501249375312}
- consistency LUV: mean 357.7, median participant 354.8, null 365.8, p 0.1039, below 135.30: 0.00
- consistency RGB: mean 3.585, median participant 3.536, null 3.581, p 0.5219, below 1.43: 0.00
- palette match r(B, M): slot {"r": 0.735809988931195, "null_95": 0.33407540798778496, "p": 9.999000099990002e-05}; name counts {"r": 0.6300530186760841, "null_95": 0.2940048695788113, "p": 9.999000099990002e-05}; hex nearest {"r": 0.2857154295265648, "null_95": 0.19264580129489292, "p": 0.0033996600339966003}
- hits: {'0_achromatic': True, '1_white': True, '4_yellow': True, '7_purple': True}
- slot-profile tops: 0: black, white, gray; 1: white, blue, red; 2: yellow, green, pink; 3: blue, green, pink; 4: yellow, brown, orange; 5: gray, pink, purple; 6: orange, purple, brown; 7: purple, red, pink; 8: black, brown, white; 9: purple, blue, black
- modal names: 0: [['black', 18], ['yellow', 10], ['white', 8]]; 1: [['blue', 26], ['white', 11], ['red', 9]]; 2: [['yellow', 16], ['green', 15], ['red', 6]]; 3: [['green', 16], ['red', 11], ['blue', 9]]; 4: [['yellow', 14], ['orange', 12], ['green', 8]]; 5: [['other', 12], ['orange', 7], ['green', 6]]; 6: [['orange', 12], ['purple', 10], ['yellow', 9]]; 7: [['other', 11], ['yellow', 9], ['purple', 9]]; 8: [['black', 13], ['brown', 9], ['orange', 8]]; 9: [['purple', 18], ['red', 11], ['other', 10]]
- modal hex→name: 0: [['red', 13], ['black', 10], ['orange', 9]]; 1: [['red', 16], ['yellow', 11], ['blue', 7]]; 2: [['yellow', 13], ['orange', 13], ['green', 11]]; 3: [['green', 14], ['pink', 8], ['yellow', 6]]; 4: [['orange', 17], ['yellow', 11], ['red', 9]]; 5: [['red', 17], ['pink', 12], ['orange', 7]]; 6: [['red', 12], ['orange', 12], ['yellow', 11]]; 7: [['red', 16], ['pink', 7], ['blue', 6]]; 8: [['orange', 20], ['red', 11], ['yellow', 7]]; 9: [['yellow', 15], ['red', 11], ['purple', 6]]
- hex mean color: {'0': '#b8854c', '1': '#df8171', '2': '#c2af5d', '3': '#b68c78', '4': '#d29956', '5': '#e5786b', '6': '#de816c', '7': '#d98070', '8': '#d18b3f', '9': '#c68878'}
- position V 0.166; previous-answer V 0.219; same as previous 0.05263157894736842; distinct per run {'median': 8.0, 'share_ge7': 0.85}
- off-palette words: [['violet', 12], ['magenta', 10], ['teal', 6], ['gold', 6], ['cyan', 4], ['crimson', 4], ['indigo', 2], ['amber', 2], ['silver', 2], ['maroon', 2], ['**charcoal**', 1], ['**violet', 1], ['**burgundy', 1], ['**coral', 1], ['**golden', 1]]

Examples:

    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → [' Red  ', ' Violet', ' Green', ' Magenta', ' Black', ' Blue', ' Orange', ' Yellow', ' Cyan', ' Teal']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → [' Red  ', ' Blue', ' Teal', ' Green', ' Yellow', ' Purple', ' Orange', ' Yellow (wait actually 7 is often', " Gold/Red? Let's think classic", ' Pink? Hmm.']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → [' Red  ', ' Yellow', " Green (or Blue? Let's decide", ' Blue', ' Black or Brown? Often associated with "', ' Purple', ' White or Gold?', ' Orange? or Blue?', ' Cyan/Green?', '-red']
    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → ['FFDAB9  ', 'B22222', 'FFFF00', 'FF0000', '8B0000', '1E90FF', '000000', 'FF1493', 'FF8C00', 'FF6347']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → ['FF33AA  ', 'F88333', '00FF99', 'FFFF00', '000000', '6F0000', '990000', 'FF0000', '00FF00', '0000FF']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → ['FFD700 (Gold)', 'FF874C (Vermillion)', 'E60000 (Bright Red', '000000000000? Wait, that', '00FF00 (Green? No,', "00FF00 maybe? Let's pick", 'FF0000 (Red)', '00CED1 (Dark Blue?', 'FF69B4 (Hot Pink', 'FF4500 (Orange-Red']

## instruct / greedy

- parse: name 0.972 (palette 0.890), hex 1.000
- digit specificity (name): {"V": 0.3338985945274487, "null_mean": 0.14124330391738976, "null_95": 0.15873693965885086, "p": 0.0004997501249375312}
- digit specificity (hex → nearest name): {"V": 0.3844142926084401, "null_mean": 0.1225785109302357, "null_95": 0.13703895786313436, "p": 0.0004997501249375312}
- consistency LUV: mean 285.4, median participant 293.7, null 337.3, p 0.0005, below 135.30: 0.05
- consistency RGB: mean 2.512, median participant 2.660, null 2.952, p 0.0005, below 1.43: 0.05
- palette match r(B, M): slot {"r": 0.6006358098801754, "null_95": 0.28110532467801497, "p": 9.999000099990002e-05}; name counts {"r": 0.6814412613377382, "null_95": 0.33051024112547683, "p": 9.999000099990002e-05}; hex nearest {"r": 0.44535235474985263, "null_95": 0.25605509544089, "p": 0.00019998000199980003}
- hits: {'0_achromatic': True, '1_white': True, '4_yellow': True, '7_purple': True}
- slot-profile tops: 0: white, black, gray; 1: white, yellow, blue; 2: yellow, white, orange; 3: green, blue, red; 4: brown, yellow, orange; 5: gray, purple, pink; 6: brown, gray, orange; 7: purple, pink, red; 8: black, brown, white; 9: purple, red, blue
- modal names: 0: [['black', 27], ['white', 15], ['yellow', 12]]; 1: [['blue', 17], ['white', 15], ['red', 9]]; 2: [['yellow', 20], ['orange', 9], ['green', 8]]; 3: [['red', 15], ['green', 13], ['blue', 10]]; 4: [['yellow', 15], ['orange', 12], ['red', 11]]; 5: [['purple', 10], ['blue', 10], ['green', 9]]; 6: [['orange', 11], ['brown', 11], ['green', 9]]; 7: [['purple', 18], ['other', 8], ['orange', 7]]; 8: [['black', 16], ['brown', 12], ['other', 7]]; 9: [['purple', 22], ['blue', 11], ['red', 8]]
- modal hex→name: 0: [['white', 20], ['black', 14], ['orange', 12]]; 1: [['red', 39], ['purple', 9], ['yellow', 7]]; 2: [['orange', 23], ['yellow', 17], ['green', 14]]; 3: [['pink', 24], ['yellow', 14], ['red', 12]]; 4: [['orange', 23], ['red', 17], ['yellow', 11]]; 5: [['pink', 28], ['yellow', 11], ['purple', 9]]; 6: [['orange', 27], ['yellow', 14], ['red', 12]]; 7: [['red', 35], ['yellow', 8], ['purple', 7]]; 8: [['red', 34], ['orange', 21], ['yellow', 5]]; 9: [['yellow', 21], ['red', 16], ['purple', 8]]
- hex mean color: {'0': '#c49461', '1': '#ff414c', '2': '#dfbf2b', '3': '#f8697e', '4': '#ea980b', '5': '#ff768f', '6': '#fe8a30', '7': '#f74f4b', '8': '#cd5801', '9': '#e38458'}
- position V 0.319; previous-answer V 0.276; same as previous 0.036608863198458574; distinct per run {'median': 8.0, 'share_ge7': 0.95}
- off-palette words: [['**teal', 12], ['**gold', 9], ['**indigo', 9], ['**magenta', 5], ['indigo', 4], ['**cyan', 2], ['teal', 2], ['**violet**', 2], ['**silver', 1], ['violet', 1], ['cyan', 1], ['magenta', 1]]

Examples:

    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → [' Red  ', ' Orange', ' Yellow', ' Green', ' Black', ' Blue', ' Purple', ' White', ' Blue (or Red? but typical association', ' Yellow? Wait, need to pick one']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → [' Red  ', ' Blue', ' Green', ' Orange', ' Yellow', ' Purple', ' Pink', " Purple (or Blue? Let's pick", ' Brown', ' Green']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → [' **Red**  ', ' **Yellow**', ' **Green**', ' **Blue', ' **Black', ' **Purple', ' **White', ' **Orange', ' **Pink', ' **Brown']
    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → ['FF33A1  ', 'FFD700', '00FF00', 'FF00FF', '8B0000', 'FF0000', '0000FF', '000000', 'FF0000 (or #FF000', 'FF4500']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → ['FF33A1  ', 'FFD700', 'FF4500', 'FF8C00', 'FFFFFF', 'FF69B4', '00FF00', 'FF0000', '8B0000', 'FF8C00']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → ['FFD700 (Gold)', 'FF8C00 (Dark Orange', 'FF4500 (Orange Red)', 'FFD700 (Gold) — wait', 'FFA500 (Orange)', 'FF0000 (Red', 'FF00FF (Magenta)', 'FF0000 (Red) — hmm', 'FF69B4 (Hot Pink', 'FF8C00 (Dark Orange)']

## base / sample

- parse: name 0.823 (palette 0.637), hex 0.922
- digit specificity (name): {"V": 0.14935477775329378, "null_mean": 0.14603024466842726, "null_95": 0.16325324829480542, "p": 0.35996400359964004}
- digit specificity (hex → nearest name): {"V": 0.12978226822470942, "null_mean": 0.1298036459167655, "null_95": 0.14533599451443183, "p": 0.5002498750624688}
- consistency LUV: mean 305.4, median participant 303.9, null 306.2, p 0.4404, below 135.30: 0.00
- consistency RGB: mean 3.570, median participant 3.531, null 3.596, p 0.3128, below 1.43: 0.00
- palette match r(B, M): slot {"r": 0.7709904574247743, "null_95": 0.4597260939609723, "p": 9.999000099990002e-05}; name counts {"r": 0.27603453247073895, "null_95": 0.2461789440660235, "p": 0.0292970702929707}; hex nearest {"r": 0.038410758246878215, "null_95": 0.1648301509264957, "p": 0.3478652134786521}
- hits: {'0_achromatic': True, '1_white': True, '4_yellow': False, '7_purple': True}
- slot-profile tops: 0: black, gray, white; 1: white, pink, red; 2: green, white, black; 3: pink, blue, red; 4: brown, orange, yellow; 5: pink, purple, yellow; 6: orange, purple, yellow; 7: purple, red, yellow; 8: orange, brown, black; 9: blue, purple, black
- modal names: 0: [['other', 9], ['blue', 7], ['black', 6]]; 1: [['blue', 9], ['other', 7], ['orange', 5]]; 2: [['other', 11], ['green', 9], ['blue', 7]]; 3: [['blue', 14], ['red', 8], ['other', 7]]; 4: [['other', 14], ['yellow', 9], ['blue', 8]]; 5: [['other', 11], ['blue', 10], ['green', 9]]; 6: [['other', 11], ['blue', 8], ['green', 6]]; 7: [['other', 16], ['red', 7], ['blue', 7]]; 8: [['other', 13], ['red', 8], ['blue', 6]]; 9: [['other', 13], ['blue', 9], ['red', 6]]
- modal hex→name: 0: [['black', 14], ['gray', 9], ['purple', 6]]; 1: [['black', 8], ['white', 8], ['yellow', 7]]; 2: [['black', 12], ['gray', 12], ['green', 5]]; 3: [['gray', 9], ['black', 7], ['blue', 7]]; 4: [['gray', 11], ['yellow', 7], ['black', 6]]; 5: [['blue', 9], ['white', 8], ['gray', 7]]; 6: [['white', 9], ['gray', 9], ['purple', 9]]; 7: [['gray', 9], ['green', 9], ['purple', 7]]; 8: [['gray', 11], ['purple', 11], ['green', 7]]; 9: [['gray', 15], ['white', 7], ['black', 6]]
- hex mean color: {'0': '#786569', '1': '#948976', '2': '#795f69', '3': '#907f83', '4': '#9a7d74', '5': '#9d7790', '6': '#957a7f', '7': '#9d8a91', '8': '#a37582', '9': '#9f8386'}
- position V 0.172; previous-answer V 0.238; same as previous 0.22705314009661837; distinct per run {'median': 5.0, 'share_ge7': 0.31666666666666665}
- off-palette words: [['cyan', 6], ['magenta', 5], ['violet', 5], ['aqua', 4], ['lavender', 3], ['gold', 3], ['copper', 2], ['mauve', 2], ['turquoise', 2], ['aquamarine', 2], ['fuchsia', 2], ['lime', 2], ['maroon', 2], ['vermilion', 1], ['coral', 1]]

Examples:

    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → [' navy blue', ' vermilion', ' indanthraquinone yellow', ' borax light blue', ' coral', ' copper', ' magenta', ' the color of excellent ruby garnet', ' very violet bluish', ' light salmon pink']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → [' me: red-chert, orange-p', ' aproph, amorphous orange', ' me: white silken thread, red', ' bistero black, corn-chert', ' sulphuric ores, primrose', ' squint', ' vesuvian, citrontwilight', ' earth [5 zenith, 5', ' beetroot', ' blue']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → [' orange', ' rose', ' lavender', ' deep purple', ' lavender', ' mustard', ' yellow', ' mauve', ' mint green', ' lavender']
    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → ['00000000', '00000006', '00000002', '00000005', '00000008', '00000007', '00000009', '00000000', '00000001', '00000004']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → ['00FF9F (Hex)', 'FF57FF (Hex', 'FF58FF (Hex)', '16FFFF (Hex', 'FFF9FF (Hex', 'FF5FFF (Hex', 'F8E575 (Hex', 'F5FFF7 (Hex', 'F8FFF8 (Hex', 'E4FFFF (Hex']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → ['0c78b2', 'c6e21c', '515649', '0077bb', 'ffffff', '348df5', '2087a1', '464733', 'e38a9a', '003399']

## base / greedy

- parse: name 1.000 (palette 1.000), hex 0.980
- digit specificity (name): {"V": 0.2215973700041378, "null_mean": 0.13522075132221179, "null_95": 0.1521319702461338, "p": 0.0004997501249375312}
- digit specificity (hex → nearest name): {"V": 0.15334664001108098, "null_mean": 0.10322903955229729, "null_95": 0.11447034629772594, "p": 0.0004997501249375312}
- consistency LUV: mean 392.9, median participant 408.2, null 403.4, p 0.0125, below 135.30: 0.00
- consistency RGB: mean 3.853, median participant 3.849, null 4.002, p 0.0015, below 1.43: 0.00
- palette match r(B, M): slot {"r": 0.49436194576839404, "null_95": 0.33240444915403594, "p": 0.00039996000399960006}; name counts {"r": 0.36842427172484665, "null_95": 0.24105719070409218, "p": 0.0025997400259974}; hex nearest {"r": 0.13923955248827613, "null_95": 0.14004933527483, "p": 0.051794820517948204}
- hits: {'0_achromatic': True, '1_white': True, '4_yellow': False, '7_purple': False}
- slot-profile tops: 0: black, white, gray; 1: white, yellow, green; 2: brown, gray, white; 3: red, pink, green; 4: orange, brown, green; 5: purple, blue, orange; 6: orange, brown, blue; 7: orange, green, pink; 8: brown, purple, gray; 9: blue, purple, pink
- modal names: 0: [['black', 29], ['white', 7], ['yellow', 7]]; 1: [['yellow', 14], ['white', 12], ['red', 7]]; 2: [['yellow', 11], ['purple', 9], ['brown', 7]]; 3: [['red', 15], ['pink', 11], ['green', 6]]; 4: [['red', 8], ['yellow', 7], ['green', 7]]; 5: [['blue', 12], ['green', 10], ['orange', 7]]; 6: [['orange', 10], ['blue', 9], ['pink', 7]]; 7: [['orange', 11], ['green', 10], ['pink', 9]]; 8: [['purple', 8], ['red', 7], ['green', 7]]; 9: [['blue', 14], ['pink', 11], ['purple', 8]]
- modal hex→name: 0: [['black', 30], ['purple', 12], ['red', 5]]; 1: [['black', 24], ['purple', 14], ['red', 6]]; 2: [['black', 17], ['green', 14], ['purple', 12]]; 3: [['black', 17], ['blue', 11], ['green', 11]]; 4: [['purple', 16], ['black', 11], ['green', 10]]; 5: [['purple', 13], ['black', 13], ['blue', 11]]; 6: [['purple', 16], ['black', 12], ['blue', 8]]; 7: [['purple', 18], ['red', 11], ['black', 11]]; 8: [['purple', 21], ['black', 12], ['red', 8]]; 9: [['purple', 20], ['black', 11], ['gray', 9]]
- hex mean color: {'0': '#693352', '1': '#854665', '2': '#8e6a6d', '3': '#875f77', '4': '#ac7676', '5': '#935e8b', '6': '#a45783', '7': '#bb6278', '8': '#b65588', '9': '#b75292'}
- position V 0.675; previous-answer V 0.632; same as previous 0.0; distinct per run {'median': 10.0, 'share_ge7': 1.0}
- off-palette words: []

Examples:

    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → [' blue', ' red', ' green', ' yellow', ' purple', ' orange', ' pink', ' black', ' white', ' gray']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → [' blue', ' red', ' green', ' yellow', ' purple', ' orange', ' pink', ' black', ' white', ' gray']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → [' blue', ' yellow', ' red', ' green', ' purple', ' orange', ' pink', ' brown', ' black', ' white']
    ['3', '6', '2', '5', '8', '7', '9', '0', '1', '4'] → ['3F00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF', 'FF00FF']
    ['3', '1', '9', '2', '0', '5', '4', '7', '8', '6'] → ['3F00FF', '00FF00', '00FF00', '00FF00', '00FF00', '00FF00', '00FF00', '00FF00', '00FF00', '00FF00']
    ['9', '4', '8', '3', '0', '7', '1', '6', '5', '2'] → ['9F0B', 'F0B0', 'F0B0', 'F0B0', 'F0B0', 'F0B0', 'F0B0', 'F0B0', 'F0B0', 'F0B0']

Base vs instruct slot profiles: {"r": 0.706868349510564, "null_95": 0.3799218517018707, "p": 9.999000099990002e-05}

## Predictions

- 1_pipeline: {"instruct_name": 0.9483333333333334, "instruct_hex": 0.985, "base_name": 0.8233333333333334, "base_hex": 0.9216666666666666, "preflight": true, "right": false}
- 2_digit_specificity: {"V": 0.29979449915875667, "null_mean": 0.14115658253457833, "null_95": 0.15740747791616794, "p": 9.999000099990002e-05, "right": true}
- 3_consistency: {"sample_mean": 357.7066367549063, "sample_null_mean": 365.78524181602967, "p": 0.10388961103889612, "sample_median_participant": 354.8248393009438, "greedy_mean": 285.4261463990743, "greedy_median_participant": 293.71583560710104, "right": false}
- 4_palette_match: {"r": 0.735809988931195, "null_95": 0.33407540798778496, "p": 9.999000099990002e-05, "hits": 4, "right": true}
- 5_spread: {"median": 8.0, "share_ge7": 0.85, "right": true}
- 6_base_vs_instruct: {"r": 0.706868349510564, "null_95": 0.3799218517018707, "p": 9.999000099990002e-05, "right": true}
