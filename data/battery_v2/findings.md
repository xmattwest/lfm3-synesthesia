# Track 23 digit color battery v2 — auto-generated findings

Config `6b0c4ccb648a…`, 1000 runs, instruct, name format, sampled (T = 1).

- preflight: {"config_hash": "6b0c4ccb648a02de82a5599f5b5dacf48ffb44f0df9a1451ad232ef1cbb946ec", "max_pad_vs_single": 3.719329833984375e-05, "max_repeat_diff": 0.0, "greedy_batched_equals_single": true, "n_orders_checked": 8, "n_orders_identical": 8, "max_slot_logprob_batched_vs_single": 4.482269287109375e-05, "passed": true}
- parse rate 0.9536; palette share 0.8584
- digit specificity: {"V": 0.26126657461721814, "null_mean": 0.034626976565642675, "null_95": 0.03866476804039044, "p": 9.999000099990002e-05}
- r(B, M): {"r": 0.7500076825510972, "null_95": 0.3152876540106467, "p": 9.999000099990002e-05}
- r(B, B_v1): {"r": 0.9673973204656284, "null_95": 0.3657177209127908, "p": 9.999000099990002e-05}
- hits: {'0_achromatic': True, '1_white': True, '4_yellow': True, '7_purple': True}
- numeral fills v2: 0 black, 1 white, 2 yellow, 3 blue, 4 yellow, 5 gray, 6 brown, 7 purple, 8 black, 9 purple
- numeral fills v1: 0 black, 1 white, 2 yellow, 3 blue, 4 yellow, 5 gray, 6 orange, 7 purple, 8 black, 9 purple
- median distinct colors per run: 8.0
- off-palette words: [['violet', 143], ['magenta', 135], ['teal', 81], ['indigo', 65], ['cyan', 63], ['gold', 47], ['maroon', 47], ['crimson', 34], ['silver', 17], ['coral', 14], ['**violet', 13], ['**gold**', 11], ['lavender', 11], ['**teal', 11], ['**cyan', 10], ['turquoise', 10], ['aqua', 10], ['azure', 9], ['**indigo', 8], ['**magenta', 8]]

## Per digit (sampled share [95% Wilson]; exact palette share [95% context bootstrap])

- 0: digit-relative tops ['black', 'gray', 'white'] | sampled: black 0.249 [0.223, 0.277]; brown 0.153 [0.132, 0.177]; white 0.152 [0.131, 0.176]; yellow 0.139 [0.119, 0.162]; gray 0.083 [0.067, 0.102] | exact (tops): black 0.202 [0.191, 0.213]; gray 0.070 [0.065, 0.077]; white 0.142 [0.133, 0.152]
- 1: digit-relative tops ['white', 'blue', 'red'] | sampled: white 0.249 [0.223, 0.277]; blue 0.243 [0.217, 0.271]; red 0.160 [0.139, 0.184]; yellow 0.099 [0.082, 0.119]; other 0.054 [0.042, 0.070] | exact (tops): white 0.230 [0.215, 0.245]; blue 0.232 [0.218, 0.247]; red 0.202 [0.186, 0.219]
- 2: digit-relative tops ['yellow', 'green', 'orange'] | sampled: yellow 0.257 [0.231, 0.285]; green 0.223 [0.198, 0.250]; red 0.126 [0.107, 0.148]; orange 0.112 [0.094, 0.133]; blue 0.065 [0.051, 0.082] | exact (tops): yellow 0.248 [0.233, 0.264]; green 0.205 [0.191, 0.218]; orange 0.198 [0.183, 0.213]
- 3: digit-relative tops ['blue', 'green', 'red'] | sampled: blue 0.226 [0.201, 0.253]; green 0.222 [0.197, 0.249]; red 0.152 [0.131, 0.176]; orange 0.108 [0.090, 0.129]; other 0.083 [0.067, 0.102] | exact (tops): blue 0.218 [0.204, 0.232]; green 0.229 [0.214, 0.244]; red 0.161 [0.149, 0.174]
- 4: digit-relative tops ['yellow', 'brown', 'orange'] | sampled: yellow 0.191 [0.168, 0.217]; orange 0.184 [0.161, 0.209]; green 0.137 [0.117, 0.160]; red 0.131 [0.111, 0.153]; blue 0.075 [0.060, 0.093] | exact (tops): yellow 0.187 [0.173, 0.201]; brown 0.060 [0.052, 0.068]; orange 0.251 [0.235, 0.268]
- 5: digit-relative tops ['gray', 'purple', 'pink'] | sampled: purple 0.161 [0.140, 0.185]; green 0.153 [0.132, 0.177]; other 0.128 [0.109, 0.150]; orange 0.107 [0.089, 0.128]; yellow 0.078 [0.063, 0.096] | exact (tops): gray 0.033 [0.029, 0.037]; purple 0.183 [0.170, 0.196]; pink 0.089 [0.080, 0.099]
- 6: digit-relative tops ['brown', 'orange', 'purple'] | sampled: orange 0.198 [0.174, 0.224]; other 0.126 [0.107, 0.148]; green 0.118 [0.099, 0.139]; purple 0.113 [0.095, 0.134]; red 0.105 [0.087, 0.126] | exact (tops): brown 0.075 [0.067, 0.085]; orange 0.305 [0.289, 0.320]; purple 0.135 [0.123, 0.147]
- 7: digit-relative tops ['purple', 'pink', 'blue'] | sampled: purple 0.218 [0.194, 0.245]; other 0.153 [0.132, 0.177]; blue 0.135 [0.115, 0.158]; red 0.112 [0.094, 0.133]; orange 0.092 [0.076, 0.112] | exact (tops): purple 0.231 [0.216, 0.247]; pink 0.076 [0.066, 0.086]; blue 0.120 [0.109, 0.130]
- 8: digit-relative tops ['black', 'brown', 'white'] | sampled: black 0.242 [0.216, 0.270]; other 0.095 [0.078, 0.115]; red 0.094 [0.077, 0.114]; orange 0.094 [0.077, 0.114]; brown 0.093 [0.077, 0.113] | exact (tops): black 0.230 [0.216, 0.244]; brown 0.111 [0.101, 0.121]; white 0.041 [0.036, 0.047]
- 9: digit-relative tops ['purple', 'blue', 'pink'] | sampled: purple 0.269 [0.242, 0.297]; blue 0.160 [0.139, 0.184]; other 0.139 [0.119, 0.162]; red 0.103 [0.086, 0.123]; green 0.074 [0.059, 0.092] | exact (tops): purple 0.308 [0.291, 0.325]; blue 0.166 [0.154, 0.177]; pink 0.071 [0.063, 0.079]

Examples:

    ['6', '8', '4', '7', '0', '5', '9', '2', '1', '3'] → [' Magenta (deep purple)  ', ' Omega (black and white)', ' Orange', ' Royal Blue', ' Indigo (purple-blue)', ' Gold', ' Forest Green', ' Aqua (cyan)', ' White', ' Crimson (red-pink)']
    ['9', '1', '3', '2', '5', '4', '7', '6', '0', '8'] → [' blue  ', ' red', ' teal', ' purple', ' green', ' orange', ' yellow', ' pink', ' gold', ' brown']
    ['8', '4', '5', '3', '1', '7', '6', '2', '0', '9'] → [' orange  ', ' red', ' purple', ' green', ' blue', ' yellow', ' brown', ' white', ' black', 'arial pink? Actually typical: "yellow']
    ['1', '4', '2', '3', '8', '0', '7', '5', '9', '6'] → [' Violet  ', ' Blue', ' Green', ' Orange', ' Gold', ' Black (or Dark Gray)', ' Red', ' Purple', ' Pink', ' Yellow']
    ['3', '9', '5', '6', '8', '2', '0', '1', '4', '7'] → [' Red  ', ' Yellow', ' Blue', ' Sky Blue', ' Green', ' Green', ' Brown', ' Blue', ' Yellow', ' Orange']

## Predictions

- 1_pipeline: {"parse_rate_name": 0.9536, "preflight": true, "right": true}
- 2_digit_specificity: {"V": 0.26126657461721814, "null_mean": 0.034626976565642675, "null_95": 0.03866476804039044, "p": 9.999000099990002e-05, "right": true}
- 3_palette_replicates: {"r_v1": 0.9673973204656284, "r_M": 0.7500076825510972, "hits": 4, "right": true}
- 4_seven_purple: {"top": "purple", "sampled_share": 0.218, "exact_share": 0.23130550312741882, "right": true}
