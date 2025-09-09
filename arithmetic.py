import io
import arithmeticcoding

# библиотека работает с потоками байтов

def bits_to_bytes(bit_string: str) -> bytes:
    """Преобразует строку битов в байты."""
    # Дополняем строку нулями до длины, кратной 8
    padding_needed = (8 - len(bit_string) % 8) % 8
    padded_bit_string = bit_string + '0' * padding_needed
    
    # Создаем байтовый массив
    byte_array = bytearray()
    for i in range(0, len(padded_bit_string), 8):
        byte_chunk = padded_bit_string[i:i+8]
        byte_array.append(int(byte_chunk, 2))
    return bytes(byte_array)

def bytes_to_bits(byte_data: bytes) -> str:
    return ''.join(format(byte, '08b') for byte in byte_data)

def din_arithmetic_compression(source_message: list, bit_precision_config: int) -> str:
    max_symbol = max(source_message) if source_message else -1
    if max_symbol < 0:
        return ""
        
    init_freqs = arithmeticcoding.FlatFrequencyTable(max_symbol + 1)    
    freqs = arithmeticcoding.SimpleFrequencyTable(init_freqs)
    
    buffer = io.BytesIO()
    bitout = arithmeticcoding.BitOutputStream(buffer)
    enc = arithmeticcoding.ArithmeticEncoder(bit_precision_config, bitout)

    for symbol in source_message:
        enc.write(freqs, symbol)
        freqs.increment(symbol)
    
    enc.finish()
    while bitout.numbitsfilled != 0:
        bitout.write(0)
    compressed_bytes = buffer.getvalue()
    buffer.close()
    return bytes_to_bits(compressed_bytes)



def decompress(encoded_sequence: str, N: int, ordered_alphabet: list, message_len: int) -> list:
    if message_len == 0:
        return []

    compressed_bytes = bits_to_bytes(encoded_sequence)
    alphabet_size = len(ordered_alphabet)
    init_freqs = arithmeticcoding.FlatFrequencyTable(alphabet_size)

    freqs = arithmeticcoding.SimpleFrequencyTable(init_freqs)

    decoded_message = [] # символы из плотного алфавита
    buffer = io.BytesIO(compressed_bytes)
    bitin = arithmeticcoding.BitInputStream(buffer)
    dec = arithmeticcoding.ArithmeticDecoder(N, bitin)

    for _ in range(message_len):
        symbol = dec.read(freqs)
        decoded_message.append(symbol)
        freqs.increment(symbol)

    bitin.close()
    return decoded_message 