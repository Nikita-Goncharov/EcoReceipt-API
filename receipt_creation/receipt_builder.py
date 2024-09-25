import os
import json
from datetime import datetime
from typing import TypedDict, NamedTuple
from decimal import Decimal

from PIL import Image, ImageFont, ImageDraw

from .generate_barcode import BarCodeOptions, generate_barcode_img


class DateTimeAndDecimalEncoder(json.JSONEncoder):
    """ Instead of letting the default encoder convert datetime to string,
        convert datetime objects into a dict, which can be decoded by the
        DateTimeDecoder
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return {
                '__type__': 'datetime',
                'year': obj.year,
                'month': obj.month,
                'day': obj.day,
                'hour': obj.hour,
                'minute': obj.minute,
                'second': obj.second,
                'microsecond': obj.microsecond,
            }
        elif isinstance(obj, Decimal):
            return round(float(obj), 2)
        else:
            return json.JSONEncoder.default(self, obj)


class ReceiptHeader(TypedDict):
    title: str
    address: str
    hotline_phone: str
    datetime: datetime


class ReceiptBody(TypedDict):
    products: list[tuple[str, Decimal]]
    amount: Decimal


class ReceiptFooter(TypedDict):
    card_number: str
    wish_phrase: str


class ReceiptData(TypedDict):
    header: ReceiptHeader
    body: ReceiptBody
    footer: ReceiptFooter


class Coords(NamedTuple):
    x: int
    y: int


class ReceiptCornerCoords(TypedDict):
    top_left: Coords
    top_right: Coords
    bottom_left: Coords
    bottom_right: Coords


class ReceiptBuilder:
    def __init__(self, empty_receipt_path: str, full_receipt_save_path: str):
        """ Attention. This class do not create directories in empty_receipt_path and full_receipt_save_path.
            They should be already created.

        """

        if os.path.exists(empty_receipt_path):
            self.empty_receipt_path = empty_receipt_path
            self.original_image = Image.open(empty_receipt_path)
            self.image = self.original_image.copy()
            self.receipt_draw = ImageDraw.Draw(self.image)
        else:
            raise Exception("Error. Empty receipt path is not valid")
        save_receipt_path = os.path.dirname(full_receipt_save_path)
        if os.path.exists(save_receipt_path):
            self.full_receipt_save_path = full_receipt_save_path
        else:
            raise Exception("Error. Full receipt path is not valid")

    def set_params(self, data: ReceiptData, corner_coords: ReceiptCornerCoords):
        self.monospace_header = ImageFont.truetype("./internal_fonts/NotoSansMono-Regular.ttf", 32)
        self.monospace_paragraph = ImageFont.truetype("./internal_fonts/NotoSansMono-Regular.ttf", 12)
        self.header_symbol_width = 16  # 3  -  count of pixels between symbols
        self.paragraph_symbol_width = 5  # 2

        self.data = data

        self.corner_coords = corner_coords
        self.receipt_width = self.corner_coords["top_right"].x - self.corner_coords["top_left"].x
        self.receipt_height = self.corner_coords["bottom_left"].y - self.corner_coords["top_left"].y
        self.ox_middle_coords = self.corner_coords["top_left"].x + self.receipt_width // 2
        self.receipt_next_line_oy = 20

    def add_receipt_sections(self, coords: Coords, text: str, font: ImageFont.FreeTypeFont | None = None, color: tuple = (0, 0, 0)):
        if font is None:
            font = self.monospace_paragraph

        self.receipt_draw.text(
            coords,
            text,
            color,
            font=font
        )

    def paste_image(self, coords: Coords, img: Image):
        self.image.paste(img, (coords.x, coords.y), img)

    def make_receipt(self):
        receipt_datetime = self.data["header"]["datetime"]
        year, month, day, hour, minute = receipt_datetime.year, receipt_datetime.month, receipt_datetime.day, receipt_datetime.hour, receipt_datetime.minute
        # TODO: paste it in receipt photo if need change height
        # TODO: Add few layouts for receipts

        # Add company name to receipt
        company_name_count_symbols = len(self.data["header"]["title"])
        company_name_spaces_count = company_name_count_symbols - 1
        # Using Mono font, every symbol width 16 px and +-3 for space between symbols
        company_name_width = company_name_count_symbols * 16 + company_name_spaces_count * 3

        coords: Coords = Coords(
            self.ox_middle_coords - company_name_width // 2,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )
        self.add_receipt_sections(coords, self.data["header"]["title"], self.monospace_header)
        self.receipt_next_line_oy += 70

        # Add address
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )
        self.add_receipt_sections(coords, f'Address: {self.data["header"]["address"]}')
        self.receipt_next_line_oy += 30

        # Add phone
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, f'Telephone: {self.data["header"]["hotline_phone"]}')
        self.receipt_next_line_oy += 30

        # Add date and time
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(
            coords,
            f'Date and time: {self.data["header"]["datetime"].strftime("%d/%m/%Y %H:%M:%S")}'
        )
        self.receipt_next_line_oy += 20

        # Add list of bought goods
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, "-----------------------------------------------------")
        self.receipt_next_line_oy += 30

        for product_tuple in self.data["body"]["products"]:
            product_name, product_cost = product_tuple
            coords: Coords = Coords(
                self.corner_coords["top_left"].x + 10,
                self.corner_coords["top_left"].y + self.receipt_next_line_oy
            )
            self.add_receipt_sections(coords, product_name)

            coords: Coords = Coords(
                self.corner_coords["top_right"].x - 40,
                self.corner_coords["top_left"].y + self.receipt_next_line_oy
            )
            self.add_receipt_sections(coords, f'{round(product_cost, 2)}$')

            self.receipt_next_line_oy += 25

        self.receipt_next_line_oy += 5

        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, "-----------------------------------------------------")
        self.receipt_next_line_oy += 20

        # Add total sum
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, "AMOUNT")

        coords: Coords = Coords(
            self.corner_coords["top_right"].x - 40,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, f'{round(self.data["body"]["amount"], 2)}$')
        self.receipt_next_line_oy += 30

        # Add user card number
        coords: Coords = Coords(
            self.corner_coords["top_left"].x + 10,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, f'Payment card: {self.data["footer"]["card_number"]}')
        self.receipt_next_line_oy += 30

        # Add wish phrase
        phrase_count_symbols = len(self.data["footer"]["wish_phrase"])
        phrase_spaces_count = phrase_count_symbols - 1
        phrase_width = phrase_count_symbols * 5 + phrase_spaces_count * 2

        coords: Coords = Coords(
            self.ox_middle_coords - phrase_width // 2,
            self.corner_coords["top_left"].y + self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, self.data["footer"]["wish_phrase"])
        self.receipt_next_line_oy += 30

        options: BarCodeOptions = {
            "text": json.dumps(self.data, cls=DateTimeAndDecimalEncoder),
            "format": "PNG",
            "font_size": 10,
            "module_width": .7,
            "module_height": 15.0,
            "quiet_zone": 1
        }

        barcode_save_path = os.path.join(os.path.dirname(self.full_receipt_save_path), f"barcode_{year}_{month}_{day}_{hour}_{minute}.png")
        bar_code = generate_barcode_img(options, barcode_save_path)
        if bar_code is not None:
            bar_code_new_width = self.receipt_width - 100
            bar_code_resize_coef = bar_code_new_width / bar_code.width

            bar_code = bar_code.resize((bar_code_new_width, int(bar_code.height * bar_code_resize_coef)))
            bar_code_middle_ox = bar_code.width // 2
            # print(bar_code.height)
            barcode_coords: Coords = Coords(
                self.ox_middle_coords - bar_code_middle_ox,
                self.corner_coords["bottom_left"].y - bar_code.height - 30
            )
            print(barcode_coords)
            self.paste_image(barcode_coords, bar_code.copy())

        self.image.save(self.full_receipt_save_path)

        # last_line_oy = self.corner_coords["top_left"].y + self.receipt_next_line_oy
        #
        # if last_line_oy + bar_code.height + 40 < self.corner_coords["bottom_left"].y:
        #     print(last_line_oy + bar_code.height + 40,  self.corner_coords["bottom_left"].y)
        #     new_height = last_line_oy + bar_code.height + 40
        #     height_difference = self.corner_coords["bottom_left"].y - new_height
        #     print(new_height, height_difference)
        #
        #
        #     self.corner_coords: ReceiptCornerCoords = {
        #         "top_left": self.corner_coords["top_left"],
        #         "top_right": self.corner_coords["top_right"],
        #
        #         "bottom_left": Coords(
        #             self.corner_coords["bottom_left"].x,
        #             self.corner_coords["bottom_left"].y - height_difference
        #         ),
        #         "bottom_right": Coords(
        #             self.corner_coords["bottom_left"].x,
        #             self.corner_coords["bottom_right"].y - height_difference
        #         ),
        #     }
        #
        #     self.receipt_width = self.corner_coords["top_right"].x - self.corner_coords["top_left"].x
        #     self.receipt_height = self.corner_coords["bottom_left"].y - self.corner_coords["top_left"].y
        #     print(self.receipt_height)
        #     self.ox_middle_coords = self.corner_coords["top_left"].x + self.receipt_width // 2
        #     self.receipt_next_line_oy = 20
        #
        #     self.image = self.original_image.copy()
        #     self.image = self.image.resize((self.image.width, self.receipt_height))
        #     self.make_receipt()
        # elif False:  # TODO: check if receipt small
        #     pass
        return os.path.join(self.full_receipt_save_path)