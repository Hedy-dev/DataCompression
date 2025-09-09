import pydivsufsort
import numpy as np

def bwt_suffix_arr(text: str) -> tuple[str, int]:
    # добавление специального символа конца текста # либо /x00
    if not text:
        return "", -1
    # if not text.endswith('#'):
    #     text += '#'
    text += '\x00'
    
    byte_array = (text).encode('utf-8')  
    n_bytes = len(byte_array)

    sa = pydivsufsort.divsufsort(np.frombuffer(byte_array, dtype=np.uint8).copy())

    bwt_bytes = np.empty(n_bytes, dtype=np.uint8)
    original_row_index = -1

    for i in range(n_bytes):
        suffix_start_index = sa[i]
        if suffix_start_index == 0:
            original_row_index = i
            bwt_bytes[i] = byte_array[n_bytes - 1]
        else:
            bwt_bytes[i] = byte_array[suffix_start_index - 1]

    if original_row_index == -1:
        raise RuntimeError("Original index not found.")

    return bwt_bytes.tobytes().decode('latin-1'), original_row_index

def bwt_decode(bwt_string: str, original_row_index: int) -> str:
    # декодирование BWT, с учетом наличия спец символа в конце

    if not bwt_string:
        return ""

    bwt_array = np.frombuffer(bwt_string.encode('latin-1'), dtype=np.uint8)
    n = len(bwt_array)

    char_counts = np.zeros(256, dtype=np.int32)
    for byte_val in bwt_array:
        char_counts[byte_val] += 1

    char_start_positions = np.zeros(256, dtype=np.int32)
    for i in range(1, 256):
        char_start_positions[i] = char_start_positions[i-1] + char_counts[i-1]

    lf_mapping = np.zeros(n, dtype=np.int32)
    for i in range(n):
        char = bwt_array[i]
        lf_mapping[i] = char_start_positions[char]
        char_start_positions[char] += 1

    decoded_array = np.empty(n, dtype=np.uint8)
    current_index = original_row_index

    for i in range(n - 1, -1, -1):
        decoded_array[i] = bwt_array[current_index]
        current_index = lf_mapping[current_index]

    decoded_bytes = decoded_array.tobytes()

    # Удаляем — символ конца строки
    hash_byte_value = ord('\x00')
    if decoded_bytes[-1] != hash_byte_value:
        raise ValueError("Decoded string does not end with expected null byte.")
    
    return decoded_bytes[:-1].decode('utf-8')