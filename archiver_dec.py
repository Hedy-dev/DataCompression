import argparse
import json
import os
import struct  # Для упаковки длины заголовка в байты
from bwt import bwt_suffix_arr, bwt_decode
from mtf import mtf_encode, mtf_decode
from zle import zle_encode, zle_decode
from arithmetic import din_arithmetic_compression, decompress
#from tqdm import tqdm
import capitalization as cap
import struct 

# константа для точности ставим 32 бита, хотя можно было бы передавать ее в качестве параметра
BIT_PRECISION_CONFIG = 32
# заголовок в 8 байт (unsigned long long)
HEADER_LENGTH_BYTES = 8
SPECIAL_CASES = [
    'Paris', 'Warrens', 'Luxembourg', 'Epinay', 'Geneva', 'Theresa', 
    'France', 'Diderot', 'Grimm', 'Abbe', 'Houdetot', 'Hermitage', 'French', 
    'Mademoiselle', 'Dupin', 'Madam de Warrens','Madam de Dupin'
]

def bits_to_bytes(bit_string: str) -> tuple[bytes, int]:
    padding_needed = (8 - len(bit_string) % 8) % 8
    padded_bit_string = bit_string + '0' * padding_needed
    byte_array = bytearray()
    for i in range(0, len(padded_bit_string), 8):
        byte_chunk = padded_bit_string[i:i+8]
        byte_array.append(int(byte_chunk, 2))
    return bytes(byte_array), padding_needed

def bytes_to_bits(byte_data: bytes, padding_bits: int) -> str:
    bit_string = ''.join(format(byte, '08b') for byte in byte_data)
    if padding_bits > 0:
        return bit_string[:-padding_bits]
    return bit_string

def compress_file(input_path, output_path, use_decapitalize=False):
    print(f"[*] Сжатие файла: {input_path}")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"[!] Ошибка: Файл не найден {input_path}")
        return

    original_size = os.path.getsize(input_path)
    print(f"[*] Размер исходного файла: {original_size} байт")

    if not text:
        print("[!] Входной файл пуст")
        with open(output_path, 'wb') as f:
            pass
        return

    # для капитализации
    packed_exceptions_data = b''
    alphabet_dl_bytes = b''
    L_dl = 0
    exceptions_padding = 0

    if use_decapitalize:
        print("[*] Декапитализация DEC...")
        text_lower, exception_list = cap.decapitalize_text(text, SPECIAL_CASES)
        text = text_lower
        distance_list = cap.exeptions_dist(exception_list)

        if distance_list:
            print("[*] Сжатие данных о капитализации Compress DEC data...")
            alphabet_dl = list(dict.fromkeys(distance_list))
            L_dl = len(distance_list)
            exception_bit_string = din_arithmetic_compression(distance_list, BIT_PRECISION_CONFIG)
            packed_exceptions_data, exceptions_padding = bits_to_bytes(exception_bit_string)

            # Сериализуем алфавит в байты
            alphabet_dl_str = ",".join(map(str, alphabet_dl))
            alphabet_dl_bytes = alphabet_dl_str.encode('utf-8')

    # Основной конвейер сжатия
    print("[*] BWT...")
    bwt_result, eof_pos = bwt_suffix_arr(text)
    
    print("[*] MTF...")
    mtf_result = mtf_encode(bwt_result)
    
    print("[*] ZLE...")
    zle_encoded = zle_encode(mtf_result)
    # TODO
    alphabet = sorted(list(set(zle_encoded)))
    # Создаем карту для преобразования в плотный алфавит 0..N-1
    symbol_map = {symbol: i for i, symbol in enumerate(alphabet)}
    # Преобразуем исходные данные
    mapped_zle_encoded = [symbol_map[s] for s in zle_encoded]
    # TODO

    print("[*] ARI...может занять немного времени (минут)")
    #zle_encoded_ari_bit_string = din_arithmetic_compression(zle_encoded, BIT_PRECISION_CONFIG)
    zle_encoded_ari_bit_string = din_arithmetic_compression(mapped_zle_encoded, BIT_PRECISION_CONFIG)
    packed_data, padding_bits = bits_to_bytes(zle_encoded_ari_bit_string)

    #alphabet = list(dict.fromkeys(zle_encoded))
    alphabet = list(set(zle_encoded))
    #alphabet_main_str = ",".join(map(str, alphabet))
    alphabet_main_str = ",".join(map(str, alphabet)) # TODO
    alphabet_main_bytes = alphabet_main_str.encode('utf-8')
    original_len = len(zle_encoded)
    with open(output_path, 'wb') as f:
        # флаги бит 0 - используется ли декапитализация
        flags = 1 if use_decapitalize and L_dl > 0 else 0
        f.write(struct.pack('!B', flags))

        # если декапитализация, пишем блок метаданных о ней
        if flags & 1:
            # Длина алфавита, L, паддинг, длина сжатых данных
            f.write(struct.pack('!IIBI', len(alphabet_dl_bytes), L_dl, exceptions_padding, len(packed_exceptions_data)))
            f.write(alphabet_dl_bytes)
            f.write(packed_exceptions_data)

        # блок метаданных
        # eof_pos, алфавита, L, паддинг, длина сжатых данных
        f.write(struct.pack('!IIIBI', eof_pos, len(alphabet_main_bytes), original_len, padding_bits, len(packed_data)))
        f.write(alphabet_main_bytes)
        f.write(packed_data)

    compressed_size = os.path.getsize(output_path)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
    print(f"[+] Сжатие завершено")
    print(f"[+] Выходной файл: {output_path}")
    print(f"[+] Размер сжатого файла: {compressed_size} байт")
    print(f"[+] Коэффициент сжатия: {compression_ratio:.2f}x")


def decompress_file(input_path, output_path):
    print(f"[*] Распаковка файла: {input_path}")
    try:
        with open(input_path, 'rb') as f:
            # заголовок
            # флаги
            flags_byte = f.read(1)
            if not flags_byte:
                print("[!] Ошибка: Архив пуст или поврежден.")
                return
            flags = struct.unpack('!B', flags_byte)[0]
            was_decapitalized = (flags & 1)

            distance_list = []
            if was_decapitalized:
                #  заголовок капитализация
                cap_header_data = f.read(struct.calcsize('!IIBI'))
                len_alpha_dl, L_dl, exceptions_padding, len_packed_exc = struct.unpack('!IIBI', cap_header_data)
                alphabet_dl_bytes = f.read(len_alpha_dl)
                packed_exceptions_data = f.read(len_packed_exc)
                # распаковка
                alphabet_dl_str = alphabet_dl_bytes.decode('utf-8')
                alphabet_dl = [int(x) for x in alphabet_dl_str.split(',')]
                exception_bit_string = bytes_to_bits(packed_exceptions_data, exceptions_padding)
                distance_list = decompress(exception_bit_string, BIT_PRECISION_CONFIG, alphabet_dl, L_dl)

            # основной заголовок
            main_header_data = f.read(struct.calcsize('!IIIBI'))
            eof_pos, len_alpha_main, original_len, padding_bits, len_packed_main = struct.unpack('!IIIBI', main_header_data)
            alphabet_main_bytes = f.read(len_alpha_main)
            compressed_data = f.read(len_packed_main)
            alphabet_main_str = alphabet_main_bytes.decode('utf-8')
            alphabet = [int(x) for x in alphabet_main_str.split(',')]
            bit_string_to_decompress = bytes_to_bits(compressed_data, padding_bits)

    except (FileNotFoundError, struct.error, EOFError):
        print(f"[!] Ошибка: Файл не найден или архив поврежден.")
        return
    # TODO
    alphabet = [int(x) for x in alphabet_main_str.split(',')]
    bit_string_to_decompress = bytes_to_bits(compressed_data, padding_bits)
    # Декодирование
    print("[*] ARI DEC...")
    mapped_decoded = decompress(bit_string_to_decompress, BIT_PRECISION_CONFIG, alphabet, original_len)

    # --- НАЧАЛО ИЗМЕНЕНИЙ (РАСПАКОВКА) ---
    # Обратное преобразование из плотного алфавита в исходные символы
    try:
        zle_decoded = [alphabet[i] for i in mapped_decoded]
    except IndexError:
        print("[!] Ошибка: Ошибка восстановления алфавита. Архив может быть поврежден.")
        return
    #zle_decoded = decompress(bit_string_to_decompress, BIT_PRECISION_CONFIG, alphabet, original_len)
    
    print("[*] ZLE DEC...")
    mtf_decoded = zle_decode(zle_decoded)
    
    print("[*] MTF DEC...")
    bwt_decoded = mtf_decode(mtf_decoded)
    
    print("[*] BWT DEC...")
    decoded_text = bwt_decode(bwt_decoded, eof_pos)
    
    if was_decapitalized and distance_list:
        print("[*] Восстановление капитализации...")
        try:
            # SPECIAL_CASES берутся из константы 
            decoded_text = cap.recapitalize(distance_list, decoded_text, SPECIAL_CASES)
        except Exception as e:
            print(f"[!] Что-то не так. Не удалось восстановить капитализацию: {e}. Текст сохранен в нижнем регистре.")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(decoded_text)

    print(f"[+] Распаковка завершена")
    print(f"[+] Исходный текст сохранен в: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Простой BWT-архиватор на Python.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Доступные команды")

    # сжатия
    parser_compress = subparsers.add_parser("compress", help="Сжать файл.")
    parser_compress.add_argument("input", type=str, help="Путь к исходному файлу.")
    parser_compress.add_argument("output", type=str, help="Путь к сжатому файлу.")
    # является ли текст декапитализированным, нужно ли его декапитализировать
    parser_compress.add_argument("-d", "--decapitalize", action="store_true", help="Применить декапитализацию")
    # распаковка
    parser_decompress = subparsers.add_parser("decompress", help="Распаковать файл.")
    parser_decompress.add_argument("input", type=str, help="Путь к сжатому файлу.")
    parser_decompress.add_argument("output", type=str, help="Путь к распакованному файлу.")
    args = parser.parse_args()

    if args.command == "compress":
        compress_file(args.input, args.output, use_decapitalize=args.decapitalize)
    elif args.command == "decompress":
        decompress_file(args.input, args.output)

if __name__ == "__main__":
    main()