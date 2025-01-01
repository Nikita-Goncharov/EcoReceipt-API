import os
import json
import logging
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


class ReceiptDataItem(NamedTuple):
    data: str | datetime | Decimal | list[tuple[str, Decimal]]
    height: int


class ReceiptHeader(TypedDict):
    title: ReceiptDataItem
    address: ReceiptDataItem
    hotline_phone: ReceiptDataItem
    datetime: ReceiptDataItem


class ReceiptBody(TypedDict):
    products: ReceiptDataItem
    amount: ReceiptDataItem


class ReceiptFooter(TypedDict):
    card_number: ReceiptDataItem
    wish_phrase: ReceiptDataItem


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
    def __init__(self, receipt_background_path: str, exact_receipt_path: str, full_receipt_save_path: str):
        """ Attention. This class do not create directories in receipt_background_path, exact_receipt_path and full_receipt_save_path.
            They should be already created.

        """
        self.bar_code = None
        if os.path.exists(exact_receipt_path):
            self.exact_receipt_path = exact_receipt_path
            self.exact_receipt_original = Image.open(exact_receipt_path)
            self.exact_receipt = self.exact_receipt_original.copy()
            self.exact_receipt_draw = ImageDraw.Draw(self.exact_receipt)
        else:
            raise Exception("Error. Exact receipt path is not valid")

        if os.path.exists(receipt_background_path):
            self.receipt_background_path = receipt_background_path
            self.receipt_background_original = Image.open(receipt_background_path)
            self.receipt_background = self.receipt_background_original.copy()
        else:
            raise Exception("Error. Receipt background path is not valid")

        save_receipt_path = os.path.dirname(full_receipt_save_path)
        if os.path.exists(save_receipt_path):
            self.full_receipt_save_path = full_receipt_save_path
        else:
            raise Exception("Error. Full receipt path is not valid")

    def set_params(self, data: ReceiptData):
        logging.log(logging.INFO, f"Current working directory: {os.getcwd()}")
        self.monospace_header = ImageFont.truetype("./receipt_creation/internal_fonts/NotoSansMono-Regular.ttf", 32)  # TODO: font by default
        self.monospace_paragraph = ImageFont.truetype("./receipt_creation/internal_fonts/NotoSansMono-Regular.ttf", 12)
        self.header_symbol_width = 16  # 3  -  count of pixels between symbols
        self.paragraph_symbol_width = 5  # 2

        self.data = data

        self.receipt_width = self.exact_receipt.width
        self.receipt_height = self.exact_receipt.height
        self.ox_middle_coords = self.receipt_width // 2
        self.receipt_next_line_oy = 20

    def add_receipt_sections(self, coords: Coords, text: str, font: ImageFont.FreeTypeFont | None = None, color: tuple = (0, 0, 0)):
        if font is None:
            font = self.monospace_paragraph

        logging.log(logging.INFO, text)
        logging.log(logging.INFO, f"Add text by coords: {(coords.x, coords.y)}")
        self.exact_receipt_draw.text(
            coords,
            text,
            color,
            font=font
        )

    def paste_image(self, coords: Coords, img: Image):
        self.exact_receipt.paste(img, (coords.x, coords.y), img)

    def generate_barcode_img(self):
        receipt_datetime = self.data["header"]["datetime"].data
        year, month, day, hour, minute = receipt_datetime.year, receipt_datetime.month, receipt_datetime.day, receipt_datetime.hour, receipt_datetime.minute

        options: BarCodeOptions = {
            "text": json.dumps(self.data, cls=DateTimeAndDecimalEncoder),
            "format": "PNG",
            "font_size": 10,
            "module_width": .7,
            "module_height": 15.0,
            "quiet_zone": 1
        }

        barcode_save_path = os.path.join(os.path.dirname(self.full_receipt_save_path),
                                         f"barcode_{year}_{month}_{day}_{hour}_{minute}.png")
        bar_code = generate_barcode_img(options, barcode_save_path)
        if bar_code is not None:
            self.bar_code_new_width = self.receipt_width - 100
            bar_code_resize_coef = self.bar_code_new_width / bar_code.width
            self.bar_code_new_height = int(bar_code.height * bar_code_resize_coef)

            bar_code = bar_code.resize((self.bar_code_new_width, self.bar_code_new_height))
            self.bar_code_middle_ox = bar_code.width // 2
            self.bar_code = bar_code

    def calc_receipt_content_height(self):
        receipt_data_height = self.receipt_next_line_oy
        receipt_data_height += self.data["header"]["title"].height
        receipt_data_height += self.data["header"]["address"].height
        receipt_data_height += self.data["header"]["hotline_phone"].height
        receipt_data_height += self.data["header"]["datetime"].height

        receipt_data_height += self.data["body"]["products"].height
        receipt_data_height += self.data["body"]["amount"].height

        receipt_data_height += self.data["footer"]["card_number"].height
        receipt_data_height += self.data["footer"]["wish_phrase"].height

        receipt_data_height += 30 + self.bar_code_new_height + 30  # + top and bottom padding on receipt
        logging.log(logging.INFO, f"Needed receipt height: {receipt_data_height}")
        return receipt_data_height

    def resize_receipt_img(self):
        needed_receipt_height = self.calc_receipt_content_height()

        bottom_height = top_height = int(self.exact_receipt.height * 0.2)
        middle_height = self.receipt_height - top_height - bottom_height

        top = self.exact_receipt.crop((0, 0, self.receipt_width, top_height))
        middle = self.exact_receipt.crop((0, top_height, self.receipt_width, top_height + middle_height))
        bottom = self.exact_receipt.crop((0, top_height + middle_height, self.receipt_width, self.receipt_height))

        new_middle_height = needed_receipt_height - top_height - bottom_height
        middle_resized = middle.resize((middle.width, new_middle_height))
        self.exact_receipt = Image.new('RGB', (self.receipt_width, top_height + new_middle_height + bottom_height))

        self.exact_receipt.paste(top, (0, 0))
        self.exact_receipt.paste(middle_resized, (0, top_height))
        self.exact_receipt.paste(bottom, (0, top_height + new_middle_height))

        self.exact_receipt_draw = ImageDraw.Draw(self.exact_receipt)
        self.receipt_width = self.exact_receipt.width
        self.receipt_height = self.exact_receipt.height
        self.ox_middle_coords = self.receipt_width // 2

        logging.log(logging.INFO, f"Resized receipt w - {self.receipt_width}, h - {self.receipt_height}, middle_ox - {self.ox_middle_coords}")

    def add_receipt_background(self):
        self.receipt_background = self.receipt_background.resize((self.receipt_width+50, self.receipt_height+50))
        self.receipt_background.paste(self.exact_receipt, (25, 25))
        self.receipt_background.save(self.full_receipt_save_path)

    def fill_receipt_img(self):
        # Add company name to receipt
        company_name_count_symbols = len(self.data["header"]["title"].data)
        company_name_spaces_count = company_name_count_symbols - 1
        # Using Mono font, every symbol width 16 px and +-3 for space between symbols
        company_name_width = company_name_count_symbols * self.header_symbol_width + company_name_spaces_count * 3

        coords: Coords = Coords(
            self.ox_middle_coords - company_name_width // 2,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Company name receipt coords: x - {coords.x}, y - {coords.y}")
        title_data, title_height = self.data["header"]["title"]
        self.add_receipt_sections(coords, title_data, self.monospace_header)
        self.receipt_next_line_oy += title_height

        # Add address
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Company address receipt coords: x - {coords.x}, y - {coords.y}")
        address_data, address_height = self.data["header"]["address"]
        self.add_receipt_sections(coords, f'Address: {address_data}')
        self.receipt_next_line_oy += address_height

        # Add phone
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Company phone receipt coords: x - {coords.x}, y - {coords.y}")
        phone_data, phone_height = self.data["header"]["hotline_phone"]
        self.add_receipt_sections(coords, f'Telephone: {phone_data}')
        self.receipt_next_line_oy += phone_height

        # Add date and time
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Receipt datetime coords: x - {coords.x}, y - {coords.y}")
        datetime_data, datetime_height = self.data["header"]["datetime"]
        self.add_receipt_sections(
            coords,
            f'Date and time: {datetime_data.strftime("%d/%m/%Y %H:%M:%S")}'
        )
        self.receipt_next_line_oy += datetime_height

        # Add list of bought goods
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Start line of list of products coords: x - {coords.x}, y - {coords.y}")
        self.add_receipt_sections(coords, "-----------------------------------------------------")
        self.receipt_next_line_oy += 30

        for product_tuple in self.data["body"]["products"].data:
            product_name, product_cost = product_tuple
            coords: Coords = Coords(
                10,
                self.receipt_next_line_oy
            )
            logging.log(logging.INFO, f"Product coords: x - {coords.x}, y - {coords.y}")
            self.add_receipt_sections(coords, product_name)

            cost_str = f'{round(product_cost, 2)}$'
            cost_str_width = len(cost_str)*self.paragraph_symbol_width + (len(cost_str) - 1)*2
            coords: Coords = Coords(
                self.receipt_width - 30 - cost_str_width,
                self.receipt_next_line_oy
            )

            self.add_receipt_sections(coords, cost_str)

            self.receipt_next_line_oy += 25

        self.receipt_next_line_oy += 5

        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"End line of list of products coords: x - {coords.x}, y - {coords.y}")
        self.add_receipt_sections(coords, "-----------------------------------------------------")
        self.receipt_next_line_oy += 20

        # Add total sum
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Text 'AMOUNT' coords: x - {coords.x}, y - {coords.y}")
        self.add_receipt_sections(coords, "AMOUNT")
        logging.log(logging.INFO, f"Amount sum coords: x - {coords.x}, y - {coords.y}")

        amount_data, amount_height = self.data["body"]["amount"]
        amount_str = f'{round(amount_data, 2)}$'
        amount_str_width = len(amount_str)*self.paragraph_symbol_width + (len(amount_str) - 1)*2

        coords: Coords = Coords(
            self.receipt_width - 30 - amount_str_width,
            self.receipt_next_line_oy
        )

        self.add_receipt_sections(coords, amount_str)
        self.receipt_next_line_oy += amount_height

        # Add user card number
        coords: Coords = Coords(
            10,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Payment card coords: x - {coords.x}, y - {coords.y}")
        card_number_data, card_number_height = self.data["footer"]["card_number"]
        self.add_receipt_sections(coords, f'Payment card: {card_number_data}')
        self.receipt_next_line_oy += card_number_height

        # Add wish phrase
        wish_phrase_data, wish_phrase_height = self.data["footer"]["wish_phrase"]
        phrase_count_symbols = len(wish_phrase_data)
        phrase_spaces_count = phrase_count_symbols - 1
        phrase_width = phrase_count_symbols * 5 + phrase_spaces_count * 2

        coords: Coords = Coords(
            self.ox_middle_coords - phrase_width // 2,
            self.receipt_next_line_oy
        )
        logging.log(logging.INFO, f"Wish phrase coords: x - {coords.x}, y - {coords.y}")
        self.add_receipt_sections(coords, wish_phrase_data)
        self.receipt_next_line_oy += wish_phrase_height

        if self.bar_code is not None:
            barcode_coords: Coords = Coords(
                self.ox_middle_coords - self.bar_code_middle_ox,
                self.receipt_height - self.bar_code.height - 30
            )
            logging.log(logging.INFO, f"Barcode coords: x - {barcode_coords.x}, y - {barcode_coords.y}")
            self.paste_image(barcode_coords, self.bar_code.copy())

        self.exact_receipt.save(self.full_receipt_save_path)

    def make_receipt(self):
        self.generate_barcode_img()
        self.resize_receipt_img()
        self.fill_receipt_img()
        self.add_receipt_background()
        return os.path.join(self.full_receipt_save_path)
