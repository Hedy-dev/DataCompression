import argparse
import json
import os
import struct  # Для упаковки длины заголовка в байты
from bwt import bwt_suffix_arr, bwt_decode
from mtf import mtf_encode, mtf_decode
from zle import zle_encode, zle_decode
from arithmetic import din_arithmetic_compression, decompress
#from tqdm import tqdm

# константа для точности ставим 32 бита, хотя можно было бы передавать ее в качестве параметра
BIT_PRECISION_CONFIG = 32
# заголовок в 8 байт (unsigned long long)
HEADER_LENGTH_BYTES = 8

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

def compress_file(input_path, output_path):
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

    # сжатие
    print("[*] BWT...")
    bwt_result, eof_pos = bwt_suffix_arr(text)
    
    print("[*] MTF...")
    mtf_result = mtf_encode(bwt_result)
    
    print("[*] ZLE...")
    zle_encoded = zle_encode(mtf_result)
    
    print("[*] ARI...может занять немного времени (минут)")
    zle_encoded_ari_bit_string = din_arithmetic_compression(zle_encoded, BIT_PRECISION_CONFIG)
    packed_data, padding_bits = bits_to_bytes(zle_encoded_ari_bit_string)

    # алфавит
    alphabet = list(dict.fromkeys(zle_encoded))
    header_data = {
        "eof_pos": eof_pos,
        "alphabet": alphabet,
        "original_len": len(zle_encoded), # L 
        "bit_precision": BIT_PRECISION_CONFIG,
        "padding_bits": padding_bits 
    }

    # ням
    header_json = json.dumps(header_data)
    header_bytes = header_json.encode('utf-8')

    # выходной файл
    with open(output_path, 'wb') as f:
        # длина заголовка (8 байт)
        f.write(struct.pack('!Q', len(header_bytes)))
        # заголовок
        f.write(header_bytes)
        # Записываем сжатые данные
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
            # длина заголовка
            packed_header_len = f.read(HEADER_LENGTH_BYTES)
            if not packed_header_len:
                print("[!] Ошибка: Архив поврежден.")
                return
            header_len = struct.unpack('!Q', packed_header_len)[0]
            # ням десериализация
            header_bytes = f.read(header_len)
            header_data = json.loads(header_bytes.decode('utf-8'))
            # метаданные
            eof_pos = header_data["eof_pos"]
            alphabet = header_data["alphabet"]
            original_len = header_data["original_len"] # Наша L
            bit_precision = header_data["bit_precision"]
            padding_bits = header_data["padding_bits"]
            # данные 
            compressed_data = f.read()
            bit_string_to_decompress = bytes_to_bits(compressed_data, padding_bits)
    except FileNotFoundError:
        print(f"[!] Ошибка: Файл не найден по пути {input_path}")
        return
    except (struct.error, json.JSONDecodeError):
        print(f"[!] Ошибка: Формат архива некорректен или файл поврежден")
        return
    # декодирование
    print("[*] ARI DEC...может занять немного времени (минут)")
    zle_decoded = decompress(bit_string_to_decompress, bit_precision, alphabet, original_len)
    
    print("[*] ZLE DEC...")
    mtf_decoded = zle_decode(zle_decoded)
    
    print("[*] MTF DEC...")
    bwt_decoded = mtf_decode(mtf_decoded)
    
    print("[*] BWT DEC...")
    decoded_text = bwt_decode(bwt_decoded, eof_pos)

    # запись результата в файл
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

    # распаковка
    parser_decompress = subparsers.add_parser("decompress", help="Распаковать файл.")
    parser_decompress.add_argument("input", type=str, help="Путь к сжатому файлу.")
    parser_decompress.add_argument("output", type=str, help="Путь к распакованному файлу.")
    args = parser.parse_args()

    if args.command == "compress":
        compress_file(args.input, args.output)
    elif args.command == "decompress":
        decompress_file(args.input, args.output)

if __name__ == "__main__":
    main()