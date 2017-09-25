""" Python Character Mapping for ANSEL (https://en.wikipedia.org/wiki/ANSEL).

"""

from __future__ import print_function, absolute_import, division

import codecs


class AnselCodec(codecs.Codec):

    def encode(self, input, errors='strict'):
        return codecs.charmap_encode(input, errors, ansel_encoding_table)

    def decode(self, input, errors='strict'):
        return codecs.charmap_decode(input, errors, ansel_decoding_table)


class AnselIncrementalEncoder(codecs.IncrementalEncoder):
    def encode(self, input, final=False):
        return codecs.charmap_encode(input, self.errors,
                                     ansel_encoding_table)[0]


class AnselIncrementalDecoder(codecs.IncrementalDecoder):
    def decode(self, input, final=False):
        return codecs.charmap_decode(input, self.errors,
                                     ansel_decoding_table)[0]


class AnselStreamWriter(AnselCodec, codecs.StreamWriter):
    pass


class AnselStreamReader(AnselCodec, codecs.StreamReader):
    pass


def _search_function(encoding):
    if encoding == 'ansel':
        return codecs.CodecInfo(
            name='ansel',
            encode=AnselCodec().encode,
            decode=AnselCodec().decode,
            incrementalencoder=AnselIncrementalEncoder,
            incrementaldecoder=AnselIncrementalDecoder,
            streamreader=AnselStreamReader,
            streamwriter=AnselStreamWriter,
        )


codecs.register(_search_function)

# ## Decoding Table
# from https://en.wikipedia.org/wiki/ANSEL
ansel_decoding_table = (
    u'\x00'  # 0x00 -> NULL
    u'\x01'  # 0x01 -> START OF HEADING
    u'\x02'  # 0x02 -> START OF TEXT
    u'\x03'  # 0x03 -> END OF TEXT
    u'\x04'  # 0x04 -> END OF TRANSMISSION
    u'\x05'  # 0x05 -> ENQUIRY
    u'\x06'  # 0x06 -> ACKNOWLEDGE
    u'\x07'  # 0x07 -> BELL
    u'\x08'  # 0x08 -> BACKSPACE
    u'\t'  # 0x09 -> HORIZONTAL TABULATION
    u'\n'  # 0x0A -> LINE FEED
    u'\x0b'  # 0x0B -> VERTICAL TABULATION
    u'\x0c'  # 0x0C -> FORM FEED
    u'\r'  # 0x0D -> CARRIAGE RETURN
    u'\x0e'  # 0x0E -> SHIFT OUT
    u'\x0f'  # 0x0F -> SHIFT IN
    u'\x10'  # 0x10 -> DATA LINK ESCAPE
    u'\x11'  # 0x11 -> DEVICE CONTROL ONE
    u'\x12'  # 0x12 -> DEVICE CONTROL TWO
    u'\x13'  # 0x13 -> DEVICE CONTROL THREE
    u'\x14'  # 0x14 -> DEVICE CONTROL FOUR
    u'\x15'  # 0x15 -> NEGATIVE ACKNOWLEDGE
    u'\x16'  # 0x16 -> SYNCHRONOUS IDLE
    u'\x17'  # 0x17 -> END OF TRANSMISSION BLOCK
    u'\x18'  # 0x18 -> CANCEL
    u'\x19'  # 0x19 -> END OF MEDIUM
    u'\x1a'  # 0x1A -> SUBSTITUTE
    u'\x1b'  # 0x1B -> ESCAPE
    u'\x1c'  # 0x1C -> FILE SEPARATOR
    u'\x1d'  # 0x1D -> GROUP SEPARATOR
    u'\x1e'  # 0x1E -> RECORD SEPARATOR
    u'\x1f'  # 0x1F -> UNIT SEPARATOR
    u' '  # 0x20 -> SPACE
    u'!'  # 0x21 -> EXCLAMATION MARK
    u'"'  # 0x22 -> QUOTATION MARK
    u'#'  # 0x23 -> NUMBER SIGN
    u'$'  # 0x24 -> DOLLAR SIGN
    u'%'  # 0x25 -> PERCENT SIGN
    u'&'  # 0x26 -> AMPERSAND
    u"'"  # 0x27 -> APOSTROPHE
    u'('  # 0x28 -> LEFT PARENTHESIS
    u')'  # 0x29 -> RIGHT PARENTHESIS
    u'*'  # 0x2A -> ASTERISK
    u'+'  # 0x2B -> PLUS SIGN
    u','  # 0x2C -> COMMA
    u'-'  # 0x2D -> HYPHEN-MINUS
    u'.'  # 0x2E -> FULL STOP
    u'/'  # 0x2F -> SOLIDUS
    u'0'  # 0x30 -> DIGIT ZERO
    u'1'  # 0x31 -> DIGIT ONE
    u'2'  # 0x32 -> DIGIT TWO
    u'3'  # 0x33 -> DIGIT THREE
    u'4'  # 0x34 -> DIGIT FOUR
    u'5'  # 0x35 -> DIGIT FIVE
    u'6'  # 0x36 -> DIGIT SIX
    u'7'  # 0x37 -> DIGIT SEVEN
    u'8'  # 0x38 -> DIGIT EIGHT
    u'9'  # 0x39 -> DIGIT NINE
    u':'  # 0x3A -> COLON
    u';'  # 0x3B -> SEMICOLON
    u'<'  # 0x3C -> LESS-THAN SIGN
    u'='  # 0x3D -> EQUALS SIGN
    u'>'  # 0x3E -> GREATER-THAN SIGN
    u'?'  # 0x3F -> QUESTION MARK
    u'@'  # 0x40 -> COMMERCIAL AT
    u'A'  # 0x41 -> LATIN CAPITAL LETTER A
    u'B'  # 0x42 -> LATIN CAPITAL LETTER B
    u'C'  # 0x43 -> LATIN CAPITAL LETTER C
    u'D'  # 0x44 -> LATIN CAPITAL LETTER D
    u'E'  # 0x45 -> LATIN CAPITAL LETTER E
    u'F'  # 0x46 -> LATIN CAPITAL LETTER F
    u'G'  # 0x47 -> LATIN CAPITAL LETTER G
    u'H'  # 0x48 -> LATIN CAPITAL LETTER H
    u'I'  # 0x49 -> LATIN CAPITAL LETTER I
    u'J'  # 0x4A -> LATIN CAPITAL LETTER J
    u'K'  # 0x4B -> LATIN CAPITAL LETTER K
    u'L'  # 0x4C -> LATIN CAPITAL LETTER L
    u'M'  # 0x4D -> LATIN CAPITAL LETTER M
    u'N'  # 0x4E -> LATIN CAPITAL LETTER N
    u'O'  # 0x4F -> LATIN CAPITAL LETTER O
    u'P'  # 0x50 -> LATIN CAPITAL LETTER P
    u'Q'  # 0x51 -> LATIN CAPITAL LETTER Q
    u'R'  # 0x52 -> LATIN CAPITAL LETTER R
    u'S'  # 0x53 -> LATIN CAPITAL LETTER S
    u'T'  # 0x54 -> LATIN CAPITAL LETTER T
    u'U'  # 0x55 -> LATIN CAPITAL LETTER U
    u'V'  # 0x56 -> LATIN CAPITAL LETTER V
    u'W'  # 0x57 -> LATIN CAPITAL LETTER W
    u'X'  # 0x58 -> LATIN CAPITAL LETTER X
    u'Y'  # 0x59 -> LATIN CAPITAL LETTER Y
    u'Z'  # 0x5A -> LATIN CAPITAL LETTER Z
    u'['  # 0x5B -> LEFT SQUARE BRACKET
    u'\\'  # 0x5C -> REVERSE SOLIDUS
    u']'  # 0x5D -> RIGHT SQUARE BRACKET
    u'^'  # 0x5E -> CIRCUMFLEX ACCENT
    u'_'  # 0x5F -> LOW LINE
    u'`'  # 0x60 -> GRAVE ACCENT
    u'a'  # 0x61 -> LATIN SMALL LETTER A
    u'b'  # 0x62 -> LATIN SMALL LETTER B
    u'c'  # 0x63 -> LATIN SMALL LETTER C
    u'd'  # 0x64 -> LATIN SMALL LETTER D
    u'e'  # 0x65 -> LATIN SMALL LETTER E
    u'f'  # 0x66 -> LATIN SMALL LETTER F
    u'g'  # 0x67 -> LATIN SMALL LETTER G
    u'h'  # 0x68 -> LATIN SMALL LETTER H
    u'i'  # 0x69 -> LATIN SMALL LETTER I
    u'j'  # 0x6A -> LATIN SMALL LETTER J
    u'k'  # 0x6B -> LATIN SMALL LETTER K
    u'l'  # 0x6C -> LATIN SMALL LETTER L
    u'm'  # 0x6D -> LATIN SMALL LETTER M
    u'n'  # 0x6E -> LATIN SMALL LETTER N
    u'o'  # 0x6F -> LATIN SMALL LETTER O
    u'p'  # 0x70 -> LATIN SMALL LETTER P
    u'q'  # 0x71 -> LATIN SMALL LETTER Q
    u'r'  # 0x72 -> LATIN SMALL LETTER R
    u's'  # 0x73 -> LATIN SMALL LETTER S
    u't'  # 0x74 -> LATIN SMALL LETTER T
    u'u'  # 0x75 -> LATIN SMALL LETTER U
    u'v'  # 0x76 -> LATIN SMALL LETTER V
    u'w'  # 0x77 -> LATIN SMALL LETTER W
    u'x'  # 0x78 -> LATIN SMALL LETTER X
    u'y'  # 0x79 -> LATIN SMALL LETTER Y
    u'z'  # 0x7A -> LATIN SMALL LETTER Z
    u'{'  # 0x7B -> LEFT CURLY BRACKET
    u'|'  # 0x7C -> VERTICAL LINE
    u'}'  # 0x7D -> RIGHT CURLY BRACKET
    u'~'  # 0x7E -> TILDE
    u'\x7f'  # 0x7F -> DELETE
    u'\x80'  # 0x80 -> <control>
    u'\x81'  # 0x81 -> <control>
    u'\x82'  # 0x82 -> <control>
    u'\x83'  # 0x83 -> <control>
    u'\x84'  # 0x84 -> <control>
    u'\x85'  # 0x85 -> <control>
    u'\x86'  # 0x86 -> <control>
    u'\x87'  # 0x87 -> <control>
    u'\x88'  # 0x88 -> <control>
    u'\x89'  # 0x89 -> <control>
    u'\x8a'  # 0x8A -> <control>
    u'\x8b'  # 0x8B -> <control>
    u'\x8c'  # 0x8C -> <control>
    u'\x8d'  # 0x8D -> <control>
    u'\x8e'  # 0x8E -> <control>
    u'\x8f'  # 0x8F -> <control>
    u'\x90'  # 0x90 -> <control>
    u'\x91'  # 0x91 -> <control>
    u'\x92'  # 0x92 -> <control>
    u'\x93'  # 0x93 -> <control>
    u'\x94'  # 0x94 -> <control>
    u'\x95'  # 0x95 -> <control>
    u'\x96'  # 0x96 -> <control>
    u'\x97'  # 0x97 -> <control>
    u'\x98'  # 0x98 -> <control>
    u'\x99'  # 0x99 -> <control>
    u'\x9a'  # 0x9A -> <control>
    u'\x9b'  # 0x9B -> <control>
    u'\x9c'  # 0x9C -> <control>
    u'\x9d'  # 0x9D -> <control>
    u'\x9e'  # 0x9E -> <control>
    u'\x9f'  # 0x9F -> <control>
    u'\ufffe'  # 0xA0 ->
    u'\u0141'  # 0xA1 -> Latin Capital Letter L with Stroke
    u'\xD8'  # 0xA2 -> Latin Capital Letter O with Stroke
    u'\u0110'  # 0xA3 -> Latin Capital Letter D with Stroke
    u'\xDE'  # 0xA4 -> Latin Capital Letter Thorn
    u'\xC6'  # 0xA5 -> Latin Capital Letter Ae
    u'\u0152'  # 0xA6 -> Latin Capital Ligature Oe
    u'\u02B9'  # 0xA7 -> Modifier Letter Prime
    u'\xB7'  # 0xA8 -> Middle Dot
    u'\u266D'  # 0xA9 -> Music Flat Sign
    u'\xAE'  # 0xAA -> Registered Sign
    u'\xB1'  # 0xAB -> Plus-Minus Sign
    u'\u01A0'  # 0xAC -> Latin Capital Letter O with Horn
    u'\u01AF'  # 0xAD -> Latin Capital Letter U with Horn
    u'\u02BC'  # 0xAE -> Modifier Letter Apostrophe
    u'\xAF'  # 0xAF -> Macron
    u'\u02BB'  # 0xB0 -> Modifier Letter Turned Comma
    u'\u0142'  # 0xB1 -> Latin Small Letter L with Stroke
    u'\xF8'  # 0xB2 -> Latin Small Letter O with Stroke
    u'\u0111'  # 0xB3 -> Latin Small Letter D with Stroke
    u'\xFE'  # 0xB4 -> Latin Small Letter Thorn
    u'\xE6'  # 0xB5 -> Latin Small Letter Ae
    u'\u0153'  # 0xB6 -> Latin Small Ligature Oe
    u'\u02BA'  # 0xB7 -> Modifier Letter Double Prime
    u'\u0131'  # 0xB8 -> Latin Small Letter Dotless I
    u'\xA3'  # 0xB9 -> Pound Sign
    u'\xF0'  # 0xBA -> Latin Small Letter Eth
    u'\ufffe'  # 0xBB ->
    u'\u01A1'  # 0xBC -> Latin Small Letter O with Horn
    u'\u01B0'  # 0xBD -> Latin Small Letter U with Horn
    u'\u25A1'  # 0xBE -> White Square (GEDCOM extension?)
    u'\u25A0'  # 0xBF -> Black Square (GEDCOM extension?)
    u'\xB0'  # 0xC0 -> Degree Sign
    u'\u2113'  # 0xC1 -> Script Small L
    u'\u2117'  # 0xC2 -> Sound Recording Copyright
    u'\xA9'  # 0xC3 -> Copyright Sign
    u'\u266F'  # 0xC4 -> Music Sharp Sign
    u'\xBF'  # 0xC5 -> Inverted Question Mark
    u'\xA1'  # 0xC6 -> Inverted Exclamation Mark
    u'\ufffe'  # 0xC7 ->
    u'\ufffe'  # 0xC8 ->
    u'\ufffe'  # 0xC9 ->
    u'\ufffe'  # 0xCA ->
    u'\ufffe'  # 0xCB ->
    u'\ufffe'  # 0xCC ->
    u'\ufffe'  # 0xCD ->
    u'\ufffe'  # 0xCE ->
    u'\ufffe'  # 0xCF ->
    u'\ufffe'  # 0xD0 ->
    u'\ufffe'  # 0xD1 ->
    u'\ufffe'  # 0xD2 ->
    u'\ufffe'  # 0xD3 ->
    u'\ufffe'  # 0xD4 ->
    u'\ufffe'  # 0xD5 ->
    u'\ufffe'  # 0xD6 ->
    u'\ufffe'  # 0xD7 ->
    u'\ufffe'  # 0xD8 ->
    u'\ufffe'  # 0xD9 ->
    u'\ufffe'  # 0xDA ->
    u'\ufffe'  # 0xDB ->
    u'\ufffe'  # 0xDC ->
    u'\ufffe'  # 0xDD ->
    u'\ufffe'  # 0xDE ->
    u'\ufffe'  # 0xDF ->
    u'\u0309'  # 0xE0 -> Combining Hook Above
    u'\u0300'  # 0xE1 -> Combining Grave Accent
    u'\u0301'  # 0xE2 -> Combining Acute Accent
    u'\u0302'  # 0xE3 -> Combining Circumflex Accent
    u'\u0303'  # 0xE4 -> Combining Tilde
    u'\u0304'  # 0xE5 -> Combining Macron
    u'\u0306'  # 0xE6 -> Combining Breve
    u'\u0307'  # 0xE7 -> Combining Dot Above
    u'\u0308'  # 0xE8 -> Combining Diaeresis
    u'\u030C'  # 0xE9 -> Combining Caron
    u'\u030A'  # 0xEA -> Combining Ring Above
    u'\uFE20'  # 0xEB -> COMBINING LIGATURE LEFT HALF
    u'\uFE21'  # 0xEC -> COMBINING LIGATURE RIGHT HALF
    u'\u0315'  # 0xED -> Combining Comma Above Right
    u'\u030B'  # 0xEE -> Combining Horn
    u'\u0310'  # 0xEF -> Combining Candrabindu
    u'\u0327'  # 0xF0 -> Combining Cedilla
    u'\u0328'  # 0xF1 -> Combining Ogonek
    u'\u0323'  # 0xF2 -> Combining Dot Below
    u'\u0324'  # 0xF3 -> Combining Diaeresis Below
    u'\u0325'  # 0xF4 -> Combining Ring Below
    u'\u0333'  # 0xF5 -> Combining Double Low Line
    u'\u0332'  # 0xF6 -> Combining Low Line
    u'\u0326'  # 0xF7 -> Combining Comma Below
    u'\u031C'  # 0xF8 -> Combining Left Half Ring
    u'\u032E'  # 0xF9 -> Combining Breve Below
    u'\uFE22'  # 0xFA -> COMBINING DOUBLE TILDE LEFT HALF
    u'\uFE23'  # 0xFB -> COMBINING DOUBLE TILDE RIGHT HALF
    u'\u0338'  # 0xFC -> Combining Long Solidus Overlay  (GEDCOM extension?)
    u'\ufffe'  # 0xFD ->
    u'\u0313'  # 0xFE ->Combining Comma Above
    u'\ufffe'  # 0xFF ->
)

# ## Encoding table
ansel_encoding_table = codecs.charmap_build(ansel_decoding_table)
